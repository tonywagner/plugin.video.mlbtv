from resources.lib.globals import *


def categories():      
    addDir('Today\'s Games','/live',100,ICON,FANART)
    addDir('Yesterday\'s Games','/live',105,ICON,FANART)
    #addDir('Favorite Team Recent Games','favteam',500,ICON,FANART)
    addDir('Goto Date','/date',200,ICON,FANART)  
        

def todaysGames(game_day):    
    if game_day == None:
        game_day = localToEastern()

    print "GAME DAY = " + str(game_day)            
    settings.setSetting(id='stream_date', value=game_day)    

    display_day = stringToDate(game_day, "%Y-%m-%d")
    url_game_day = display_day.strftime('year_%Y/month_%m/day_%d')            
    prev_day = display_day - timedelta(days=1)                

    addDir('[B]<< Previous Day[/B]','/live',101,PREV_ICON,FANART,prev_day.strftime("%Y-%m-%d"))

    date_display = '[B][I]'+ colorString(display_day.strftime("%A, %m/%d/%Y"),GAMETIME_COLOR)+'[/I][/B]'
    #addPlaylist(date_display,display_day,'/playhighlights',900,ICON,FANART)
    addPlaylist(date_display,display_day,'/playhighlights',999,ICON,FANART)

    url = 'http://gdx.mlb.com/components/game/mlb/'+url_game_day+'/grid_ce.json'    
    print "URL GAME DAY"
    print url

    req = urllib2.Request(url)    
    req.add_header('Connection', 'close')
    req.add_header('User-Agent', UA_PS4)

    try:    
        response = urllib2.urlopen(req)            
        json_source = json.load(response)                           
        response.close()                
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code          
        sys.exit()

    global RECAP_PLAYLIST
    global EXTENDED_PLAYLIST
    RECAP_PLAYLIST.clear()
    EXTENDED_PLAYLIST.clear()
    #try:
    for game in json_source['data']['games']['game']:        
        createGameListItem(game, game_day)
    #except:
    #pass
    
    next_day = display_day + timedelta(days=1)
    addDir('[B]Next Day >>[/B]','/live',101,NEXT_ICON,FANART,next_day.strftime("%Y-%m-%d"))    


