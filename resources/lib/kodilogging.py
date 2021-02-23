# coding: utf-8

from resources.lib.kodiUtilities import getSettingAsBool

import logging
import xbmc
import xbmcaddon


class KodiLogHandler(logging.StreamHandler):
    """Generate Handler for logging

    Args:
        logging (logging.StreamHandler): informations about logging
    """

    def __init__(self):
        logging.StreamHandler.__init__(self)
        addon_id = xbmcaddon.Addon().getAddonInfo("id")
        prefix = f"[{addon_id}] "
        formatter = logging.Formatter(prefix + "%(name)s: %(message)s")
        self.setFormatter(formatter)

    def emit(self, record):
        levels = {
            logging.CRITICAL: xbmc.LOGFATAL,
            logging.ERROR: xbmc.LOGERROR,
            logging.WARNING: xbmc.LOGWARNING,
            logging.INFO: xbmc.LOGINFO,
            logging.DEBUG: xbmc.LOGDEBUG,
            logging.NOTSET: xbmc.LOGNONE,
        }
        if getSettingAsBool("betaverbose"):
            xbmc.log(self.format(record), levels[record.levelno])

    def flush(self):
        pass


def config():
    """generate logger"""
    logger = logging.getLogger()
    logger.addHandler(KodiLogHandler())
    logger.setLevel(logging.DEBUG)
