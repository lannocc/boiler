#!/usr/bin/env python3
# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

from datetime import datetime
from steem import Steem
from steem.account import Account
from steem.blockchain import Blockchain
from steem.commit import Commit
from steem.post import Post
from steem.utils import construct_identifier
from steembase.exceptions import PostDoesNotExist, RPCError

import ag.logging as log

from ag.boiler.__version__ import __version__
from ag.boiler.config import account as cred, mask
log.debug("Account credentials loaded", id=cred.id, key=mask(cred.key))


def run():
    log.info("Timely post mode activated")

    log.debug("initializing...")
    steem = Steem(keys=[cred.key])
    account = Account(cred.id, steem)
    chain = Blockchain(steem)
    commit = Commit(steem)
    log.debug("ready", steem=steem, account=account, blockchain=chain, commit=commit)

    # Because subsequent edits to a post show up as separate post entries in the blockchain,
    # we'll keep a list of candidates keyed by the post identifier which the edits share.
    candidates = {}

    log.info("Checking post history...")
    history = map(Post, account.history(filter_by=['comment']))

    # FIXME: use steem.get_posts() instead?

    for post in history:
        if post.is_main_post():
            log.debug("found a top-level post", post=post, tags=post.tags)

            if len(post.tags) == 2 and post.tags[0] == cred.id and post.tags[1] == cred.id:
                candidates[post.identifier] = post

    if len(candidates) > 0:
        log.debug("found one or more historical posts to process", posts=candidates)

        for key, post in candidates.items():
            result = process(commit, post)
            if result or result is None:
                del candidates[key]

    log.info("Watching for new posts...")
    while True:
        stream = map(Post, chain.stream(filter_by=['comment']))

        try:
            for post in stream:
                if post.is_main_post() and post.author == cred.id:
                    log.debug("found a top-level post", post=post, tags=post.tags)

                    if len(post.tags) == 2 and post.tags[0] == cred.id and post.tags[1] == cred.id:
                        candidates[post.identifier] = post

                for key, post in candidates.items():
                    result = process(commit, post)
                    if result or result is None:
                        del candidates[key]

        except PostDoesNotExist as e:
            log.warn("Post has vanished", exception=e)

        except RPCError as e:
            log.error("RPC problem while streaming posts", exception=e)


def process(commit, post):
    log.debug("checking post", post=post.__dict__)

    lines = post.body.splitlines()
    if len(lines) < 2:
        log.warn("this post appears to be empty or lacking timely data", post=post)
        return None

    timely = lines[-1].split(' ')
    if len(timely) < 3:
        log.warn("this post lacks timely data: <date> <time> <tag> ...", post=post)
        return None

    when = datetime.strptime('{} {}'.format(timely[0], timely[1]), '%Y-%m-%d %H:%M')

    if datetime.now() >= when:
        log.info("This post is boiling!", post=post)

        tags = timely[2:]
        meta = {'app' : 'boiler/{}'.format(__version__)}
        link = '-' + post.permlink

        if lines[-2] == '```':
            body = "\n".join(lines[:-2])
        else:
            body = "\n".join(lines[:-1])
        body += "\n*This post made timely by the [Alpha Griffin Boiler bot](http://git.alphagriffin.com/AlphaGriffin/boiler).*"

        newpost = commit.post(
                permlink = link,
                title = post.title,
                author = post.author,
                body = body,
                tags = tags,
                json_metadata = meta,
                self_vote = True
                )
        log.debug("new post committed!", result=newpost)

        body = "This post has boiled! Find it now: "
        body += "\n* https://steemit.com/"+tags[0]+"/@"+post.author+"/"+link
        body += "\n\n*Timely posts made possible by the [Alpha Griffin Boiler bot](http://git.alphagriffin.com/AlphaGriffin/boiler).*"

        meta['tags'] = [post.category, 'boiled']

        edited = commit.post(
                permlink = post.permlink
                title = post.title,
                author = post.author,
                body = body,
                tags = meta['tags'],
                json_metadata = meta,
                reply_identifier = construct_identifier(post["parent_author"], post["parent_permlink"])
                )
        log.debug("original post edited!", result=edited)

        return True

    else:
        return False


if __name__ == '__main__':
    from contextlib import suppress

    with suppress(KeyboardInterrupt):
        run()