def createGameListItem(game, game_day):
    icon = getGameIcon(game['home_team_id'],game['away_team_id'])
    #http://mlb.mlb.com/mlb/images/devices/ballpark/1920x1080/2681.jpg
    fanart = 'http://mlb.mlb.com/mlb/images/devices/ballpark/1920x1080/'+game['venue_id']+'.jpg'   
    
    if TEAM_NAMES == "0":
        away_team = game['away_team_name']
        home_team = game['home_team_name']  
    else:
        away_team = game['away_name_abbrev']
        home_team = game['home_name_abbrev']  


    fav_game = False
    
    if game['away_team_name'].encode('utf-8') in FAV_TEAM :
        fav_game = True
        away_team = colorString(away_team,getFavTeamColor())           
    
    if game['home_team_name'].encode('utf-8') in FAV_TEAM:
        fav_game = True
        home_team = colorString(home_team,getFavTeamColor())
    

    game_time = ''
    if game['status'] == 'Preview':
        game_time = game_day+' '+game['event_time']
        print game_time
        game_time = stringToDate(game_time, "%Y-%m-%d %I:%M %p")        
        game_time = easternToLocal(game_time)
       
        if TIME_FORMAT == '0':
             game_time = game_time.strftime('%I:%M %p').lstrip('0')
        else:
             game_time = game_time.strftime('%H:%M')

        game_time = colorString(game_time,UPCOMING)            

    else:
        game_time = game['status']

        if game_time == 'Final':                  
            game_time = colorString(game_time,FINAL)
            
        elif 'In Progress' in game_time:           
            if game['top_inning'] == 'Y':
                #up triangle
                #top_bottom = u"\u25B2"               
                top_bottom = "T"
            else:
                #down triangle
                #top_bottom = u"\u25BC"
                top_bottom = "B"                

            inning = game['inning']
            if int(inning) == 1:
                ordinal_indicator = "st"
            elif int(inning) == 2:
                ordinal_indicator = "nd"
            elif int(inning) == 3:
                ordinal_indicator = "rd"
            else:
                ordinal_indicator = "th"

            game_time = top_bottom + ' ' + inning + ordinal_indicator
            
            if int(inning) == 9:
                color = CRITICAL
            else:
                color = LIVE

            game_time = colorString(game_time,color)
        
        else:            
            game_time = colorString(game_time,LIVE)
        
        
    event_id = str(game['calendar_event_id'])

    #live_video = game['gameLiveVideo']    
    print away_team + ' ' + home_team
    epg = None
    try:
        epg = json.dumps(game['game_media']['homebase']['media'])
    except:
        pass
    live_feeds = 0
    archive_feeds = 0
    teams_stream = game['away_name_abbrev'] + game['home_name_abbrev']
    stream_date = str(game_day)

    
    desc = ''       
    hide_spoilers = 0
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game_day == localToEastern()) or (NO_SPOILERS == '4' and game_day < localToEastern()) or game['status'] == 'Preview':
        name = game_time + ' ' + away_team + ' at ' + home_team    
        hide_spoilers = 1
    else:    
        name = game_time + ' ' + away_team + ' ' + colorString(str(game['away_score']),SCORE_COLOR) + ' at ' + home_team + ' ' + colorString(str(game['home_score']),SCORE_COLOR)             

    #fanart = None   
    '''
    try:        
        if game_day < localToEastern():
            fanart = str(game['content']['media']['epg'][3]['items'][0]['image']['cuts']['1136x640']['src'])
            if hide_spoilers == 0:
                soup = BeautifulSoup(str(game['content']['editorial']['recap']['items'][0]['preview']))
                desc = soup.get_text()
        else:            
            url = 'http://statsapi.web.nhl.com/api/v1/game/'+str(game['gamePk'])+'/content?site=en_nhl'
            req = urllib2.Request(url)    
            req.add_header('Connection', 'close')
            req.add_header('User-Agent', UA_PS4)

            try:    
                response = urllib2.urlopen(req)            
                json_source = json.load(response)     
                fanart = str(json_source['editorial']['preview']['items'][0]['media']['image']['cuts']['1284x722']['src'])                                      
                soup = BeautifulSoup(str(json_source['editorial']['preview']['items'][0]['preview']))
                desc = soup.get_text()
                response.close()                
            except HTTPError as e:
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code                                  
    except:
        pass
    '''

    name = name.encode('utf-8')
    if fav_game:
        name = '[B]'+name+'[/B]'
    
    title = away_team + ' at ' + home_team
    title = title.encode('utf-8')

    #Label free game of the day if applicable
    #if bool(game['content']['media']['epg'][0]['items'][0]['freeGame']) and game_day >= localToEastern():
    #name = name + colorString(" Free", FREE)
    
    #Set audio/video info based on stream quality setting
    audio_info, video_info = getAudioVideoInfo()
    #'duration':length
    info = {'plot':desc,'tvshowtitle':'MLB','title':title,'originaltitle':title,'aired':game_day,'genre':'Sports'}

    #Create Playlist for all highlights    
    '''
    try:
        global RECAP_PLAYLIST    
        temp_recap_stream_url = createHighlightStream(game['content']['media']['epg'][3]['items'][0]['playbacks'][3]['url'])   
        listitem = xbmcgui.ListItem(title, thumbnailImage=icon)    
        listitem.setInfo( type="Video", infoLabels={ "Title": title })
        RECAP_PLAYLIST.add(temp_recap_stream_url, listitem)

        global EXTENDED_PLAYLIST
        temp_extended_stream_url = createHighlightStream(game['content']['media']['epg'][2]['items'][0]['playbacks'][3]['url'])   
        listitem = xbmcgui.ListItem(title, thumbnailImage=icon)      
        listitem.setInfo( type="Video", infoLabels={ "Title": title } )
        EXTENDED_PLAYLIST.add(temp_extended_stream_url, listitem)
    except:
        pass
    '''

    addStream(name,'',title,event_id,epg,icon,fanart,info,video_info,audio_info,teams_stream,stream_date)



