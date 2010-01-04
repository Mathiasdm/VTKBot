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

import settings

from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor

from sqlalchemy import create_engine

import re
import os
import imp

from plugin import Plugin

class VTKBot(LineOnlyReceiver):

    #========================
    #    CONNECTION SETUP   #
    #========================

    def connectionMade(self):
        #Authenticate
        self.send_message("USER %s %s %s %s" % (self.factory.username, self.factory.host, self.factory.server, self.factory.realname))
        self.send_message("NICK %s" % self.factory.nickname)

        #Join channels
        reactor.callLater(10, self.joinChannels)

    def joinChannels(self):
        for channel in self.factory.channels:
            self.send_join(channel)

    #========================
    #    SENDING MESSAGES   #
    #========================

    #Send a raw IRC message
    def send_message(self, message):
        message = message.encode('utf-8')
        print message
        self.transport.write(message + '\n')

    #Send PONG back after receiving ping
    def send_pong(self, target):
        self.send_message("PONG %s" % target)

    #Send JOIN message to enter a channel
    def send_join(self, channel):
        self.send_message("JOIN %s" % channel)

    #Send PART message to leave a channel
    def send_leave(self, channel, reason):
        self.send_message("PART %s :%s" % (channel, reason))

    def send_kick(self, channel, user, reason):
        self.send_message("KICK %s %s :%s" % (channel, user, reason))

    #Kill a nickname
    def send_kill(self, nick, comment):
        self.send_message("KILL %s : %s" % (nick, comment))

    #Set user modes
    def send_user_mode(self, target, mode):
        self.send_message("MODE %s %s" % (target, mode))

    def send_channel_message(self, channel, message):
        self.send_message("PRIVMSG %s :%s" % (channel, message))

    #Set channel modes
    def send_channel_mode(self, target, mode, user=None):
        if user == None:
            self.send_message("MODE %s %s" % (target, mode))
        else:
            self.send_message("MODE %s %s %s" % (target, mode, user))

    #Identify as operator
    def send_oper(self, name="root", password="12345"):
        self.send_message("OPER %s %s" % (name, password))

    #Send private message to user
    def send_private_message(self, nick, message):
        self.send_message("PRIVMSG %s :%s" % (nick, message))

    #========================
    #  RECEIVING MESSAGES   #
    #========================

    #Received a raw IRC message
    def lineReceived(self, message):
        print message
        message = message.decode('utf-8')

        #INVITE message
        match = re.match(":([^ ]*?)!([^ ]*?)@([^ ]*?) INVITE ([^ ]*?) :(.*)", message)
        if match:
            self.on_invite(match.group(1), match.group(2), match.group(3), match.group(4), match.group(5))
            return

        #JOIN message
        match = re.match(":([^ ]*?)!([^ ]*?)@([^ ]*?) JOIN :(.*)", message)
        if match:
            self.on_user_join(match.group(1), match.group(2), match.group(3), match.group(4))
            return

        #KICK message
        match = re.match(":([^ ]*?)!([^ ]*?)@([^ ]*?) KICK (.*?) %s :" % self.factory.nickname, message)
        if match:
            self.on_kick(match.group(1), match.group(2), match.group(3), match.group(4))

        #NOTICE message
        match = re.match("[^ ]* NOTICE ([^ ]*) :(.*)", message)
        if match:
            self.on_notice(match.group(1), match.group(2))
            return

        #PART message
        match = re.match(":([^ ]*?)!([^ ]*?)@([^ ]*?) PART (.*?) :(.*)", message)
        if match:
            self.on_user_leave(match.group(1), match.group(2), match.group(3), match.group(4), match.group(5))
            return

        #PING message
        match = re.match("PING ([^ ]*)", message)
        if match:
            self.on_ping(match.group(1))
            return

        #PRIVATE message
        match = re.match(":([^ ]*?)!([^ ]*?)@([^ ]*?) PRIVMSG ([^ ]*?) :([^\n\r]*)", message)
        if match:
            if match.group(4) == self.factory.nickname:
                self.on_private_message(match.group(1), match.group(2), match.group(3), match.group(5))
            else:
                self.on_channel_message(match.group(1), match.group(2), match.group(3), match.group(4), match.group(5))
            return

        #CODE 'You are banned'
        match = re.match(":[^ ]*? 474 ([^ ]*?) ([^ ]*?) :(.*)", message)
        if match:
            self.on_banned_code(match.group(1), match.group(2))
            return

        #CODE 'Banlist
        match = re.match(":[^ ]*? 367 (.*?) (.*?) (.*?) (.*?) (.*)", message)
        if match:
            self.banlist += [(match.group(2), match.group(3), match.group(4), match.group(5))]
            return

        #CODE 'End-of-banlist'
        match = re.match(":[^ ]*? 368 (.*?) (.*?) :", message)
        if match:
            oldbanlist = self.banlist
            self.banlist = []
            self.on_banlist(oldbanlist)
            return

    #Received a banlist
    def on_banlist(self, banlist):
        pass

    #Received a channel ban
    def on_banned_code(self, nick, channel):
        pass

    #Received a channel creation message
    def on_channel_create(self, channel, nick, nickmask, hostmask):
        pass

    #Received a channel message
    def on_channel_message(self, nick, nickmask, hostmask, channel, message):
        for plugin in self.factory.plugins:
            if plugin.channel_message_rule != "":
                match = re.match(plugin.channel_message_rule, message)
                if match:
                    plugin.on_channel_message(self, nick, nickmask, hostmask, channel, message, match)

    #Received a channel invitation
    def on_invite(self, nick, nickmask, hostmask, invitee, channel):
        pass

    #Received a channel kick
    def on_kick(self, nick, nickmask, hostmask, channel):
        pass

    #Received a notice (careful when overriding, there are a lot of subnotices!)
    def on_notice(self, nick, text):
        #Channel creation
        match = re.match("\*\*\* CHANCREATE: Channel ([^ ]*?) created by ([^ ]*?)\!([^ ]*?)@([^ ]*)", text)
        if match:
            self.on_channel_create(match.group(1), match.group(2), match.group(3), match.group(4))
            return

        #User quit
        match = re.match("\*\*\* QUIT: Client exiting: ([^ ]*?)\!([^ ]*?)@([^ ]*?) ", text)
        if match:
            self.on_user_quit(match.group(1), match.group(2), match.group(3))
            return

        #User connect
        match = re.match("\*\*\* CONNECT: Client connecting on port [0-9]*?: ([^ ]*?)\!([^ ]*?)@([^ ]*?) ", text)
        if match:
            self.on_user_connect(match.group(1), match.group(2), match.group(3))
            return

        #Nickname changed
        match = re.match("\*\*\* NICK: User ([^ ]*?) changed their nickname to ([^ ]*)\s+", text)
        if match:
            self.on_user_changed_nickname(match.group(1), match.group(2))
            return
        
    #Received a PING message (automatically answering with a PONG message)
    def on_ping(self, target):
        self.send_pong(target)

    #Received a private message
    def on_private_message(self, nick, nickmask, hostmask, message):
        pass

    #A user changed his nickname
    def on_user_changed_nickname(self, old_nick, new_nick):
        pass

    #A user connected to the server
    def on_user_connect(self, nick, nickmask, hostmask):
        pass

    #A user joined a channel
    def on_user_join(self, nick, nickmask, hostmask, channel):
        for plugin in self.factory.plugins:
            if plugin.channel_message_rule != "":
                plugin.on_user_join(self, nick, nickmask, hostmask, channel)

    def on_user_leave(self, nick, nickmask, hostmask, channel, reason):
        pass

    #A user quit
    def on_user_quit(self, nick, nickmask, hostmask):
        pass

