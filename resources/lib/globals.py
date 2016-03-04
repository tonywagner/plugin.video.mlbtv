# coding=utf-8
import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import calendar
import pytz
import urllib, urllib2
import json
import cookielib
import time
from bs4 import BeautifulSoup 
from datetime import date, datetime, timedelta
from urllib2 import URLError, HTTPError
from PIL import Image
from cStringIO import StringIO


addon_handle = int(sys.argv[1])


#Addon Info
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
XBMC_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString

#Settings
settings = xbmcaddon.Addon(id='plugin.video.mlbtv')
USERNAME = str(settings.getSetting(id="username"))
PASSWORD = str(settings.getSetting(id="password"))
ROGERS_SUBSCRIBER = str(settings.getSetting(id="rogers"))
QUALITY = str(settings.getSetting(id="quality"))
NO_SPOILERS = settings.getSetting(id="no_spoilers")
FAV_TEAM = str(settings.getSetting(id="fav_team"))
TEAM_NAMES = settings.getSetting(id="team_names")
TIME_FORMAT = settings.getSetting(id="time_format")
VIEW_MODE = settings.getSetting(id='view_mode')


#Colors
SCORE_COLOR = 'FF00B7EB'
GAMETIME_COLOR = 'FFFFFF66'
#FAV_TEAM_COLOR = 'FFFF0000'
FREE_GAME_COLOR = 'FF43CD80'

#Game Time Colors
UPCOMING = 'FFD2D2D2'
LIVE = 'FFF69E20'
CRITICAL ='FFD10D0D'
FINAL = 'FF666666'
FREE = 'FF43CD80'

#Localization
local_string = xbmcaddon.Addon(id='plugin.video.mlbtv').getLocalizedString
ROOTDIR = xbmcaddon.Addon(id='plugin.video.mlbtv').getAddonInfo('path')

#Images
ICON = ROOTDIR+"/icon.png"
FANART = ROOTDIR+"/fanart.jpg"
#PREV_ICON = ROOTDIR+"/resources/images/prev.png"
#NEXT_ICON = ROOTDIR+"/resources/images/next.png"
PREV_ICON = ROOTDIR+"/icon.png"
NEXT_ICON = ROOTDIR+"/icon.png"

MASTER_FILE_TYPE = 'master_wired.m3u8'

#User Agents
UA_IPHONE = 'AppleCoreMedia/1.0.0.13D15 (iPhone; U; CPU OS 9_2_1 like Mac OS X; en_us)'
UA_IPAD = 'Mozilla/5.0 (iPad; CPU OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12H143 ipad nhl 5.0925'
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36'         
UA_PS4 = 'PS4Application libhttp/1.000 (PS4) libhttp/3.15 (PlayStation 4)'
UA_ATBAT = 'At Bat/13268 CFNetwork/758.2.8 Darwin/15.0.0'

#Playlists
RECAP_PLAYLIST = xbmc.PlayList(0)
EXTENDED_PLAYLIST = xbmc.PlayList(1)


def find(source,start_str,end_str):    
    start = source.find(start_str)
    end = source.find(end_str,start+len(start_str))

    if start != -1:        
        return source[start+len(start_str):end]
    else:
        return ''

def getGameIcon(home,away):
    #Check if game image already exists
    image_path = ROOTDIR+'/resources/images/'+away+'vs'+home+'.png'
    file_name = os.path.join(image_path)
    if not os.path.isfile(file_name): 
        try:
            createGameIcon(home,away,image_path)
        except:
            pass

    return image_path


def createGameIcon(home,away,image_path):    
    #bg = Image.new('RGB', (400,225), (0,0,0))    
    bg = Image.new('RGB', (500,250), (0,0,0)) 
    #http://mlb.mlb.com/mlb/images/devices/240x240/110.png
    #img_file = urllib.urlopen('http://mlb.mlb.com/mlb/images/devices/76x76/'+home+'.png ')
    img_file = urllib.urlopen('http://mlb.mlb.com/mlb/images/devices/240x240/'+home+'.png ')
    im = StringIO(img_file.read())
    home_image = Image.open(im)
    #bg.paste(home_image, (267,74), home_image)
    bg.paste(home_image, (255,5), home_image)

    #img_file = urllib.urlopen('http://mlb.mlb.com/mlb/images/devices/76x76/'+away+'.png ')
    img_file = urllib.urlopen('http://mlb.mlb.com/mlb/images/devices/240x240/'+away+'.png ')
    im = StringIO(img_file.read())
    away_image = Image.open(im)
    #bg.paste(away_image, (57,74), away_image)    
    bg.paste(away_image, (5,5), away_image)    
    
    bg.save(image_path)        
    

