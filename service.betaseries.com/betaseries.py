# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# * code structure and portions of code based on service.scrobbler.librefm by Team-XBMC

import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, socket, hashlib, time, platform
import xbmc, xbmcgui, xbmcaddon
from xml.dom import minidom
import simplejson as json

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')
__addonname__    = __addon__.getAddonInfo('name')
__addonversion__ = __addon__.getAddonInfo('version')
__icon__         = __addon__.getAddonInfo('icon')
__platform__     = platform.system() + " " + platform.release()
__language__     = __addon__.getLocalizedString

socket.setdefaulttimeout(10)

def log(txt, loglevel=xbmc.LOGDEBUG):
    message = '%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message, level=loglevel)

def set_user_agent():
    json_query = json.loads(xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }'))
    try:
        major = str(json_query['result']['version']['major'])
        minor = str(json_query['result']['version']['minor'])
        name = "Kodi" if int(major) >= 14 else "XBMC"
        version = "%s %s.%s" % (name, major, minor)
    except:
        log("could not get app version")
        version = "XBMC"
    return "Mozilla/5.0 (compatible; " + __platform__ + "; " + version + "; " + __addonid__ + "/" + __addonversion__ + ")"

def get_urldata(url, urldata, method):
    # create a handler
    handler = urllib.request.HTTPSHandler()
    # create an openerdirector instance
    opener = urllib.request.build_opener(handler)
    # encode urldata
    body = None if urldata == '' else urllib.parse.urlencode(urldata).encode("utf-8")
    # build a request
    req = urllib.request.Request(url, data=body)
    # add any other information you want
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', __useragent__)
    # overload the get method function
    req.get_method = lambda: method
    log(('fetching URL: %s - data: %s - method: %s' % (url, body, method)))
    try:
        #response = urllib2.urlopen(req)
        connection = opener.open(req)
    except urllib.error.HTTPError as e:
        connection = e
    if connection.code:
        response = connection.read()
        return response
    else:
        log('response empty')
        return 0

