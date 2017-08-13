#!/usr/bin/env python3
# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

from steem import Steem
from steem.account import Account
from steem.blockchain import Blockchain
from steem.post import Post
from steembase.exceptions import PostDoesNotExist, RPCError

import ag.logging as log

from ag.boiler.config import account as cred, mask
log.debug("Account credentials loaded", id=cred.id, key=mask(cred.key))
from ag.boiler.utils import have_bandwidth


def run(tags):
    log.info("Follow mode activated", tags=tags)

    if tags is None or len(tags) < 1:
        raise ValueError("You must specify at least one tag")

    log.debug("initializing...")
    steem = Steem(keys=[cred.key])
    account = Account(cred.id, steem)
    chain = Blockchain(steem)
    log.debug("ready", steem=steem, account=account, blockchain=chain)

    log.info("Gathering our following list...")
    following = account.get_following()
    pending = []
    log.info("Following list retrieved", count=len(following))

    log.info("Watching for new posts...")
    while True:
        stream = map(Post, chain.stream(filter_by=['comment']))

        try:
            for post in stream:
                count = len(pending)
                if count > 0:
                    copy = list(pending)
                    for i in range(count):
                        if have_bandwidth(steem, account):
                            user = copy[i]
                            log.info("following user", user=user)
                            steem.follow(user, account=cred.id)
                            del pending[i]

                        else:
                            log.warn("Waiting for more bandwidth before following another user")
                            break


                if post.is_main_post():
                    log.debug("found a top-level post", author=post.author, tags=post.tags)

                    for tag in tags:
                        if tag in post.tags:
                            if post.author not in following:
                                pending.append(post.author)
                                following.append(post.author)
                                break

        except PostDoesNotExist as e:
            log.debug("Post has vanished", exception=e)

        except RPCError as e:
            log.error("RPC problem while streaming posts", exception=e)


if __name__ == '__main__':
    from contextlib import suppress
    from sys import argv

    with suppress(KeyboardInterrupt):
        run(argv[1:])

