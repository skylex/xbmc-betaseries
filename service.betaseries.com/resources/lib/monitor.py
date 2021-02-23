#!/usr/bin/python
# coding: utf-8

import xbmc
import logging

logger = logging.getLogger(__name__)


class MyMonitor(xbmc.Monitor):
    """monitor settings change"""

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.action = kwargs["action"]

    def onSettingsChanged(self):
        logger.debug("onSettingsChanged")
        self.action()
