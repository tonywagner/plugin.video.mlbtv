from resources.lib.globals import *


def categories():
    addDir('Today\'s Games', 100, ICON, FANART)
    addDir('Yesterday\'s Games', 105, ICON, FANART)
    # addDir('Favorite Team Recent Games','favteam',500,ICON,FANART)
    addDir('Goto Date', 200, ICON, FANART)


def todays_games(game_day):
    if game_day is None:
        game_day = localToEastern()

    settings.setSetting(id='stream_date', value=game_day)

    display_day = stringToDate(game_day, "%Y-%m-%d")
    #url_game_day = display_day.strftime('year_%Y/month_%m/day_%d')
    prev_day = display_day - timedelta(days=1)

    addDir('[B]<< Previous Day[/B]', 101, PREV_ICON, FANART, prev_day.strftime("%Y-%m-%d"))

    date_display = '[B][I]' + colorString(display_day.strftime("%A, %m/%d/%Y"), GAMETIME_COLOR) + '[/I][/B]'

    addPlaylist(date_display, str(game_day), 900, ICON, FANART)

    # addPlaylist(date_display,display_day,'/playhighlights',999,ICON,FANART)

    #url = 'http://gdx.mlb.com/components/game/mlb/' + url_game_day + '/grid_ce.json'
    url = 'https://statsapi.mlb.com/api/v1/schedule'
    url += '?hydrate=broadcasts(all),game(content(all)),linescore,team'
    url += '&sportId=1,51'
    url += '&date=' + game_day


    """
    req = urllib2.Request(url)
    req.add_header('Connection', 'close')
    req.add_header('User-Agent', UA_PS4)

    try:
        response = urllib2.urlopen(req)
        json_source = json.load(response)
        response.close()
    except HTTPError as e:
        xbmc.log('The server couldn\'t fulfill the request.')
        xbmc.log('Error code: ', e.code)
        sys.exit()
    """
    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url,headers=headers, verify=VERIFY)
    json_source = r.json()

    global RECAP_PLAYLIST
    global EXTENDED_PLAYLIST
    RECAP_PLAYLIST.clear()
    EXTENDED_PLAYLIST.clear()

    for game in json_source['dates'][0]['games']:
        create_game_listitem(game, game_day)

    next_day = display_day + timedelta(days=1)
    addDir('[B]Next Day >>[/B]', 101, NEXT_ICON, FANART, next_day.strftime("%Y-%m-%d"))


def create_game_listitem(game, game_day):
    # icon = getGameIcon(game['home_team_id'],game['away_team_id'])
    icon = ICON
    # http://mlb.mlb.com/mlb/images/devices/ballpark/1920x1080/2681.jpg
    # B&W
    # fanart = 'http://mlb.mlb.com/mlb/images/devices/ballpark/1920x1080/'+game['venue_id']+'.jpg'
    # Color
    fanart = 'http://www.mlb.com/mlb/images/devices/ballpark/1920x1080/color/' + str(game['venue']['id']) + '.jpg'

    xbmc.log(str(game['gamePk']))

    if TEAM_NAMES == "0":
        away_team = game['teams']['away']['team']['teamName']
        home_team = game['teams']['home']['team']['teamName']
    else:
        away_team = game['teams']['away']['team']['abbreviation']
        home_team = game['teams']['home']['team']['abbreviation']

    fav_game = False

    if game['teams']['away']['team']['name'].encode('utf-8') in FAV_TEAM:
        fav_game = True
        away_team = colorString(away_team, getFavTeamColor())

    if game['teams']['home']['team']['name'].encode('utf-8') in FAV_TEAM:
        fav_game = True
        home_team = colorString(home_team, getFavTeamColor())

    game_time = ''
    if game['status']['abstractGameState'] == 'Preview':
        game_time = game['gameDate']
        game_time = stringToDate(game_time, "%Y-%m-%dT%H:%M:%SZ")
        game_time = easternToLocal(game_time)

        if TIME_FORMAT == '0':
            game_time = game_time.strftime('%I:%M %p').lstrip('0')
        else:
            game_time = game_time.strftime('%H:%M')

        game_time = colorString(game_time, UPCOMING)

    else:
        game_time = game['status']['abstractGameState']

        if game_time == 'Final':
            game_time = colorString(game_time, FINAL)

        elif game['status']['abstractGameState'] == 'Live':
            if game['linescore']['isTopInning']:
                # up triangle
                # top_bottom = u"\u25B2"
                top_bottom = "T"
            else:
                # down triangle
                # top_bottom = u"\u25BC"
                top_bottom = "B"

            inning = game['linescore']['currentInningOrdinal']
            game_time = top_bottom + ' ' + inning

            if game['linescore']['currentInning'] >= 9:
                color = CRITICAL
            else:
                color = LIVE

            game_time = colorString(game_time, color)

        else:
            game_time = colorString(game_time, LIVE)

    #event_id = str(game['calendar_event_id'])
    game_pk = game['gamePk']
    #gid = game['id']
    gid = 'junk'

    live_feeds = 0
    archive_feeds = 0
    stream_date = str(game_day)

    desc = ''
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game_day == localToEastern()) or (NO_SPOILERS == '4' and game_day < localToEastern()) or game['status']['abstractGameState'] == 'Preview':
        name = game_time + ' ' + away_team + ' at ' + home_team
    else:
        name = game_time + ' ' + away_team + ' ' + colorString(str(game['linescore']['teams']['away']['runs']), SCORE_COLOR) + ' at ' + home_team + ' ' + colorString(str(game['linescore']['teams']['home']['runs']), SCORE_COLOR)

    name = name.encode('utf-8')
    if fav_game:
        name = '[B]' + name + '[/B]'

    title = away_team + ' at ' + home_team
    title = title.encode('utf-8')

    # Label free game of the day if applicable
    try:
        if game['content']['media']['freeGame']:
            # and game_day >= localToEastern():
            name = colorString(name, FREE)
    except:
        pass


    # Set audio/video info based on stream quality setting
    audio_info, video_info = getAudioVideoInfo()
    # 'duration':length
    info = {'plot': desc, 'tvshowtitle': 'MLB', 'title': title, 'originaltitle': title, 'aired': game_day, 'genre': LOCAL_STRING(700), 'mediatype': 'video'}

    # Create Playlist for the days recaps and condensed
    """
    try:
        recap_url, condensed_url = getHighlightLinks(teams_stream, stream_date)
        global RECAP_PLAYLIST
        listitem = xbmcgui.ListItem(title, thumbnailImage=icon)
        listitem.setInfo(type="Video", infoLabels={"Title": title})
        RECAP_PLAYLIST.add(recap_url, listitem)

        global EXTENDED_PLAYLIST
        listitem = xbmcgui.ListItem(title, thumbnailImage=icon)
        listitem.setInfo(type="Video", infoLabels={"Title": title})
        EXTENDED_PLAYLIST.add(condensed_url, listitem)
    except:
        pass
    """

    addStream(name, title, game_pk, icon, fanart, info, video_info, audio_info, stream_date)


