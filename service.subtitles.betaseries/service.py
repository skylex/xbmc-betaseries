# -*- coding: utf-8 -*- 
#
# fdonv based (almost copied) on amet source code.
#
# next :
# - add sync icon based on rlz group (lol = dimension etc.)
# - check the sort version to priorize french in the top of the list

import sys
import os
import re
import time
import urllib
import urllib2
import xbmc
import xbmcgui
import string
import shutil
from xml.dom import minidom
import xbmcaddon
import os.path
import xbmcvfs
import xbmcplugin
import unicodedata
import simplejson as json

__addon__ 		=	xbmcaddon.Addon()
__language__	=	__addon__.getLocalizedString
__scriptid__	=	__addon__.getAddonInfo('id')
__profile__		=	xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__temp__		=	xbmc.translatePath( os.path.join( __profile__, 'temp') ).decode("utf-8")

user_agent = 'Mozilla/5.0 (compatible; XBMC.Subtitle; XBMC)'

apikey = 'db81cb96baf8'
apiurl = 'api.betaseries.com'

if not xbmcvfs.exists(__temp__):
	xbmcvfs.mkdirs(__temp__)

LANGUAGES      = (
    # Full Language name[0]     podnapisi[1]  ISO 639-1[2]   ISO 639-1 Code[3]   Script Setting Language[4]   localized name id number[5]
    ("English"                    , "2",        "en",            "eng",                 "11",                    30212  ),
    ("French"                     , "8",        "fr",            "fre",                 "15",                    30215  ))

def normalizeString(str):
  return unicodedata.normalize('NFKD', unicode(unicode(str, 'utf-8'))).encode('ascii','ignore')

def get_languages(languages):
	if languages == 'VF':
		code = 'fr'
	if languages == 'VO':
		code = 'en'
	if languages == 'VOVF':
		code = 'fr'
	return code 

def languageTranslate(lang, lang_from, lang_to):
  for x in LANGUAGES:
    if lang == x[lang_from] :
      return x[lang_to]
	
def getShowId():
    try:
      searchurl = 'http://' + apiurl + '/shows/search?title=' + urllib.quote(item['tvshow']) + '&key=' + apikey
      return str(json.load(urllib.urlopen(searchurl))['shows'][0]['thetvdb_id'])
    except:
      print "[SCRIPT] [EXCEPTION] BETASERIESSUBTITLES - no show id found"

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

params = get_params()

