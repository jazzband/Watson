#!/bin/bash

set -euo pipefail

function print_help() {

  cat <<EOF
Usage: $0 shell-type

This script generates the auto completion receipt required by Bash or Zsh.
Since the generated receipt is only a wrapper around the click framework, this
results in correct tab completion, regardless of the currently used version
watson.

The argument shell-type must be either "bash" or "zsh".
EOF
}

# Parse command line parameters
if [[ $# -ne 1 ]]
then
  echo "Please provide exactly one input argument." >&2
  exit 1
fi

case $1 in
  -h|--help)
    print_help
    exit 0
    ;;
  bash)
    src_command="source"
    target_file="watson.completion"
    ;;
  zsh)
    src_command="source_zsh"
    target_file="watson.zsh-completion"
    ;;
  *)
    echo "Unknown argument '$1'. Please consult help text." >&2
    exit 1
esac

_WATSON_COMPLETE=$src_command watson > "$target_file" || true