def streamSelect(event_id, epg, teams_stream, stream_date):    
    epg = json.loads(epg)    
    stream_title = []    
    content_id = []
    free_game = []
    media_state = []
    playback_scenario = []
    #archive_type = ['Recap','Extended Highlights','Full Game']    
        
    for item in epg:                
        #if str(item['playback_scenario']) == "HTTP_CLOUD_WIRED_60":                        
        if str(item['playback_scenario']) == "HTTP_CLOUD_WIRED":
            stream_title.append(str(item['type'])[-4:].title() + " ("+item['display']+")")
            media_state.append(item['state'])             
            content_id.append(item['id'])  
            playback_scenario.append(str(item['playback_scenario']))       

        elif str(item['playback_scenario']) == "HTTP_CLOUD_AUDIO" and item['state'] != 'MEDIA_OFF':
            title = str(item['type']).title()
            title = title.replace('_', ' ')
            stream_title.append(title + " ("+item['display']+")")
            media_state.append(item['state'])             
            content_id.append(item['id'])  
            playback_scenario.append(str(item['playback_scenario']))          
    
    
    if len(stream_title) == 0:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Streams Not Found', msg)        
        sys.exit()

    #Reverse Order for display purposes
    #stream_title.reverse()
    #ft.reverse()
    print "MEDIA STATE"
    print media_state

    stream_url = ''
    media_auth = ''
    

    if media_state[0] == 'MEDIA_ARCHIVE':
        '''
        dialog = xbmcgui.Dialog()         
        a = dialog.select('Choose Archive', archive_type)
        if a < 2:
            if a == 0:
                #Recap                 
                try:            
                    stream_url = createHighlightStream(recap_items[0]['playbacks'][3]['url'])                
                except:
                    pass
            elif a == 1:
                #Extended Highlights                
                try:
                    stream_url = createHighlightStream(highlight_items[0]['playbacks'][3]['url'])
                except:
                    pass
        elif a == 2:
        '''
        dialog = xbmcgui.Dialog() 
        n = dialog.select('Choose Stream', stream_title)
        if n > -1:                            
            stream_url, media_auth = fetchStream(content_id[n],event_id,playback_scenario[n])            
            stream_url = createFullGameStream(stream_url,media_auth,media_state[n])  
            
            #stream_url = 'http://mlblive-akc.mlb.com/ls04/mlbam/2016/03/02/MLB_GAME_VIDEO_DETNYA_HOME_20160302/master_wired.m3u8|User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36&Cookie=mediaAuth=a06e2dc0e366b956c91a6e3cab8762e8b94e17a748934f1fac6b2c9046a8f2ef98d878b56f5d2d65b2793114f7ae0bee854ef2b9bfcfea4992fb2a8d79454176a8aa0d7fce453a519164fd743d5e208c80ce73ee1448a971a9904a6bafc9aea610c2a475f0b81a3bcfb3d1edcc02051f633cde560e571385581ec3c078e5e46a6bb21b26bf9271f449b95f2eac4a7144a26217623ebe1c2082a754defcd8209e14363854e3d8174eb88a63d151678167d0c69199f89d6139237e5be6e61b5ca5fce496d1430bfb2e86a9dc876e94de3c39087066c8538bb91f27fdfd5f25030d8f98da313afbe6a7'
            #http://mlblive-akc.mlb.com/ls04/mlbam/2016/03/07/MLB_GAME_AUDIO_HOUNYA_VISIT_20160307/master_radio.m3u8
    else:
        dialog = xbmcgui.Dialog() 
        n = dialog.select('Choose Stream', stream_title)
        if n > -1:                        
            stream_url, media_auth = fetchStream(content_id[n],event_id,playback_scenario[n])            
            stream_url = createFullGameStream(stream_url,media_auth,media_state[n])           
            
            #stream_url = 'http://mlblive-akc.mlb.com/ls04/mlbam/2016/03/02/MLB_GAME_VIDEO_DETNYA_HOME_20160302/master_wired.m3u8|User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36&Cookie=mediaAuth=a06e2dc0e366b956c91a6e3cab8762e8b94e17a748934f1fac6b2c9046a8f2ef98d878b56f5d2d65b2793114f7ae0bee854ef2b9bfcfea4992fb2a8d79454176a8aa0d7fce453a519164fd743d5e208c80ce73ee1448a971a9904a6bafc9aea610c2a475f0b81a3bcfb3d1edcc02051f633cde560e571385581ec3c078e5e46a6bb21b26bf9271f449b95f2eac4a7144a26217623ebe1c2082a754defcd8209e14363854e3d8174eb88a63d151678167d0c69199f89d6139237e5be6e61b5ca5fce496d1430bfb2e86a9dc876e94de3c39087066c8538bb91f27fdfd5f25030d8f98da313afbe6a7'
       
    
    print "STREAM BEFORE PLAY"
    print stream_url
    #example
    #http://mlblive-l3c.mlb.com/ls04/mlbam/2016/03/01/MLB_GAME_VIDEO_TORPHI_HOME_20160301/2400K/2400_complete.m3u8|User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36&Cookie=mediaAuth_v2=e3a8cff5910f220164a55042ac35b339b24eed30da31ce67b69183e8d88b8eea7acea1e1a93d5fdb18f2b9f7fcc12900f03ecb850d6b073b30d8014740e032a7d72576a96bfd2044e4883434cdbf7502f4489215b344cf2299a46b920253e0aaf1f410fdbbb2935959b005ebade07c928ead8e0322ce63ffcc86e0c058be56e48ea7272d4d56840dcd0dff6b287878a0e7d6c51535417be99545184fcbb9562578b0c1585f696a8423e1ecaf186e4d6cf536f14d372c46696c773b522c75acecf051e527623da5c26f696d53974f909568759486a0efc99484cce35493a6e829c2e90df4a2bd4f248ece44388df4667071ae414e99cb50127a1e7add204a8d27d30ffb6f3c0fbf3ee388038bb988d50a2a13effc4500653718e6eb17dd7db425df5f7c54a983ea3b8adee75a9b1daf823f3dc05ffc44f4ff2a7bb0ccf8284ac208ee09b5d14e355689a38b1e9160f4f46e5f305b9ae86063782db56aec8fef1d7394ec36ddc9e53f30659d395b194c66b9ff4d099e8825183fbd0d3aa896c612d77c8c5a593a216772a49fbbb44f2c185a65e3c4fa2ea2bd3031f3cf1185bf51c2a1390d8e0c5aedf25674527da8c06f3b6704246b1c0652de4ef50f85d2fb09681a39f791e74b1e9d490f79328267ed19c79c450c1b88cc5c3ad38894e8f4d50df0f026b4eb770fba6fefa4589451ad30f8b3d2e17312ba140c4021fe3bcbadb7b80cf38dbe45fabf03beb077807f649792f3f2052a11fe1cc7dbb738e9f5a4ef1af31f0fd49c68dd917b3a79a2296547f822cc595f817d4f4a69f4ee2275420ed9274973df19304c1baa2c9a5db19c6a6fa190c8d1fe1b7f70e667a8824ea4c975c318a01cc4e1885cbdf3d4e0288c7450beda7d1f764c8d6a39b7ce1b8f7f0235335b08252bbaeaf3f2c3bdc5736d2ecbe6c3e80e1b405c35b2c68b7968692a8a9ebea81566105872a70bb58e5b18"
    #http://mlblive-akc.mlb.com/ls04/mlbam/2016/03/01/MLB_GAME_VIDEO_CINCLE_HOME_20160301/master_wired.m3u8 
    #http://mlblive-l3c.mlb.com/ls04/mlbam/2016/03/01/MLB_GAME_VIDEO_TORPHI_HOME_20160301/2400K/2400_complete.m3u8|User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36&Cookie=mediaAuth_v2=e3a8cff5910f220164a55042ac35b339b24eed30da31ce67b69183e8d88b8eea7acea1e1a93d5fdb18f2b9f7fcc12900f03ecb850d6b073b30d8014740e032a7d72576a96bfd2044e4883434cdbf7502f4489215b344cf2299a46b920253e0aaf1f410fdbbb2935959b005ebade07c928ead8e0322ce63ffcc86e0c058be56e48ea7272d4d56840dcd0dff6b287878a0e7d6c51535417be99545184fcbb9562578b0c1585f696a8423e1ecaf186e4d6cf536f14d372c46696c773b522c75acecf051e527623da5c26f696d53974f909568759486a0efc99484cce35493a6e829c2e90df4a2bd4f248ece44388df4667071ae414e99cb50127a1e7add204a8d27d30ffb6f3c0fbf3ee388038bb988d50a2a13effc4500653718e6eb17dd7db425df5f7c54a983ea3b8adee75a9b1daf823f3dc05ffc44f4ff2a7bb0ccf8284ac208ee09b5d14e355689a38b1e9160f4f46e5f305b9ae86063782db56aec8fef1d7394ec36ddc9e53f30659d395b194c66b9ff4d099e8825183fbd0d3aa896c612d77c8c5a593a216772a49fbbb44f2c185a65e3c4fa2ea2bd3031f3cf1185bf51c2a1390d8e0c5aedf25674527da8c06f3b6704246b1c0652de4ef50f85d2fb09681a39f791e74b1e9d490f79328267ed19c79c450c1b88cc5c3ad38894e8f4d50df0f026b4eb770fba6fefa4589451ad30f8b3d2e17312ba140c4021fe3bcbadb7b80cf38dbe45fabf03beb077807f649792f3f2052a11fe1cc7dbb738e9f5a4ef1af31f0fd49c68dd917b3a79a2296547f822cc595f817d4f4a69f4ee2275420ed9274973df19304c1baa2c9a5db19c6a6fa190c8d1fe1b7f70e667a8824ea4c975c318a01cc4e1885cbdf3d4e0288c7450beda7d1f764c8d6a39b7ce1b8f7f0235335b08252bbaeaf3f2c3bdc5736d2ecbe6c3e80e1b405c35b2c68b7968692a8a9ebea81566105872a70bb58e5b18"
    #http://mlblive-akc.mlb.com/ls04/mlbam/2016/03/02/MLB_GAME_VIDEO_DETNYA_HOME_20160302/master_wired.m3u8|User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36&Cookie=mediaAuth=a06e2dc0e366b956c91a6e3cab8762e8b94e17a748934f1fac6b2c9046a8f2ef98d878b56f5d2d65b2793114f7ae0bee854ef2b9bfcfea4992fb2a8d79454176a8aa0d7fce453a519164fd743d5e208c80ce73ee1448a971a9904a6bafc9aea610c2a475f0b81a3bcfb3d1edcc02051f633cde560e571385581ec3c078e5e46a6bb21b26bf9271f449b95f2eac4a7144a26217623ebe1c2082a754defcd8209e14363854e3d8174eb88a63d151678167d0c69199f89d6139237e5be6e61b5ca5fce496d1430bfb2e86a9dc876e94de3c39087066c8538bb91f27fdfd5f25030d8f98da313afbe6a7
    listitem = xbmcgui.ListItem(path=stream_url)

    if stream_url != '':            
        #listitem.setMimeType("application/x-mpegURL")
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem)        
    else:        
        xbmcplugin.setResolvedUrl(addon_handle, False, listitem) 