def stream_select(game_pk, stream_date):
    url = 'https://statsapi.mlb.com/api/v1/game/' + game_pk + '/content'
    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url,headers=headers, verify=VERIFY)
    json_source = r.json()

    stream_title = []
    media_id = []
    free_game = []
    media_state = []
    playback_scenario = []
    epg = json_source['media']['epg'][0]['items']
    for item in epg:
        xbmc.log(str(item))
        if item['mediaState'] != 'MEDIA_OFF':
            title = str(item['mediaFeedType']).title()
            title = title.replace('_', ' ')
            stream_title.append(title + " (" + item['callLetters'].encode('utf-8') + ")")
            media_state.append(item['mediaState'])
            media_id.append(item['mediaId'])
            # content_id.append(item['guid'])
            # playback_scenario.append(str(item['playback_scenario']))

    '''
    elif str(item['playback_scenario']) == "FLASH_2500K_1280X720" and item['type'] != 'condensed_game':
        title = str(item['type']).title()
        title = title.replace('_', ' ')
        stream_title.append(title + " ("+item['display']+")")
        media_state.append(item['state'])             
        content_id.append(item['id'])  
        playback_scenario.append("HTTP_CLOUD_WIRED_60") 
    '''
    # All past games should have highlights
    if len(stream_title) == 0 and stream_date > localToEastern():
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog()
        dialog.ok('Streams Not Found', msg)
        sys.exit()


    """        
    play_highlights = 0
    if len(media_state) > 0:
        if media_state[0] == 'MEDIA_ARCHIVE':
            stream_url = choose_archive(stream_title, media_id)
        else:
            # Add Highlights option to live games
            #stream_title.insert(0, 'Highlights')
            dialog = xbmcgui.Dialog()
            n = dialog.select('Choose Stream', stream_title)
            if n > -1:
                if stream_title[n] == 'Highlights':
                    recap, condensed, highlights = getHighlightLinks(teams_stream, stream_date)
                    if len(highlights) > 0:
                        play_highlights = 1
                        if QUALITY == 'Always Ask':
                            bandwidth = getStreamQuality(str(highlights[0][0]))
                        else:
                            bandwidth = find(QUALITY, '(', ' kbps)')
                else:
                    stream_url = get_stream(media_id[n])
    else:
        archive_type = ['Highlights']
        dialog = xbmcgui.Dialog()
        a = dialog.select('Choose Archive', archive_type)
        if a == 0:
            # getHighlightLinks(teams_stream, stream_date)
            play_highlights = 1
    """
    dialog = xbmcgui.Dialog()
    n = dialog.select('Choose Stream', stream_title)
    stream_url = get_stream(media_id[n])

    listitem = xbmcgui.ListItem(path=stream_url)
    listitem.setMimeType("application/x-mpegURL")

    if '.m3u8' in stream_url:
        xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)

    elif play_highlights == 1:
        highlight_name = ['Play All']
        highlight_url = ['junk']
        for i in range(0, len(highlights) - 1):
            # highlights.append([clip_url,headline,icon])
            highlight_url.append(highlights[i][0])
            highlight_name.append(highlights[i][1])

        dialog = xbmcgui.Dialog()
        a = dialog.select('Choose Highlight', highlight_name)
        if a > 0:
            # listitem = xbmcgui.ListItem(thumbnailImage=highlights[a-1][2], path=highlights[a-1][0])
            listitem = xbmcgui.ListItem(path=createHighlightStream(highlight_url[a], bandwidth))
            listitem.setInfo(type="Video", infoLabels={"Title": highlight_name[a]})
            xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)
        elif a == 0:
            HIGHLIGHT_PLAYLIST = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            HIGHLIGHT_PLAYLIST.clear()
            xbmc.log(str(highlights))

            listitem = xbmcgui.ListItem('dummy', thumbnailImage='')
            listitem.setInfo(type="Video", infoLabels={"Title": 'dummy'})
            HIGHLIGHT_PLAYLIST.add('http://cdn.gravlab.net/sparse/v1d30/2013/nightskyHLS/Lapse2.m3u8', listitem)

            for i in range(0, len(highlights) - 1):
                # highlights.append([clip_url,headline,icon])
                listitem = xbmcgui.ListItem(highlights[i][1], thumbnailImage=highlights[i][2])
                listitem.setInfo(type="Video", infoLabels={"Title": highlights[i][1]})
                HIGHLIGHT_PLAYLIST.add(createHighlightStream(highlights[i][0], bandwidth), listitem)
    else:
        # xbmcplugin.setResolvedUrl(addon_handle, False, listitem)
        xbmc.executebuiltin('Dialog.Close(all,true)')


