# -*- coding: utf-8 -*-

import os, sys, re, string, urllib, urllib2, socket, unicodedata, shutil, time
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')
__addonname__    = __addon__.getAddonInfo('name')
__icon__         = __addon__.getAddonInfo('icon')
__language__     = __addon__.getLocalizedString
__profile__      = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__temp__         = xbmc.translatePath( os.path.join( __profile__, 'temp') ).decode("utf-8")

sys.path.append( os.path.join( __profile__, "lib") )
from BeautifulSoup import BeautifulSoup

self_host = "http://www.tvsubtitles.net"
self_user_agent = "Mozilla/5.0 (X11; Linux i686; rv:29.0) Gecko/20100101 Firefox/29.0"
self_team_pattern = re.compile(".*-([^-]+)$")
self_notify = __addon__.getSetting('notify') == 'true'

if xbmcvfs.exists(__temp__):
  shutil.rmtree(__temp__)
xbmcvfs.mkdirs(__temp__)

TEAMS = (
    # SD[0]              HD[1]
    ("lol|sys|dim",      "dimension"),
    ("asap|xii|fqm|imm", "immerse|orenji"),
    ("excellence",       "remarkable"),
    ("2hd|xor",          "ctu"),
    ("tla",              "bia"))

LANGUAGES = (
    # [0]  [1]
    ("br", "pt"),
    ("gr", "el"))

def other_team(team, team_from, team_to):
    # get other team using TEAMS table
    for x in TEAMS:
        if len(re.findall(x[team_from], team)) > 0:
            return x[team_to]
    # return team if not found
    log("other team not found")
    return team

def normalize_lang(lang, lang_from, lang_to):
    # normalize lang using LANGUAGES table
    for x in LANGUAGES:
        if len(re.findall(x[lang_from], lang)) > 0:
            return x[lang_to]
    # return lang if not found
    return lang

def normalize_string(str):
    return unicodedata.normalize('NFKD', unicode(unicode(str, 'utf-8'))).encode('ascii','ignore')

def log(txt, level=xbmc.LOGDEBUG):
    message = u'%s: %s' % (__addonid__, txt)
    xbmc.log(msg=message, level=level)

def get_params(string=""):
  param=[]
  if string == "":
    paramstring=sys.argv[2]
  else:
    paramstring=string 
  if len(paramstring)>=2:
    params=paramstring
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
                                
  return param

def get_url(url, referer=self_host):
    req_headers = {
    'User-Agent': self_user_agent,
    'Cache-Control': 'no-store, no-cache, must-revalidate',
    'Pragma': 'no-cache',
    'Referer': referer}
    request = urllib2.Request(url, headers=req_headers)
    opener = urllib2.build_opener()
    try:
        response = opener.open(request)
        contents = response.read()
        return contents
    except urllib2.HTTPError, e:
        log('HTTPError = ' + str(e.code), xbmc.LOGERROR)
    except urllib2.URLError, e:
        log('URLError = ' + str(e.reason), xbmc.LOGERROR)
    except httplib.HTTPException, e:
        log('HTTPException', xbmc.LOGERROR)
    except Exception:
        import traceback
        log('generic exception: ' + traceback.format_exc(), xbmc.LOGERROR)
    # when error occured
    if self_notify:
        xbmc.executebuiltin((u'Notification(%s,%s,%s,%s)' % (__addonname__, __language__(30008), 750, __icon__)).encode('utf-8', 'ignore'))
    return False

