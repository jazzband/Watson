# -*- coding: utf-8 -*-

import datetime
import json
import operator
import os
import uuid

from functools import reduce

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import arrow
import click
import requests

from .config import ConfigParser
from .frames import Frames
from .utils import deduplicate, make_json_writer, safe_save, sorted_groupby
from .version import version as __version__  # noqa


class WatsonError(RuntimeError):
    pass


class ConfigurationError(configparser.Error, WatsonError):
    pass


class Watson(object):
    def __init__(self, **kwargs):
        """
        :param frames: If given, should be a list representating the
                        frames.
                        If not given, the value is extracted
                        from the frames file.
        :type frames: list

        :param current: If given, should be a dict representating the
                        current frame.
                        If not given, the value is extracted
                        from the state file.
        :type current: dict

        :param config_dir: If given, the directory where the configuration
                           files will be
        """
        self._current = None
        self._old_state = None
        self._frames = None
        self._last_sync = None
        self._config = None
        self._config_changed = False

        self._dir = (kwargs.pop('config_dir', None) or
                     click.get_app_dir('watson'))

        self.config_file = os.path.join(self._dir, 'config')
        self.frames_file = os.path.join(self._dir, 'frames')
        self.state_file = os.path.join(self._dir, 'state')
        self.last_sync_file = os.path.join(self._dir, 'last_sync')

        if 'frames' in kwargs:
            self.frames = kwargs['frames']

        if 'current' in kwargs:
            self.current = kwargs['current']

        if 'last_sync' in kwargs:
            self.last_sync = kwargs['last_sync']

    def _load_json_file(self, filename, type=dict):
        """
        Return the content of the the given JSON file.
        If the file doesn't exist, return an empty instance of the
        given type.
        """
        try:
            with open(filename) as f:
                return json.load(f)
        except IOError:
            return type()
        except ValueError as e:
            # If we get an error because the file is empty, we ignore
            # it and return an empty dict. Otherwise, we raise
            # an exception in order to avoid corrupting the file.
            if os.path.getsize(filename) == 0:
                return type()
            else:
                raise WatsonError(
                    "Invalid JSON file {}: {}".format(filename, e)
                )
        except Exception as e:
            raise WatsonError(
                "Unexpected error while loading JSON file {}: {}".format(
                    filename, e
                )
            )

    def _parse_date(self, date):
        return arrow.Arrow.utcfromtimestamp(date).to('local')

    def _format_date(self, date):
        if not isinstance(date, arrow.Arrow):
            date = arrow.get(date)

        return date.timestamp

    @property
    def config(self):
        """
        Return Watson's config as a ConfigParser object.
        """
        if not self._config:
            try:
                config = ConfigParser()
                config.read(self.config_file)
            except configparser.Error as e:
                raise ConfigurationError(
                    "Cannot parse config file: {}".format(e))

            self._config = config

        return self._config

    @config.setter
    def config(self, value):
        """
        Set a ConfigParser object as the current configuration.
        """
        self._config = value
        self._config_changed = True

    def save(self):
        """
        Save the state in the appropriate files. Create them if necessary.
        """
        try:
            if not os.path.isdir(self._dir):
                os.makedirs(self._dir)

            if self._current is not None and self._old_state != self._current:
                if self.is_started:
                    current = {
                        'project': self.current['project'],
                        'start': self._format_date(self.current['start']),
                        'tags': self.current['tags'],
                    }
                else:
                    current = {}

                safe_save(self.state_file, make_json_writer(lambda: current))

            if self._frames is not None and self._frames.changed:
                safe_save(self.frames_file,
                          make_json_writer(self.frames.dump))

            if self._config_changed:
                safe_save(self.config_file, self.config.write)

            if self._last_sync is not None:
                safe_save(self.last_sync_file,
                          make_json_writer(self._format_date, self.last_sync))
        except OSError as e:
            raise WatsonError(
                "Impossible to write {}: {}".format(e.filename, e)
            )

    @property
    def frames(self):
        if self._frames is None:
            self.frames = self._load_json_file(self.frames_file, type=list)

        return self._frames

    @frames.setter
    def frames(self, frames):
        self._frames = Frames(frames)

    @property
    def current(self):
        if self._current is None:
            self.current = self._load_json_file(self.state_file)

        if self._old_state is None:
            self._old_state = self._current

        return dict(self._current)

    @current.setter
    def current(self, value):
        if not value or 'project' not in value:
            self._current = {}

            if self._old_state is None:
                self._old_state = {}

            return

        start = value.get('start', arrow.now())

        if not isinstance(start, arrow.Arrow):
            start = self._parse_date(start)

        self._current = {
            'project': value['project'],
            'start': start,
            'tags': value.get('tags') or []
        }

        if self._old_state is None:
            self._old_state = self._current

    @property
    def last_sync(self):
        if self._last_sync is None:
            self.last_sync = self._load_json_file(
                self.last_sync_file, type=int
            )

        return self._last_sync

    @last_sync.setter
    def last_sync(self, value):
        if not value:
            self._last_sync = arrow.get(0)
            return

        if not isinstance(value, arrow.Arrow):
            value = self._parse_date(value)

        self._last_sync = value

    @property
    def is_started(self):
        return bool(self.current)

    def start(self, project, tags=None, restart=False):
        if not project:
            raise WatsonError("No project given.")

        if self.is_started:
            raise WatsonError(
                "Project {} is already started.".format(
                    self.current['project']
                )
            )

        default_tags = self.config.getlist('default_tags', project)
        if not restart:
            tags = (tags or []) + default_tags

        self.current = {'project': project, 'tags': deduplicate(tags)}
        return self.current

    def stop(self):
        if not self.is_started:
            raise WatsonError("No project started.")

        old = self.current
        frame = self.frames.add(
            old['project'], old['start'], arrow.now(), tags=old['tags']
        )
        self.current = None

        return frame

    def cancel(self):
        if not self.is_started:
            raise WatsonError("No project started.")

        old_current = self.current
        self.current = None
        return old_current

    @property
    def projects(self):
        """
        Return the list of all the existing projects, sorted by name.
        """
        return sorted(set(self.frames['project']))

    @property
    def tags(self):
        """
        Return the list of the tags, sorted by name.
        """
        return sorted(set(tag for tags in self.frames['tags'] for tag in tags))

    def _get_request_info(self, route):
        config = self.config

        dest = config.get('backend', 'url')
        token = config.get('backend', 'token')

        if dest and token:
            dest = "{}/{}/".format(
                dest.rstrip('/'),
                route.strip('/')
            )
        else:
            raise ConfigurationError(
                "You must specify a remote URL (backend.url) and a token "
                "(backend.token) using the config command."
            )

        headers = {
            'content-type': 'application/json',
            'Authorization': "Token {}".format(token)
        }

        return dest, headers

    def _get_remote_projects(self):
        if not hasattr(self, '_remote_projects'):
            dest, headers = self._get_request_info('projects')

            try:
                response = requests.get(dest, headers=headers)
                assert response.status_code == 200

                self._remote_projects = response.json()
            except requests.ConnectionError:
                raise WatsonError("Unable to reach the server.")
            except AssertionError:
                raise WatsonError(
                    "An error occured with the remote "
                    "server: {}".format(response.json())
                )

        return self._remote_projects['projects']

    def pull(self):
        dest, headers = self._get_request_info('frames')

        try:
            response = requests.get(
                dest, params={'last_sync': self.last_sync}, headers=headers
            )
            assert response.status_code == 200
        except requests.ConnectionError:
            raise WatsonError("Unable to reach the server.")
        except AssertionError:
            raise WatsonError(
                "An error occured with the remote "
                "server: {}".format(response.json())
            )

        frames = response.json() or ()

        for frame in frames:
            frame_id = uuid.UUID(frame['id']).hex
            self.frames[frame_id] = (
                frame['project'],
                frame['start_at'],
                frame['end_at'],
                frame['tags']
            )

        return frames

    def push(self, last_pull):
        dest, headers = self._get_request_info('frames/bulk')

        frames = []

        for frame in self.frames:
            if last_pull > frame.updated_at > self.last_sync:
                frames.append({
                    'id': uuid.UUID(frame.id).urn,
                    'start_at': str(frame.start.to('utc')),
                    'end_at': str(frame.stop.to('utc')),
                    'project': frame.project,
                    'tags': frame.tags
                })

        try:
            response = requests.post(dest, json.dumps(frames), headers=headers)
            assert response.status_code == 201
        except requests.ConnectionError:
            raise WatsonError("Unable to reach the server.")
        except AssertionError:
            raise WatsonError(
                "An error occured with the remote server (status: {}). "
                "Response was:\n{}".format(
                    response.status_code,
                    response.text
                )
            )

        return frames

    def merge_report(self, frames_with_conflict):
        conflict_file_frames = Frames(self._load_json_file(
                                      frames_with_conflict, type=list))
        conflicting = []
        merging = []

        for conflict_frame in conflict_file_frames:
            try:
                original_frame = self.frames[conflict_frame.id]

                if original_frame != conflict_frame:
                    # frame from conflict frames file conflicts with frame
                    # from original frames file
                    conflicting.append(conflict_frame)

            except KeyError:
                # conflicting frame doesn't exist in original frame
                merging.append(conflict_frame)

        return conflicting, merging

    def report(self, from_, to, current=None, projects=None, tags=None,
               year=None, month=None, week=None, day=None):
        for start_time in (_ for _ in [day, week, month, year]
                           if _ is not None):
            from_ = start_time

        if from_ > to:
            raise WatsonError("'from' must be anterior to 'to'")

        if tags is None:
            tags = []

        if self.current:
            if current or (current is None and
                           self.config.getboolean(
                               'options', 'report_current')):
                cur = self.current
                self.frames.add(cur['project'], cur['start'], arrow.utcnow(),
                                cur['tags'], id="current")

        span = self.frames.span(from_, to)

        frames_by_project = sorted_groupby(
            self.frames.filter(
                projects=projects or None, tags=tags or None, span=span
            ),
            operator.attrgetter('project')
        )

        total = datetime.timedelta()

        report = {
             'timespan': {
                 'from': str(span.start),
                 'to': str(span.stop),
             },
             'projects': []
         }

        for project, frames in frames_by_project:
            frames = tuple(frames)
            delta = reduce(
                operator.add,
                (f.stop - f.start for f in frames),
                datetime.timedelta()
            )
            total += delta

            project_report = {
                'name': project,
                'time': delta.total_seconds(),
                'tags': []
            }

            tags_to_print = sorted(
                set(tag for frame in frames for tag in frame.tags
                    if tag in tags or not tags)
            )

            for tag in tags_to_print:
                delta = reduce(
                    operator.add,
                    (f.stop - f.start for f in frames if tag in f.tags),
                    datetime.timedelta()
                )

                project_report['tags'].append({
                    'name': tag,
                    'time': delta.total_seconds()
                })

            report['projects'].append(project_report)

        report['time'] = total.total_seconds()
        return report
