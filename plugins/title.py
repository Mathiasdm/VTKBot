#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
VTKBot is an IRC bot
Copyright (C) 2010 Mathias De Maré

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; version 2
of the License, no other.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from plugin import Plugin

import re
import urllib2
from urlparse import urlparse
from twisted.internet import reactor, threads
from BeautifulSoup import BeautifulSoup

class Title(Plugin):

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.channel_message_rule = "(?i).*(http://[^\s]*).*"

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        url = match.group(1)
        d = threads.deferToThread(self.get_url_title, url)
        d.addCallback(self.show_result, vtkbot, channel)
        #print self.get_url_title(url) #(useful for debugging errors)

    def get_url_title(self, url):
        data = self.get_url_data(url)
        if data != None:
            return self.get_data_title(data)
        return None

    def get_url_data(self, url):
        try:
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            conn = opener.open(url)
            data = conn.read(10000)
            return data
        except Exception:
            return None

    def get_data_title(self, data):
        soup = BeautifulSoup(data)
        title = soup.find('title')
        if title != None:
            title_contents = title.string
            if title_contents != None:
                return title_contents.replace('\r', '').replace('\n', '').replace('\t', '') #Don't add newlines and tabs to the IRC conversation
        return None

    def show_result(self, result, vtkbot, channel):
        if result != None and result != '':
            vtkbot.send_channel_message(channel, "Title: %s" % result)
