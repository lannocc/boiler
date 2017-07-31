#!/usr/bin/env python3
# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

from steem import Steem
from steem.blockchain import Blockchain
from steem.post import Post
from steembase.exceptions import PostDoesNotExist, RPCError

import ag.logging as log

from ag.boiler.config import account, mask
log.debug("Account credentials loaded", id=account.id, key=mask(account.key))


def run(tags):
    log.info("Follow mode activated", tags=tags)

    if tags is None or len(tags) < 1:
        raise ValueError("You must specify at least one tag")

    log.debug("initializing...")
    steem = Steem(keys=[account.key])
    chain = Blockchain(steem)
    log.debug("ready", steem=steem, blockchain=chain)

    log.info("Watching for new posts...")
    while True:
        stream = map(Post, chain.stream(filter_by=['comment']))

        try:
            for post in stream:
                if post.is_main_post():
                    log.debug("found a top-level post", author=post.author, tags=post.tags)

                    for tag in tags:
                        if tag in post.tags:
                            log.info("following user", user=post.author)
                            steem.follow(post.author, account=account.id)
                            break

        except PostDoesNotExist as e:
            log.warn("Post has vanished", exception=e)

        except RPCError as e:
            log.error("RPC problem while streaming posts", exception=e)


if __name__ == '__main__':
    from contextlib import suppress
    from sys import argv

    with suppress(KeyboardInterrupt):
        run(argv[1:])

