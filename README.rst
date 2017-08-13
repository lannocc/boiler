==============
Steemit Boiler
==============

Python Steemit bot for automatically following people, making timely posts, maximizing curation rewards, and posting market summaries.


Dependencies
------------

Tested in Python 3.6 in Linux and OSX.

Requires the following Python modules installed:

* appdirs
* ag.logging (aka logpy: https://git.alphagriffin.com/AlphaGriffin/logpy)
* matplotlib (for market mode graphs)
* steemit


Setup
-----

To build and install this application to the local system::

    make all && sudo make install

The above command installs the python module and ``boiler`` command to your system.

Alternatively, you can run the application in-place without installing::

    ./boiler

Without any arguments this command will display the usage help.


Account Credentials
-------------------

When you first enter follow mode (see next section) you will be asked for your account credentials, specifically your Account ID (Steemit username) and Private Posting Key. To get your Private Posting Key, go to your account permission page (https://steemit.com/@your_username/permissions), and click "Show Private Key" for the "Posting" key. This is the key you will enter into Boiler when prompted.

WARNING: Boiler stores these credentials unencrypted in your user home directory. A future release will encrypt these files or utilize the `steempy` client for credential management.


Automatically Follow Users
--------------------------

To automatically follow users, you must specify one or more tags where boiler will look for new posts. For example, to follow all users posting in "bitcoin" and "life"::

    ./boiler follow bitcoin life


Timely Posting
--------------

This bot can re-post a post at a time you specify. Simply craft a normal post with the following additional characteristics:

1. **Tag it to your username**. Your username must be the only tag.
2. **Add timely data on the last line**. The last line of your post must contain the date, time and tags that define when and where it will be re-posted. Here's an example::

    This post will be re-posted on Christmas day at 4:20 PM to the 'spam' and 'testing' tags.

    2017-12-25 16:20 spam testing

When running the bot in timely mode, it will first scan your post history to see if any timely posts are due (or overdue). It will then continuously scan for any new posts that you make::

    ./boiler timely


Curate Posts
------------

This bot can attempt to maximize curation rewards by voting on posts that are between 27 and 30 minutes old, up to 11 votes per day. The algorithm looks for posts in the tags you specify with successively higher pending payouts::

    ./boiler curate bitcoin life


Summarize the Market
--------------------

This bot can automatically post a cryptocurrency market summary for any given currency pair. Poloniex is used for market data, so the pair must exist there. If there is an RPC error while posting (usually because you've exceeded your STEEM bandwidth allocation) then it will keep trying every minute for up to an hour. To summarize a market, simply invoke market mode with a currency pair, post title, and tag(s)::

    ./boiler market btc-usdt "Summarizing the Bitcoin Market" bitcoin spam

The title you specify will be appended with a colon character followed by the latest action.


Support
-------

Alpha Griffin is just a couple guys working on cool projects in our spare time. Join our Gitter chat (https://gitter.im/AlphaGriffin/Lobby) for help, suggestions, or just to see what we're up to.

If you find this software useful, please consider a small STEEM donation to @lannocc .

