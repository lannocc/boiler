==============
Steemit Boiler
==============

Python Steemit bot for automatically following people using specific tags.


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


Automatically Follow Users
--------------------------

To automatically follow users, you must specify one or more tags where boiler will look for new posts. For example, to follow all users posting in "bitcoin" and "life"::

    ./boiler follow bitcoin life