class VTKBotFactory(ClientFactory):

    protocol = VTKBot

    def __init__(self, realname="RealName", host="localhost", server="localhost", port=9999, nickname="NickName", username="UserName",
            databasefile="sqlite:///vtk.db", channels=["#test", "#test2"]):
        self.nickname = nickname
        self.username = username
        self.realname = realname
        self.host = host
        self.server = server
        self.port = port
        self.databasefile = databasefile
        self.engine = create_engine(self.databasefile, echo=True)
        self.channels = channels
        self.load_plugins()

    def setting_defined(self, setting):
        try:
            setting
            return True
        except NameError:
            return False

    def load_plugins(self):
        #Load source code
        for candidate_file in os.listdir('./plugins'):
            if hasattr(settings, 'plugin_list') and not self.endswith(candidate_file, settings.plugin_list): 
                continue #There's a list of allowed plugins, and ours is not in it
            try:
                fp, pathname, description = imp.find_module(candidate_file[:-3], ['./plugins'])
                imp.load_module(candidate_file[:-3], fp, pathname, description)
            except:
                pass

        #See what classes we managed to load
        pluginclasses = Plugin.__subclasses__()
        print 'Plugins: ' + str(pluginclasses)
        self.plugins = []
        for pluginclass in pluginclasses:
            plugin = object.__new__(pluginclass)
            plugin.__init__(self)
            plugin.create_database_tables()
            self.plugins.append(plugin)

    def endswith(self, candidate, plugin_list):
        for plugin in plugin_list:
            if candidate.endswith(plugin):
                return True
        return False