def choose_archive(stream_title, media_id):
    archive_type = ['Highlights', 'Recap', 'Condensed', 'Full Game']
    dialog = xbmcgui.Dialog()
    a = dialog.select('Choose Archive', archive_type)

    if a > -1:
        if archive_type[a].lower() != 'full game':
            #recap, condensed, highlights = getHighlightLinks(teams_stream, stream_date)
            if archive_type[a].lower() == 'highlights':
                play_highlights = 1
            elif archive_type[a].lower() == 'recap':
                if 'url' in recap:
                    stream_url = recap['url']
                else:
                    dialog = xbmcgui.Dialog()
                    dialog.ok('Recap Not Available', 'The recap for this game is not yet available. \nPlease check back later.')
            else:
                if 'url' in condensed:
                    stream_url = condensed['url']
                else:
                    dialog = xbmcgui.Dialog()
                    dialog.ok('Condensed Game Not Available', 'The condensed game is not yet available. \nPlease check back later.')
            """                    
            if QUALITY == 'Always Ask' and ((len(highlights) > 0 and play_highlights == 1) or stream_url != ''):
                bandwidth = getStreamQuality(str(highlights[0][0]))
            else:
                bandwidth = find(QUALITY, '(', ' kbps)')
            """
            stream_url = createHighlightStream(stream_url, bandwidth)
        else:
            dialog = xbmcgui.Dialog()
            n = dialog.select('Choose Stream', stream_title)
            if n > -1:
                # stream_url, media_auth = fetchStream(content_id[n], event_id, playback_scenario[n])
                # stream_url = createFullGameStream(stream_url, media_auth, media_state[n])
                stream_url = get_stream(media_id[n])

        return stream_url


def playAllHighlights():
    stream_title = ['Recap', 'Condensed']
    dialog = xbmcgui.Dialog()
    n = dialog.select('View All', stream_title)

    if n == 0:
        xbmc.Player().play(RECAP_PLAYLIST)
    elif n == 1:
        xbmc.Player().play(EXTENDED_PLAYLIST)


