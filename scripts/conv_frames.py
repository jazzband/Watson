#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Convert the watson frames file from the old to new format and vice versa."""

from __future__ import print_function

import json
import os
import tempfile

import click


def main():
    app_dir = os.environ.get('WATSON_DIR', click.get_app_dir('watson'))
    frames_file = os.path.join(app_dir, 'frames')
    backup_file = frames_file + '.old'

    try:
        with open(frames_file) as fp:
            frames = json.load(fp)
    except Exception as exc:
        return "Error loading frames file: {}".format(exc)

    if frames:
        if isinstance(frames[0][0], int) and isinstance(frames[0][1], int):
            print("Converting frames to new format...")
            converted_frames = [[f[3], f[2], f[0], f[1], f[4], f[5]]
                                for f in frames]
        else:
            print("Converting frames to old format...")
            converted_frames = [[f[2], f[3], f[1], f[0], f[4], f[5]]
                                for f in frames]

        try:
            with tempfile.NamedTemporaryFile('w', delete=False) as tmpfp:
                json.dump(converted_frames, tmpfp, indent=1,
                          ensure_ascii=False)

            if os.path.exists(backup_file):
                return ("Backup file '{}' already exists. It will not be "
                        "overwritten. Aborting save.".format(backup_file))
            else:
                os.rename(frames_file, backup_file)

            os.rename(tmpfp.name, frames_file)
        finally:
            try:
                os.unlink(tmpfp.name)
            except:
                pass
    else:
        return "No frames found. Nothing to do."


if __name__ == '__main__':
    import sys
    sys.exit(main() or 0)
