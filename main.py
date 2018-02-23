from resources.lib.mlb import *

    
params=get_params()
name=None
mode=None
game_day=None
event_id=None
gid=None
teams_stream=None
stream_date=None

try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    game_day=urllib.unquote_plus(params["game_day"])
except:    
    pass
try:
    event_id=urllib.unquote_plus(params["event_id"])
except:
    pass
try:
    gid=urllib.unquote_plus(params["gid"])
except:
    pass
try:
    teams_stream=urllib.unquote_plus(params["teams_stream"])
except:
    pass
try:
    stream_date=urllib.unquote_plus(params["stream_date"])
except:
    pass

if mode is None:
    categories()  

elif mode == 100:
    todaysGames(None)    

elif mode == 101:
    #Prev and Next 
    todaysGames(game_day)    

elif mode == 104:    
    streamSelect(event_id, gid, teams_stream, stream_date)

elif mode == 105:
    #Yesterday's Games
    game_day = localToEastern()
    display_day = stringToDate(game_day, "%Y-%m-%d")            
    prev_day = display_day - timedelta(days=1)                
    todaysGames(prev_day.strftime("%Y-%m-%d"))

elif mode == 200:
    #Goto Date
    search_txt = ''
    dialog = xbmcgui.Dialog()
    game_day = dialog.input('Enter date (yyyy-mm-dd)', type=xbmcgui.INPUT_ALPHANUM)    
    mat=re.match('(\d{4})-(\d{2})-(\d{2})$', game_day)        
    if mat is not None:    
        todaysGames(game_day)
    else:    
        if game_day != '':    
            msg = "The date entered is not in the format required."
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Invalid Date', msg)

        sys.exit()        

elif mode == 400:    
    logout()

elif mode == 500:
    myTeamsGames()

elif mode == 900:        
    getGamesForDate(stream_date)
    playAllHighlights()    

elif mode == 999:
    sys.exit()

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 101:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)