def download_subtitle(url, referer):
    local_tmp_file = os.path.join(__temp__, "tvsubtitles.zip")
    log("dowloading url : %s" % (url))
    socket.setdefaulttimeout(15)
    content = get_url(url, referer)
    if content:
        local_file_handle = open(local_tmp_file, "w" + "b")
        local_file_handle.write(content)
        local_file_handle.close()
        try:
            files = os.listdir(__temp__)
            init_filecount = len(files)
            log("number of files : %s" % (init_filecount))
            filecount = init_filecount
            max_mtime = 0
            for file in files:
                if (string.split(file,'.')[-1] in ['srt','sub','txt','ass']):
                    mtime = os.stat(os.path.join(__temp__.encode("utf-8"), file.encode("utf-8"))).st_mtime
                    if mtime > max_mtime:
                        max_mtime =  mtime
            init_max_mtime = max_mtime
            time.sleep(2)
            log("extracting zip file : %s" % (local_tmp_file))
            xbmc.executebuiltin("XBMC.Extract(" + local_tmp_file + "," + __temp__ +")")
            waittime  = 0
            while (filecount == init_filecount) and (waittime < 20) and (init_max_mtime == max_mtime): # nothing yet extracted
                time.sleep(1)  # wait 1 second to let the builtin function 'XBMC.extract' unpack
                files = os.listdir(__temp__)
                filecount = len(files)
            # determine if there is a newer file created in __temp__ (marks that the extraction had completed)
            for file in files:
                log("file inside the temp folder : %s" % (file))
                if (string.split(file,'.')[-1] in ['srt','sub','txt','ass']):
                    mtime = os.stat(os.path.join(__temp__, file)).st_mtime
                    if (mtime > max_mtime):
                        max_mtime =  mtime
                    if filecount == (init_filecount + 1): filename = file
            waittime = waittime + 1
            if waittime == 20:
                log("error unpacking files are in : %s" % (__temp__))
            else:
                log("unpacked files in : %s" % (__temp__))
                log("checking file %s" % (os.path.join(__temp__, filename)))
                if os.path.exists(os.path.join(__temp__, filename)):
                    file = str(os.path.normpath(os.path.join(__temp__, filename)))
                    log("selected file : %s" % (filename))
                    return file
        except:
            log("not a zip file")
            #raise
        return local_tmp_file
    else:
        return False

def get_soup(content):
    # check if page content can be used
    pattern = "TVsubtitles.net - "
    try:
        soup = BeautifulSoup(content)
        title = str(soup.findAll("title")[0])
        if title.find(pattern) > -1:
            return soup
        else:
            log("bad page, maybe index after 404")
            return False
    except:
        log("badly formatted content")
        if self_notify:
            xbmc.executebuiltin((u'Notification(%s,%s,%s,%s)' % (__addonname__, __language__(30009), 750, __icon__)).encode('utf-8', 'ignore'))
        return False

