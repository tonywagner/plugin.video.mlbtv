import requests
from utils import Util
from resources.lib.globals import *
import xbmc, xbmcaddon, xbmcgui


class Account:
    addon = xbmcaddon.Addon()
    username = ''
    password = ''
    session_key = ''
    verify = False

    def __init__(self):
        self.username = self.addon.getSetting('username')
        self.password = self.addon.getSetting('password')
        self.session_key = self.addon.getSetting('session_key')
        self.util = Util()

    def login(self):
        # Check if username and password are provided
        if self.username == '':
            dialog = xbmcgui.Dialog()
            username = dialog.input('Please enter your username', type=xbmcgui.INPUT_ALPHANUM)
            self.addon.setSetting(id='username', value=username)

        if self.password == '':
            dialog = xbmcgui.Dialog()
            password = dialog.input('Please enter your password', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
            self.addon.setSetting(id='password', value=password)

        if self.username == '' or self.password == '':
            sys.exit()
        else:
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
            payload += '<tns:address>' + self.username + '</tns:address>'
            payload += '</tns:email>'
            payload += '<tns:password>' + self.password + '</tns:password>'
            payload += '<tns:mobilePhone xsi:nil="true"/>'
            payload += '<tns:profileProperty xsi:nil="true"/>'
            payload += '</tns:identification>'
            payload += '</tns:identityPoint_identify_request>'
            payload += '</SOAP-ENV:Body>'
            payload += '</SOAP-ENV:Envelope>'

            r = requests.post(url, headers=headers, data=payload, verify=self.verify)

            """
            Bad username => <status><code>-1000</code><message> [Invalid credentials for identification] [com.bamnetworks.registration.types.exception.IdentificationException: Account doesn't exits]</message><exceptionClass>com.bamnetworks.registration.types.exception.IdentificationException</exceptionClass><detail type="identityPoint" field="exists" message="false" messageKey="identityPoint.exists" /><detail type="identityPoint" field="email-password" message="identification error on identity point of type email-password" messageKey="identityPoint.email-password" /></status>
            Bad password => <status><code>-1000</code><message> [Invalid credentials for identification] [com.bamnetworks.registration.types.exception.IdentificationException: Invalid Password]</message><exceptionClass>com.bamnetworks.registration.types.exception.IdentificationException</exceptionClass><detail type="identityPoint" field="exists" message="true" messageKey="identityPoint.exists" /><detail type="identityPoint" field="email-password" message="identification error on identity point of type email-password" messageKey="identityPoint.email-password" /></status>
            Good => <status><code>1</code><message>OK</message></status>
            """
            if self.util.find(r.text, '<code>', '</code>') != '1':
                title = self.util.find(r.text, '<message> [', '] [')
                msg = self.util.find(r.text, 'com.bamnetworks.registration.types.exception.IdentificationException: ', ']</message>')
                dialog = xbmcgui.Dialog()
                dialog.ok(title, msg)
                sys.exit()
            else:
                self.util.save_cookies(r.cookies)

    def feature_service(self):
        if self.util.check_cookies():
            self.login()
        cookies = requests.utils.dict_from_cookiejar(self.util.load_cookies())
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

        if 'ipid' in cookies and 'fprt' in cookies and self.session_key != '':
            payload += "<identification type='fingerprint'>"
            payload += '<id>' + cookies['ipid'] + '</id>'
            payload += '<fingerprint>' + cookies['fprt'] + '</fingerprint>'
            payload += "<signOnRestriction type='mobileApp'>"
            payload += '<location>ANDROID_21d994bd-ebb1-4253-bcab-3550e7882294</location>'
            payload += '<sessionKey>' + self.session_key + '</sessionKey>'
        else:
            payload += "<identification type='email-password'>"
            payload += '<email><address>' + self.username + '</address></email>'
            payload += '<password>' + self.password + '</password>'
            payload += '<signOnRestriction type="mobileApp">'
            payload += '<location>ANDROID_21d994bd-ebb1-4253-bcab-3550e7882294</location>'

        payload += '</signOnRestriction>'
        payload += '</identification>'
        payload += '<featureContextName>MLBTV2017.INAPPPURCHASE</featureContextName>'
        payload += '</feature_findEntitled_request>'
        payload += '</soapenv:Body>'
        payload += '</soapenv:Envelope>'

        r = requests.post(url, headers=headers, data=payload, verify=self.verify)
        if self.util.find(r.text, '<code>', '</code>') != '1':
            title = self.util.find(r.text, '<message> [', '] [')
            msg = self.util.find(r.text, 'com.bamnetworks.registration.types.exception.IdentificationException: ', ']</message>')
            dialog = xbmcgui.Dialog()
            dialog.ok(title, msg)
            sys.exit()
        else:
            self.session_key = self.util.find(r.text, '<sessionKey>', '</sessionKey>')
            self.addon.setSetting("session_key", self.session_key)
            self.util.save_cookies(r.cookies)

    def logout(self):
        self.util.delete_cookies()

    def media_entitlement(self):
        # check_cookies()
        self.feature_service()
        cookies = requests.utils.dict_from_cookiejar(self.util.load_cookies())
        url = 'https://media-entitlement.mlb.com/jwt'
        url += '?ipid=' + cookies['ipid']
        url += '&fingerprint=' + cookies['fprt']
        url += '&os=Android'
        url += '&appname=AtBat'
        headers = {
            'x-api-key': 'arBv5yTc359fDsqKdhYC41NZnIFZqEkY5Wyyn9uA',
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive',
            'User-Agent': 'okhttp/3.9.0'
        }

        r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)

        return r.text

    def access_token(self):
        url = 'https://edge.bamgrid.com/token'

        headers = {
            'Origin': 'https://www.mlb.com',
            'x-bamsdk-version': '3.0',
            'authorization': 'Bearer bWxidHYmYnJvd3NlciYxLjAuMA.VfmGMGituFykTR89LFD-Gr5G-lwJ9QbHfXXNBMkuM9M',
            'content-type': 'application/x-www-form-urlencoded',
            'x-bamsdk-platform': 'windows',
            'accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
            'Referer': 'https://www.mlb.com/tv/g529459/v8539eb7d-e8de-4b8d-84aa-d5026e632f36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        payload = 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange'
        payload += '&subject_token=' + self.media_entitlement()
        payload += '&subject_token_type=urn:ietf:params:oauth:token-type:jwt'
        payload += '&platform=browser'

        r = requests.post(url, headers=headers, data=payload, cookies=self.util.load_cookies(), verify=self.verify)
        access_token = r.json()['access_token']
        # refresh_toekn = r.json()['refresh_token']
        return access_token

    def get_stream(self, media_id):
        auth = self.access_token()
        url = 'https://edge.svcs.mlb.com/media/' + media_id + '/scenarios/browser~csai'
        headers = {
            'Accept': 'application/vnd.media-service+json; version=2',
            'Authorization': auth,
            'X-BAMSDK-Version': '3.0',
            'X-BAMSDK-Platform': 'windows',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }

        r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)
        if r.status_code != 200:
            dialog = xbmcgui.Dialog()
            title = "Error Occured"
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(title, msg, ICON, 5000, False)
            sys.exit()

        stream_url = r.json()['stream']['complete']
        stream_url = self.get_stream_quality(stream_url)
        headers = '|User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        headers += '&Authorization=' + auth
        headers += '&Cookie='
        cookies = requests.utils.dict_from_cookiejar(self.util.load_cookies())
        for key, value in cookies.iteritems():
            headers += key + '=' + value + '; '

        return stream_url, headers

    def get_stream_quality(self, stream_url):
        """
        #EXTM3U
        #EXT-X-INDEPENDENT-SEGMENTS
        #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aac",LANGUAGE="en",NAME="English",AUTOSELECT=YES,DEFAULT=YES
        #EXT-X-MEDIA:TYPE=CLOSED-CAPTIONS,GROUP-ID="cc",LANGUAGE="en",NAME="English",INSTREAM-ID="CC1"
        #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aac",NAME="Natural Sound",LANGUAGE="zxx",AUTOSELECT=NO,URI="ballpark_48K/48_complete.m3u8"
        #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aac",NAME="English Radio",LANGUAGE="en",AUTOSELECT=NO,URI="eng_48K/48_complete.m3u8"
        #EXT-X-STREAM-INF:BANDWIDTH=2120000,RESOLUTION=896x504,FRAME-RATE=29.97,CODECS="mp4a.40.2,avc1.4d001f",CLOSED-CAPTIONS="cc",AUDIO="aac"
        1800K/1800_complete.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=620000,RESOLUTION=400x224,FRAME-RATE=29.97,CODECS="mp4a.40.2,avc1.4d001f",CLOSED-CAPTIONS="cc",AUDIO="aac"
        514K/514_complete.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=960000,RESOLUTION=512x288,FRAME-RATE=29.97,CODECS="mp4a.40.2,avc1.4d001f",CLOSED-CAPTIONS="cc",AUDIO="aac"
        800K/800_complete.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=640x360,FRAME-RATE=29.97,CODECS="mp4a.40.2,avc1.4d001f",CLOSED-CAPTIONS="cc",AUDIO="aac"
        1200K/1200_complete.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=2950000,RESOLUTION=960x540,FRAME-RATE=29.97,CODECS="mp4a.40.2,avc1.4d001f",CLOSED-CAPTIONS="cc",AUDIO="aac"
        2500K/2500_complete.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=4160000,RESOLUTION=1280x720,FRAME-RATE=29.97,CODECS="mp4a.40.2,avc1.640028",CLOSED-CAPTIONS="cc",AUDIO="aac"
        3500K/3500_complete.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=6600000,RESOLUTION=1280x720,FRAME-RATE=59.94,CODECS="mp4a.40.2,avc1.640028",CLOSED-CAPTIONS="cc",AUDIO="aac"
        5600K/5600_complete.m3u8
        #EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=62000,RESOLUTION=400x224,CODECS="avc1.4d001f,mp4a.40.2",URI="514K/514_complete_iframe.m3u8"
        #EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=295000,RESOLUTION=960x540,CODECS="avc1.4d001f,mp4a.40.2",URI="2500K/2500_complete_iframe.m3u8"
        """
        stream_title = []
        stream_urls = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}

        r = requests.get(stream_url, headers=headers, verify=False)
        master = r.text

        xbmc.log(stream_url)
        xbmc.log(master)

        line = re.compile("(.+?)\n").findall(master)

        for temp_url in line:
            if '.m3u8' in temp_url:
                temp_url = temp_url
                match = re.search(r'(\d.+?)K', temp_url, re.IGNORECASE)
                if match:
                    bandwidth = match.group()
                    if 0 < len(bandwidth) < 6:
                        bandwidth = bandwidth.replace('K', ' kbps')
                        stream_title.append(bandwidth)
                        stream_urls.append(temp_url)

        stream_title.sort(key=self.util.natural_sort_key, reverse=True)
        dialog = xbmcgui.Dialog()
        ret = dialog.select('Choose Stream Quality', stream_urls)
        if ret >= 0:
            #bandwidth = self.util.find(stream_title[ret], '', ' kbps')
            if 'http' not in stream_urls[ret]:
                #https://hlslive-aksc-ewr1.media.mlb.com/ls01/mlb/2018/04/02/Home_VIDEO_eng_Chicago_Cubs_Cincinnati_R_20180402_1522691569600/master_wired60_complete.m3u8
                #https://hlslive-aksc-ewr1.media.mlb.com/ls01/mlb/2018/04/02/Home_VIDEO_eng_Chicago_Cubs_Cincinnati_R_20180402_1522691569600/2500K/2500_complete.m3u8|
                #https://hlslive-l3c-ewr1.media.mlb.com/ls01/mlb/2018/04/02/Away_VIDEO_eng_Chicago_Cubs_Cincinnati_R_20180402_1522691569609/5600K/5600_complete.m3u8
                stream_url = stream_url.replace(stream_url.rsplit('/', 1)[-1], stream_urls[ret])
            else:
                stream_url = stream_urls[ret]

        return stream_url