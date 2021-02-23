# -*- coding: utf-8 -*-
#

import xbmc
import xbmcaddon
import json

import logging


# read settings
__addon__ = xbmcaddon.Addon("script.betaseries")

logger = logging.getLogger(__name__)


def notification(
    header: str, message: str, time=5000, icon=__addon__.getAddonInfo("icon")
):
    """On Screen notification

    Args:
        header (str): title
        message (str): body
        time (int, optional): time before disappears. Defaults to 5000.
        icon ([type], optional): icon. Defaults to __addon__.getAddonInfo("icon").
    """
    # 0101 définir le temps dans les settings
    xbmc.executebuiltin("Notification(%s,%s,%d,%s)" % (header, message, time, icon))


def showSettings():
    """Open settings dialog"""
    __addon__.openSettings()


def getSetting(setting):
    """retrieve user setting

    Args:
        setting (str): setting name

    Returns:
        str: setting value
    """
    return __addon__.getSetting(setting).strip()


def setSetting(setting, value):
    """update user setting

    Args:
        setting (str): setting name
        value (): setting value (transfromed in str)
    """
    __addon__.setSetting(setting, str(value))


def getSettingAsBool(setting):
    """retrieve user setting

    Args:
        setting (str): setting name

    Returns:
        bool: setting value
    """
    return getSetting(setting).lower() == "true"


def getSettingAsFloat(setting):
    """retrieve user setting

    Args:
        setting (str): setting name

    Returns:
        float: setting value
    """
    try:
        return float(getSetting(setting))
    except ValueError:
        return 0


def getSettingAsInt(setting):
    """retrieve user setting

    Args:
        setting (str): setting name

    Returns:
        int: setting value
    """
    try:
        return int(getSettingAsFloat(setting))
    except ValueError:
        return 0


def getString(string_id, var=None):
    """return localized string by id

    Args:
        string_id (int): id of the text in string.po
        var ([type], optional): variable added into string. Defaults to None.

    Returns:
        str: text localized
    """
    if var:
        return __addon__.getLocalizedString(string_id) % var
    else:
        return __addon__.getLocalizedString(string_id)


def kodiJsonRequest(params):
    """get json for kodi request

    Args:
        params (dict): jso informations

    Returns:
        dict: response founded in ["result"]
    """
    data = json.dumps(params)
    request = xbmc.executeJSONRPC(data)

    response = json.loads(request)

    try:
        if "result" in response:
            return response["result"]
        return None
    except KeyError:
        logger.warn(f"[{params['method']}] {response['error']['message']}")
        return None


def getEpisodesFromKodi():
    """return list of episodes in Kodi

    Returns:
        dict: list of episodes
    """
    result = kodiJsonRequest(
        {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetEpisodes",
            "id": 1,
        }
    )
    logger.debug("getEpisodesFromKodi(): %s" % str(result))

    if not result:
        logger.debug("getEpisodesFromKodi(): Result from Kodi was empty.")
        return None

    try:
        return result
    except KeyError:
        logger.debug("getEpisodesFromKodi(): KeyError: result")
        return None


def GetRecentlyAddedEpisodesFromKodi(fields):
    """Return list of recently added episodes in Kodi

    Args:
        fields (dict): list of field to return

    Returns:
        dict: list of episodes
    """
    result = kodiJsonRequest(
        {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetRecentlyAddedEpisodes",
            "params": fields,
            "id": 1,
        }
    )
    logger.debug("GetRecentlyAddedEpisodesFromKodi(): %s" % str(result))

    if not result:
        logger.debug("GetRecentlyAddedEpisodesFromKodi(): Result from Kodi was empty.")
        return None

    try:
        return result["episodes"]
    except KeyError:
        logger.debug("GetRecentlyAddedEpisodesFromKodi(): KeyError: result['episodes']")
        return None


def getShowDetailsFromKodi(showID, fields):
    """return detailled Show information from Kodi based on TVShowID

    Args:
        showID (int): internal ID
        fields (dict):  list of field to return

    Returns:
        dict: list of informations requested in field
    """
    result = kodiJsonRequest(
        {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetTVShowDetails",
            "params": {"tvshowid": showID, "properties": fields},
            "id": 1,
        }
    )
    logger.debug("getShowDetailsFromKodi(): %s" % str(result))

    if not result:
        logger.debug("getShowDetailsFromKodi(): Result from Kodi was empty.")
        return None

    try:
        return result["tvshowdetails"]
    except KeyError:
        logger.debug("getShowDetailsFromKodi(): KeyError: result['tvshowdetails']")
        return None


def getSeasonDetailsFromKodi(seasonID, fields):
    """return detailled Season information from Kodi based on SeasonID

    Args:
        seasonID (int): internal ID
        fields (dict):  list of field to return
    Returns:
        dict: list of informations requested in field
    """
    result = kodiJsonRequest(
        {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetSeasonDetails",
            "params": {"seasonid": seasonID, "properties": fields},
            "id": 1,
        }
    )
    logger.debug("getSeasonDetailsFromKodi(): %s" % str(result))

    if not result:
        logger.debug("getSeasonDetailsFromKodi(): Result from Kodi was empty.")
        return None

    try:
        return result["seasondetails"]
    except KeyError:
        logger.debug("getSeasonDetailsFromKodi(): KeyError: result['seasondetails']")
        return None


def setEpisodeDetailsOnKodi(libraryId, fields):
    """Set info on a single episode from kodi given the id

    Args:
        libraryId (int): internal ID
        fields (dict): list of field and value to update
    Returns:
        str: return
                - True if update is ok
                - False or None if problem
    """
    result = kodiJsonRequest(
        {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.SetEpisodeDetails",
            "params": dict({"episodeid": libraryId}, **fields),
            "id": 1,
        }
    )
    logger.debug("setEpisodeDetailsOnKodi(): %s" % str(result))

    if not result:
        logger.debug("setEpisodeDetailsOnKodi(): Result from Kodi was empty.")
        return None
    try:
        return result == "OK"
    except KeyError:
        logger.debug("setEpisodeDetailsOnKodi(): KeyError: result")
        return None


def getEpisodeDetailsFromKodi(libraryId, fields):
    """Get a single episode from kodi given the id

    Args:
        libraryId (int): internal ID
        fields (dict):  list of field to return
    Returns:
        dict: list of informations requested in field
    """
    result = kodiJsonRequest(
        {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetEpisodeDetails",
            "params": {"episodeid": libraryId, "properties": fields},
            "id": 1,
        }
    )
    logger.debug("getEpisodeDetailsFromKodi(): %s" % str(result))

    if not result:
        logger.debug("getEpisodeDetailsFromKodi(): Result from Kodi was empty.")
        return None
    try:
        return result["episodedetails"]
    except KeyError:
        logger.debug("getEpisodeDetailsFromKodi(): KeyError: result['episodedetails']")
        return None


def getMovieDetailsFromKodi(libraryId, fields):
    """Get a single movie from kodi given the id

    Args:
        libraryId (int): internal ID
        fields (dict):  list of field to return
    Returns:
        dict: list of informations requested in field
    """
    result = kodiJsonRequest(
        {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetMovieDetails",
            "params": {"movieid": libraryId, "properties": fields},
            "id": 1,
        }
    )
    logger.debug("getMovieDetailsFromKodi(): %s" % str(result))

    if not result:
        logger.debug("getMovieDetailsFromKodi(): Result from Kodi was empty.")
        return None

    try:
        return result["moviedetails"]
    except KeyError:
        logger.debug("getMovieDetailsFromKodi(): KeyError: result['moviedetails']")
        return None