def search_subtitles(**search):
    subtitles = []
    log("Entering search_subtitles()")
    # get video file name
    dirsync = __addon__.getSetting('dirsync') == 'true'
    if dirsync:
        filename = os.path.basename(os.path.dirname(search['path'])).lower()
    else:
        filename = os.path.basename(search['path']).lower()
        # remove file extension
        filename = re.sub("\.[^.]+$", "", filename)
    log("after filename = %s" % (filename))
    # strip trailing characters and lower name
    name = search['name'].strip().lower() # ex: house of cards (us)
    log("after name = %s" % (name))
    # if it is a tvshow
    if search['video'] == "tvshow":
        # replace chars for "$#*! My Dad Says"
        name = name.replace("$#*!","shit")
        # remove US for The Office
        name = name.replace("the office (us)","the office")
        # House MD specific
        if name == "house":
            name = "house m.d."
        # remove year
        name2 = re.sub(" \([0-9]+\)$", "", name) # ex: house of cards (us)
        log("after name2 = %s" % (name2))
        # set list url
        listurl = "%s/tvshows.html" % (self_host)
    else:
        log("film subtitles not supported")
        return False
    # get data
    socket.setdefaulttimeout(10)
    content = get_url(listurl)
    soup = get_soup(content)
    if not soup:
        log("no data, cannot continue")
        return False
    # for each release version
    log("parsing soup after urlopen")
    log("--------------------------")
    for html_links in soup.find("table", {"id": "table5"}).findAll("tr", {"bgcolor": "#ffffff"}):
        # get tvshow id and name
        tvshowid = re.sub("^tvshow-([0-9]+)-[0-9]+\.html$", "\\1", html_links.find("a")['href'])
        tvshowname =  html_links.find("b").contents[0].encode('utf-8', 'ignore').strip().lower()
        if tvshowname == name or tvshowname == name2:
            log("we have a match : %s" % (tvshowname))
            seasonurl = "%s/tvshow-%s-%s.html" % (self_host, tvshowid, search['season'])
            content = get_url(seasonurl)
            subsoup = get_soup(content)
            for html_tables in subsoup.find("table", {"id": "table5"}).findAll("tr", {"align": "middle"}):
                if len(html_tables.findNext("td").contents) > 0:
                    tvshowep = str(html_tables.findNext("td").contents[0])
                    tvshowep = re.sub("^[0-9]+x([0-9]+)$", "\\1", tvshowep.strip().lower())
                    #log("after tvshowep = %s" % (int(tvshowep)))
                    if int(tvshowep) == int(search['episode']):
                        log("got subtitles for season %s episode %s" % (search['season'], tvshowep))
                        log("--------------------------")
                        episodelink = html_tables.findNext("td", {"align": "left"}).find("a")['href']
                        episodeurl = "%s/%s" % (self_host, episodelink)
                        content = get_url(episodeurl)
                        epsoup = get_soup(content)
                        for html_subs in epsoup.find("div", {"class": "left_articles"}).findAll("a"):
                            if html_subs['href'].find("/subtitle-") > -1:
                                log("found subtitle : %s" % (html_subs['href']))
                                # get link
                                link = re.sub("^/subtitle-([0-9]+).html$", "/download-\\1.html", str(html_subs['href']))
                                link = "%s%s" % (self_host, link)
                                log("after link = %s" % (link))
                                # get user ratings
                                ratebad = int(html_subs.find("span", {"style": "color:red"}).contents[0])
                                rategood = int(html_subs.find("span", {"style": "color:green"}).contents[0])
                                log("after rategood = %s / ratebad = %s" % (rategood, ratebad))
                                if rategood > ratebad:
                                    if rategood > 2:
                                        note = '1'
                                    else:
                                        note = '2'
                                else:
                                    note = '3'
                                log("after note = %s" % (note))
                                # get subtitle version name
                                html_vers = html_subs.find("h5")
                                subversion = str(html_vers.contents[1])
                                log("after subversion = %s" % (subversion))
                                # get language code
                                html_lang = html_vers.find("img")
                                lang2 = re.sub("^images/flags/([a-z]+)\.gif$", "\\1", str(html_lang['src']))
                                lang2 = normalize_lang(lang2,0,1)
                                try:
                                    # get full language name
                                    lang = xbmc.convertLanguage(lang2, xbmc.ENGLISH_NAME)
                                except:
                                    log("unsupported language")
                                    continue
                                # if lang = user gui language
                                if lang == search['uilang']:
                                    # put this file on top
                                    order = 0
                                else:
                                    order = 1
                                log("after lang = %s, lang2 = %s" % (lang, lang2))
                                # get subtitle team
                                subteam = str(html_subs.find("p", {"title": "release"}).contents[1]).strip().replace(".","-")
                                if len(subteam) > 0:
                                    # get team name (everything after "-")
                                    subteam = str(self_team_pattern.match("-" + subteam).groups()[0]).lower()
                                    log("after subteam = %s" % (subteam))
                                    # find HD equivalent team if exists (or SD equivalent)
                                    if filename.find("720p") > -1:
                                        subteam2 = other_team(subteam,0,1)
                                    else:
                                        subteam2 = other_team(subteam,1,0)
                                    log("after subteam2 = %s" % (subteam2))
                                    # if team corresponds
                                    if len(re.findall("-(" + subteam + "|" + subteam2 + ")$", filename)) > 0:
                                        # set sync tag
                                        sync = True
                                    else:
                                        sync = False
                                else:
                                    sync = False
                                log("after sync = %s" % (sync))
                                cc = False
                                # if language allowed by user
                                if lang2 in search['langs']:
                                    # add subtitle to list
                                    subtitles.append({'order':order,'filename':subversion,'link':link,'lang':lang,'lang2':lang2,"cc":cc,"sync":sync,"note":note})
                                    log("subtitle added : %s" % (subversion))
                                log("--------------------------")
    if subtitles:
        # get settings for order
        uifirst = __addon__.getSetting('uifirst') == 'true'
        ccfirst = __addon__.getSetting('ccfirst') == 'true'
        # order accordingly
        if uifirst:
            if ccfirst:
                subtitles.sort(key=lambda x: [not x['sync'], x['order'], not x['cc'], x['lang'], x['note'], x['filename']])
            else:
                subtitles.sort(key=lambda x: [not x['sync'], x['order'], x['lang'], x['note'], x['cc'], x['filename']])
        else:
            if ccfirst:
                subtitles.sort(key=lambda x: [not x['sync'], not x['cc'], x['lang'], x['note'], x['filename']])
            else:
                subtitles.sort(key=lambda x: [not x['sync'], x['lang'], x['note'], x['cc'], x['filename']])
        log("sorted subtitles = %s" % (subtitles))
        # for each subtitle
        for item in subtitles:
            # set rating
            item["rating"] = {
                "1": "5",
                "2": "3",
                "3": "0"
            }[item["note"]]
            # xbmc list item format
            listitem = xbmcgui.ListItem(label=item["lang"],
              label2=item["filename"],
              iconImage=item["rating"],
              thumbnailImage=item["lang2"])
            # setting sync / CC tag
            listitem.setProperty("sync", 'true' if item["sync"] else 'false')
            listitem.setProperty("hearing_imp", 'true' if item["cc"] else 'false')
            # adding item to GUI list
            url = "plugin://%s/?action=download&link=%s&filename=%s" % (__addonid__, item["link"], urllib.quote(item["filename"]))
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)
    else:
        if self_notify:
            xbmc.executebuiltin((u'Notification(%s,%s,%s,%s)' % (__addonname__, __language__(30010), 750, __icon__)).encode('utf-8', 'ignore'))
        log("nothing found")
    log("End of search_subtitles()")