def getGamesForDate(stream_date):
    stream_date_new = stringToDate(stream_date, "%Y-%m-%d")
    year = stream_date_new.strftime("%Y")
    month = stream_date_new.strftime("%m")
    day = stream_date_new.strftime("%d")

    url = 'http://gdx.mlb.com/components/game/mlb/year_' + year + '/month_' + month + '/day_' + day + '/'
    req = urllib2.Request(url)
    req.add_header('Connection', 'close')
    req.add_header('User-Agent', UA_IPAD)

    try:
        response = urllib2.urlopen(req)
        html_data = response.read()
        response.close()
    except HTTPError as e:
        xbmc.log('The server couldn\'t fulfill the request.')
        xbmc.log('Error code: ', e.code)
        sys.exit()

    # <li><a href="gid_2016_03_13_arimlb_chamlb_1/"> gid_2016_03_13_arimlb_chamlb_1/</a></li>
    match = re.compile('<li><a href="gid_(.+?)/">(.+?)</a></li>', re.DOTALL).findall(html_data)
    global RECAP_PLAYLIST
    global EXTENDED_PLAYLIST
    RECAP_PLAYLIST.clear()
    EXTENDED_PLAYLIST.clear()

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create('MLB Highlights', 'Retrieving Streams ...')
    match_count = len(match)
    if match_count == 0:
        match_count = 1  # prevent division by zero when no games
    perc_increments = 100 / match_count
    first_time_thru = True
    bandwidth = find(QUALITY, '(', ' kbps)')

    for gid, junk in match:
        pDialog.update(perc_increments, message='Downloading ' + gid)
        try:
            recap, condensed, highlights = getHighlightLinks(None, stream_date, gid)

            if first_time_thru and QUALITY == 'Always Ask':
                bandwidth = getStreamQuality(str(recap['url']))
                first_time_thru = False

            listitem = xbmcgui.ListItem(recap['title'], thumbnailImage=recap['icon'])
            listitem.setInfo(type="Video", infoLabels={"Title": recap['title']})
            RECAP_PLAYLIST.add(createHighlightStream(recap['url'], bandwidth), listitem)

            listitem = xbmcgui.ListItem(condensed['title'], thumbnailImage=condensed['icon'])
            listitem.setInfo(type="Video", infoLabels={"Title": condensed['title']})
            EXTENDED_PLAYLIST.add(createHighlightStream(condensed['url'], bandwidth), listitem)
        except:
            pass

        perc_increments += perc_increments

    pDialog.close()


def createHighlightStream(url, bandwidth):
    if bandwidth != '' and int(bandwidth) < 4500:
        url = url.replace('master_tablet_60.m3u8', 'asset_' + bandwidth + 'K.m3u8')

    url = url + '|User-Agent=' + UA_IPAD

    return url


def getHighlightLinks(teams_stream, stream_date, gid=None, bandwidth=None):
    # global HIGHLIGHT_PLAYLIST
    # HIGHLIGHT_PLAYLIST.clear()
    stream_date = stringToDate(stream_date, "%Y-%m-%d")
    year = stream_date.strftime("%Y")
    month = stream_date.strftime("%m")
    day = stream_date.strftime("%d")

    if gid is None:
        away = teams_stream[:3].lower()
        home = teams_stream[3:].lower()
        url = 'http://gdx.mlb.com/components/game/mlb/year_' + year + '/month_' + month + '/day_' + day + '/gid_' + year + '_' + month + '_' + day + '_' + away + 'mlb_' + home + 'mlb_1/media/mobile.xml'
    else:
        url = 'http://gdx.mlb.com/components/game/mlb/year_' + year + '/month_' + month + '/day_' + day + '/gid_' + gid + '/media/mobile.xml'

    req = urllib2.Request(url)
    req.add_header('Connection', 'close')
    req.add_header('User-Agent', UA_IPAD)
    try:
        response = urllib2.urlopen(req)
        xml_data = response.read()
        response.close()
    except HTTPError as e:
        xbmc.log('The server couldn\'t fulfill the request.')
        xbmc.log('Error code: ', e.code)
        sys.exit()

    match = re.compile('<media id="(.+?)"(.+?)<headline>(.+?)</headline>(.+?)<thumb type="22">(.+?)</thumb>(.+?)<url playback-scenario="HTTP_CLOUD_TABLET_60">(.+?)</url>', re.DOTALL).findall(xml_data)
    bandwidth = find(QUALITY, '(', ' kbps)')

    recap = {}
    condensed = {}
    highlights = []

    for media_id, media_tag, headline, junk1, icon, junk2, clip_url in match:
        if 'media-type="T"' in media_tag:
            # if bandwidth != '' and int(bandwidth) < 4500:
            # clip_url = clip_url.replace('master_tablet_60.m3u8', 'asset_'+bandwidth+'K.m3u8')

            # clip_url = clip_url + '|User-Agent='+UA_IPAD
            highlights.append([clip_url, headline, icon])

        if 'media-type="R"' in media_tag:
            # icon = 'http://mediadownloads.mlb.com/mlbam/'+year+'/'+month+'/'+day+'/images/mlbf_'+media_id+'_th_43.jpg'
            title = headline
            recap = {'url': clip_url, 'icon': icon, 'title': headline}
        elif 'media-type="C"' in media_tag:
            # icon = 'http://mediadownloads.mlb.com/mlbam/'+year+'/'+month+'/'+day+'/images/mlbf_'+media_id+'_th_43.jpg'
            title = headline
            condensed = {'url': clip_url, 'icon': icon, 'title': headline}

    return recap, condensed, highlights