def colorString(string, color):
    return '[COLOR='+color+']'+string+'[/COLOR]'


def stringToDate(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))                

    return date


def easternToLocal(eastern_time):
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')    
    eastern_time = eastern.localize(eastern_time)
    # Convert it from Eastern to UTC
    utc_time = eastern_time.astimezone(utc)
    timestamp = calendar.timegm(utc_time.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    # Convert it from UTC to local time
    assert utc_time.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_time.microsecond)

def UTCToLocal(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def localToEastern():    
    eastern = pytz.timezone('US/Eastern')    
    local_to_utc = datetime.now(pytz.timezone('UTC'))  

    eastern_hour = local_to_utc.astimezone(eastern).strftime('%H')    
    eastern_date = local_to_utc.astimezone(eastern)
    #Don't switch to the current day until 4:01 AM est
    if int(eastern_hour) < 3:
        eastern_date = eastern_date - timedelta(days=1)  

    local_to_eastern = eastern_date.strftime('%Y-%m-%d')
    return local_to_eastern

def easternToUTC(eastern_time):    
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')    
    eastern_time = eastern.localize(eastern_time)
    # Convert it from Eastern to UTC
    utc_time = eastern_time.astimezone(utc)
    return utc_time



def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
            params=sys.argv[2]
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



def addStream(name,link_url,title,event_id,epg,icon=None,fanart=None,info=None,video_info=None,audio_info=None,teams_stream=None,stream_date=None):
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode="+str(104)+"&name="+urllib.quote_plus(name)+"&event_id="+urllib.quote_plus(str(event_id))+"&epg="+urllib.quote_plus(str(epg))+"&teams_stream="+urllib.quote_plus(str(teams_stream))+"&stream_date="+urllib.quote_plus(str(stream_date))
    
    #if icon != None:
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=icon) 
    #else:
    #liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 
    
    if fanart != None:
        liz.setProperty('fanart_image', fanart)       
    else:
        liz.setProperty('fanart_image', FANART)

    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)
    if video_info != None:
        liz.addStreamInfo('video', video_info)
    if audio_info != None:
        liz.addStreamInfo('audio', audio_info)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'episodes')
    
    return ok


def addLink(name,url,title,iconimage,info=None,video_info=None,audio_info=None,fanart=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)    
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setProperty('fanart_image', FANART)
    #if iconimage != None:
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage) 
    #else:
    #liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 

    if info != None:
        liz.setInfo( type="Video", infoLabels=info)
    if video_info != None:
        liz.addStreamInfo('video', video_info)
    if audio_info != None:
        liz.addStreamInfo('audio', audio_info)

    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    xbmcplugin.setContent(addon_handle, 'episodes')
    return ok




def addDir(name,url,mode,iconimage,fanart=None,game_day=None):       
    ok=True    
    
    #Set day to today if none given
    #game_day = time.strftime("%Y-%m-%d")
    #game_day = localToEastern()
    #game_day = '2016-01-27'

    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(iconimage)
    if game_day != None:
        u = u+"&game_day="+urllib.quote_plus(game_day)

    if iconimage != None:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage) 
    else:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 

    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)


    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def addPlaylist(name,game_day,url,mode,iconimage,fanart=None):       
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(iconimage)

    if iconimage != None:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage) 
    else:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 

    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    '''
    info = {'plot':'Watch all the days highlights for '+game_day.strftime("%m/%d/%Y"),'tvshowtitle':'NHL','title':name,'originaltitle':name,'aired':game_day.strftime("%Y-%m-%d"),'genre':'Sports'}
    audio_info, video_info = getAudioVideoInfo()

    if info != None:
        liz.setInfo( type="Video", infoLabels=info)
    if video_info != None:
        liz.addStreamInfo('video', video_info)
    if audio_info != None:
        liz.addStreamInfo('audio', audio_info)
    '''

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)    
    #xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def scoreUpdates():
    #s = ScoreThread()
    t = threading.Thread(target = scoringUpdates)
    t.start() 

