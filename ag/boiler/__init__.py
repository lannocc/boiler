# Copyright (C) 2017 Alpha Griffin
# @%@~LICENSE~@%@
"""Alpha Griffin Python Starter Project

Python Steemit bot for automatically following people posting with specified tags.

.. module:: ag.boiler
   :platform: Unix
   :synopsis: Python Steemit bot for automatically following people posting with specified tags
.. moduleauthor:: Shawn Wilson <lannocc@alphagriffin.com>
"""

from ag.boiler.__version__ import __version__
print ("Steemit Boiler %s detected" % (__version__))

import ag.logging as log
log.set(log.INFO)

