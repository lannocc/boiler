# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@
#
# Taken from https://pastebin.com/fbkheaRb and modified.

import requests
import json
import time

def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))

class Poloniex:

    timeout = 30  # seconds to wait for a response

    def __init__(self):
        pass

    def post_process(self, before):
        after = before

        # Add timestamps if there isnt one but is a datetime
        if('return' in after):
            if(isinstance(after['return'], list)):
                for x in xrange(0, len(after['return'])):
                    if(isinstance(after['return'][x], dict)):
                        if('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):
                            after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))
                            
        return after

    def api(self, command, req={}):

        if(command == "returnTicker" or command == "return24Volume"):
            ret = requests.get('https://poloniex.com/public?command=' + command, timeout=self.timeout)
            return ret.json()

        else:
            url = 'https://poloniex.com/public?command=' + command

            for key, data in req.items():
                url += '&' + key + '=' + str(data)

            ret = requests.get(url, timeout=self.timeout)
            return ret.json()

    def ticker(self):
        return self.api("returnTicker")

    def marketVolume(self):
        return self.api("return24Volume")

    def chartData(self, pair, start, period=300, end=None):
        if end is not None:
            return self.api("returnChartData", {"currencyPair":pair, "start":start, "period":period, "end":end})
        else:
            return self.api("returnChartData", {"currencyPair":pair, "start":start, "period":period})

