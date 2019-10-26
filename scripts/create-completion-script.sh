#!/bin/bash

set -euo pipefail

function print_help() {

  cat <<EOF
Usage: $0 shell-type

This script generates the auto completion receipt required by Bash or Zsh and
automatically puts it into the systems folder. Since the receipt is only a
wrapper around the click framework, this results in correct tab completion,
regardless of the currently used version watson.

The argument shell-type must be either "bash" or "zsh".
EOF
}

# Parse command line parameters
if [[ $# -ne 1 ]]
then
  echo "Please provide exactly one input argument." >&2
  exit 1
fi

if [[ $1 == "-h" || $1 == "--help" ]]
then
  print_help
  exit 0
fi

case $1 in
  -h|--help)
    print_help
    exit 0
    ;;
  bash)
    src_command="source"
    ;;
  zsh)
    src_command="source_zsh"
    ;;
  *)
    echo "Unknown argument '$1'. Please consult help text." >&2
    exit 1
esac


# NOTE: Putting `sudo` in the very beginning might result in executing the
# wrong `watson` command or in a failure altogether. `sudo` changes the user
# to root and the root user might not be aware of the currently active virtual
# environment etc.
_WATSON_COMPLETE=$src_command watson | sudo tee /etc/bash_completion.d/watson >/dev/null
