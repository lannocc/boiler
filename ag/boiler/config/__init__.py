# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

import ag.logging as log

from os import mkdir, path

from appdirs import AppDirs
dirs = AppDirs("boiler", "Alpha Griffin")

dir = dirs.user_config_dir
log.debug("Starting up", configdir=dir)

if not path.exists(dir):
    log.info("Running first-time setup for configuration...")

    log.debug("Creating user config directory")
    mkdir(dir)

if not path.isdir(dir):
    log.fatal("Expected a directory for configdir", configdir=dir)
    raise Exception("Not a directory: " + dir)


def mask(secret):
    if secret is None:
        return ''
    elif len(secret) < 10:
        return '*' * len(secret)
    else:
        return secret[:3] + ('*' * (len(secret) - 6)) + secret[-3:]

