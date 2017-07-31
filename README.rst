==============
Steemit Boiler
==============

Python Steemit bot for automatically following people and making timely posts.


Dependencies
------------

Tested in Python 3.6 in Linux and OSX.

Requires the following Python modules installed::

* appdirs
* ag.logging (aka logpy: https://git.alphagriffin.com/AlphaGriffin/logpy)
* steemit


Setup
-----

To build and install this application to the local system::

    make all && sudo make install

The above command installs the python module and `boiler` command to your system.

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
```
    This post will be re-posted on Christmas day at 4:20 PM to the 'spam' and 'testing' tags.

    2017-12-25 16:20 spam testing
```

When running the bot in timely mode, it will first scan your post history to see if any timely posts are due (or overdue). It will then continuously scan for any new posts that you make::

    ./boiler timely


Support
-------

Alpha Griffin is just a couple guys working on cool projects in our spare time. If you need help, join our Gitter chat at https://gitter.im/AlphaGriffin/Lobby.

If you find this software useful, please consider a small STEEM donation to @lannocc.