def playAllHighlights():
    stream_title = ['Recap','Extended Highlights'] 
    dialog = xbmcgui.Dialog() 
    n = dialog.select('View All', stream_title)

    if n == 0:
        xbmc.Player().play(RECAP_PLAYLIST)
    elif n == 1:
        xbmc.Player().play(EXTENDED_PLAYLIST)


def createHighlightStream(stream_url):
    bandwidth = ''
    bandwidth = find(QUALITY,'(',' kbps)') 
    #Switch to ipad master file
    stream_url = stream_url.replace('master_wired.m3u8', MASTER_FILE_TYPE)

    if bandwidth != '':
        stream_url = stream_url.replace(MASTER_FILE_TYPE, 'asset_'+bandwidth+'k.m3u8')
        stream_url = stream_url + '|User-Agent='+UA_IPAD

    print stream_url
    return stream_url


def createFullGameStream(stream_url, media_auth, media_state):
    #SD (800 kbps)|SD (1600 kbps)|HD (3000 kbps)|HD (5000 kbps)        
    bandwidth = ''
    bandwidth = find(QUALITY,'(',' kbps)')

    #Only set bandwidth if it's explicitly set
    if bandwidth != '':
        if media_state == 'MEDIA_ARCHIVE':                
            #ARCHIVE
            #http://mlblive-akc.mlb.com/ls04/mlbam/2016/03/02/MLB_GAME_VIDEO_DETNYA_HOME_20160302/master_wired.m3u8 
            #http://mlblive-akc.mlb.com/ls04/mlbam/2016/03/02/MLB_GAME_VIDEO_DETNYA_HOME_20160302/1800K/1800_complete-trimmed.m3u8
            stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth+'K/'+bandwidth+'_complete-trimmed.m3u8') 

        elif media_state == 'MEDIA_ON':
            #LIVE    
            #5000K/5000_slide.m3u8 OR #3500K/3500_complete.m3u8
            # Slide = Live, Complete = Watch from beginning?
            stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth+'K/'+bandwidth+'_complete.m3u8') 

    
    #cj = cookielib.LWPCookieJar()
    #cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
    stream_url = stream_url + '|User-Agent='+UA_PS4+'&Cookie='+media_auth

    print "STREAM URL: "+stream_url
    return stream_url
    



