# Frequently Asked Questions

## Can I delete all my frames?

Yes! To do so, delete the `frames` file in your configuration folder (see [configuration](user-guide/configuration.md) to find its location).

## what is a frame? 

A frame it's a single logging unit that gets created when you issue the start command

## what to do if I forgot to start the watson when I started working?

You have a couple of options:
If you are still working on the project, you can use the watson start command, and then the watson edit command and change the starting time (the edit command defaults to the current or last frame if no frame is specified)
If you already finished working, you can use watson add to add frame
A start --at option is currently being developed

## what can I do if I forgot to stop watson when I finished working?

If you forgot to stop the project on time, you can specify an earlier stopping time with the --at option, like `watson stop --at 12:00:00`

## Can I import a project?

There is currently no "official" way to import frames from other projects, but you can see this link for a workaround:
https://github.com/TailorDev/Watson/issues/137

## Which python versions does watson support?

See setup.py and tox.ini

## Where does Watson store data?

Data is stored in a plain old JSON file, in the watson app directory usually. See: http://click.pocoo.org/5/api/#click.get_app_dir.
