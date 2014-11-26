# -*- coding: utf-8 -*-

import os
import json

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser  # noqa

import arrow

WATSON_FILE = os.path.join(os.path.expanduser('~'), '.watson')
WATSON_CONF = os.path.join(os.path.expanduser('~'), '.watson.conf')


class WatsonError(RuntimeError):
    pass


class Watson(object):
    def __init__(self, content=None, filename=WATSON_FILE):
        self.filename = filename
        self.tree = None
        self._current = None

        self._load(content)

    def _load(self, content=None):
        """
        Initialize the class attributes from `content`.

        :param content: If given, should be a dict obtained by parsing a
                        Watson file. If not given, the content is extracted
                        from the Watson file.
        :type content: dict
        """
        if content is None:
            content = self._load_watson_file()

        self.tree = {'projects': content.get('projects', {})}
        self.current = content.get('current')

    def _load_watson_file(self):
        """
        Return the content of the current Watson file as a dict.
        If the file doesn't exist, return an empty dict.
        """
        try:
            with open(self.filename) as f:
                return json.load(f)
        except IOError:
            return {}
        except ValueError as e:
            # If we get an error because the file is empty, we ignore
            # it and return an empty dict. Otherwise, we raise
            # an exception in order to avoid corrupting the file.
            if os.path.getsize(self.filename) == 0:
                return {}
            else:
                raise WatsonError(
                    "Invalid Watson file {}: {}".format(self.filename, e)
                )
        else:
            raise WatsonError(
                "Impossible to open Watson file in {}".format(self.filename)
            )

    @property
    def config(self):
        """
        Return Watson's config as a dict-like object.
        """
        config = ConfigParser()
        config.read(WATSON_CONF)

        if ('crick' not in config or
                not all(k in config['crick'] for k in ('url', 'token'))):
            raise WatsonError(
                "You must specify a remote URL and a token by putting it in"
                "Watson's config file at '{}'".format(WATSON_CONF)
            )

        return config

    def dump(self):
        """
        Return a new dict which can be saved in the Watson file.
        """
        content = dict(self.tree)

        if self.is_started:
            current = self.current
            content['current'] = {
                'project': current['project'],
                'start': str(current['start'])
            }

        return content

    def save(self):
        """
        Save the given dict in the Watson file. Create the file in necessary.
        """
        try:
            with open(self.filename, 'w+') as f:
                json.dump(self.dump(), f, indent=2)
        except OSError:
            raise WatsonError(
                "Impossible to open Watson file in {}".format(self.filename)
            )

    @property
    def current(self):
        if not self._current:
            return None

        return dict(self._current)

    @current.setter
    def current(self, value):
        if not value or 'project' not in value:
            self._current = None
            return

        start = arrow.get(value.get('start', arrow.now()))

        self._current = {
            'project': value['project'],
            'start': start
        }

    @property
    def is_started(self):
        return self.current is not None

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

    def stop(self, message=None):
        if not self.is_started:
            raise WatsonError("No project started.")

        old = self.current
        project = self.project(old['project'])
        self.current = None

        frame = {
            'start': str(old['start']),
            'stop': str(arrow.now())
        }

        if message:
            frame['message'] = message

        project['frames'].append(frame)

        return old

    def cancel(self):
        if not self.is_started:
            raise WatsonError("No project started.")

        self.current = None

    def project(self, name):
        """
        Return the project from the projects tree with the given name. The name
        can be separated by '/' for sub-projects.
        """
        project = self.tree
        for name in name.split('/'):
            if name not in project['projects']:
                project['projects'][name] = {'frames': [], 'projects': {}}
            project = project['projects'][name]

        return project

    def projects(self):
        """
        Return the list of all the existing projects, sorted by name.
        """
        def get_projects(project, parent):
            result = []

            for name, child in project.get('projects', {}).items():
                name = parent + name
                result.append(name)
                result += get_projects(child, name + '/')

            return result

        return sorted(get_projects(self.tree, ''))

    def frames(self, upstream=False):
        """
        Return a list of all the frames, sorted by start time.

        :param upstream: If True, return only the frames that where pushed
                         to the server. If False, returns only the new frames.
                         Default to False.
        :type upstream: bool
        """
        def get_frames(parent, ancestors):
            frames = []

            for name, project in parent['projects'].items():
                for frame in project['frames']:
                    if 'id' in frame:
                        if not upstream:
                            continue
                    else:
                        if upstream:
                            continue

                    frame['project'] = ancestors + [name]
                    frames.append(frame)

                frames += get_frames(project, ancestors + [name])
            return frames

        return sorted(get_frames(self.tree, []), key=lambda e: e['start'])

    def push(self, force=False):
        import requests

        config = self.config

        dest = config['crick']['url'] + '/frames/'
        token = config['crick']['token']

        new_frames = self.frames(upstream=False)

        if force:
            existing_frames = self.frames(upstream=True)
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

            for frame, _id in zip(new_frames, ids):
                frame['id'] = _id
                del frame['project']

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