def fetchStream(content_id,event_id,playback_scenario):        
    stream_url = ''
    media_auth = ''       
    identity_point_id = ''
    fingerprint = '' 

    expired_cookies = True
    try:
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')) 
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)        

        #Check if cookies have expired
        at_least_one_expired = False
        for cookie in cj:                        
            print cookie.name
            print cookie.expires
            print cookie.is_expired()
            if cookie.is_expired():
                at_least_one_expired = True
                break

        if not at_least_one_expired:
            expired_cookies = False
    except:
        pass

    if expired_cookies:
        login()


    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))     
    cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
    for cookie in cj: 
        print cookie           
        if cookie.name == "ipid":
            identity_point_id = cookie.value
        elif cookie.name == "fprt":
            fingerprint = cookie.value

    if identity_point_id == '' or fingerprint == '':
        return stream_url, media_auth


    session_key = getSessionKey(content_id,event_id,identity_point_id,fingerprint)
    #Reload Cookies
    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))     
    cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))        

    if session_key == '':
        return stream_url, media_auth
    elif session_key == 'blackout':
        msg = "The game you are trying to access is not currently available due to local or national blackout restrictions.\n Full game archives will be available 48 hours after completion of this game."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Game Blacked Out', msg) 
        return stream_url, media_auth

   
    #epoch_time_now = str(int(round(time.time()*1000)))

    #-------------------------
    #Playback Scenario's
    #-------------------------
    '''
    HTTP_CLOUD_WIRED
    HTTP_CLOUD_WIRED_ADS
    HTTP_CLOUD_WIRED_IRDETO
    HTTP_CLOUD_WIRED_WEB
    FMS_CLOUD
    HTTP_CLOUD_WIRED_60
    HTTP_CLOUD_WIRED_ADS_60
    HTTP_CLOUD_WIRED_IRDETO_60
    FLASH_500K_400X224
    HTTP_CLOUD_AUDIO
    AUDIO_FMS_32K
    HTTP_CLOUD_AUDIO_TS
    '''
    #https://mlb-ws.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3?identityPointId=31998790&fingerprint=dUVQMTF5bjRrd1N4Rnp0NlVTUk5wR1NMV0E4PXwxNDU3Mzc0NjI0MDU1fGlwdD1lbWFpbC1wYXNzd29yZA==&eventId=14-469489-2016-03-07&platform=WIN8&playbackScenario=HTTP_CLOUD_AUDIO&contentId=546192183&sessionKey=&subject=LIVE_EVENT_COVERAGE
    url = 'https://mlb-ws-mf.media.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
    #url = 'https://mlb-ws.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
    url = url + '?identityPointId='+identity_point_id
    url = url + '&fingerprint='+fingerprint
    url = url + '&contentId='+content_id    
    url = url + '&eventId='+event_id
    url = url + '&playbackScenario='+playback_scenario    
    url = url + '&subject=LIVE_EVENT_COVERAGE'
    url = url + '&sessionKey='+urllib.quote_plus(session_key)
    url = url + '&platform=WIN8'
    #url = url + '&frameworkURL=https%3A%2F%2Fmlb-ws-mf.media.mlb.com&frameworkEndPoint=%2Fpubajaxws%2Fbamrest%2FMediaService2_0%2Fop-findUserVerifiedEvent%2Fv-2.3'
    #url = url + '&_='+epoch_time_now
    req = urllib2.Request(url)       
    req.add_header("Accept", "*/*")
    req.add_header("Accept-Encoding", "deflate")
    req.add_header("Accept-Language", "en-US,en;q=0.8")                       
    req.add_header("Connection", "keep-alive")    
    req.add_header("User-Agent", UA_PC)

    response = opener.open(req)
    xml_data = response.read()
    response.close()
    
    stream_url = find(xml_data,'<url><![CDATA[',']]></url>')   

    print "STREAM FROM XML" 
    print stream_url
    
    #media_auth_type = find(xml_data,'<session-attribute name="','"')    
    #media_auth = media_auth_type + '=' + find(xml_data,'<session-attribute name="'+media_auth_type+'" value="','"/>')
    #if media_auth == '':
    for cookie in cj:         
        if cookie.name == "mediaAuth":
            media_auth = "mediaAuth="+cookie.value
            settings.setSetting(id='media_auth', value=media_auth)
    #else:            
    #settings.setSetting(id='media_auth', value=media_auth) 

    #Update Session Key
    session_key = find(xml_data,'<session-key>','</session-key>')
    if session_key != '':
        settings.setSetting(id='session_key', value=session_key)

    cj.save(ignore_discard=True); 

    '''
    if json_source['status_code'] == 1:
        if json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status']['status'] == 'BlackedOutStatus':
            msg = "You do not have access to view this content. To watch live games and learn more about blackout restrictions, please visit NHL.TV"
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Game Blacked Out', msg) 
        else:
            stream_url = json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['url']    
            media_auth = str(json_source['session_info']['sessionAttributes'][0]['attributeName']) + "=" + str(json_source['session_info']['sessionAttributes'][0]['attributeValue'])
            session_key = json_source['session_key']
            settings.setSetting(id='media_auth', value=media_auth) 
            #Update Session Key
            settings.setSetting(id='session_key', value=session_key)   
    else:
        msg = json_source['status_message']
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Error Fetching Stream', msg)       
    '''

    return stream_url, media_auth    
   



