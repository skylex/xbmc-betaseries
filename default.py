#!/usr/bin/python
# coding: utf-8
# import web_pdb; web_pdb.set_trace()
import logging
import xbmcaddon
from resources.lib import kodilogging
from resources.lib.service import betaseriesService
from resources.lib.kodiUtilities import setSetting, getSetting
from resources.lib.utilities import createError, checkIfNewVersion

__addon__ = xbmcaddon.Addon("script.betaseries")
__addonversion__ = __addon__.getAddonInfo("version")
__addonid__ = __addon__.getAddonInfo("id")
kodilogging.config()
logger = logging.getLogger(__name__)


logger.debug(f"Loading '{__addonid__}' version '{__addonversion__}'")
if checkIfNewVersion(str(getSetting("version")), str(__addonversion__)):
    setSetting("version", __addonversion__)

try:
    betaseriesService()
except Exception as ex:
    message = createError(ex)
    logger.fatal(message)

logger.debug(f"'{__addonid__}' shutting down.")
