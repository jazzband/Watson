import inspect

from click.core import Command, Context
from click.formatting import HelpFormatter
from watson import cli as watson_cli


def is_click_command(obj):
    """A filter for click command objects"""

    if type(obj) is Command:
        return True
    return False


class MarkdownFormatter(HelpFormatter):

    def write_dl(self, rows, **kwargs):
        rows = list(rows)
        self.write('\n')

        self.write('Option | Help\n')
        self.write('-------|-----\n')

        for row in rows:
            self.write('`{}` | {}\n'.format(*row))


class MkdocsContext(Context):

    def make_formatter(self):
        return MarkdownFormatter()


md_content = """
<!-- This document has been automatically generated.
     It should NOT BE EDITED.
     To update this part of the documentation,
     please refer to Watson's documentation (sic!) -->

# Commands

"""

# Iterate over commands to build docs
for obj in inspect.getmembers(watson_cli, is_click_command):

    formatter = MarkdownFormatter()
    cmd = obj[0]
    doc = inspect.getdoc(obj[1])

    _cmd = obj[1]
    ctx = MkdocsContext(_cmd)
    _cmd.format_options(ctx, formatter)

    # Each command is a section
    md_content += "## {}\n\n".format(cmd)

    md_content += ''.join(formatter.buffer)

    should_indent = False
    cmd_docs = []

    for doc_row in doc.split('\n'):

        if should_indent:
            doc_row = '    {}'.format(doc_row)

        if '\b' in doc_row:
            doc_row = doc_row.replace('\b', '', 1)
            should_indent = True
        elif not len(doc_row.strip()):
            should_indent = False

        cmd_docs.append(doc_row)

    md_content += "{}\n\n\n".format('\n'.join(cmd_docs))

# Write the commands documentation file
with open('docs/user-guide/commands.md', 'w') as f:
    f.write(md_content)