def getSessionKey(content_id,event_id,identity_point_id,fingerprint):    
    #session_key = ''
    session_key = str(settings.getSetting(id="session_key"))

    if session_key == '':               
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')) 
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))  

        epoch_time_now = str(int(round(time.time()*1000)))   
        #url = 'https://mf.svc.nhl.com/ws/media/mf/v2.4/stream?eventId='+event_id+'&format=json&platform=WEB_MEDIAPLAYER&subject=NHLTV&_='+epoch_time_now        
        url = 'https://mlb-ws-mf.media.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
        url = url + '?identityPointId='+identity_point_id
        url = url + '&fingerprint='+fingerprint
        url = url + '&eventId='+event_id
        url = url + '&subject=LIVE_EVENT_COVERAGE'
        url = url + '&platform=WIN8'
        url = url + '&frameworkURL=https://mlb-ws-mf.media.mlb.com&frameworkEndPoint=/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
        url = url + '&_='+epoch_time_now

        req = urllib2.Request(url)       
        req.add_header("Accept", "*/*")
        req.add_header("Accept-Encoding", "deflate")
        req.add_header("Accept-Language", "en-US,en;q=0.8")                       
        req.add_header("Connection", "keep-alive")        
        req.add_header("User-Agent", UA_PC)
        req.add_header("Origin", "http://m.mlb.com")        
        req.add_header("Referer", "http://m.mlb.com/tv/e"+event_id+"/v"+content_id+"/?&media_type=video&clickOrigin=Media Grid&team=mlb&forwardUrl=http://m.mlb.com/tv/e"+event_id+"/v"+content_id+"/?&media_type=video&clickOrigin=Media%20Grid&team=mlb&template=mp5default&flowId=registration.dynaindex&mediaTypeTemplate=video")
        
        response = opener.open(req)
        xml_data = response.read()
        response.close()
        
        print "REQUESTED SESSION KEY"
        session_key = find(xml_data,'<session-key>','</session-key>')
        settings.setSetting(id='session_key', value=session_key)

        '''
        if json_source['status_code'] == 1:      
            if json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status']['status'] == 'BlackedOutStatus':
                msg = "You do not have access to view this content. To watch live games and learn more about blackout restrictions, please visit NHL.TV"
                session_key = 'blackout'
            else:    
                session_key = str(json_source['session_key'])
                settings.setSetting(id='session_key', value=session_key)                              
        else:
            msg = json_source['status_message']
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Error Fetching Stream', msg)            
        '''
    return session_key  
    