def getFavTeamColor():
    #Hex code taken from http://teamcolors.arc90.com/    
    team_colors = {'Arizona Diamondbacks':'FFA71930',
                'Atlanta Braves':'FFCE1141',
                'Baltimore Orioles':'FFDF4601',
                'Boston Red Sox':'FFBD3039',
                'Chicago Cubs':'FFCC3433',
                'Chicago White Sox':'FFC4CED4',
                'Cincinnati Reds':'FFC6011F',
                'Cleveland Indians':'FFE31937',
                'Colorado Rockies':'FFC4CED4',
                'Detroit Tigers':'FF0C2C56',
                'Houston Astros':'FFEB6E1F',
                'Kansas City Royals':'FFC09A5B',
                'Los Angeles Angels':'FFBA0021',
                'Los Angeles Dodgers':'FFEF3E42',
                'Miami Marlins':'FFFF6600',
                'Milwaukee Brewers':'FFB6922E',
                'Minnesota Twins':'FFD31145',
                'New York Mets':'FFFF5910',
                'New York Yankees':'FFE4002B',
                'Oakland Athletics':'FFEFB21E',
                'Philadelphia Phillies':'FFE81828',
                'Pittsburgh Pirates':'FFFDB827',
                'St. Louis Cardinals':'FFC41E3A',
                'San Diego Padres':'FF05143F',
                'San Francisco Giants':'FFFD5A1E',
                'Seattle Mariners':'FFC4CED4',
                'Tampa Bay Rays':'FF8FBCE6',
                'Texas Rangers':'FFC0111F',
                'Toronto Blue Jays':'FFE8291C',
                'Washington Nationals':'FFAB0003'}

    # Default to red
    #fav_team_color = "FFFF0000"                
    #try:
    print FAV_TEAM
    fav_team_color = team_colors[FAV_TEAM]
    print fav_team_color
    #except:
    #pass

    return  fav_team_color


def getFavTeamId():
    #possibly use the xml file in the future
    #http://mlb.mlb.com/shared/properties/mlb_properties.xml  
    team_ids = {'Arizona Diamondbacks':'109',
                'Atlanta Braves':'144',
                'Baltimore Orioles':'110',
                'Boston Red Sox':'111',
                'Chicago Cubs':'112',
                'Chicago White Sox':'145',
                'Cincinnati Reds':'113',
                'Cleveland Indians':'114',
                'Colorado Rockies':'115',
                'Detroit Tigers':'116',
                'Houston Astros':'117',
                'Kansas City Royals':'118',
                'Los Angeles Angels':'108',
                'Los Angeles Dodgers':'119',
                'Miami Marlins':'146',
                'Milwaukee Brewers':'158',
                'Minnesota Twins':'142',
                'New York Mets':'121',
                'New York Yankees':'147',
                'Oakland Athletics':'133',
                'Philadelphia Phillies':'143',
                'Pittsburgh Pirates':'134',
                'St. Louis Cardinals':'138',
                'San Diego Padres':'135',
                'San Francisco Giants':'137',
                'Seattle Mariners':'136',
                'Tampa Bay Rays':'139',
                'Texas Rangers':'140',
                'Toronto Blue Jays':'141',
                'Washington Nationals':'120'}

    print FAV_TEAM
    fav_team_id = team_ids[FAV_TEAM]
    print fav_team_id
    #except:
    #pass

    return  fav_team_id

def getAudioVideoInfo():
    #SD (800 kbps)|SD (1600 kbps)|HD (3000 kbps)|HD (5000 kbps)
    if QUALITY == 'SD (800 kbps)':        
        video_info = { 'codec': 'h264', 'width' : 512, 'height' : 288, 'aspect' : 1.78 }        
    elif QUALITY == 'SD (1200 kbps)':
        video_info = { 'codec': 'h264', 'width' : 640, 'height' : 360, 'aspect' : 1.78 }        
    else:
        #elif QUALITY == 'HD (2500 kbps)' or QUALITY == 'HD (3500 kbps)' or QUALITY == 'HD (5000 kbps)':
        video_info = { 'codec': 'h264', 'width' : 1280, 'height' : 720, 'aspect' : 1.78 }        

    audio_info = { 'codec': 'aac', 'language': 'en', 'channels': 2 }
    return audio_info, video_info

def getConfigFile():
    '''
    GET http://lwsa.mlb.com/partner-config/config?company=sony-tri&type=nhl&productYear=2015&model=PS4&firmware=default&app_version=1_0 HTTP/1.0
    Host: lwsa.mlb.com
    User-Agent: PS4Application libhttp/1.000 (PS4) libhttp/3.15 (PlayStation 4)
    Connection: close
    '''
    url = 'http://lwsa.mlb.com/partner-config/config?company=sony-tri&type=nhl&productYear=2015&model=PS4&firmware=default&app_version=1_0'
    req = urllib2.Request(url)       
    req.add_header("Connection", "close")
    req.add_header("User-Agent", UA_PS4)

    response = urllib2.urlopen(req, '')
    json_source = json.load(response)   
    response.close()

def setViewMode():
    global VIEW_MODE
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    current_view_mode = str(window.getFocusId())
    if current_view_mode != VIEW_MODE and current_view_mode != "0":
        settings.setSetting(id='view_mode', value=current_view_mode) 
        VIEW_MODE = settings.getSetting(id='view_mode')

    getViewMode()
    
def getViewMode():
    xbmc.executebuiltin("Container.SetViewMode("+VIEW_MODE+")")