class Main:
    def __init__( self ):
        self._service_setup()
        monitor = xbmc.Monitor()
        while not monitor.abortRequested():
            # Sleep/wait for abort for 1 second
            if monitor.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break

    def _service_setup( self ):
        self.apikey       = 'cca540f2c2c4'
        self.apiurl       = 'https://api.betaseries.com'
        self.apiver       = '2.2'
        self.Monitor      = MyMonitor(action = self._get_settings)
        self._get_settings()

    def _get_settings( self ):
        log('reading settings')
        service    = []
        BetaActive = __addon__.getSetting('betaactive') == 'true'
        BetaFirst  = __addon__.getSetting('betafirst') == 'true'
        BetaUser   = __addon__.getSetting('betauser')
        BetaPass   = __addon__.getSetting('betapass').encode('utf-8')
        BetaBulk   = __addon__.getSetting('betabulk') == 'true'
        BetaMark   = __addon__.getSetting('betamark') == 'true'
        BetaUnMark = __addon__.getSetting('betaunmark') == 'true'
        BetaFollow = __addon__.getSetting('betafollow') == 'true'
        BetaNotify = __addon__.getSetting('betanotify') == 'true'
        if BetaActive and BetaUser and BetaPass:
            # [service, api-url, api-key, user, pass, first-only, token, auth-fail, failurecount, timercounter, timerexpiretime, bulk, mark, unmark, follow]
            service = ['betaseries', self.apiurl, self.apikey, BetaUser, BetaPass, BetaFirst, '', False, 0, 0, 0, BetaBulk, BetaMark, BetaUnMark, BetaFollow, BetaNotify]
            self.Player = MyPlayer(action = self._service_betaserie, service = service)
            if service[15]:
                xbmc.executebuiltin(('Notification(%s,%s,%s,%s)' % (__addonname__, __language__(30003), 750, __icon__)))

    def _service_betaserie( self, episode, service ):
        tstamp = int(time.time())
        # don't proceed if we had an authentication failure
        if not service[7]:
            # test if we are authenticated
            if not service[6]:
                # authenticate
                service = self._service_authenticate(service, str(tstamp))
            # only proceed if authentication was succesful
            if service[6]:
                # mark as watched if we still have a valid session key after submission and have episode info
                if episode[0] and episode[1]:
                    # first-only check
                    if not service[5] or (service[5] and episode[2] <= 1):
                        # mark as watched
                        service = self._service_mark(service, episode)

    def _service_authenticate( self, service, timestamp ):
        # don't proceed if timeout timer has not expired
        if service[10] > int(timestamp):
            return service
        # create a pass hash
        md5pass = hashlib.md5()
        md5pass.update(service[4])
        url = service[1] + '/members/auth'
        urldata = {'v':self.apiver, 'key':service[2], 'login':service[3], 'password':md5pass.hexdigest()}
        try:
            # authentication request
            response = get_urldata(url, urldata, "POST")
            # authentication response
            data = json.loads(response)
            log('successfully authenticated')
        except:
            service = self._service_fail( service, True )
            xbmc.executebuiltin(('Notification(%s,%s,%s,%s)' % (__addonname__, __language__(32003), 750, __icon__)))
            log('failed to connect for authentication', xbmc.LOGINFO)
            return service
        # parse results
        if 'token' in data:
            # get token
            service[6] = str(data['token'])
            # reset failure count
            service[8] = 0
            # reset timer
            service[9] = 0
            service[10] = 0
        if data['errors']:
            log("%s error %s : %s" % (service[0], data['errors'][0]['code'], data['errors'][0]['text']), xbmc.LOGINFO)
            if data['errors'][0]['code'] < 2000:
                # API error
                xbmc.executebuiltin(('Notification(%s,%s,%s,%s)' % (__addonname__, __language__(32002), 750, __icon__)))
                log('bad API usage', xbmc.LOGINFO)
                # disable the service, the monitor class will pick up the changes
                __addon__.setSetting('betaactive', 'false')
            elif data['errors'][0]['code'] > 4001:
                # login error
                xbmc.executebuiltin(('Notification(%s,%s,%s,%s)' % (__addonname__, __language__(32004), 750, __icon__)))
                log('login or password incorrect', xbmc.LOGINFO)
                service[7] = True
            else:
                # everything else
                service = self._service_fail( service, True )
                xbmc.executebuiltin(('Notification(%s,%s,%s,%s)' % (__addonname__, __language__(32001), 750, __icon__)))
                log('server error while authenticating', xbmc.LOGINFO)
        return service

    def _service_mark( self, service, episode ):
        log(('marking episode: %s' % (episode)))
        # abort if betamark = false and playcount > 0 and play = false
        if not service[12] and episode[2] > 0 and not episode[3]:
            log("abort marking, as play = %s" % episode[3])
            return service
        # abort if betaunmark = false and playcount = 0 and play = false
        elif not service[13] and episode[2] == 0 and not episode[3]:
            log("abort unmarking, as play = %s" % episode[3])
            return service
        if episode[6]=='episode':
            # follow show if BetaFollow = true
            if service[14] and episode[2] != -1:
                url = service[1] + "/shows/show"
                urldata = {'v':self.apiver, 'key':service[2], 'token':service[6], 'thetvdb_id':episode[0]}
                try:
                    # marking request
                    response = get_urldata(url, urldata, "POST")
                    # marking response
                    data = json.loads(response)
                except:
                    service = self._service_fail( service, False )
                    log('failed to follow show %s' % episode[4], xbmc.LOGINFO)
                    return service
                # parse results
                if data['errors']:
                    log("%s error : %s %s" % (service[0], data['errors'][0]['code'], data['errors'][0]['text']), xbmc.LOGINFO)
                    if data['errors'][0]['code'] == 2001:
                        # drop our session key
                        service[6] = ''
                        log('bad token while following show', xbmc.LOGINFO)
                        return service
                    elif data['errors'][0]['code'] == 2003:
                        log('already following show %s' % episode[4])
                    else:
                        xbmc.executebuiltin(('Notification(%s,%s,%s,%s)' % (__addonname__, __language__(32005) + episode[4], 750, __icon__)))
                        log('failed to follow show %s' % episode[4], xbmc.LOGINFO)
                        return service
                else:
                    if service[15]:
                        xbmc.executebuiltin(('Notification(%s,%s,%s,%s)' % (__addonname__, __language__(30013) + episode[4], 750, __icon__)))
                    log('now following show %s' % (episode[4]))
        if episode[6]=='movie':
            # mark movie as watched
            url = service[1] + "/movies/movie"
            urldata = {'v':self.apiver, 'key':service[2], 'token':service[6], 'id':episode[0],'state': episode[2]}
            method = "POST"
            if episode[2] == 0:
                act = "not watched"
                actlang = 30017
            else:
                act = "watched"
                actlang = 30016
        elif episode[6]=='episode':
            # mark episode as watched
            urldata = {'v':self.apiver, 'key':service[2], 'token':service[6], 'thetvdb_id':episode[1]}
            if service[11]:
                urldata.update({'bulk': 1})
            if episode[2] == 0:
                url = service[1] + "/episodes/watched"
                method = "DELETE"
                act = "not watched"
                actlang = 30015
            elif episode[2] == -1:
                url = service[1] + "/episodes/downloaded"
                method = "POST"
                act = "downloaded"
                actlang = 30101
            else:
                url = service[1] + "/episodes/watched"
                method = "POST"
                act = "watched"
                actlang = 30014
        try:
            # marking request
            response = get_urldata(url, urldata, method)
            # marking response
            data = json.loads(response)
        except:
            service = self._service_fail( service, False )
            log('failed to mark as %s' % act, xbmc.LOGINFO)
            return service
        # parse results
        if data['errors']:
            log("%s error : %s %s" % (service[0], data['errors'][0]['code'], data['errors'][0]['text']), xbmc.LOGINFO)
            if data['errors'][0]['code'] == 2001:
                # drop our session key
                service[6] = ''
                log('bad token while marking %s' % (episode[6]), xbmc.LOGINFO)
            elif data['errors'][0]['code'] == 0:
                if episode[6]=='movie':
                    log('%s already marked as %s' % (episode[5], act), xbmc.LOGINFO)
                else:
                    log('not following show, or %s %s already marked as %s' % (episode[6],episode[5], act), xbmc.LOGINFO)
            else:
                if episode[6]=='movie':
                    actlang = 32007
                else:
                    actlang = 32006
                xbmc.executebuiltin(('Notification(%s,%s,%s,%s)' % (__addonname__, __language__(actlang), 750, __icon__)))
                log('error marking %s %s as %s' % (episode[6],episode[5], act), xbmc.LOGINFO)
        else:
            if service[15]:
                xbmc.executebuiltin(('Notification(%s,%s,%s,%s)' % (__addonname__, __language__(actlang), 750, __icon__)))
            log('%s %s %s marked as %s' % (episode[4], episode[6], episode[5], act))
        return service

    def _service_fail( self, service, timer ):
        timestamp = int(time.time())
        # increment failure counter
        service[8] += 1
        # drop our session key if we encouter three failures
        if service[8] > 2:
            service[6] = ''
        # set a timer if failure occurred during authentication phase
        if timer:
            # wrap timer if we cycled through all timeout values
            if service[9] == 0 or service[9] == 7680:
                service[9] = 60
            else:
                # increment timer
                service[9] = 2 * service[9]
        # set timer expire time
        service[10] = timestamp + service[9]
        return service

