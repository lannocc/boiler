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
    print("   curate <tag>...   - Actively curate posts in the specified tag(s)")
    print("   timely            - Actively watch for posts by you tagged to your username, remove them and re-post later")
    print("   market <pair> <title> <tag>...")
    print("                     - Automatically compose cryptocurrency market summary for the given currency pair,")
    print("                       using supplied title and tag(s)")
    print("   market-ath <pair> <price>")
    print("                     - Set all-time-high price for given currency pair.")
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

        from ag.boiler.follow import run
        run(argv[2:])

    elif argv[1] == 'curate':
        if len(argv) < 3:
            usage()
            exit(3)

        from ag.boiler.curate import run
        run(argv[2:])

    elif argv[1] == 'timely':
        from ag.boiler.timely import run
        run()

    elif argv[1] == 'market':
        if len(argv) < 5:
            usage()
            exit(4)

        from ag.boiler.market import run
        run(argv[2:])

    elif argv[1] == 'market-ath':
        if len(argv) != 4:
            usage()
            exit(5)

        from ag.boiler.market import all_time_high
        all_time_high(argv[2], argv[3])

    else:
        log.error("unknown command", command=argv[1])
        print("boiler: unknown command: " + argv[1])
        usage()
        exit(99)

