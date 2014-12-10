# -*- coding: utf-8 -*-

import os
import json

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser  # noqa

import arrow
import click

from .frames import Frames


class WatsonError(RuntimeError):
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
        """
        self._current = None
        self._old_state = None
        self._frames = None

        self._dir = click.get_app_dir('watson')

        self.config_file = os.path.join(self._dir, 'config')
        self.frames_file = os.path.join(self._dir, 'frames')
        self.state_file = os.path.join(self._dir, 'state')

        if 'frames' in kwargs:
            self.frames = kwargs['frames']

        if 'current' in kwargs:
            self.current = kwargs['current']

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
        else:
            raise WatsonError(
                "Impossible to open JSON file in {}".format(filename)
            )

    def _parse_date(self, date):
        return arrow.Arrow.utcfromtimestamp(date)

    def _format_date(self, date):
        if not isinstance(date, arrow.Arrow):
            date = arrow.get(date)

        return date.timestamp

    @property
    def config(self):
        """
        Return Watson's config as a dict-like object.
        """
        config = ConfigParser()
        config.read(self.config_file)

        if not config.has_option('crick', 'url') \
                or not config.has_option('crick', 'token'):
            raise WatsonError(
                "You must specify a remote URL and a token by putting it in "
                "Watson's config file at '{}'".format(self.config_file)
            )

        return config

    def save(self):
        """
        Save the state in the appropriate files. Create them if necessary.
        """
        try:
            if not os.path.isdir(self._dir):
                os.mkdir(self._dir)

            if self._current is not None and self._old_state != self._current:
                if self.is_started:
                    current = {
                        'project': self.current['project'],
                        'start': self._format_date(self.current['start'])
                    }
                else:
                    current = {}

                with open(self.state_file, 'w+') as f:
                    json.dump(current, f, indent=1)

            if self._frames and self._frames.changed:
                with open(self.frames_file, 'w+') as f:
                    json.dump(self.frames.dump(), f, indent=1)
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
            'start': start
        }

        if self._old_state is None:
            self._old_state = self._current

    @property
    def is_started(self):
        return bool(self.current)

    def start(self, project):
        if self.is_started:
            raise WatsonError(
                "Project {} is already started.".format(
                    self.current['project']
                )
            )

        if not project:
            raise WatsonError("No project given.")

        self.current = {'project': project}
        return self.current

    def stop(self):
        if not self.is_started:
            raise WatsonError("No project started.")

        old = self.current
        self.frames.add(old['project'], old['start'], arrow.now())
        self.current = None

        return old

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

    def push(self, force=False):
        import requests

        config = self.config

        dest = config.get('crick', 'url') + '/frames/'
        token = config.get('crick', 'token')

        frames = tuple(
            {
                'id': f.id,
                'index': i,
                'start': str(f.start),
                'stop': str(f.stop),
                'project': f.project.split('/')
            }
            for i, f in enumerate(self.frames)
        )

        new_frames = tuple(f for f in frames if f['id'] is None)

        if force:
            existing_frames = tuple(f for f in frames if f['id'] is not None)
        else:
            existing_frames = []

        headers = {
            'content-type': 'application/json',
            'Authorization': "Token {}".format(token)
        }

        if new_frames:
            data = json.dumps({'frames': new_frames})
            try:
                response = requests.post(
                    dest, data, headers=headers
                )
            except requests.ConnectionError:
                raise WatsonError("Unable to reach the server.")

            if response.status_code != 201:
                raise WatsonError(
                    "An error occured with the remote "
                    "server: {}".format(response.json())
                )

            ids = response.json()
            for frame, id in zip(new_frames, ids):
                index = frame['index']
                self.frames.replace(index, id=id)

        if existing_frames:
            data = json.dumps({'frames': existing_frames})
            try:
                response = requests.put(
                    dest, data, headers=headers
                )
            except requests.ConnectionError:
                raise WatsonError("Unable to reach the server.")

            if response.status_code != 200:
                raise WatsonError(
                    "An error occured with the remote server: "
                    "{}".format(response.json())
                )

        return new_frames
