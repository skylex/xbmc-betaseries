# coding: utf-8
#
"""Some useful base functions"""
import logging
import traceback
import urllib.request
import urllib.parse
import urllib.error

import json
import xbmc
import xbmcaddon
import platform

__addon__ = xbmcaddon.Addon("script.betaseries")
logger = logging.getLogger(__name__)


def user_agent():
    """return appropriate header for user agent header information

    Returns:
        str: text to put in user agent header
    """
    json_query = json.loads(
        xbmc.executeJSONRPC(
            '{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }'
        )
    )
    try:
        major = str(json_query["result"]["version"]["major"])
        minor = str(json_query["result"]["version"]["minor"])
        name = "Kodi"
        version = f"{name} {major}.{minor}"
    except Exception:
        logger.error("could not get app version")
        version = "XBMC"
    splatform = platform.system() + " " + platform.release()
    addon_id = __addon__.getAddonInfo("id")
    addon_version = __addon__.getAddonInfo("version")
    return (
        f"Mozilla/5.0 (compatible; {splatform}; {version}; {addon_id}/{addon_version})"
    )


def get_urldata(url, urldata, method):
    """get json informations

    Args:
        url (str): address
        urldata (dict): body to send
        method (str): HTTP method (GET, POST, PUT, DELETE, ....)

    Returns:
        dict: informations from url
    """
    # create a handler
    handler = urllib.request.HTTPSHandler()
    # create an openerdirector instance
    opener = urllib.request.build_opener(handler)
    # encode urldata
    body = urllib.parse.urlencode(urldata).encode("utf-8")
    # build a request
    req = urllib.request.Request(url, data=body)
    # add any other information you want
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", user_agent())
    # overload the get method function
    req.get_method = lambda: method
    try:
        # response = urllib2.urlopen(req)
        connection = opener.open(req)
    except urllib.error.HTTPError as e:
        connection = e
    if connection.code:
        response = connection.read()
        return response
    else:
        logger.error("response empty")
        return 0


def isMovie(type):
    """know if type is a movie

    Args:
        type (str): information to test

    Returns:
        bool: True if Ok, else False
    """
    return type == "movie"


def isEpisode(type):
    """know if type is an episode

    Args:
        type (str): information to test

    Returns:
        bool: True if Ok, else False
    """
    return type == "episode"


def isShow(type):
    """know if type is a show

    Args:
        type (str): information to test

    Returns:
        bool: True if Ok, else False
    """
    return type == "show"


def isSeason(type):
    """know if type is a season

    Args:
        type (str): information to test

    Returns:
        bool: True if Ok, else False
    """
    return type == "season"


def isValidMediaType(type):
    """know if type is ok

    Args:
        type (str): information to test

    Returns:
        bool: True if Ok, else False
    """
    return type in ["movie", "show", "season", "episode"]


def createError(ex):
    """Templating for error logger

    Args:
        ex (object): Exception information

    Returns:
        str: message to put in logger
    """
    template = (
        "EXCEPTION Thrown (PythonToCppException) : -->Python callback/script returned the following error<--\n"
        " - NOTE: IGNORING THIS CAN LEAD TO MEMORY LEAKS!\n"
        "Error Type: <type '{0}'>\n"
        "Error Contents: {1!r}\n"
        "{2}"
        "-->End of Python script error report<--"
    )
    return template.format(type(ex).__name__, ex.args, traceback.format_exc())


def checkIfNewVersion(old, new):
    """compare old and new version

    Args:
        old (str): old version must be 0.0.0 format
        new ([type]): new version must be 0.0.0 format

    Returns:
        bool: True if new version
    """
    # Check if old is empty, it might be the first time we check
    if old == "":
        return True
    # Major
    if old[0] < new[0]:
        return True
    # Minor
    if old[1] < new[1]:
        return True
    # Revision
    if old[2] < new[2]:
        return True
    return False
