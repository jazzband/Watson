import abc

from .watson import WatsonError


class BaseImporter(object):
    """
    The abstract class implemented by each importer.
    """
    __metaclass__ = abc.ABCMeta

    extensions = ()
    """
    All the file extensions (like 'json' or 'html') recognized by the importer
    """

    def __init__(self, exporter):
        """
        :param exporter: A function which will be called for each parsed frame.
                         It should accept the arguments `start`, `stop`,
                         `project` and some keyword arguments passed by
                         the importer (there is no constraint about those
                         keyword arguments)
        :type exporter: function
        """
        assert callable(exporter)
        self.exporter = exporter

    @abc.abstractmethod
    def parse(self, stream):
        """
        Parse an IO stream and call `exporter` for each parsed frame.
        """
        pass


class ICSImporter(BaseImporter):
    """
    Parse ICS (and ICal) calendar files. Requires the `icalendar` module.
    """

    extensions = ('ics', 'ical')

    def parse(self, stream):
        try:
            from icalendar import Calendar, Event
        except ImportError:
            raise WatsonError(
                "You need to have the 'icalendar' module installed to parse "
                "ICS files."
            )

        cal = Calendar.from_ical(stream.read())

        for event in (c for c in cal.subcomponents if isinstance(c, Event)):
            try:
                start = event['DTSTART'].dt
                stop = event['DTEND'].dt
                project = event['SUMMARY']
                uid = event.get('UID')
            except KeyError:
                continue

            self.exporter(start, stop, project, uid=uid)


IMPORTERS = (ICSImporter,)
"""
All the available importers
"""


def get_importer(ext, *args, **kwargs):
    """
    Return an instantiated importer able to parse the given extension, or
    `None` if no such importer is available.
    """
    ext = ext.lstrip('.')

    for importer in IMPORTERS:
        if ext in importer.extensions:
            return importer(*args, **kwargs)