# monitor notifications
class MyPlayer(xbmc.Monitor):
    def __init__( self, *args, **kwargs ):
        xbmc.Monitor.__init__( self )
        self.action = kwargs['action']
        self.service = kwargs['service']
        self.Play = False
        log('Player Class Init')
        self.ScanRecentlyadded()

    def onNotification( self, sender, method, data ):
        if sender == 'xbmc':
            if method == 'VideoLibrary.OnScanFinished':
                self.ScanRecentlyadded()
            elif method == 'Player.OnPlay':
                result = json.loads(data)
                if 'item' in result and 'id' in result['item']:
                    if result['item']['type'] == 'episode':
                        # in case Player.OnPlay comes to fast after Player.OnStop
                        xbmc.sleep(1000)
                        log("watching episode, library id = %s" % result['item']['id'])
                        self.Play = True
                    elif result['item']['type'] == 'movie':
                        # in case Player.OnPlay comes to fast after Player.OnStop
                        xbmc.sleep(1000)
                        log("watching movie, library id = %s" % result['item']['id'])
                        self.Play = True

            elif method == 'Player.OnStop':
                result = json.loads(data)
                # if viewing in file mode and playback stopped at the end
                if 'item' in result and 'title' in result["item"] and 'id' in result["item"] and result["end"]:
                    if result['item']['type'] == 'episode':
                        # scrap episode infos from filename (item -> title)
                        scraper_url = "%s/episodes/scraper?file=%s&key=%s" % (self.service[1], result["item"]["title"], self.service[2])
                        scraper_data = json.loads(get_urldata(scraper_url,"","GET"))["episode"]
                        title = str(scraper_data["season"]) + "x" + str(scraper_data["episode"])
                        # get show's tvdbid from showid
                        show_url = "%s/shows/display?id=%s&key=%s" % (self.service[1], scraper_data["show_id"], self.service[2])
                        tvdbid = json.loads(get_urldata(show_url,"","GET"))["show"]["thetvdb_id"]
                        # set episode infos
                        episode = [int(tvdbid), int(scraper_data["thetvdb_id"]), 1, True, str(scraper_data["show_title"]), title,'episode']
                        # mark episode as watched
                        self.action(episode, self.service)
                    elif result['item']['type'] == 'movie':
                        # scrap movie infos from filename (item -> title)
                        scraper_url = "%s/movies/scraper?file=%s&key=%s" % (self.service[1], result["item"]["title"], self.service[2])
                        scraper_data = json.loads(get_urldata(scraper_url,"","GET"))["movie"]
                        # set movie infos
                        movie = [int(scraper_data["id"]), int(scraper_data["thetvdb_id"]), 1, True, '', str(scraper_data["title"]), 'movie']
                        # mark movie as watched
                        self.action(movie, self.service)
                else:
                    # wait 1s to avoid setting Play=False before marking episode
                    xbmc.sleep(1000)
                self.Play = False
            elif method == 'VideoLibrary.OnUpdate':
                result = json.loads(data)
                if 'playcount' in result:
                    if 'item' in result:
                        if result['item']['type'] == 'episode':
                            log("episode status changed for library id = %s, playcount = %s" % (result['item']['id'], result['playcount']))
                            episode = self._get_episode_info( result['item']['id'], result['playcount'], self.Play)
                            if episode:
                                # mark as watched or not, depending on playcount
                                self.action(episode, self.service)
                                self.Play = False
                                if result['playcount']==0:
                                    # mark as downloaded
                                    episode[2]=-1
                                    self.action(episode, self.service)
                        elif result['item']['type'] == 'movie':
                            log("movie status changed for library id = %s, playcount = %s" % (result['item']['id'], result['playcount']))
                            movie = self._get_movie_info( result['item']['id'], result['playcount'], self.Play)
                            if movie:
                                # mark as watched or not, depending on playcount
                                self.action(movie, self.service)
                                self.Play = False

    def ScanRecentlyadded ( self):
        f =  __addon__.getAddonInfo('path') + '/lastdate.tmp'
        try:
            with open (f,"r") as fic:
                lastdate = fic.read()
        except:
            lastdate = '2001-01-01 00:00:00'
        newdate = lastdate
        # result_movies = json.loads(xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "VideoLibrary.GetRecentlyAddedMovies", "params": {"properties": ["dateadded"]}, "id": 1 }'))
        # if 'result' in result_movies:
            # log("VideoLirary GetRecentlyAddedMovies : %s" % result_movies['result']['movies'])
            # for movie in result_movies['result']['movies']:
                # log("id %s has been added %s" % (movie['movieid'],movie['dateadded']))
        # else:
            # log("VideoLirary GetRecentlyAddedMovies in ERROR : %s" % result_movies)
        result_episodes = json.loads(xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "VideoLibrary.GetRecentlyAddedEpisodes", "params": {"properties": ["dateadded"]}, "id": 1 }'))
        if 'result' in result_episodes:
            # log("VideoLirary GetRecentlyAddedEpisodes : %s" % result_episodes['result']['episodes'])
            for episode in result_episodes['result']['episodes']:
                 if episode['dateadded'] > lastdate:
                    if episode['dateadded'] > newdate:
                        newdate = episode['dateadded']
                    log("%s with id %s has been added %s" % (episode['label'],episode['episodeid'],episode['dateadded']))
                    episode = self._get_episode_info( episode['episodeid'], -1, self.Play)
                    if episode and type(episode) is list:
                        episode[2]=-1
                        self.action(episode, self.service)
            with open (f,'wb') as fic:
                fic.write(newdate.encode('utf-8'))
        else:
            log("VideoLirary GetRecentlyAddedEpisodes in ERROR : %s" % result_episodes)

    def _get_episode_info( self, episodeid, playcount, playstatus ):
        tvdbid = False
        tvdbepid = False
        try:
            tvshow_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodeDetails", "params": {"episodeid": ' + str(episodeid) + ', "properties": ["tvshowid", "showtitle", "season", "episode", "uniqueid"]}, "id": 1}'
            tvshow = json.loads(xbmc.executeJSONRPC (tvshow_query))['result']['episodedetails']
            if 'uniqueid' in tvshow and 'unknown' in tvshow['uniqueid']:
                tvdbepid = tvshow['uniqueid']['unknown']
                log("theTvDb episode id : %s" % tvdbepid)
            tvdbid_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShowDetails", "params": {"tvshowid": ' + str(tvshow['tvshowid']) + ', "properties": ["imdbnumber"]}, "id": 1}'
            tvdbid = json.loads(xbmc.executeJSONRPC (tvdbid_query))['result']['tvshowdetails']['imdbnumber']
            showtitle = tvshow['showtitle']
            epname = str(tvshow['season']) + 'x' + str(tvshow['episode'])
        except:
            log("could not get tvshow/episode details", xbmc.LOGINFO)
        if not tvdbid:
            url = self.service[1] + '/shows/search'
            urldata = '?v=2.2&key=' + self.service[2] + '&title=' + showtitle
            try:
                tvdbid_query = get_urldata(url + urldata, '', "GET")
                tvdbid_query = json.loads(tvdbid_query)
                tvdbid = tvdbid_query['shows'][0]['thetvdb_id']
            except:
                log("could not fetch tvshow's thetvdb_id", xbmc.LOGINFO)
                return False
        if not tvdbepid:
            url = self.service[1] + '/shows/episodes'
            urldata = '?v=2.2&key=' + self.service[2] + '&thetvdb_id=' + str(tvdbid) + '&season=' + str(tvshow['season']) + '&episode=' + str(tvshow['episode'])
            try:
                tvdbepid_query = get_urldata(url + urldata, '', "GET")
                tvdbepid_query = json.loads(tvdbepid_query)
                tvdbepid = tvdbepid_query['episodes'][0]['thetvdb_id']
            except:
                log("could not fetch episode's thetvdb_id", xbmc.LOGINFO)
                return False

        epinfo = [int(tvdbid), int(tvdbepid), int(playcount), bool(playstatus), showtitle, epname, 'episode']
        return epinfo

    def _get_movie_info( self, episodeid, playcount, playstatus ):
        method = 'VideoLibrary.GetMovieDetails'
        params = '"movieid": ' + str(episodeid) + ', "properties": ["imdbnumber", "originaltitle", "sorttitle", "title", "uniqueid"]'
        returncode = 'moviedetails'
        movie_query = '{"jsonrpc": "2.0", "method": "' + str(method) + '", "params": {' + str(params) + '}, "id": 1}'
        movie = json.loads(xbmc.executeJSONRPC (movie_query))['result']['moviedetails']
        imdbid = ''
        tvdbid = ''
        id = ''
        try:
            imdbid = movie['imdbnumber']
            moviename = movie['originaltitle']
            log('movie found= %s    %s' % (moviename, imdbid))
        except:
            log("could not get movie details", xbmc.LOGINFO)
        if not imdbid:
            url = self.service[1] + '/movies/search'
            urldata = '?v=2.2&key=' + self.service[2] + '&title=' + moviename
            try:
                imdbid_query = get_urldata(url + urldata, '', "GET")
                imdbid_query = json.loads(imdbid_query)
                imdbid = imdbid_query['movies'][0]['imdb_id']
            except:
                log("could not fetch movie's %s imdb_id : %s " % (moviename, imdbid), xbmc.LOGINFO)
                return False
        url = self.service[1] + '/movies/movie'
        urldata = '?key=' + self.service[2] + '&imdb_id=' + str(imdbid)
        try:
            tvdbid_query = get_urldata(url + urldata, '', "GET")
            log(tvdbid_query)
            tvdbid_query = json.loads(tvdbid_query)
            tvdbid = tvdbid_query['movie']['tmdb_id']
            id = tvdbid_query['movie']['id']
        except:
            log("could not fetch movie %s thetmdb_id : %s , %s" % (imdbid, tvdbid , id ), xbmc.LOGINFO)
            return False
        epinfo = [int(id), int(tvdbid), int(playcount), bool(playstatus), '', moviename, 'movie']
        return epinfo

# monitor settings change
class MyMonitor(xbmc.Monitor):
    def __init__( self, *args, **kwargs ):
        xbmc.Monitor.__init__( self )
        self.action = kwargs['action']

    def onSettingsChanged( self ):
        log('onSettingsChanged')
        self.action()

# start script
if ( __name__ == "__main__" ):
    log('script version %s started' % __addonversion__)
    __useragent__ = set_user_agent()
    Main()