def createFullGameStream(stream_url, media_auth, media_state):
    # SD (800 kbps)|SD (1600 kbps)|HD (3000 kbps)|HD (5000 kbps)
    bandwidth = ''
    bandwidth = find(QUALITY, '(', ' kbps)')

    if QUALITY == 'Always Ask':
        bandwidth = getStreamQuality(stream_url)

    # Only set bandwidth if it's explicitly set
    if bandwidth != '':
        if media_state == 'MEDIA_ARCHIVE':
            # ARCHIVE
            # stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth+'K/'+bandwidth+'_complete_fwv2-trimmed.m3u8')
            stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth + 'K/' + bandwidth + '_complete-trimmed.m3u8')
        elif media_state == 'MEDIA_ON':
            # LIVE
            # stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth+'K/'+bandwidth+'_slide_fwv2.m3u8')
            stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth + 'K/' + bandwidth + '_complete.m3u8')

    # CDN
    akc_url = 'akc.mlb.com'
    l3c_url = 'l3c.mlb.com'
    if CDN == 'Akamai' and akc_url not in stream_url:
        stream_url = stream_url.replace(l3c_url, akc_url)
    elif CDN == 'Level 3' and l3c_url not in stream_url:
        stream_url = stream_url.replace(akc_url, l3c_url)

    # stream_url = stream_url + '|User-Agent='+UA_IPAD+'&Cookie='+media_auth
    stream_url = stream_url + '|User-Agent=' + UA_PS4 + '&Cookie=' + media_auth

    return stream_url


def fetchStream(content_id, event_id, playback_scenario):
    stream_url = ''
    media_auth = ''
    identity_point_id = ''
    fingerprint = ''

    expired_cookies = True
    try:
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'), ignore_discard=True)

        # Check if cookies have expired
        at_least_one_expired = False
        num_cookies = 0
        for cookie in cj:
            num_cookies += 1
            if cookie.is_expired():
                at_least_one_expired = True
                break

        if not at_least_one_expired:
            expired_cookies = False
    except:
        pass

    if expired_cookies or num_cookies == 0 or USERNAME != OLD_USERNAME or PASSWORD != OLD_PASSWORD:
        # Remove cookie file
        cookie_file = xbmc.translatePath(os.path.join(ADDON_PATH_PROFILE + 'cookies.lwp'))
        try:
            os.remove(cookie_file)
        except:
            pass
        login()

    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
    cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'), ignore_discard=True)
    for cookie in cj:
        if cookie.name == "ipid":
            identity_point_id = cookie.value
        elif cookie.name == "fprt":
            fingerprint = cookie.value

    if identity_point_id == '' or fingerprint == '':
        return stream_url, media_auth

    session_key = getSessionKey(content_id, event_id, identity_point_id, fingerprint)
    # Reload Cookies
    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
    cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'), ignore_discard=True)

    if PROXY_ENABLED != 'true':
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    else:
        proxy_url = 'http://' + PROXY_SERVER + ':' + PROXY_PORT
        proxy_support = urllib2.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        if PROXY_USER != '' and PROXY_PWD != '':
            auth_handler = urllib2.ProxyBasicAuthHandler()
            auth_handler.add_password(None, proxy_url, PROXY_USER, PROXY_PWD)
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), proxy_support, auth_handler)
        else:
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), proxy_support)

        urllib2.install_opener(opener)

    if session_key == '':
        return stream_url, media_auth
    elif session_key == 'blackout':
        msg = "The game you are trying to access is not currently available due to local or national blackout restrictions.\n Full game archives will be available 48 hours after completion of this game."
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('Game Blacked Out', msg)
        return stream_url, media_auth

    url = 'https://mlb-ws-mf.media.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
    url = url + '?identityPointId=' + identity_point_id
    url = url + '&fingerprint=' + fingerprint
    url = url + '&contentId=' + content_id
    url = url + '&eventId=' + event_id
    url = url + '&playbackScenario=' + playback_scenario
    url = url + '&subject=LIVE_EVENT_COVERAGE'
    url = url + '&sessionKey=' + urllib.quote_plus(session_key)
    url = url + '&platform=PS4'
    url = url + '&format=json'
    req = urllib2.Request(url)
    req.add_header("Accept", "*/*")
    req.add_header("Accept-Encoding", "deflate")
    req.add_header("Accept-Language", "en-US,en;q=0.8")
    req.add_header("Connection", "keep-alive")
    req.add_header("User-Agent", UA_PS4)

    response = opener.open(req)
    json_source = json.load(response)
    response.close()

    if json_source['status_code'] == 1:
        uv_media_item = json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]
        if 'BLACKOUT' in str(uv_media_item['blackout_status']).upper():
            msg = "We're sorry.  We have determined that you are blacked out of watching the game you selected due to Major League Baseball exclusivities."
            # try:
            if str(uv_media_item['media_item']['state']).upper() == 'MEDIA_ARCHIVE':
                # cc_url = str(json_source['user_verified_event'][0]['user_verified_content'][0]['domain_specific_attributes'][3]['value'])
                for attribute in json_source['user_verified_event'][0]['user_verified_content'][0]['domain_specific_attributes']:
                    if str(attribute['name']).lower() == 'inning_index_location_xml':
                        inning_xml_url = str(attribute['value'])
                        # inning_xml_url = "http://mlb.mlb.com/mlb/mmls2016/447002.xml"
                        blackout_lift_min, blackout_lift_time = getBlackoutLiftTime(inning_xml_url)
                        msg = msg + " This blackout will expire in " + str(blackout_lift_min) + " minutes at approximately " + str(blackout_lift_time) + "."
                        break

            dialog = xbmcgui.Dialog()
            ok = dialog.ok('Game Blacked Out', msg)
            sys.exit()
            xbmc.executebuiltin('Dialog.Close(all,true)')
        elif str(uv_media_item['auth_status']) == 'NotAuthorizedStatus':
            msg = "You do not have an active MLB.TV premium subscription. If you are using a Single Team or Free subscription please check this is enabled in the addon settings."
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('Account Not Authorized', msg)
            sys.exit()
            xbmc.executebuiltin('Dialog.Close(all,true)')
        else:
            stream_url = uv_media_item['url']
            # Find subtitles
            '''
            for item in json_source['user_verified_event'][0]['user_verified_content'][0]['domain_specific_attributes']:
                if item['name'] == 'closed_captions_location_ttml':
                    subtitles_url = item['value']
                    convertSubtitles(subtitles_url)
            '''
            session_key = json_source['session_key']
            # Update Session Key
            settings.setSetting(id='session_key', value=session_key)
    else:
        msg = json_source['status_message']
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('Error Fetching Stream', msg)

    for cookie in cj:
        if cookie.name == "mediaAuth":
            media_auth = "mediaAuth=" + cookie.value
            settings.setSetting(id='media_auth', value=media_auth)

    cj.save(ignore_discard=True)

    return stream_url, media_auth


