#!/usr/bin/env python3
# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

from datetime import datetime, timedelta
from decimal import Decimal
from time import sleep

from steem import Steem
from steem.blockchain import Blockchain
from steem.post import Post
from steembase.exceptions import PostDoesNotExist, RPCError

import ag.logging as log

from ag.boiler.config import account, mask
log.debug("Account credentials loaded", id=account.id, key=mask(account.key))


class Curation():

    def __init__(self, chain):
        self.chain = chain
        self.posts = {}                 # queue of curation candidates, keyed by post id
        self.first_vote = None          # time of our first vote (today)
        self.votes_today = 0            # number of times we have voted in the 24 hours since first_vote
        self.max_payout = Decimal("0")  # maximum pending payout ecountered today

    def watch(self, tags):
        log.info("Watching for new posts...")
        while True:
            stream = map(Post, self.chain.stream(filter_by=['comment']))

            try:
                for post in stream:
                    self.process()

                    if self.votes_today > 11:
                        wait = timedelta(hours=24) - (datetime.utcnow() - self.first_vote)
                        log.info("Maximum votes reached for today, going to sleep now", wait=wait)
                        sleep(wait)

                        self.first_vote = None
                        self.votes_today = 0
                        self.max_payout = Decimal("0")

                        break

                    if post.is_main_post():
                        log.debug("found a top-level post", post=post, elapsed=post.time_elapsed(), tags=post.tags, total_payout=post.get("total_payout_value"), pending_payout=post.get("pending_payout_value"))

                        for tag in tags:
                            if tag in post.tags:
                                log.info("found a possible curation candidate", post=post)
                                self.posts[post.identifier] = post
                                break

            except PostDoesNotExist as e:
                log.warn("Post has vanished", exception=e)

            except RPCError as e:
                log.error("RPC problem while streaming posts", exception=e)

    def process(self):
        try_again = {}

        local_max_payout = Decimal("0")
        local_max_post = None

        for key, post in self.posts.items():
            try:
                now = datetime.utcnow()

                if now - post['created'] >= timedelta(minutes=27):
                    if now - post['created'] < timedelta(minutes=30):
                        post.refresh()
                        payout = Decimal(post.get("pending_payout_value").amount)

                        if payout > local_max_payout:
                            local_max_payout = payout
                            local_max_post = post

                else:
                    try_again[post.identifier] = post

            except PostDoesNotExist as e:
                log.warn("Post has vanished", exception=e)

            except RPCError as e:
                log.error("RPC problem while refreshing post", exception=e)

        self.posts = try_again

        if local_max_post is not None and local_max_payout > self.max_payout:
            log.info("upvoting post", post=local_max_post, elapsed=local_max_post.time_elapsed(), payout=local_max_payout)
            local_max_post.upvote(voter=account.id)

            self.max_payout = local_max_payout
            self.votes_today += 1

            if self.first_vote is None:
                self.first_vote = now


def run(tags):
    log.info("Curate mode activated", tags=tags)

    if tags is None or len(tags) < 1:
        raise ValueError("You must specify at least one tag")

    log.debug("initializing...")
    steem = Steem(keys=[account.key])
    chain = Blockchain(steem)
    curation = Curation(chain)
    log.debug("ready", steem=steem, blockchain=chain)

    curation.watch(tags)


if __name__ == '__main__':
    from contextlib import suppress
    from sys import argv

    with suppress(KeyboardInterrupt):
        run(argv[1:])

