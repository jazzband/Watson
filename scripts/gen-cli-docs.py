import inspect

from click.core import Command
from watson import cli as watson_cli


def is_click_command(obj):
    """A filter for click command objects"""

    if type(obj) is Command:
        return True
    return False

commands_rst = """.. This document has been automatically generated.
   It should NOT BE EDITED.
   To update this part of the documentation,
   please refer to Watson's documentation (sic!)

Commands
########

"""

# Iterate over commands to build docs
for obj in inspect.getmembers(watson_cli, is_click_command):

    cmd = obj[0]
    doc = inspect.getdoc(obj[1])

    # Each command is a section
    commands_rst += "``{}``\n{}\n\n".format(cmd, "=" * (len(cmd) + 4))

    # Escaped paragraph should be considered as litteral blocks
    doc = doc.replace('\b', '::\n', 1)

    # Indent litteral block if any
    sp = doc.split('\n')
    if '::' in sp:
        idx = sp.index('::')

        doc = '\n'.join(sp[:idx])
        doc += "\n::\n"

        for r in sp[idx+1:]:
            doc += '\t{}\n'.format(r)

    # Add substituted docs
    commands_rst += "{}\n\n\n".format(doc)

# Write the commands documentation file
with open('docs/commands.rst', 'w') as f:
    f.write(commands_rst)
