# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

import ag.logging as log

from os import remove, path
from sys import stdin, stdout

from ag.boiler.config import dir

id = None
key = None

idfile = path.join(dir, 'account')
keyfile = path.join(dir, 'posting')


def save(id, key):
    if len(id) < 1:
        raise ValueError("Account ID cannot be empty!")
    if len(key) < 1:
        raise ValueError("Posting Private Key cannot be empty!")

    try:
        with open(idfile, 'w') as out:
            out.write(id)
            print("Saved Account ID to: " + idfile)
        with open(keyfile, 'w') as out:
            out.write(key)
            print("Saved Posting Private Key to: " + keyfile)

    except Exception as e:
        log.fatal("Failed to save account credentials", exception=e)

        try:
            if path.exists(idfile):
                remove(idfile)
        except Exception as ee:
            log.fatal("Error removing Account ID file!", exception=ee, file=idfile)

        try:
            if path.exists(keyfile):
                remove(keyfile)
        except Exception as ee:
            log.fatal("Error removing Posting Private Key file!", exception=ee, file=keyfile)

        raise e


if not path.exists(idfile) or not path.exists(keyfile):
    print("We need to set up your Steem credentials...")

    stdout.write("            Account ID: ")
    stdout.flush()
    id = stdin.readline().strip()
    if len(id) < 1:
        raise ValueError("Account ID cannot be empty!")

    stdout.write("   Posting Private Key: ")
    stdout.flush()
    key = stdin.readline().strip()
    if len(key) < 1:
        raise ValueError("Posting Private Key cannot be empty!")

    save(id, key)

    print()
    print("SECURITY: Your account credentials have been saved. Keep these files protected!")
    print()

with open(idfile, 'r') as infile:
    id = infile.readline().strip()
with open(keyfile, 'r') as infile:
    key = infile.readline().strip()

