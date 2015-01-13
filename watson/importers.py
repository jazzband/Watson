import abc


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
