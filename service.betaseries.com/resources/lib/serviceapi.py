#!/usr/bin/python
# coding: utf-8
# import web_pdb

import logging
import hashlib
import json
import time
from resources.lib import utilities
from resources.lib.kodiUtilities import notification, getString  # , setSetting

logger = logging.getLogger(__name__)


class ServiceApi:
    """Class to exchange with betaseries.com api"""

    apikey = "2b78f54a7cc3"
    apiurl = "https://api.betaseries.com"
    apiver = "3.0"

    def __init__(self, betaseriesService):
        # web_pdb.set_trace()
        self.user = ""
        self.pw = ""
        self.bsService = betaseriesService
        self.token = ""
        self.auth_fail = False
        self.failurecount = 0
        self.timercounter = 0
        self.timerexpiretime = 0

    def __auth(self):
        """low level Authenticate into betaseries.com

        Returns:
            True or None
        """
        # create a pass hash
        md5pass = hashlib.md5()
        md5pass.update(self.pw.encode("utf8"))
        url = self.apiurl + "/members/auth"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "login": self.user,
            "password": md5pass.hexdigest(),
        }
        try:
            # authentication request
            response = utilities.get_urldata(url, urldata, "POST")
            # authentication response
            data = json.loads(response)
            logger.info("successfully authenticated")
        except Exception:
            logger.error("failed to connect for authentication")
            return None

        # parse results
        if "token" in data:
            # get token
            self.token = str(data["token"])
            # reset failure count
            self.failurecount = 0
            # reset timer
            self.timercounter = 0
            self.timerexpiretime = 0
        if data["errors"]:
            self.__checkerrors(data["errors"][0], auth=True)
            return None
        else:
            logger.debug("token find:" + self.token)
            notification(getString(32010), getString(32008))
            return True

    def __checkerrors(self, error, auth=False, infos=""):
        """treatment about error returned by betaseries API

        Args:
            error (dict): error returned by API
            auth (bool, optional): error occured during authentication process. Defaults to False.
            infos (str, optional): text to add to message. Defaults to "".
        Returns:
            True on real error
            False on non real error (informations returned by API with 0 code)
        """
        if auth is False and error["code"] == 0:
            return False
        if error["code"] < 2000:
            # API error
            notification(getString(32010), getString(32002))
            logger.warning(f"bad API usage : [{error['code']}] - {error['text']}")
            # disable the service, the monitor class will pick up the changes
            # setSetting("betaactive", "false")
        elif error["code"] > 4001:
            # login error
            notification(getString(32010), getString(32004))
            logger.warning("login or password incorrect")
            self.auth_fail = True
        elif error["code"] == 2001:
            # drop our session key
            self.token = ""
            logger.info("bad token")
            return True
        elif error["code"] == 2003:
            logger.info(f"already following show {infos}")
        # everything else
        elif auth is True:
            self.__service_fail(True)
            notification(getString(32010), getString(32001))
            logger.error("server error while authenticating")
            notification(getString(32010), getString(32009))
        else:
            notification(getString(32010), getString(32005, infos))
            logger.info(f"failed to follow show {infos}")
        return True

    def __service_fail(self, timer):
        """update informations when API auth failure

        Args:
            timer (bool): set a timer if failure occurred during authentication phase
        """
        timestamp = int(time.time())
        # increment failure counter
        self.failurecount += 1
        # drop our session key if we encouter three failures
        if self.failurecount > 2:
            self.token = ""
        # set a timer if failure occurred during authentication phase
        if timer:
            # wrap timer if we cycled through all timeout values
            if self.timercounter == 0 or self.timercounter == 7680:
                self.timercounter = 60
            else:
                # increment timer
                self.timercounter = 2 * self.timercounter
        # set timer expire time
        self.timerexpiretime = timestamp + self.timercounter

    def followFromtvdbid(self, tvdbid, showtitle, logstr):
        """Find if Show is followed

        Args:
            tvdbid (int): thetvdb_id for show
            showtitle (str): show title for message
            logstr (str): process information returned

        Returns:
            bool
        """
        url = self.apiurl + "/shows/display"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "token": self.token,
            "thetvdb_id": tvdbid,
        }
        try:
            tvdbid_query = utilities.get_urldata(url, urldata, "GET")
            tvdbid_query = json.loads(tvdbid_query)
            follow = tvdbid_query["show"]["in_account"]
            logstr += f" follow status: {follow}"
            return follow
        except Exception:
            logger.warning("could not get follow tvshow's status for " + showtitle)
        return False

    def tvdbidFromTitle(self, showtitle, logstr):
        """Find TVdbId from title for a Show

        Args:
            showtitle (str): show title
            logstr (str): process information returned

        Returns:
            int or None: TVdbId Show
        """
        url = self.apiurl + "/shows/list"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "token": self.token,
            "order": "popularity",
            "summary": "true",
            "starting": (showtitle.encode("ascii", "xmlcharrefreplace")).replace(
                " ", "+"
            ),
        }
        logger.info(urldata)
        try:
            tvdbid_query = utilities.get_urldata(url, urldata, "GET")
            tvdbid_query = json.loads(tvdbid_query)
            for found in tvdbid_query["shows"]:
                if (
                    found["title"] == showtitle
                    or found["title"].lower() == showtitle.lower()
                ):
                    if "thetvdb_id" in found:
                        tvdbid = found["thetvdb_id"]
                        logstr += "tvdbid: " + str(tvdbid)
                        return tvdbid
        except Exception:
            logger.info(logstr)
            logger.warning("No search result for tvshow's " + showtitle)

    def tvdbidFromimbd(self, imdbid, logstr):
        """Find TVdbId from imdbId for a Show

        Args:
            imdbid (int): thetvdb_id for show
            logstr (str): process information returned

        Returns:
            int or None: TVdbId Show
        """
        url = self.apiurl + "/shows/display"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "token": self.token,
            "imdb_id": imdbid,
        }
        try:
            tvdbid_query = utilities.get_urldata(url, urldata, "GET")
            tvdbid_query = json.loads(tvdbid_query)
            tvdbid = tvdbid_query["show"]["thetvdb_id"]
            logstr += f" convert to {tvdbid} "
        except Exception:
            logger.info(logstr)
            logger.error(f"Cannot convert from {imdbid}")
            return False
        return tvdbid

    def tvdbInfFromtvdbepid(self, tvdbepid, showtitle, logstr):
        """Find Information Episode from TVdbId episode

        Args:
            tvdbepid (int): TVdbId episode
            showtitle (str): show title for message
            logstr (str): process information returned

        Returns:
            dict: Betaseries information on media
        """
        url = self.apiurl + "/episodes/display"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "token": self.token,
            "thetvdb_id": tvdbepid,
        }
        try:
            tvdbid_query = utilities.get_urldata(url, urldata, "GET")
            tvdbid_query = json.loads(tvdbid_query)
            # logger.info(tvdbid_query)
            return tvdbid_query["episode"]
        except Exception:
            logger.info(logstr)
            logger.error("failed to get Episode information for " + showtitle)

    def tvdbidFromtvdbepid(self, tvdbepid, showtitle, logstr):
        """Find TVdbId Show from TVdbId episode

        Args:
            tvdbepid (int): TVdbId episode
            showtitle (str): show title for message
            logstr (str): process information returned

        Returns:
            int or None: TVdbId Show
        """
        showid = False
        url = self.apiurl + "/episodes/display"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "token": self.token,
            "thetvdb_id": tvdbepid,
        }
        try:
            tvdbid_query = utilities.get_urldata(url, urldata, "GET")
            tvdbid_query = json.loads(tvdbid_query)
            # logger.info(tvdbid_query)
            if "show" in tvdbid_query["episode"]:
                tvdbid = tvdbid_query["episode"]["show"]["thetvdb_id"]
                logstr += "\nBS tvdbid from tvdbepid: %s" % (tvdbid)
                return tvdbid
            else:
                showid = tvdbid_query["episode"]["show_id"]
        except Exception:
            logger.info(logstr)
            logger.error("failed to get show_id for " + showtitle)

        if showid:
            url = self.apiurl + "/shows/display"
            urldata = {
                "v": self.apiver,
                "key": self.apikey,
                "token": self.token,
                "id": showid,
            }
            try:
                tvdbid_query = utilities.get_urldata(url, urldata, "GET")
                tvdbid_query = json.loads(tvdbid_query)
                tvdbid = tvdbid_query["show"]["thetvdb_id"]
                logstr += f"\nBS tvdbid from tvdbepid: {tvdbid}"
                return tvdbid
            except Exception:
                logger.info(logstr)
                logger.error(
                    "could not fetch tvshow's thetvdb_id from show_id for " + showtitle
                )
        return False

    def tvdbepidFromtvdbid(self, tvdbid, showtitle, season, episode, logstr):
        """Find TVdbId episode from TVdbId show, season and episode num

        Args:
            tvdbid (int): TVdbId show
            showtitle (str): show title for message
            season (int): season number
            episode (int): episode number
            logstr (str): process information returned

        Returns:
            int or None: TVdbId Episode
        """
        epname = str(season) + "x" + str(episode)
        url = self.apiurl + "/shows/episodes"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "token": self.token,
            "thetvdb_id": tvdbid,
            "season": season,
            "episode": episode,
        }
        try:
            tvdbepid_query = utilities.get_urldata(url, urldata, "GET")
            tvdbepid_query = json.loads(tvdbepid_query)
            tvdbepid = tvdbepid_query["episodes"][0]["thetvdb_id"]
            logstr += f" tvdbepid: {tvdbepid} for Ep {epname}"
        except Exception:
            if logstr:
                logger.info(logstr)
            logger.error(
                f"could not fetch episode's thetvdb_id for {showtitle}-{epname}"
            )
            return False
        return tvdbepid

    def imdbFromId(self, showtitle, logstr):
        """Find imdbId from filename for a movie

        Args:
            showtitle (str): movie filename
            logstr (str): process information returned

        Returns:
            int or None: imdbId Show
        """
        url = self.apiurl + "/movies/scraper"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "token": self.token,
            "file": showtitle.encode("ascii", "xmlcharrefreplace").replace(" ", "+"),
        }
        logger.debug(urldata)
        try:
            tvdbid_query = utilities.get_urldata(url, urldata, "GET")
            tvdbid_query = json.loads(tvdbid_query)
            return tvdbid_query["movie"]
        except Exception:
            logger.info(logstr)
            logger.info(f"could not fetch movie's {showtitle} imdb_id")
        return False

    def imdbidFromTitle(self, showtitle, logstr):
        """Find imdbId from title for a movie

        Args:
            showtitle (str): movie title
            logstr (str): process information returned

        Returns:
            int or None: imdbId Show
        """
        url = self.apiurl + "/movies/scraper"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "token": self.token,
            "file": showtitle.encode("ascii", "xmlcharrefreplace").replace(" ", "+"),
        }
        logger.debug(urldata)
        try:
            tvdbid_query = utilities.get_urldata(url, urldata, "GET")
            tvdbid_query = json.loads(tvdbid_query)
            for found in tvdbid_query["movies"]:
                # logger.info(found)
                logger.info("testing " + found["title"])
                if (
                    found["title"] == showtitle
                    or found["title"].lower() == showtitle.lower()
                ):
                    logger.info("found " + found["title"])
                    if "imdb_id" in found:
                        tvdbid = found["imdb_id"]
                        logger.info("imdb_id: " + str(tvdbid))
                        return tvdbid
        except Exception:
            logger.info(logstr)
            logger.info(f"could not fetch movie's {showtitle} imdb_id")
        return False

    def imdbidFromId(self, showid, logstr):
        """Find information from imdbid for a movie

        Args:
            showid (int): imdbid
            logstr (str): process information returned

        Returns:
            [dict]: movie informations
        """
        url = self.apiurl + "/movies/movie"
        urldata = {
            "v": self.apiver,
            "key": self.apikey,
            "token": self.token,
            "imdb_id": showid,
        }
        logger.debug(urldata)
        try:
            tvdbid_query = utilities.get_urldata(url, urldata, "GET")
            tvdbid_query = json.loads(tvdbid_query)
            return tvdbid_query
        except Exception:
            logger.info(logstr)
            logger.info(f"could not fetch movie's {showid} imdb_infos")
        return False

    def _service_betaserie(self, episode, service):
        """mark as watched

        Args:
            episode (dict): information on media
            service (class): user settings
        """
        # web_pdb.set_trace()

        # don't proceed if we had an authentication failure
        if not self.auth_fail:
            # test if we are authenticated
            if not self.token:
                # authenticate
                self._service_authenticate()
            # only proceed if authentication was succesful
            if self.token:
                # mark as watched if we still have a valid session key after submission and have episode info
                if episode["int_id"] and episode["remote_id"]:
                    # first-only check
                    if not service.first or (
                        service.first and episode["playcount"] <= 1
                    ):
                        # mark as watched
                        self._service_mark(episode, service)

    def _service_authenticate(self, user=None, pw=None):
        """authenticate if necessary into betaseries.com

        Args:
            user ([str], optional): username. Defaults to None.
            pw ([str], optional): password. Defaults to None.
        """
        if user:
            self.user = user
        if pw:
            self.pw = pw
        # don't proceed if timeout timer has not expired
        if self.timerexpiretime > int(time.time()):
            return
        if self.__auth():
            logger.info("successfully authenticated")
        else:
            notification(getString(32010), getString(32003))
            logger.error("failed to connect for authentication")

    def _service_mark(self, episode, service):
        # abort if betamark = false and playcount > 0 and play = false
        if not service.mark and episode["playcount"] > 0 and not episode["playstatus"]:
            logger.info(f"abort marking, as play = {episode['playstatus']}")
            return
        # abort if betaunmark = false and playcount = 0 and play = false
        elif (
            not service.unMark
            and episode["playcount"] == 0
            and not episode["playstatus"]
        ):
            logger.info(f"abort unmarking, as play = {episode['playstatus']}")
            return
        if utilities.isEpisode(episode["type"]):
            # follow show if BetaFollow = true
            # if service.follow and episode["playcount"] != -1:
            if service.follow and not episode["followed"]:
                url = self.apiurl + "/shows/show"
                urldata = {
                    "v": self.apiver,
                    "key": self.apikey,
                    "token": self.token,
                    "thetvdb_id": episode["int_id"],
                }
                try:
                    # marking request
                    response = utilities.get_urldata(url, urldata, "POST")
                    # marking response
                    data = json.loads(response)
                except Exception:
                    self.__service_fail(False)
                    logger.info(f"failed to follow TV show {episode['showtitle']}")
                # parse results
                if data["errors"]:
                    if self.__checkerrors(
                        data["errors"][0], infos=episode["showtitle"]
                    ):
                        return None

                if service.notify:
                    notification(
                        getString(32010), getString(30013, episode["showtitle"])
                    )
                logger.info(f"now following show {episode['showtitle']}")
        if utilities.isMovie(episode["type"]):
            # mark movie as watched
            url = self.apiurl + "/movies/movie"
            urldata = {
                "v": self.apiver,
                "key": self.apikey,
                "token": self.token,
                "id": episode["int_id"],
                "state": episode["playcount"],
            }
            method = "POST"
            if episode["playcount"] == 0:
                act = "not watched"
                actlang = 30017
            else:
                act = "watched"
                actlang = 30016
        elif utilities.isEpisode(episode["type"]):
            # mark episode as watched, unwatched or downloaded
            urldata = {
                "v": self.apiver,
                "key": self.apikey,
                "token": self.token,
                "thetvdb_id": episode["remote_id"],
            }
            if service.bulk:
                urldata.update({"bulk": 1})
            if episode["playcount"] == 0:
                url = self.apiurl + "/episodes/watched"
                method = "DELETE"
                act = "not watched"
                actlang = 30015
            elif episode["playcount"] == -1:
                url = self.apiurl + "/episodes/downloaded"
                method = "POST"
                act = "downloaded"
                actlang = 30101
            else:
                url = self.apiurl + "/episodes/watched"
                method = "POST"
                act = "watched"
                actlang = 30014
        try:
            # marking request
            response = utilities.get_urldata(url, urldata, method)
            # marking response
            data = json.loads(response)
        except Exception:
            self.__service_fail(False)
            logger.warning(f"failed to mark as {act}")
            return
        # parse results
        if data["errors"]:
            if self.__checkerrors(
                data["errors"][0], infos=episode["type"] + episode["title"]
            ):
                return None

        if service.notify:
            notification(getString(32010), getString(actlang))
        logger.info(f"{episode['showtitle']} {episode['title']} marked as {act}")
        return None