if params['action'] == 'search':
	print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - search fonction called"
	item = {}
	item['temp']               = False
	item['rar']                = False
	item['year']               = xbmc.getInfoLabel("VideoPlayer.Year")
	item['season']             = str(xbmc.getInfoLabel("VideoPlayer.Season"))
	item['episode']            = str(xbmc.getInfoLabel("VideoPlayer.Episode"))
	item['tvshow']             = normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))
	item['title']              = normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle"))
	item['file_original_path'] = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))
	item['3let_language']      = []
	
	for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
		item['3let_language'].append(xbmc.convertLanguage(lang,xbmc.ISO_639_2))
		print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - 3let_lang : '%s'" % (item['3let_language'])

	episode = item['episode']
	season = item['season']
	
	subtitles_list = []

	if ( item['file_original_path'].find("rar://") > -1 ):
		item['rar']  = True
		item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

	elif ( item['file_original_path'].find("stack://") > -1 ):
		stackPath = item['file_original_path'].split(" , ")
		item['file_original_path'] = stackPath[0][8:]

	tvdbid = getShowId()
	if tvdbid:
		print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - tvdbid '%s'" % (tvdbid)

		searchurl = 'http://' + apiurl + '/shows/display/' + tvdbid + '.xml?key=' + apikey
		print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - search url is : '%s'" % (searchurl)

		dom = minidom.parse(urllib.urlopen(searchurl))

		if len(dom.getElementsByTagName('url')):
			url = dom.getElementsByTagName('url')[0].childNodes[0]
			url = url.nodeValue
			print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - show name is '%s'" % (url)

        if url:
			french = 0
			english = 0
			if 'fre' in item['3let_language']: 
				french = 1
			if 'eng' in item['3let_language']: 
				english = 1
			if ((french > 0 and english > 0) or (french == 0 and english == 0)):
				searchsuburl = 'http://' + apiurl + '/subtitles/show/' + url + '.xml?season=' + item['season'] + '&episode=' + item['episode'] + '&language=VOVF' + '&key=' + apikey
			elif (french > 0 and english == 0):
				searchsuburl = 'http://' + apiurl + '/subtitles/show/' + url + '.xml?season=' + item['season'] + '&episode=' + item['episode'] + '&language=VF' + '&key=' + apikey
			elif (french == 0 and english > 0):
				searchsuburl = 'http://' + apiurl + '/subtitles/show/' + url + '.xml?season=' + item['season'] + '&episode=' + item['episode'] + '&language=VO' + '&key=' + apikey
			print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - searchsuburl is '%s'" % (searchsuburl)

			try:
				dom = minidom.parse(urllib.urlopen(searchsuburl))
				subtitles = dom.getElementsByTagName('subtitle')
				print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - found '%s' subtitles for %s" % (len(subtitles), url)

				for subtitle in subtitles:
					url = subtitle.getElementsByTagName('url')[0].childNodes[0]
					url = url.nodeValue
					print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - subtitle url is : %s" % (url)

					filename = subtitle.getElementsByTagName('file')[0].childNodes[0]
					filename = filename.nodeValue
					print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - filename is : %s" % (filename)

					language = subtitle.getElementsByTagName('language')[0].childNodes[0]
					language = get_languages(language.nodeValue)
					print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - language is : %s" % (language)

					rating = subtitle.getElementsByTagName('quality')[0].childNodes[0]
					rating = rating.nodeValue
					print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - rating is : %s" % (rating)

					ext = os.path.splitext(filename)[1]
					if ext == '.zip':
						print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - this is a zip file, analysing content."
						if len(subtitle.getElementsByTagName('content')) > 0:
							content = subtitle.getElementsByTagName('content')[0]
							items = content.getElementsByTagName('item')
							
							for item in items:
								if len(item.childNodes) < 1 : continue
								
								subfile = item.childNodes[0].nodeValue

								if os.path.splitext(subfile)[1] == '.zip': continue
								if os.path.splitext(subfile)[1] == '': continue
								
								search_string = "(s%#02de%#02d)|(%d%#02d)|(%dx%#02d)" % (int(season), int(episode),int(season), int(episode),int(season), int(episode))
								queryep = re.search(search_string, subfile, re.I)
								if queryep == None: continue

								langs = re.search('\.(VF|VO|en|fr)\..*.{3}$',subfile,re.I)

								print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES -    detecting language for : '%s' ..." % (subfile)
								try:
									langs = langs.group(1)
									lang = {
										"fr": 'fr',
										"FR": 'fr',
										"en": 'en',
										"EN": 'en',
										"VF": 'fr',
										"vf": 'fr',
										"VO": 'en',
										"vo": 'en'
									}[langs]
									print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES -    ... language is : '%s'" % (lang)
								except:
									lang = language
								
								filetest = os.path.basename(subfile)
								print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - file is : %s" % (filetest)

								subtitles_list.append({
									# if you don't want to see the parent folder for an archive use "filetest"
									#'filename'          : filetest,
									'filename'          : subfile,
									'link'              : url,
									'language_name'     : languageTranslate(lang,2,0),
									'language_flag'		: lang,
									'rating'            : rating,
									'sync'              : False,
									})
								#subtitles_list.sort(key=lambda x: [not x['sync'],x['language_name']])
								#subtitles_list.sort(key=lambda x: [ x['language_name']], reverse = True)

								if subtitles_list:
									for it in subtitles_list:
										listitem = xbmcgui.ListItem(label=it["language_name"],
										  label2=it["filename"],
										  iconImage=it["rating"],
										  thumbnailImage=it["language_flag"]
										  )

									url = "plugin://%s/?action=download&link=%s&filename=%s" % (__scriptid__, it["link"], it["filename"])

									xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

						else:
							print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - error analysing zip file : '%s'" % (filename)

					else:
						subtitles_list.append({
							'filename'          : filename,
							'link'              : url,
							'language_name'     : languageTranslate(language,2,0),
							'language_flag'		: language,						
							'rating'            : rating,
							'sync'              : False
							})

						if subtitles_list:
							for it in subtitles_list:
								listitem = xbmcgui.ListItem(label=it["language_name"],
								  label2=it["filename"],
								  iconImage=it["rating"],
								  thumbnailImage=it["language_flag"]
								  )

							url = "plugin://%s/?action=download&link=%s&filename=%s" % (__scriptid__, it["link"], it["filename"])

							xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

			except:
				print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - error"

	# else:
		# print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - show not found on tvdb, trying from betaserie search"
		# searchurl = 'http://' + apiurl + '/shows/search.xml?title=' + urllib.quote(title) + '&key=' + apikey
		# print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - betaserie search url is : '%s'" % (searchurl)
		# dom = minidom.parse(urllib.urlopen(searchurl))
		# print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - found show : '%s'" % (dom.getElementsByTagName('url').length)
		# url = [ e.childNodes[0].nodeValue for e in dom.getElementsByTagName('url') ]
		# print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - showname is '%s'" % [ e.childNodes[0].nodeValue for e in dom.getElementsByTagName('url') ]
		# return [ e.childNodes[0].nodeValue for e in dom.getElementsByTagName('url') ]

