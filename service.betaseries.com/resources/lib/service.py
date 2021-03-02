#!/usr/bin/python
# coding: utf-8
# import web_pdb

import xbmc
import logging
from resources.lib.monitor import MyMonitor
from resources.lib.player import MyPlayer
from resources.lib.serviceapi import ServiceApi
from resources.lib import globals
from resources.lib.kodiUtilities import (
    getSettingAsBool,
    getSetting,
    notification,
    getString,
)

logger = logging.getLogger(__name__)


class betaseriesService:
    """Main Service"""

    def __init__(self):
        """instanciate class"""
        self.Monitor = MyMonitor(action=self.__get_settings)
        self.service = None
        self.__get_settings()

        while not xbmc.Monitor().abortRequested():
            xbmc.sleep(1000)

    def __get_settings(self):
        """get users settings and launch actions"""
        logger.debug("reading settings")
        self.service = globals.Service(
            getSettingAsBool("betaactive"),
            getSettingAsBool("betafirst"),
            getSetting("betauser"),
            getSetting("betapass"),
            getSettingAsBool("betabulk"),
            getSettingAsBool("betamark"),
            getSettingAsBool("betaunmark"),
            getSettingAsBool("betafollow"),
            getSettingAsBool("betanotify"),
            getSettingAsBool("betaupdate"),
        )
        if self.service.active and self.service.user and self.service.password:
            globals.betaseriesapi = ServiceApi(self)
            globals.betaseriesapi._service_authenticate(
                self.service.user, self.service.password
            )
            self.Player = MyPlayer(
                action=globals.betaseriesapi._service_betaserie, service=self.service
            )
            if self.service.notify:
                notification(getString(32010), getString(30003))
