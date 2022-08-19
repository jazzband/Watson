import warnings

from .watson import __version__  # noqa
from .watson import Watson, WatsonError

__all__ = ['Watson', 'WatsonError']

warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)
