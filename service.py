# coding=UTF-8
# SPDX-License-Identifier: GPL-2.0-or-later
# Original proxy.plugin.example © matthuisman
# Modified for MLB.TV compatibility

import threading

import xbmc
import requests
import urllib

import re

from kodi_six import xbmcaddon
import json

if sys.version_info[0] > 2:
    urllib = urllib.parse

try:
    # Python3
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    from urllib.parse import urljoin
    from urllib.parse import urlparse
    from urllib.parse import parse_qs
except:
    # Python2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
    from urlparse import urljoin
    from urlparse import urlparse
    from urlparse import parse_qs

HOST = '127.0.0.1'
PORT = 43670
PROXY_URL = 'http://' + HOST + ':' + str(PORT) + '/'
STREAM_EXTENSION = '.m3u8'
URI_START_DELIMETER = 'URI="'
URI_END_DELIMETER = '"'
KEY_TEXT = '-KEY:METHOD=AES-128'
ENDLIST_TEXT = '#EXT-X-ENDLIST'
REMOVE_IN_HEADERS = ['upgrade', 'host']
REMOVE_OUT_HEADERS = ['date', 'server', 'transfer-encoding', 'keep-alive', 'connection', 'content-length', 'content-range', 'content-md5', 'access-control-allow-credentials', 'content-encoding']