# start script
params = get_params()

# called when user is searching for subtitles
if params['action'] == 'search':
    item = {}
    item['year']    = xbmc.getInfoLabel("VideoPlayer.Year")
    item['season']  = str(xbmc.getInfoLabel("VideoPlayer.Season"))
    item['episode'] = str(xbmc.getInfoLabel("VideoPlayer.Episode"))
    item['tvshow']  = normalize_string(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))
    item['title']   = normalize_string(xbmc.getInfoLabel("VideoPlayer.OriginalTitle"))
    item['path']    = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))
    item['uilang']  = str(xbmc.getLanguage())
    item['langs']   = []
    # get user preferred languages for subtitles
    for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
        item['langs'].append(xbmc.convertLanguage(lang, xbmc.ISO_639_1))
    log("user langs = %s" % (item['langs']))
    # remove rar:// or stack://
    if ( item['path'].find("rar://") > -1 ):
        item['path'] = os.path.dirname(item['path'][6:])
    elif ( item['path'].find("stack://") > -1 ):
        stackPath = item['path'].split(" , ")
        item['path'] = stackPath[0][8:]
    # call search_subtitles()
    if item['tvshow'] == "":
        search_subtitles(video="movie", name=item['title'], year=item['year'], path=item['path'], langs=item['langs'], uilang=item['uilang'])
    else:
        search_subtitles(video="tvshow", name=item['tvshow'], season=item['season'], episode=item['episode'], path=item['path'], langs=item['langs'], uilang=item['uilang'])

# called when user clicks on a subtitle
elif params['action'] == 'download':
    # download link
    sub = download_subtitle(params["link"], self_host)
    if sub:
        # xbmc handles moving and using the subtitle
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
