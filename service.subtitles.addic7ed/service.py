# -*- coding: utf-8 -*-

import os, sys, re, string, urllib, urllib2, socket, unicodedata, shutil
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

self_host = "http://www.addic7ed.com"
self_user_agent = "Mozilla/5.0 (X11; Linux i686; rv:29.0) Gecko/20100101 Firefox/29.0"
self_release_pattern = re.compile("Version (.+), ([0-9]+).([0-9])+ MBs.*")
self_team_pattern = re.compile(".*-([^-]+)$")
self_notify = __addon__.getSetting('notify') == 'true'

if xbmcvfs.exists(__temp__):
  shutil.rmtree(__temp__.encode("utf-8","ignore"))
xbmcvfs.mkdirs(__temp__)

TEAMS = (
    # SD[0]              HD[1]
    ("lol|sys|dim",      "dimension"),
    ("asap|xii|fqm|imm", "immerse|orenji"),
    ("excellence",       "remarkable"),
    ("2hd|xor",          "ctu"),
    ("tla",              "bia"))

def other_team(team, team_from, team_to):
    # get other team using TEAMS table
    for x in TEAMS:
        if len(re.findall(x[team_from], team)) > 0:
            return x[team_to]
    # return team if not found
    log("other team not found")
    return team

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
    except Exception:
        import traceback
        log('generic exception: ' + traceback.format_exc(), xbmc.LOGERROR)
    # when error occured
    if self_notify:
        xbmc.executebuiltin((u'Notification(%s,%s,%s,%s)' % (__addonname__, __language__(30008), 750, __icon__)).encode('utf-8', 'ignore'))
    return False

def download_subtitle(url, referer):
    file = os.path.join(__temp__, "adic7ed.srt")
    log("dowloading url : %s" % (url))
    socket.setdefaulttimeout(15)
    content = get_url(url, referer)
    if content:
        local_file_handle = open(file, "w" + "b")
        local_file_handle.write(content)
        local_file_handle.close()
        return file
    else:
        return False

def get_soup(content):
    # check if page content can be used
    pattern = "subtitles from the source! - Addic7ed.com"
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
    # replace some characters
    name = re.sub("[ /]+", "_", search['name'].strip().lower())
    log("after name = %s" % (name))
    # if it is a tvshow
    if search['video'] == "tvshow":
        # replace chars for "$#*! My Dad Says"
        name = name.replace("$#*!","shit")
        # remove apostrophe for "That '70s Show'
        name = name.replace("'70s","70s")
        # remove ending dot for "Awkward."
        name = name.replace("awkward.","awkward")
        # remove year
        name2 = re.sub("_\(.*\)$", "", name)
        log("after name2 = %s" % (name2))
        # set search url
        searchurl = "%s/serie/%s/%s/%s/addic7ed" %(self_host, urllib.quote(name), search['season'], search['episode'])
        searchurl2 = "%s/serie/%s/%s/%s/addic7ed" %(self_host, urllib.quote(name2), search['season'], search['episode'])
    else:
        searchurl = "%s/film/%s_(%s)-Download" %(self_host, urllib.quote(name), str(search['year']))
    # get searchurl
    log("search url = %s" % (searchurl))
    socket.setdefaulttimeout(10)
    content = get_url(searchurl)
    soup = get_soup(content)
    # or search without year
    if search['video'] == "tvshow" and not soup:
        searchurl = searchurl2
        log("trying without year/country, url = %s" % (searchurl))
        content = get_url(searchurl)
        soup = get_soup(content)
    if not soup:
        log("no data, cannot continue")
        return False
    # for each release version
    log("parsing soup after urlopen")
    log("--------------------------")
    for html_tables in soup.findAll("table", {"class":  "tabel95", "align" : "center"}):
        # get version td
        html_version = html_tables.findNext("td", {"class":  "NewsTitle", "colspan" : "3"})
        subversion = self_release_pattern.match(str(html_version.contents[1])).groups()[0]
        subversion = str(subversion).strip().replace(" ", "-").replace("--", "-")
        # for each lang of this version
        for html_lang in html_tables.findAll("td", {"class" : "language"}):
            try:
                log("subtitle version = %s" % (subversion))
                # get language name
                lang = str(html_lang.contents[0]).strip()
                log("subtitle lang = %s" % (lang))
                try:
                    # normalize language name
                    lang = re.sub(" \(.*\)", "", lang)
                    # get language codes (2 letters)
                    lang2 = xbmc.convertLanguage(lang, xbmc.ISO_639_1)
                    # if lang = user gui language
                    if lang == search['uilang']:
                        # put this file on top
                        order = 0
                    else:
                        order = 1
                    log("after lang = %s, lang2 = %s" % (lang, lang2))
                except:
                    log("unsupported language")
                    break
                # get team name (everything after "-")
                subteam = str(self_team_pattern.match("-" + subversion).groups()[0]).lower()
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
                log("after sync = %s" % (sync))
                # get status
                html_status = html_lang.findNext("td")
                status = html_status.find("b").string.strip()
                log("after status = '%s'" % (status))
                # get link
                link = str("%s%s" % (self_host, html_status.findNext("td").find("a")["href"]))
                log("after link = %s" % (link))
                # get corrected / CC
                html_imgs = html_status.findNext("td", {"class" : "newsDate", "colspan" : "2"})
                # init vars
                corrected = False
                cc = False
                # for each img tag
                for html_img in html_imgs.findAll("img", title=True):
                    if html_img['title'] == "Corrected":
                        corrected = True
                    elif html_img['title'] == "Hearing Impaired":
                        cc = True
                log("after corrected = %s, cc = %s" % (corrected, cc))
                # get value of option "hide incomplete subtitles"
                hideinc = __addon__.getSetting('hideinc') == 'true'
                # set note
                if status == "Completed":
                    if corrected:
                        note = '1'
                    else:
                        note = '2'
                else:
                    if hideinc:
                        log("incomplete subtitle, not added")
                        log("--------------------------")
                        continue
                    else:
                        log("incomplete subtitle !")
                        note = '3'
                log("after note = %s" % (note))
                # if language allowed by user
                if lang2 in search['langs']:
                    # format subtitle name for GUI list
                    if search['video'] == "tvshow":
                        subname = "%s.S%.2dE%.2d" %(name.replace("_", ".").title(), int(search['season']), int(search['episode']))
                        # add version name
                        if subversion.find("-") > -1:
                            subname = "%s.%s" % (subname, subversion)
                        else:
                            subname = "%s-%s" % (subname, subversion)
                    else:
                        subname = "%s-%s" %(name.replace("_", ".").title(), subversion)
                    # add subtitle to list
                    subtitles.append({'order':order,'filename':subname,'link':link,'lang':lang,'lang2':lang2,"cc":cc,"sync":sync,"note":note})
                    log("subtitle added : %s" % (subname))
                log("--------------------------")
            except:
                log("Error in search_subtitles!")
                raise
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
            url = "plugin://%s/?action=download&link=%s&filename=%s&searchurl=%s" % (__addonid__, item["link"], item["filename"], searchurl)
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
    sub = download_subtitle(params["link"], params["searchurl"])
    if sub:
        # xbmc handles moving and using the subtitle
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