SETTINGS = xbmcaddon.Addon(id='plugin.video.mlbtv')

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_POST(self):
        if self.path == '/':
          data = self.rfile.read(int(self.headers['content-length'])).decode('utf-8')
          stream_finder_settings = json.loads(re.findall(r"^\r\n((?:.)*?)\r\n", data, re.MULTILINE)[0])
          SETTINGS.setSetting(id='stream_finder_settings', value=json.dumps(stream_finder_settings))
          self.send_response(200)
          self.send_header('Content-type', 'text/html')
          self.end_headers()
          content = '<p><b>SUCCESS!</b></p><p>Your Stream Finder settings have been saved in Kodi.</p><p>Select the Stream Finder stream to use them, or <a href="/">click here</a> to replace them with new settings.</p>'
          self.wfile.write(content.encode('utf8'))
          
        else:
          self.send_error(404)

    def do_HEAD(self):
        self.send_error(404)

    def do_GET(self):
        content = ''
        if self.path == '/':
          self.send_response(200)
          self.send_header('Content-type', 'text/html')
          self.end_headers()
          content = '<h1>Stream Finder</h1><p><a download="KodiStreamFinder.txt" href="/downloadsettings">Click to Download Currently Stored Settings</a></p><h2>Settings update</h2><p><b><u>Step 1</b></u><br/>Export and download your desired Stream Finder settings at this link:<br/><a href="https://www.baseball-reference.com/stream-finder.shtml" target="_blank">https://www.baseball-reference.com/stream-finder.shtml</a></p><form method="POST" enctype="multipart/form-data"><p><b><u>Step 2</b></u><br/>Click this button and select the settings file you just downloaded:<br/><input name="file" type="file"/></p><p><p><b><u>Step 3</b></u><br/>Click this button to upload the selected settings file to Kodi:<br/><input type="submit" value="Upload"/></p></form>'
        elif self.path == '/downloadsettings':
          self.send_response(200)
          self.send_header('Content-type', 'text/plain')
          self.end_headers()
          content = SETTINGS.getSetting(id='stream_finder_settings')
        elif self.path == '/favicon.ico':
          self.send_error(404)
        else:
          # parse path of the incoming request into components
          parsed_url = urlparse(self.path.lstrip('/').strip('\\'))
          # build our outgoing request URL without the querystring parameters
          url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path
          if not url.endswith(STREAM_EXTENSION):
              self.send_error(404)

          headers = {}
          pad = 0

          # parse the querystring parameters component
          parsed_qs = parse_qs(parsed_url.query)
          if 'pad' in parsed_qs:
              pad = int(parsed_qs['pad'][0])

          for key in self.headers:
              if key.lower() not in REMOVE_IN_HEADERS:
                  headers[key] = self.headers[key]

          response = requests.get(url, headers=headers)

          self.send_response(response.status_code)

          for key in response.headers:
              if key.lower() not in REMOVE_OUT_HEADERS:
                  if key.lower() == 'access-control-allow-origin':
                      response.headers[key] = '*'
                  self.send_header(key, response.headers[key])

          self.end_headers()

          content = response.content.decode('utf8')
        
          # remove subtitles and extraneous lines for Kodi Inputstream Adaptive compatibility
          content = re.sub(r"(?:#EXT-X-MEDIA:TYPE=SUBTITLES[\S]+\n)", r"", content, flags=re.M)
          content = re.sub(r",SUBTITLES=\"subs\"", r"", content, flags=re.M)
          content = re.sub(r"(?:#EXT-X-I-FRAME-STREAM-INF:[\S]+\n)", r"", content, flags=re.M)
          # remove ad insertion tag lines
          content = re.sub(r"^(?:#EXT-OATCLS-SCTE35:[\S]+\n)", r"", content, flags=re.M)
          content = re.sub(r"^(?:#EXT-X-CUE-[\S]+\n)", r"", content, flags=re.M)
        
          # assume it's a master playlist until we detect that it's a variant
          if '#EXT-X-PLAYLIST-TYPE:' in content:
              playlist_type = 'variant'
          else:
              playlist_type = 'master'

          # change relative m3u8 urls to absolute urls by looking at each line
          line_array = content.splitlines()
          new_line_array = []
          for line in line_array:
              if line.startswith('#'):
                  # look for uri parameters within non-key "#" lines
                  if playlist_type == 'master' and KEY_TEXT not in line and URI_START_DELIMETER in line:
                      line_split = line.split(URI_START_DELIMETER)
                      url_split = line_split[1].split(URI_END_DELIMETER, 1)
                      absolute_url = urljoin(url, url_split[0])
                      if absolute_url.endswith(STREAM_EXTENSION) and not absolute_url.startswith(PROXY_URL):
                          absolute_url = PROXY_URL + absolute_url + '?' + parsed_url.query
                      new_line = line_split[0] + URI_START_DELIMETER + absolute_url + URI_END_DELIMETER + url_split[1]
                      new_line_array.append(new_line)
                  else:
                      new_line_array.append(line)
              elif line != '':
                  absolute_url = urljoin(url, line)
                  if absolute_url.endswith(STREAM_EXTENSION) and not absolute_url.startswith(PROXY_URL):
                      absolute_url = PROXY_URL + absolute_url + '?' + parsed_url.query
                  new_line_array.append(absolute_url)

          # pad the end of the stream by the requested number of segments
          if playlist_type == 'variant':
              last_item_index = len(new_line_array)-1
              if new_line_array[last_item_index] == ENDLIST_TEXT and int(pad) > 0:
                  new_line_array.pop()
                  last_item_index -= 1
                  #url_line = None
                  extinf_line = None
                  while extinf_line is None:
                      if new_line_array[last_item_index].startswith('#EXTINF:4'):
                          extinf_line = new_line_array[last_item_index]
                          #url_line = new_line_array[last_item_index+1]
                          break
                      last_item_index -= 1
                  for x in range(0, pad):
                      new_line_array.append(extinf_line)
                      # use base proxy URL for more graceful stream padding, instead of repeating last segment
                      #new_line_array.append(url_line)
                      new_line_array.append(PROXY_URL + 'pad')
                  new_line_array.append(ENDLIST_TEXT)

          content = "\n".join(new_line_array)

        # Output the new content
        self.wfile.write(content.encode('utf8'))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

server = ThreadedHTTPServer(('0.0.0.0', PORT), RequestHandler)
server.allow_reuse_address = True
httpd_thread = threading.Thread(target=server.serve_forever)
httpd_thread.start()

xbmc.Monitor().waitForAbort()

server.shutdown()
server.server_close()
server.socket.close()
httpd_thread.join()
