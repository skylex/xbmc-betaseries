#!/usr/bin/python
# coding: utf-8
# import web_pdb

import json
import xbmc
import xbmcaddon

import logging
from resources.lib import utilities
from resources.lib.kodiUtilities import notification, getString
from resources.lib import kodiUtilities
from resources.lib.media import Media
from resources.lib import globals

__addon__ = xbmcaddon.Addon("script.betaseries")
logger = logging.getLogger(__name__)


class MyPlayer(xbmc.Monitor):
    """Monitoring Kodi Notifications"""

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.action = kwargs["action"]
        self.service = kwargs["service"]
        self.Play = False
        logger.debug("Player Class Init")
        if self.service.update:
            self.ScanBSMarkedEpisode()

    def onNotification(self, sender, method, data):
        if sender == "xbmc":
            if method == "VideoLibrary.OnScanFinished":
                if self.service.update:
                    self.ScanBSMarkedEpisode()
            elif method == "Player.OnPlay":
                result = json.loads(data)
                logger.debug("OnPlay: " + str(result))
                if "item" in result:
                    if utilities.isEpisode(result["item"]["type"]) or utilities.isMovie(
                        result["item"]["type"]
                    ):
                        # in case Player.OnPlay comes to fast after Player.OnStop
                        xbmc.sleep(1000)
                        self.Play = True
            elif method == "Player.OnStop":
                result = json.loads(data)
                logger.debug("OnStop: " + str(result))
                # if viewing in file mode and playback stopped at the end
                if "item" in result and result["end"]:
                    item = result["item"]
                    if utilities.isEpisode(item["type"]):
                        episode = False
                        if "id" in item:
                            episode = Media(item["id"], 1, self.Play).get_media_info(
                                "episode"
                            )
                        elif (
                            "episode" in item
                            and "season" in item
                            and "showtitle" in item
                        ):
                            logstr = ""
                            tvdbid = globals.betaseriesapi.tvdbidFromTitle(
                                item["showtitle"], logstr
                            )
                            if tvdbid:
                                tvdbepid = globals.betaseriesapi.tvdbepidFromtvdbid(
                                    tvdbid,
                                    item["showtitle"],
                                    item["season"],
                                    item["episode"],
                                    logstr,
                                )
                                if tvdbepid:
                                    episode = Media(
                                        int(tvdbepid), 1, True
                                    ).get_media_info("episode")
                        if not episode and "title" in item:
                            episode = Media(item["title"], 1, True).get_media_info(
                                "episode"
                            )
                        # mark episode as watched
                        if episode:
                            logger.debug(episode)
                            self.action(episode, self.service)
                    elif utilities.isMovie(item["type"]):
                        movie = False
                        if "id" in item:
                            movie = Media(item["id"], 1, self.Play).get_media_info(
                                "movie"
                            )
                        elif "title" in item:
                            movie = Media(item["title"], 1, self.Play).get_media_info(
                                "movie"
                            )
                        # mark movie as watched
                        if movie:
                            self.action(movie, self.service)
                else:
                    # wait 1s to avoid setting Play=False before marking episode
                    xbmc.sleep(1000)
                self.Play = False
            elif method == "VideoLibrary.OnUpdate":
                result = json.loads(data)
                logger.debug("OnUpdate: " + str(result))
                if "playcount" in result:
                    if "item" in result:
                        item = result["item"]
                        if utilities.isEpisode(item["type"]):
                            logger.debug(
                                "episode status changed for library id = %s, playcount = %s"
                                % (item["id"], result["playcount"])
                            )
                            episode = Media(
                                item["id"], result["playcount"], self.Play
                            ).get_media_info("episode")
                            logger.debug(episode)
                            if episode:
                                if result["playcount"] == 0 and not episode["seen"]:
                                    # mark as downloaded
                                    episode["playcount"] = -1
                                    self.action(episode, self.service)
                                self.action(episode, self.service)
                                self.Play = False
                        elif utilities.isMovie(item["type"]):
                            logger.debug(
                                "movie status changed for library id = %s, playcount = %s"
                                % (item["id"], result["playcount"])
                            )
                            movie = Media(
                                item["id"], result["playcount"], self.Play
                            ).get_media_info("movie")
                            logger.debug(movie)
                            if movie:
                                # mark as watched or not, depending on playcount
                                self.action(movie, self.service)
                                self.Play = False

    # rechercher les episodes non marques
    def ScanBSMarkedEpisode(self):
        """Do self.action on recently added media in kodi based on lastdate treatment"""
        f = __addon__.getAddonInfo("path") + "/lastdate.tmp"
        try:
            with open(f, "r") as fic:
                lastdate = fic.read()
        except Exception:
            lastdate = "2001-01-01 00:00:00"
        newdate = lastdate
        new = False
        counter = 0
        # cree table de tous les episodes
        result_episodes = kodiUtilities.getEpisodesFromKodi()

        if "episodes" in result_episodes:
            logger.debug(
                "Start scanning BS for viewed episode and compare with Kodi database"
            )
            for media in result_episodes["episodes"]:
                # web_pdb.set_trace()
                ep_id = media["episodeid"]
                seen = False
                try:
                    tvshow = kodiUtilities.getEpisodeDetailsFromKodi(
                        ep_id, ["dateadded", "playcount"]
                    )
                    if tvshow["playcount"] > 0:
                        seen = True
                except Exception as e:
                    logger.error(f"getEpisodeDetailsFromKodi error for {ep_id} : {e}")
                    # passe au suivant si erreur
                    continue

                if tvshow["dateadded"] > lastdate:
                    new = True
                    if tvshow["dateadded"] > newdate:
                        newdate = tvshow["dateadded"]
                # 0101 voir pour l'interet de not seen
                if new:  # or not seen:
                    # si pas vu, regarder sur BS si marque

                    episode = Media(ep_id, -1, self.Play).get_media_info("episode")
                    if episode:
                        if seen:
                            episode["playcount"] = 1
                        # follow ?    # downloaded ?
                        if not episode["followed"] or not episode["downloaded"]:
                            self.action(episode, self.service)
                        if episode["tvshow_playcount"] < 1 and episode["seen"]:
                            result = kodiUtilities.setEpisodeDetailsOnKodi(
                                ep_id, {"playcount": 1}
                            )
                            logger.info(
                                f"info :{episode['showtitle']},{episode['title']}"
                            )
                            if result == "OK":
                                # logger.info(result,)
                                logger.info(
                                    "episode marked watched or downloaded on BetaSeries.com",
                                )
                                counter += 1
                            else:
                                logger.error(
                                    "error: failed to mark watched or downloaded on Betaseries.com",
                                )
            if counter > 0:
                # xbmc.executebuiltin((u'Notification(%s,%s,%s,%s)' % (ADDON_NAME, ("Marked " + str(counter) + "episode(s) as watched"), 750, ADDON_ICON)).encode('utf-8', 'ignore'))
                notification(getString(32010), getString(30021, str(counter)))
            else:
                logger.info("Scan finished, all episodes updated")
            with open(f, "w") as fic:
                fic.write(newdate)

    # def ScanRecentlyadded(self):
    #     """Do self.action on recently added media in kodi based on lastdate treatment"""
    #     f = __addon__.getAddonInfo("path") + "/lastdate.tmp"
    #     try:
    #         with open(f, "r") as fic:
    #             lastdate = fic.read()
    #     except Exception:
    #         lastdate = "2001-01-01 00:00:00"
    #     newdate = lastdate
    #     result_episodes = kodiUtilities.GetRecentlyAddedEpisodesFromKodi(
    #         {"properties": ["dateadded"]}
    #     )
    #     if result_episodes:
    #         logger.debug(
    #             "Start scanning Kodi database for recent files and update BS for downloaded episode"
    #         )
    #         # logger.debug("VideoLirary GetRecentlyAddedEpisodes : %s" % result_episodes['result']['episodes'])
    #         for episode in result_episodes:
    #             if episode["dateadded"] > lastdate:
    #                 if episode["dateadded"] > newdate:
    #                     newdate = episode["dateadded"]
    #                 logger.debug(
    #                     f"{episode['label']} with id {episode['episodeid']} has been added {episode['dateadded']}"
    #                 )
    #                 episode = Media(episode["episodeid"], -1, self.Play).get_media_info(
    #                     "episode"
    #                 )
    #                 if episode:
    #                     if not episode["downloaded"]:
    #                         logger.debug("call service")
    #                         episode["playcount"] = -1
    #                         self.action(episode, self.service)
    #         with open(f, "w") as fic:
    #             fic.write(newdate)
    #     else:
    #         logger.debug(f"GetRecentlyAddedEpisodesFromKodi ERROR : {result_episodes}")
