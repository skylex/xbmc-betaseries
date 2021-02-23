#!/usr/bin/python
# coding: utf-8
# import web_pdb

import logging
from resources.lib import kodiUtilities
from resources.lib import globals

logger = logging.getLogger(__name__)


class Media:
    """Provides information about media (episode or movie)"""

    type_media = None

    def __init__(self, media_id, playcount, playstatus):
        self.media_id = media_id
        self.playcount = playcount
        self.playstatus = playstatus

    def get_media_info(self, type_media):
        """Provides information about media

        Args:
            type_media (str): episode or movie

        Returns:
            [dict]: media information
        """
        if type_media == "episode":
            self.type_media = type_media
            return self.__get_episode_info()
        if type_media == "movie":
            self.type_media = type_media
            return self.__get_movie_info()

    def __get_episode_info(self):
        """Provides information about episode

        Returns:
            [dict]: media information
        """
        tvdbid = False
        tmdbid = False
        tvdbepid = False
        logstr = ""
        try:
            tvshow = kodiUtilities.getEpisodeDetailsFromKodi(
                self.media_id,
                [
                    "tvshowid",
                    "showtitle",
                    "season",
                    "episode",
                    "uniqueid",
                    "playcount",
                ],
            )
            if "uniqueid" in tvshow:
                if "tvdb" in tvshow["uniqueid"]:
                    tvdbepid = tvshow["uniqueid"]["tvdb"]
                elif "imdb" in tvshow["uniqueid"]:
                    tvdbepid = tvshow["uniqueid"]["imdb"]
                elif "tmdb" in tvshow["uniqueid"]:
                    tmdbid = tvshow["uniqueid"]["tmdb"]
                elif "unknown" in tvshow["uniqueid"]:
                    # suppose to be tvdbid !!!
                    tvdbepid = tvshow["uniqueid"]["unknown"]
                if tvdbepid:
                    if (tvdbepid).startswith("tt"):
                        tvdbepid = False
            showtitle = tvshow["showtitle"]
            epname = str(tvshow["season"]) + "x" + str(tvshow["episode"])
            logstr += f"Id: {self.media_id} Title: {tvshow['showtitle']} tvshowid: {tvshow['tvshowid']} tvdbepid: {tvdbepid}"
        except Exception as e:
            logger.error(f"getEpisodeDetailsFromKodi error for {self.media_id} : {e}")
            return None

        if tvshow["tvshowid"] != -1:
            try:
                tvdbid_query = kodiUtilities.getShowDetailsFromKodi(
                    tvshow["tvshowid"], ["imdbnumber", "uniqueid"]
                )
                if "uniqueid" in tvdbid_query:
                    if "tvdb" in tvdbid_query["uniqueid"]:
                        tvdbid = tvdbid_query["uniqueid"]["tvdb"]
                    elif "imdb" in tvdbid_query["uniqueid"]:
                        tvdbid = tvdbid_query["uniqueid"]["imdb"]
                    else:
                        tvdbid = tvdbid_query["imdbnumber"]
                else:
                    tvdbid = tvdbid_query["imdbnumber"]
                if tvdbid:
                    logstr += f"\ntvdbid: {tvdbid}"
                if tmdbid:
                    logstr += f"\ntmdbid: {tmdbid}"
            except Exception:
                logger.info(logstr)
                tvdbid = False
                logger.error(
                    f"could not get tvshow/episode details for {self.media_id}"
                )

        # si imbd_id, convert to thetvdb_id
        if tvdbid:
            # logger.info('tvdbid: %s' % ( tvdbid) )
            if (tvdbid).startswith("tt"):
                tvdbid = globals.betaseriesapi.tvdbidFromimbd(tvdbid, logstr)

        if not tvdbid:
            # if tvdbepid, convert to thetvdb_id
            if tvdbepid:
                tvdbid = globals.betaseriesapi.tvdbidFromtvdbepid(
                    tvdbepid, showtitle, logstr
                )

        # si aucun tvdbid, chercher avec le Titre !!!
        if not tvdbid:
            tvdbid = globals.betaseriesapi.tvdbidFromTitle(showtitle, logstr)
            if tvdbid:
                # logger.info("found tvdbid "+ str(tvdbid ) +" for " + showtitle )
                logstr += f"\nBS tvdbid from title: {tvdbid}"
            else:
                logger.error(
                    "could not fetch tvshow's thetvdb_id from title for " + showtitle
                )
                return None
        follow = globals.betaseriesapi.followFromtvdbid(tvdbid, showtitle, logstr)
        if not tvdbepid:
            tvdbepid = globals.betaseriesapi.tvdbepidFromtvdbid(
                tvdbid, showtitle, tvshow["season"], tvshow["episode"], logstr
            )
            if not tvdbepid:
                return None

        seen = False
        dl = False
        if tvshow["playcount"] < 1 and follow:
            try:
                seen_query = globals.betaseriesapi.tvdbInfFromtvdbepid(
                    tvdbepid, showtitle, logstr
                )
                seen = seen_query["user"]["seen"]
                dl = seen_query["user"]["downloaded"]
                logstr += f" dl status: {dl} seen status: {seen}"
            except Exception as e:
                logger.info(logstr)
                logger.warning(f"failed to get status for {showtitle} - {epname} : {e}")
        logger.debug(logstr)
        epinfo = {
            "int_id": int(tvdbid),
            "remote_id": int(tvdbepid),
            "playcount": int(self.playcount),
            "playstatus": bool(self.playstatus),
            "showtitle": showtitle,
            "title": epname,
            "type": "episode",
            "tvshow_playcount": tvshow["playcount"],
            "followed": bool(follow),
            "downloaded": bool(dl),
            "seen": bool(seen),
        }
        return epinfo

    def __get_movie_info(self):
        """Provides information about movie

        Returns:
            [dict]: media information
        """
        imdbid = False
        tvdbid = False
        id = False
        seen = False
        follow = False
        epinfo = False
        logstr = ""
        if isinstance(self.media_id, int):
            movie = kodiUtilities.getMovieDetailsFromKodi(
                self.media_id,
                [
                    "uniqueid",
                    "imdbnumber",
                    "originaltitle",
                    "sorttitle",
                    "title",
                ],
            )
            try:
                imdbid = movie["imdbnumber"]
                moviename = movie["originaltitle"]
                logstr += f"movie found= {moviename}    {imdbid}"
            except Exception:
                logger.info("could not get movie details")

            if not imdbid:
                imdbid = globals.betaseriesapi.imdbidFromTitle(moviename, logstr)
                if not imdbid:
                    return None

            try:
                tvdbid_query = globals.betaseriesapi.imdbidFromId(imdbid, logstr)
                tvdbid = tvdbid_query["movie"]["tmdb_id"]
                id = tvdbid_query["movie"]["id"]
            except Exception:
                logger.error(
                    "could not fetch movie {imdbid} thetmdb_id : {tvdbid} , {id}"
                )
                return None
            if "user" in tvdbid_query["movie"]:
                follow = tvdbid_query["movie"]["user"]["in_account"]
                seen = tvdbid_query["movie"]["user"]["status"]
            epinfo = {
                "int_id": int(id),
                "remote_id": tvdbid,
                "playcount": int(self.playcount),
                "playstatus": bool(self.playstatus),
                "showtitle": "",
                "title": moviename,
                "type": "movie",
                "tvshow_playcount": 0,
                "followed": bool(follow),
                "downloaded": True,
                "seen": bool(seen),
            }
        else:
            try:
                found = globals.betaseriesapi.imdbFromId(self.media_id, logstr)
                if (
                    found["title"] == self.media_id
                    or found["title"].lower() == self.media_id.lower()
                ):
                    logstr += "found " + found["title"]
                    if "imdb_id" in found:
                        tvdbid = found["imdb_id"]
                        logstr += " imdb_id: " + str(tvdbid)
                        if "user" in found:
                            seen = found["user"]["status"]
                        epinfo = {
                            "int_id": int(found["id"]),
                            "remote_id": str(tvdbid),
                            "playcount": int(self.playcount),
                            "playstatus": bool(self.playstatus),
                            "showtitle": "",
                            "title": found["original_title"],
                            "type": "movie",
                            "tvshow_playcount": 0,
                            "followed": bool(follow),
                            "downloaded": True,
                            "seen": bool(seen),
                        }
            except Exception:
                logger.error(f"could not fetch movie's {self.media_id} imdb_id")
                return None
        return epinfo
