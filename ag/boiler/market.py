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

        tz = get_localzone()
        now = datetime.now(tz)
        nowstr = now.strftime('%Y-%m-%d %H:%M:%S %Z')
        log.debug("got ticker data", now=nowstr, ticker=ticker)

        last = Decimal(ticker['last'])
        if self.against == 'USDT' or self.against == 'USD':
            symbol = '$'
            quant = Decimal('0.00')
        else:
            symbol = ''
            quant = Decimal('0.00000000')
        laststr = symbol + str(last.quantize(quant))
        log.debug("last trade", value=laststr)

        nowfile = path.join(dir, 'market.'+self.symbol+'-'+self.against+'.time')
        lastfile = path.join(dir, 'market.'+self.symbol+'-'+self.against+'.last')

        if path.exists(nowfile) and path.exists(lastfile):
            prev = True

            with open(nowfile, 'r') as infile:
                prev_now = datetime.fromtimestamp(int(infile.readline().strip()), tz=tz)

            with open(lastfile, 'r') as infile:
                prev_last = Decimal(infile.readline().strip())

            prev_permlink = self.make_permlink(prev_now)
            prev_nowstr =   prev_now.strftime('%Y-%m-%d %H:%M:%S %Z')

            change_price = last - prev_last
            if change_price < Decimal('0'):
                change_pricestr = symbol + str(change_price.copy_negate().quantize(quant))
            else:
                change_pricestr = symbol + str(change_price.quantize(quant))

            change_pct = (Decimal('100') * change_price / prev_last).quantize(Decimal('0.00'))
            if change_pct < Decimal('0'):
                change_pctstr = str(change_pct.copy_negate()) + '%'
            else:
                change_pctstr = str(change_pct) + '%'

            data = self.api.chartData(
                    pair=self.against+'_'+self.symbol,
                    start=int(prev_now.strftime("%s"))+1,
                    period=300
                    )

            highest = last
            lowest = last

            if len(data) < 0:
                raise ValueError("No data returned")
            elif len(data) == 1 and int(data[0]['date']) == 0:
                raise ValueError("Too soon! You must wait at least 5 minutes between summaries.")

            for row in data:
                high = Decimal(row['high'])
                if high > highest:
                    highest = high

                low = Decimal(row['low'])
                if low < lowest:
                    lowest = low

            higheststr = symbol + str(highest.quantize(quant))
            loweststr = symbol + str(lowest.quantize(quant))
        else:
            prev = False

        body = "Market Summary for " + self.symbol
        body += "\n=="
        body += "\n* All prices in *" + self.against + "*"
        body += "\n---"
        body += "\n"
        if prev:
            if change_pct > Decimal('0'):
                body += "\nUp " + change_pctstr
            elif change_pct < Decimal('0'):
                body += "\nDown " + change_pctstr
            else:
                body += "\nFlat"
            body += "\n-"
            body += "\n" + self.symbol + "** "
            if change_price > Decimal('0'):
                body += "gained " + change_pricestr
            elif change_price < Decimal('0'):
                body += "lost " + change_pricestr
            else:
                body += "had no change"
            body += "** since the [last market summary]"
            body += "(https://steemit.com/@" + account.id + "/" + prev_permlink + ")"
            if change_pct > Decimal('0'):
                body += ", a change of **" + change_pctstr + "**"
            elif change_pct < Decimal('0'):
                body += ", a change of **-" + change_pctstr + "**"
            body += "."
        else:
            body += "\n*This is the first market summary, so no previous comparison data is available.*"
        body += "\n"
        body += "\n* Last trade: *" + laststr + "*"
        if prev:
            body += "\n* Highest trade: *" + higheststr + "*"
            body += "\n* Lowest trade: *" + loweststr + "*"
        body += "\n"
        # TODO: insert chart here
        body += "\n---"
        body += "\n"
        body += "\n* Snapshot taken at *" + nowstr + "*"
        if prev:
            body += "\n* Previous snapshot: *[" + prev_nowstr + "]"
            body += "(https://steemit.com/@" + account.id + "/" + prev_permlink + ")*"
        body += "\n* Quote data from [Poloniex](http://poloniex.com)"
        body += "\n"
        body += "\n<center>Happy trading... stay tuned for the next summary!</center>"
        body += "\n"
        body += "\n---"
        body += "\n<center>*This market summary produced automatically by:"
        body += "\n[![Alpha Griffin logo](http://alphagriffin.com/usr/include/ag/favicon/favicon-128.png)"
        body += "\nAlpha Griffin Boiler bot](https://github.com/AlphaGriffin/boiler)"
        body += "\nv" + __version__ + "*</center>"

        permlink = self.make_permlink(now)
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

            with open(nowfile, 'w') as out:
                out.write(now.strftime("%s"))

            with open(lastfile, 'w') as out:
                out.write(str(last))

            return True

        else:
            log.error("Failed to post summary")
            return False

    def make_permlink(self, when):
        permlink = 'market-summary-' + self.symbol + '-' + self.against + '-' + when.strftime('%Y-%m-%d-%H-%M-%S-%Z')
        permlink = permlink.lower()  # STEEM permlinks must be all lowercase
        return permlink


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