def myTeamsGames():    
    if FAV_TEAM != 'None':
        fav_team_id = getFavTeamId()

        end_date = localToEastern()
        end_date = stringToDate(end_date, "%Y-%m-%d")            
        start_date = end_date - timedelta(days=30) 
        start_date = start_date.strftime("%Y%m%d")
        end_date = end_date.strftime("%Y%m%d")
        season = start_date.strftime("%Y")
        

        url = 'http://mlb.mlb.com/lookup/named.schedule_vw.bam?end_date='+end_date+'&season='+season+'&team_id='+fav_team_id+'&start_date='+start_date
        #${expand},schedule.ticket&${optionalParams}'
        req = urllib2.Request(url)   
        req.add_header('User-Agent', UA_IPAD)
        response = urllib2.urlopen(req)    
        json_source = json.load(response)                           
        response.close()

        #<row game_pk="469406" record_source="S" game_id="2016/03/01/pitmlb-detmlb-1" game_type="S" month="3" game_date="2016-03-01T00:00:00" month_abbrev="Mar" month_full="March" day="3" day_abbrev="Tue" game_day="Tuesday" double_header_sw="N" gameday_sw="Y" interleague_sw="" game_nbr="1" series_nbr="1" series_game_nbr="1" game_time_et="2016-03-01T13:05:00" if_necessary="N" scheduled_innings="9" inning="9" top_inning_sw="N" away_team_id="134" away_all_star_sw="N" away_team_file_code="pit" away_team_city="Pittsburgh" away_team_full="Pittsburgh Pirates" away_team_brief="Pirates" away_team_abbrev="PIT" away_league_id="104" away_league="NL" away_sport_code="mlb" away_parent_id="" away_parent_org="" away_split_squad="N" home_team_id="116" home_all_star_sw="N" home_team_file_code="det" home_team_city="Detroit" home_team_full="Detroit Tigers" home_team_brief="Tigers" home_team_abbrev="DET" home_league_id="103" home_league="AL" home_sport_code="mlb" home_parent_id="" home_parent_org="" home_split_squad="N" venue_id="2511" venue="Joker Marchant Stadium" venue_short="" venue_city="Lakeland" venue_state="FL" venue_country="USA" milbtv_sw="N" home_tunein="" away_tunein="" game_time_local="3/1/2016 1:05:00 PM" time_zone_local="EST" game_time_home="3/1/2016 1:05:00 PM" time_zone_home="EST" game_time_away="3/1/2016 1:05:00 PM" time_zone_away="EST" resumed_on="" resumed_at="" resumed_from="" rescheduled_to="" rescheduled_at="" rescheduled_from="" game_status_ind="F" game_status_text="Final" reason="" home_probable_id="571510" home_probable="Boyd, Matt" home_probable_wl="0-0" home_probable_era="-.--" away_probable_id="543456" away_probable="Lobstein, Kyle" away_probable_wl="0-0" away_probable_era="-.--" home_team_wl="0-1" away_team_wl="1-0" home_score="2" away_score="4" home_result="L" away_result="W" win_pitcher_id="543746" win_pitcher="Scahill, Rob" win_pitcher_wl="1-0" win_pitcher_era="18.00" loss_pitcher_id="434137" loss_pitcher="Kensing, Logan" loss_pitcher_wl="0-1" loss_pitcher_era="18.00" editorial_stats_type="S" editorial_stats_season="2016"/>
        match = re.compile('<row (.+?)/">').findall(link)   

        for game_row in match:  
        
            for game in date['games']:        
                createGameListItem(game, date['date'])  

        
    else:
        msg = "Please select your favorite team from the addon settings"
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Favorite Team Not Set', msg)