def getSessionKey(content_id, event_id, identity_point_id, fingerprint):
    # session_key = ''
    session_key = str(settings.getSetting(id="session_key"))

    if session_key == '':
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'), ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        epoch_time_now = str(int(round(time.time() * 1000)))
        url = 'https://mlb-ws-mf.media.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
        url = url + '?identityPointId=' + identity_point_id
        url = url + '&fingerprint=' + fingerprint
        url = url + '&eventId=' + event_id
        url = url + '&subject=LIVE_EVENT_COVERAGE'
        url = url + '&platform=WIN8'
        url = url + '&frameworkURL=https://mlb-ws-mf.media.mlb.com&frameworkEndPoint=/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3'
        url = url + '&_=' + epoch_time_now

        req = urllib2.Request(url)
        req.add_header("Accept", "*/*")
        req.add_header("Accept-Encoding", "deflate")
        req.add_header("Accept-Language", "en-US,en;q=0.8")
        req.add_header("Connection", "keep-alive")
        req.add_header("User-Agent", UA_PC)
        req.add_header("Origin", "http://m.mlb.com")
        req.add_header("Referer", "http://m.mlb.com/tv/e" + event_id + "/v" + content_id + "/?&media_type=video&clickOrigin=Media Grid&team=mlb&forwardUrl=http://m.mlb.com/tv/e" + event_id + "/v" + content_id + "/?&media_type=video&clickOrigin=Media%20Grid&team=mlb&template=mp5default&flowId=registration.dynaindex&mediaTypeTemplate=video")

        response = opener.open(req)
        xml_data = response.read()
        response.close()

        session_key = find(xml_data, '<session-key>', '</session-key>')
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

        url = 'http://mlb.mlb.com/lookup/named.schedule_vw.bam?end_date=' + end_date + '&season=' + season + '&team_id=' + fav_team_id + '&start_date=' + start_date
        # ${expand},schedule.ticket&${optionalParams}'
        req = urllib2.Request(url)
        req.add_header('User-Agent', UA_IPAD)
        response = urllib2.urlopen(req)
        json_source = json.load(response)
        response.close()

        # <row game_pk="469406" record_source="S" game_id="2016/03/01/pitmlb-detmlb-1" game_type="S" month="3" game_date="2016-03-01T00:00:00" month_abbrev="Mar" month_full="March" day="3" day_abbrev="Tue" game_day="Tuesday" double_header_sw="N" gameday_sw="Y" interleague_sw="" game_nbr="1" series_nbr="1" series_game_nbr="1" game_time_et="2016-03-01T13:05:00" if_necessary="N" scheduled_innings="9" inning="9" top_inning_sw="N" away_team_id="134" away_all_star_sw="N" away_team_file_code="pit" away_team_city="Pittsburgh" away_team_full="Pittsburgh Pirates" away_team_brief="Pirates" away_team_abbrev="PIT" away_league_id="104" away_league="NL" away_sport_code="mlb" away_parent_id="" away_parent_org="" away_split_squad="N" home_team_id="116" home_all_star_sw="N" home_team_file_code="det" home_team_city="Detroit" home_team_full="Detroit Tigers" home_team_brief="Tigers" home_team_abbrev="DET" home_league_id="103" home_league="AL" home_sport_code="mlb" home_parent_id="" home_parent_org="" home_split_squad="N" venue_id="2511" venue="Joker Marchant Stadium" venue_short="" venue_city="Lakeland" venue_state="FL" venue_country="USA" milbtv_sw="N" home_tunein="" away_tunein="" game_time_local="3/1/2016 1:05:00 PM" time_zone_local="EST" game_time_home="3/1/2016 1:05:00 PM" time_zone_home="EST" game_time_away="3/1/2016 1:05:00 PM" time_zone_away="EST" resumed_on="" resumed_at="" resumed_from="" rescheduled_to="" rescheduled_at="" rescheduled_from="" game_status_ind="F" game_status_text="Final" reason="" home_probable_id="571510" home_probable="Boyd, Matt" home_probable_wl="0-0" home_probable_era="-.--" away_probable_id="543456" away_probable="Lobstein, Kyle" away_probable_wl="0-0" away_probable_era="-.--" home_team_wl="0-1" away_team_wl="1-0" home_score="2" away_score="4" home_result="L" away_result="W" win_pitcher_id="543746" win_pitcher="Scahill, Rob" win_pitcher_wl="1-0" win_pitcher_era="18.00" loss_pitcher_id="434137" loss_pitcher="Kensing, Logan" loss_pitcher_wl="0-1" loss_pitcher_era="18.00" editorial_stats_type="S" editorial_stats_season="2016"/>
        match = re.compile('<row (.+?)/">').findall(link)

        for game_row in match:

            for game in date['games']:
                create_game_listitem(game, date['date'])
    else:
        msg = "Please select your favorite team from the addon settings"
        dialog = xbmcgui.Dialog()
        dialog.ok('Favorite Team Not Set', msg)


