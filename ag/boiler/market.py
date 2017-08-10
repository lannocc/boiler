#!/usr/bin/env python3
# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

from datetime import datetime, timedelta
from decimal import Decimal
from time import sleep
from tzlocal import get_localzone
from os import path

from steem import Steem
from steem.commit import Commit
from steembase.exceptions import RPCError

import ag.logging as log

from ag.boiler.__version__ import __version__
from ag.boiler.poloniex import Poloniex

from ag.boiler.config import account, mask, dir
log.debug("Account credentials loaded", id=account.id, key=mask(account.key))


class Market():

    def __init__(self, commit, api, pair, max_tries=60):
        self.commit = commit
        self.api = api
        self.max_tries = max_tries

        pair = pair.split('-')
        if len(pair) != 2:
            raise ValueError("Currency pair must be of the form XXX-YYY")

        self.symbol = pair[0].upper()
        self.against = pair[1].upper()

    def summarize(self, title, tags):
        log.info("Summarizing market...", symbol=self.symbol, against=self.against)

        ticker = self.api.ticker()
        try:
            ticker = ticker[self.against + '_' + self.symbol]
        except KeyError as e:
            log.error("Currency pair not found in ticker data", symbol=self.symbol, against=self.against, exception=e)
            raise ValueError("Currency pair not found in ticker data")

        now = datetime.now(get_localzone())
        nowstr = now.strftime('%Y-%m-%d %H:%M:%S %Z')
        log.debug("got ticker data", now=nowstr, ticker=ticker)

        last = Decimal(ticker['last'])
        if self.against == 'USDT' or self.against == 'USD':
            symbol = '$'
            laststr = symbol + str(last.quantize(Decimal('0.00')))
        else:
            symbol = ''
            laststr = str(last.quantize(Decimal('0.00000000')))
        log.debug("last trade", value=laststr)

        nowfile = path.join(dir, 'market.'+self.symbol+'-'+self.against+'.time')
        with open(nowfile, 'w') as out:
            out.write(now.strftime("%s"))

        lastfile = path.join(dir, 'market.'+self.symbol+'-'+self.against+'.last')
        with open(lastfile, 'w') as out:
            out.write(str(last))

        body = "Market Summary for " + self.symbol
        body += "\n=="
        body += "\n* All prices in *" + self.against + "*"
        body += "\n---"
        body += "\n"
        body += "\n*This is the first market summary, so no previous comparison data is available.*"
        body += "\n"
        body += "\n* Last trade: *" + laststr + "*"
        body += "\n"
        body += "\n---"
        body += "\n"
        body += "\n* Snapshot taken at *" + nowstr + "*"
        body += "\n* Quote data from [Poloniex](http://poloniex.com)"
        body += "\n"
        body += "\n<center>Happy trading... stay tuned for the next summary!</center>"
        body += "\n"
        body += "\n---"
        body += "\n<center>*This market summary produced automatically by:"
        body += "\n[![Alpha Griffin logo](http://alphagriffin.com/usr/include/ag/favicon/favicon-128.png)"
        body += "\nAlpha Griffin Boiler bot](https://github.com/AlphaGriffin/boiler)"
        body += "\nv" + __version__ + "*</center>"

        #print(body)

        permlink = 'market-summary-' + self.symbol + '-' + self.against + '-' + now.strftime('%Y-%m-%d-%H-%M-%S-%Z')
        permlink = permlink.lower()  # STEEM permlinks must be all lowercase
        tries = 0
        post = None

        while tries < self.max_tries:
            try:
                log.info("Posting summary...", permlink=permlink, title=title, last=laststr, tags=tags)

                post = self.commit.post(
                        permlink = permlink,
                        title = title,
                        author = account.id,
                        body = body,
                        tags = tags,
                        self_vote = True
                        )

                break

            except RPCError as e:
                log.warn("Got RPC error while posting, trying again in 1 minute...", exception=e)
                tries += 1
                sleep(60)

        if post is not None:
            log.info("Summary posted successfully", post=post)
            return True
        else:
            log.error("Failed to post summary")
            return False


def run(args):
    log.info("Market summary mode activated", args=args)

    if args is None or len(args) < 3:
        raise ValueError("You must specify a currency pair, title, and one or more tags")

    pair = args[0]
    title = args[1]
    tags = args[2:]

    log.debug("initializing...")
    steem = Steem(keys=[account.key])
    commit = Commit(steem)
    api = Poloniex()
    market = Market(commit, api, pair)
    log.debug("ready", steem=steem, commit=commit, api=api, market=market)

    market.summarize(title, tags)


if __name__ == '__main__':
    from contextlib import suppress
    from sys import argv

    with suppress(KeyboardInterrupt):
        run(argv[1:])

