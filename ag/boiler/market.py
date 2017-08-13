#!/usr/bin/env python3
# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@

from datetime import datetime, timedelta
from decimal import Decimal
from time import sleep
from tzlocal import get_localzone
from os import path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import base64
import json
import io

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D, TICKLEFT, TICKRIGHT
from matplotlib.dates import DateFormatter
from steem import Steem
from steem.commit import Commit
from steembase.exceptions import RPCError

import ag.logging as log

from ag.boiler.__version__ import __version__
from ag.boiler.poloniex import Poloniex

from ag.boiler.config import account, mask, dir
log.debug("Account credentials loaded", id=account.id, key=mask(account.key))


class Market():

    testing = False

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

        if self.testing:
            log.info("TESTING MODE ENABLED")

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

        ath = None
        newath = False

        nowfile = path.join(dir, 'market.'+self.symbol+'-'+self.against+'.time')
        lastfile = path.join(dir, 'market.'+self.symbol+'-'+self.against+'.last')
        img_url = None

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

            highest = last
            lowest = last

            fig = plt.figure(figsize=(10,7), facecolor='k')
            ax = fig.add_subplot(1,1,1)
            rect = ax.patch
            rect.set_facecolor('k')
            img_title = self.symbol + '-' + self.against + ' at ' + nowstr
            plt.title(img_title)
            ax.xaxis_date()
            plt.xticks(rotation=25)
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M'))

            # first graph 30-minute candlesticks
            log.info("Plotting 30-minute candlesticks...")

            data = self.api.chartData(
                    pair=self.against+'_'+self.symbol,
                    start=int(prev_now.strftime("%s"))+1,
                    period=1800
                    )

            if len(data) < 0:
                raise ValueError("No data returned")
            elif len(data) == 1:
                try:
                    error = data['error']
                    log.error("Received error from API", error=error)
                    raise ValueError("Received error from API: {}".format(error))

                except KeyError:
                    if int(data[0]['date']) == 0:
                        raise ValueError("Too soon! You must wait at least 30 minutes between summaries for candlesticks.")

            for row in data:
                high = Decimal(row['high'])
                if high > highest:
                    highest = high

                low = Decimal(row['low'])
                if low < lowest:
                    lowest = low

                time = datetime.fromtimestamp(int(row['date']))
                popen = Decimal(row['open'])
                close = Decimal(row['close'])

                if close >= popen:
                    color = 'g'
                else:
                    color = 'r'

                vline = Line2D(xdata=(time, time), ydata=(low, high),
                        linewidth=1.5, color=color, antialiased=False)
                oline = Line2D(xdata=(time, time), ydata=(popen, popen),
                        linewidth=1, color=color, antialiased=False, marker=TICKLEFT, markersize=7)
                cline = Line2D(xdata=(time, time), ydata=(close, close),
                        linewidth=1, color=color, antialiased=False, marker=TICKRIGHT, markersize=7)

                ax.add_line(vline)
                ax.add_line(oline)
                ax.add_line(cline)

            # then graph 5-minute lines
            log.info("Plotting 5-minute lines...")

            data = self.api.chartData(
                    pair=self.against+'_'+self.symbol,
                    start=int(prev_now.strftime("%s"))+1,
                    period=300
                    )

            if len(data) < 0:
                raise ValueError("No data returned")
            elif len(data) == 1:
                try:
                    error = data['error']
                    log.error("Received error from API", error=error)
                    raise ValueError("Received error from API: {}".format(error))

                except KeyError:
                    if int(data[0]['date']) == 0:
                        raise ValueError("Too soon! You must wait at least 5 minutes between summaries.")

            begin = None

            for row in data:
                high = Decimal(row['high'])
                if high > highest:
                    highest = high

                low = Decimal(row['low'])
                if low < lowest:
                    lowest = low

                time = int(row['date'])
                popen = Decimal(row['open'])
                close = Decimal(row['close'])

                if begin is None:
                    begin = popen

                line = Line2D(xdata=(datetime.fromtimestamp(time), datetime.fromtimestamp(time + 300)), ydata=(begin, close),
                        linewidth=0.7, color='#FFFF00', antialiased=True)

                ax.add_line(line)
                begin = close

            higheststr = symbol + str(highest.quantize(quant))
            loweststr = symbol + str(lowest.quantize(quant))

            athfile = path.join(dir, 'market.'+self.symbol+'-'+self.against+'.ath')
            if path.exists(athfile):
                with open(athfile, 'r') as infile:
                    ath = Decimal(infile.readline().strip())

                if highest > ath:
                    ath = highest
                    newath = True

                    with open(athfile, 'w') as out:
                        out.write(str(ath))

            ax.xaxis.grid(True, color='#555555', linestyle='dotted')
            ax.yaxis.grid(True, color='#555555', linestyle='solid')
            plt.tight_layout()
            ax.autoscale_view()

            # save image to file or memory buffer
            if self.testing:
                imgfile = '/tmp/' + self.symbol + '-' + self.against + '.png'
                fig.savefig(imgfile)
                log.info("Market graph PNG saved", file=imgfile)
            else:
                img = io.BytesIO()
                fig.savefig(img, format='png')
                img.seek(0)

            plt.close(fig)

            # now upload result to imgur
            if not self.testing:
                log.info("Uploading plot to imgur...")

                img_b64 = base64.standard_b64encode(img.read())
                client = 'bbe2ecf93d88915'
                headers = {'Authorization': 'Client-ID ' + client}
                imgur_data = {'image': img_b64, 'title': img_title}
                req = Request(url='https://api.imgur.com/3/upload.json', data=urlencode(imgur_data).encode('ASCII'), headers=headers)
                resp = urlopen(req).read()
                resp = json.loads(resp)
                log.debug("Got response from imgur", resp=resp)

                if resp['success'] == True:
                    img_url = resp['data']['link']
                    log.info("Image uploaded successfully", url=img_url)

                else:
                    log.error("Non-successful response from imgur", resp=resp)
                    raise ValueError("Non-successful response from imgur")

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
                title += ": Up " + change_pctstr
            elif change_pct < Decimal('0'):
                body += "\nDown " + change_pctstr
                title += ": Down " + change_pctstr
            else:
                body += "\nFlat"
                title += ": Flat"
            if newath:
                body += " (New All Time High Achieved)"
                title += " -- New All Time High!"
            body += "\n-"
            body += "\n" + self.symbol + " **"
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
            if newath:
                body += " (new all time high)"
            body += "\n* Lowest trade: *" + loweststr + "*"
            if img_url is not None:
                body += "\n"
                body += "\n[![market activity plot](" + img_url + ")](" + img_url + ")"
        body += "\n"
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

        if self.testing:
            print(body)

        permlink = self.make_permlink(now)
        tries = 0
        post = None

        while tries < self.max_tries:
            try:
                log.info("Posting summary...", permlink=permlink, title=title, last=laststr, tags=tags)

                if self.testing:
                    log.warn("Not actually going to post (testing mode)")
                    break

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
            if not self.testing:
                log.error("Failed to post summary")

            return False

    def make_permlink(self, when):
        permlink = 'market-summary-' + self.symbol + '-' + self.against + '-' + when.strftime('%Y-%m-%d-%H-%M-%S-%Z')
        permlink = permlink.lower()  # STEEM permlinks must be all lowercase
        return permlink


def all_time_high(pair, price):
    pair = pair.split('-')
    if len(pair) != 2:
        raise ValueError("Currency pair must be of the form XXX-YYY")

    symbol = pair[0].upper()
    against = pair[1].upper()

    price = Decimal(price)
    file = path.join(dir, 'market.'+symbol+'-'+against+'.ath')

    log.info("Saving new all-time-high...", symbol=symbol, against=against, price=price, file=file)

    with open(file, 'w') as out:
        out.write(str(price))

    print("All-time-high saved successfully.")


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