def login():
    # Check if username and password are provided
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
        settings.setSetting("old_username", USERNAME)
        settings.setSetting("old_password", PASSWORD)

        url = 'https://secure.mlb.com/pubajaxws/services/IdentityPointService'
        headers = {
            "SOAPAction": "http://services.bamnetworks.com/registration/identityPoint/identify",
            "Content-type": "text/xml; charset=utf-8",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0.1; Hub Build/MHC19J)",
            "Connection": "Keep-Alive"
        }

        payload = "<?xml version='1.0' encoding='UTF-8'?>"
        payload += '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        payload += '<SOAP-ENV:Body><tns:identityPoint_identify_request xmlns:tns="http://services.bamnetworks.com/registration/types/1.4">'
        payload += '<tns:identification type="email-password"><tns:id xsi:nil="true"/>'
        payload += '<tns:fingerprint xsi:nil="true"/>'
        payload += '<tns:email>'
        payload += '<tns:id xsi:nil="true"/>'
        payload += '<tns:address>' + USERNAME + '</tns:address>'
        payload += '</tns:email>'
        payload += '<tns:password>' + PASSWORD + '</tns:password>'
        payload += '<tns:mobilePhone xsi:nil="true"/>'
        payload += '<tns:profileProperty xsi:nil="true"/>'
        payload += '</tns:identification>'
        payload += '</tns:identityPoint_identify_request>'
        payload += '</SOAP-ENV:Body>'
        payload += '</SOAP-ENV:Envelope>'

        r = requests.post(url, headers=headers, data=payload, verify=VERIFY)
        if r.status_code == 200:
            fingerprint = find(r.text, '<fingerprint>', '</fingerprint>')
            settings.setSetting("fingerprint", fingerprint)
            save_cookies(r.cookies)


