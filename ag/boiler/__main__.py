# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

from contextlib import suppress

import ag.logging as log


def usage():
    print()
    print("Usage: boiler <command>")
    print()
    print("Where <command> is:")
    print("   help              - Display this usage screen")
    print("   follow <tag>...   - Actively follow users posting to the specified tag(s)")
    print("   timely            - Actively watch for posts by you tagged to your username, remove them and re-post later")
    print()

from sys import argv, exit

with suppress(KeyboardInterrupt):
    if len(argv) < 2:
        usage()
        exit(1)
        
    elif argv[1] == 'help':
        usage()

    elif argv[1] == 'follow':
        if len(argv) < 3:
            usage()
            exit(2)

        from ag.boiler.follow import run as follow
        follow(argv[2:])

    elif argv[1] == 'timely':
        from ag.boiler.timely import run as timely
        timely()

    else:
        log.error("unknown command", command=argv[1])
        print("boiler: unknown command: " + argv[1])
        usage()
        exit(99)