def login():    
    #Check if username and password are provided    
    global USERNAME
    if USERNAME == '':        
        dialog = xbmcgui.Dialog()
        USERNAME = dialog.input('Please enter your username', type=xbmcgui.INPUT_ALPHANUM)        
        settings.setSetting(id='username', value=USERNAME)

    global PASSWORD
    if PASSWORD == '':        
        dialog = xbmcgui.Dialog()
        PASSWORD = dialog.input('Please enter your password', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
        settings.setSetting(id='password', value=PASSWORD)

   
    if USERNAME != '' and PASSWORD != '':        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')) 
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))   
         
        url = 'https://securea.mlb.com/authenticate.do'            
        login_data = 'uri=%2Faccount%2Flogin_register.jsp&registrationAction=identify&emailAddress='+USERNAME+'&password='+PASSWORD+'&submitButton='


        req = urllib2.Request(url, data=login_data, headers=
            {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
             "Accept-Encoding": "gzip, deflate",
             "Accept-Language": "en-US,en;q=0.8",
             "Content-Type": "application/x-www-form-urlencoded",                            
             "Origin": "https://securea.mlb.com",             
             "Connection": "keep-alive",
             #"Cookie": "SESSION_1=wf_forwardUrl===http://m.mlb.com/tv/e14-469412-2016-03-02/v545147283/?&media_type=video&clickOrigin=Media%20Grid&team=mlb~wf_flowId===registration.dynaindex~wf_template===mp5default~wf_mediaTypeTemplate===video~stage===3~flowId===registration.dynaindex~forwardUrl===http://m.mlb.com/tv/e14-469412-2016-03-02/v545147283/?&media_type=video&clickOrigin=Media%20Grid&team=mlb;",
             "Cookie": "SESSION_1=wf_forwardUrl%3D%3D%3Dhttp%3A%2F%2Fm.mlb.com%2Ftv%2Fe14-469412-2016-03-02%2Fv545147283%2F%3F%26media_type%3Dvideo%26clickOrigin%3DMedia%2520Grid%26team%3Dmlb%7Ewf_flowId%3D%3D%3Dregistration.dynaindex%7Ewf_template%3D%3D%3Dmp5default%7Ewf_mediaTypeTemplate%3D%3D%3Dvideo%7Estage%3D%3D%3D3%7EflowId%3D%3D%3Dregistration.dynaindex%7EforwardUrl%3D%3D%3Dhttp%3A%2F%2Fm.mlb.com%2Ftv%2Fe14-469412-2016-03-02%2Fv545147283%2F%3F%26media_type%3Dvideo%26clickOrigin%3DMedia%2520Grid%26team%3Dmlb%3B",
             "User-Agent": UA_PC})  
             
       
        try:
            response = opener.open(req) 
        except HTTPError as e:
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code    
            print url   
            
            #Error 401 for invalid login
            if e.code == 401:
                msg = "Please check that your username and password are correct"
                dialog = xbmcgui.Dialog() 
                ok = dialog.ok('Invalid Login', msg)

        #response = opener.open(req)              
        #user_data = response.read()
        response.close()
      

        cj.save(ignore_discard=True); 


    
params=get_params()
url=None
name=None
mode=None
game_day=None
event_id=None
epg=None
teams_stream=None
stream_date=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
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
    epg=urllib.unquote_plus(params["epg"])
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


print "Mode: "+str(mode)
#print "URL: "+str(url)
print "Name: "+str(name)



if mode==None or url==None:        
    categories()  

elif mode == 100:      
    #Todays Games            
    todaysGames(None)    

elif mode == 101:
    #Prev and Next 
    todaysGames(game_day)    

elif mode == 104:    
    streamSelect(event_id, epg, teams_stream, stream_date)

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
    print game_day
    mat=re.match('(\d{4})-(\d{2})-(\d{2})$', game_day)        
    if mat is not None:    
        todaysGames(game_day)
    else:    
        if game_day != '':    
            msg = "The date entered is not in the format required."
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Invalid Date', msg)

        sys.exit()        

elif mode == 300:
    nhlVideos()

elif mode == 400:    
    logout('true')

elif mode == 500:
    myTeamsGames()

elif mode == 900:
    playAllHighlights()    

elif mode == 999:
    sys.exit()

print mode
if mode==100 or mode==101 or mode==104 or mode==105 or mode==200 or mode==300 or mode==500: 
   setViewMode()
elif mode==None:
    getViewMode()
    
print "My view mode " + VIEW_MODE

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 101:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)