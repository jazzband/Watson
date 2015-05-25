try:
    from watson import cli
except ImportError:
    from . import cli

cli.cli()