def feature_service():
    url = 'https://secure.mlb.com/pubajaxws/services/FeatureService'
    headers = {
        "SOAPAction": "http://services.bamnetworks.com/registration/feature/findEntitledFeatures",
        "Content-type": "text/xml; charset=utf-8",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0.1; Hub Build/MHC19J)",
        "Connection": "Keep-Alive"
    }

    payload = "<?xml version='1.0' encoding='UTF-8'?>"
    payload += '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
    payload += '<soapenv:Header />'
    payload += '<soapenv:Body>'
    payload += '<feature_findEntitled_request xmlns="http://services.bamnetworks.com/registration/types/1.6">'

    if settings.getSetting("fingerprint") != '' and settings.getSetting("session_key") != '':
        payload += "<identification type='fingerprint'>"
        payload += '<id></id>' # ipid from cookies
        payload += '<fingerprint>' + settings.getSetting("fingerprint") + '</fingerprint>'
        payload += "<signOnRestriction type='mobileApp'>"
        payload += '<location>ANDROID_21d994bd-ebb1-4253-bcab-3550e7882294</location>'
        payload += '<sessionKey>' + settings.getSetting("session_key") + '</sessionKey>'
    else:
        payload += "<identification type='email-password'>"
        payload += '<email><address>' + USERNAME + '</address></email>'
        payload += '<password>' + PASSWORD + '</password>'
        payload += '<signOnRestriction type="mobileApp">'
        payload += '<location>ANDROID_21d994bd-ebb1-4253-bcab-3550e7882294</location>'

    payload += '</signOnRestriction>'
    payload += '</identification>'
    payload += '<featureContextName>MLBTV2017.INAPPPURCHASE</featureContextName>'
    payload += '</feature_findEntitled_request>'
    payload += '</soapenv:Body>'
    payload += '</soapenv:Envelope>'

    r = requests.post(url, headers=headers, data=payload, verify=VERIFY)
    if r.status_code == 200:
        fingerprint = find(r.text, '<fingerprint>', '</fingerprint>')
        session_key = find(r.text, '<sessionKey>', '</sessionKey>')
        settings.setSetting("fingerprint", fingerprint)
        settings.setSetting("session_key", session_key)
        save_cookies(r.cookies)


def media_entitlement():
    cookies = requests.utils.dict_from_cookiejar(load_cookies())
    url = 'https://media-entitlement.mlb.com/jwt'
    url += '?ipid=' + cookies['ipid']
    url += '&fingerprint=' + settings.getSetting('fingerprint')
    url += '&os=Android'
    url += '&appname=AtBat'
    headers = {
        'x-api-key': 'arBv5yTc359fDsqKdhYC41NZnIFZqEkY5Wyyn9uA',
        'Cache-Control': 'no-cache',
        'Connection': 'Keep-Alive',
        'User-Agent': 'okhttp/3.9.0'
    }

    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)

    return r.text


def access_token():
    url = 'https://edge.bamgrid.com/token'
    headers = {
        'Authorization': 'Bearer bWxidHYmYW5kcm9pZCYxLjAuMA.6LZMbH2r--rbXcgEabaDdIslpo4RyZrlVfWZhsAgXIk',
        'Accept': 'application/json',
        'X-BAMSDK-Version': 'v3.0.0-beta2-3',
        'X-BAMSDK-Platform': 'Android',
        'User-Agent': 'BAMSDK/3.0.0-beta2 (mlbaseball-7993996e; v2.0/v3.0.1; android; tv) WeTek Hub (wetekhub-user 6.0.1 MHC19J 20170612 release-keys; Linux; 6.0.1; API 23)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }

    payload = 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange'
    payload += '&subject_token=' + media_entitlement()
    payload += '&subject_token_type=urn:ietf:params:oauth:token-type:jwt'
    payload += '&platform=android-tv'

    r = requests.post(url, headers=headers, data=payload, cookies=load_cookies(), verify=VERIFY)
    access_token = r.json()['access_token']
    # refresh_toekn = r.json()['refresh_token']
    return access_token


def get_stream(media_id):
    auth = access_token()
    url = 'https://edge.svcs.mlb.com/media/' + media_id + '/scenarios/android'
    headers = {
        'Accept': 'application/vnd.media-service+json; version=2',
        'Authorization': auth,
        'X-BAMSDK-Version': 'v3.0.0-beta2-3',
        'X-BAMSDK-Platform': 'Android',
        'User-Agent': 'BAMSDK/3.0.0-beta2 (mlbaseball-7993996e; v2.0/v3.0.1; android; tv) WeTek Hub (wetekhub-user 6.0.1 MHC19J 20170612 release-keys; Linux; 6.0.1; API 23)'
    }

    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)
    stream_url = r.json()['stream']['complete']
    cookies = requests.utils.dict_from_cookiejar(load_cookies())
    stream_url += '|User-Agent=MLB.TV/3.5.0 (Linux;Android 6.0.1) ExoPlayerLib/2.5.4'
    stream_url += '&Authorization=' + auth
    stream_url += '&Cookie='
    for key, value in cookies.iteritems():
        stream_url += key + '=' + value + '; '

    return stream_url


def logout():
    # Just delete the cookie file
    cookie_file = xbmc.translatePath(os.path.join(ADDON_PATH_PROFILE + 'cookies.lwp'))
    try:
        os.remove(cookie_file)
    except:
        pass

    settings.setSetting(id='session_key', value='')
    dialog = xbmcgui.Dialog()
    title = "Logout Successful"
    dialog.notification(title, 'Logout completed successfully', ICON, 5000, False)
