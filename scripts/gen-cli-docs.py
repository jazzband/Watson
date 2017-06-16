#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect

from click.core import Command, Context
from click.formatting import HelpFormatter
from watson import cli as watson_cli
# from watson import watson


class MarkdownFormatter(HelpFormatter):

    def write_heading(self, heading):
        """Writes a heading into the buffer."""
        self.write('### {}\n'.format(heading))

    def write_usage(self, prog, args='', prefix='Usage: '):
        """Writes a usage line into the buffer.
        :param prog: the program name.
        :param args: whitespace separated list of arguments.
        :param prefix: the prefix for the first line.
        """
        self.write('```bash\n{} {} {}\n```\n'.format(prefix, prog, args))

    def write_text(self, text):
        """Writes re-indented text into the buffer.
        """

        should_indent = False
        rows = []

        for row in text.split('\n'):

            if should_indent:
                row = '    {}'.format(row)

            if '\b' in row:
                row = row.replace('\b', '', 1)
                should_indent = True
            elif not len(row.strip()):
                should_indent = False

            rows.append(row)

        self.write("{}\n".format('\n'.join(rows)))

    def write_dl(self, rows, **kwargs):
        """Writes a definition list into the buffer.  This is how options
        and commands are usually formatted.
        :param rows: a list of two item tuples for the terms and values.
        """
        rows = list(rows)
        self.write('\n')

        self.write('Flag | Help\n')
        self.write('-----|-----\n')

        for row in rows:
            self.write('`{}` | {}\n'.format(*row))
        self.write('\n')


class MkdocsContext(Context):

    @property
    def command_path(self):
        # Not so proud of it
        return 'watson {}'.format(self.command.name)

    def make_formatter(self):
        return MarkdownFormatter()


def main(rowsput):
    """Iterate over watson.cli commands,
    generate commands markdown documentation and
    write it to the rowsput file.
    """

    def is_click_command(obj):
        """A filter for click command objects"""

        if type(obj) is Command:
            return True
        return False

    content = '\n'.join((
        "<!-- ",
        "    This document has been automatically generated.",
        "    It should NOT BE EDITED.",
        "    To update this part of the documentation,",
        "    please type the following from the repository root:",
        "    $ make docs"
        "-->",
        "",
        "# Commands",
        "",
    ))

    # Iterate over commands to build docs
    for cmd_name, cmd in inspect.getmembers(watson_cli, is_click_command):

        ctx = MkdocsContext(cmd)
        formatter = MarkdownFormatter()
        cmd.format_help(ctx, formatter)

        # Each command is a section
        content += "## `{}`\n\n".format(cmd_name)
        content += ''.join(formatter.buffer)

    # Write the commands documentation file
    with open(rowsput, 'w') as f:
        f.write(content)


if __name__ == '__main__':

    commands_md = 'docs/user-guide/commands.md'
    main(commands_md)