elif params['action'] == 'download':
	print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - download fonction called"

	url = params["link"]
	filename = params["filename"]

	print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - download link : %s" % (params["link"])

	response = urllib.urlopen(url)
	content = response.read()

	if xbmcvfs.exists(__temp__):
		shutil.rmtree(__temp__)
		xbmcvfs.mkdirs(__temp__) 

	if content is not None:
		header = content[:4]
		if header == 'Rar!':
			print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - the file is a rar file."
			local_tmp_file = os.path.join(__temp__, "betaseries.rar")
			packed = True
		elif header == 'PK':
			print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - the file is a zip file."
			local_tmp_file = os.path.join(__temp__, "betaseries.zip")
			packed = True
		else:
			print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - the file is a unarchived file."
			local_tmp_file = os.path.join(__temp__, "betaseries.srt")
			subs_file = local_tmp_file
			packed = False
		print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - saving file to %s" % (local_tmp_file)
		try :
			local_file_handle = open(local_tmp_file, "wb")
			local_file_handle.write(content)
			local_file_handle.close()
			print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - sucessfully saved the file :)"
		except:
			print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - unsucessfully saved the file :("
        
		if packed:
			files = os.listdir(__temp__)
			init_filecount = len(files)
			print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - nombre de fichiers : %s" % (init_filecount)

			filecount = init_filecount
			max_mtime = 0
			for file in files:
				if (string.split(file,'.')[-1] in ['srt','sub','txt','ass']):
					mtime = os.stat(os.path.join(__temp__.encode("utf-8"), file.encode("utf-8"))).st_mtime
					if mtime > max_mtime:
						max_mtime =  mtime
			init_max_mtime = max_mtime
			time.sleep(2)
			print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - extracting files"
			xbmc.executebuiltin("XBMC.Extract(" + local_tmp_file + "," + __temp__ +")")
			waittime  = 0
			while (filecount == init_filecount) and (waittime < 20) and (init_max_mtime == max_mtime): # nothing yet extracted
				time.sleep(1)  # wait 1 second to let the builtin function 'XBMC.extract' unpack
				files = os.listdir(__temp__)
				filecount = len(files)
			# determine if there is a newer file created in __temp__ (marks that the extraction had completed)
			for file in files:
				print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - file inside the temp folder : %s" % (file)
				if (string.split(file,'.')[-1] in ['srt','sub','txt','ass']):
					mtime = os.stat(os.path.join(__temp__, file)).st_mtime
					if (mtime > max_mtime):
						max_mtime =  mtime
					if filecount == (init_filecount + 1): filename = file
			waittime  = waittime + 1

			if waittime == 20:
				print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - error unpacking files are in : %s" % (__temp__)
			else:
				print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - unpacked files in : %s" % (__temp__)
				print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - checking file %s" % (os.path.join(__temp__, filename))
				if os.path.exists(os.path.join(__temp__, filename)):
					file = str(os.path.normpath(os.path.join(__temp__, filename)))
					print "[SCRIPT] [DEBUG] BETASERIESSUBTITLES - selected file : %s" % (filename)
					#ext = os.path.splitext(file)[1]
					#if ext == '.zip':
					#	log( __name__ ,"target file is zipped, copy to '%s'" % (zip_subs))
					#	shutil.copy(file, zip_subs)

					subs_file = file

					# removing temp files, (what about a user who don't use a specific subtitles folder?)
					#if xbmcvfs.exists(__temp__):
					#	shutil.rmtree(__temp__)
					#	xbmcvfs.mkdirs(__temp__) 

	listitem = xbmcgui.ListItem(label=subs_file)
	xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=subs_file,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
