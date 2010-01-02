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

from core import Plugin
from sqlalchemy import create_engine, Table, Column, Integer, Unicode, MetaData
from sqlalchemy.orm import mapper, sessionmaker

class Say(Plugin):

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.channel_message_rule = "%s: say ([^ ]*) (.*)" % factory.nickname
        self.user_join_rule = ".*?"

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        message = Message(nick, match.group(1), channel, match.group(2))
        session = self.Session()
        session.save_or_update(message)
        session.commit()
        vtkbot.send_channel_message(channel, "Ik zal tegen %s zeggen: %s" % (match.group(1), match.group(2)))

    def on_user_join(self, vtkbot, nick, nickmask, hostmask, channel):
        #Get messages
        session = self.Session()
        messages = session.query(Message).filter_by(user_to=nick, channel=channel)

        #Send messages
        for message in messages:
            vtkbot.send_channel_message(channel, "%s: <%s> %s" % (nick, message.user_from, message.text))

        #Remove messages
        for message in messages:
            session.delete(message)
        session.commit()

    def on_help(self, vtkbot, channel):
        vtkbot.send_channel_message(channel, "Say laat toe berichten te sturen naar mensen die offline zijn. Stuur een bericht door '%s: say Naam Bericht' te typen in het kanaal." % self.factory.nickname)

    def create_database_tables(self):
        metadata = MetaData()
        #Create SQL tables
        messages_table = Table('messages', metadata,
            Column('id', Integer, primary_key=True),
            Column('user_from', Unicode(length=35)),
            Column('user_to', Unicode(length=35)),
            Column('channel', Unicode(length=100)),
            Column('text', Unicode(length=150)),
        )
        mapper(Message, messages_table)
        metadata.create_all(self.factory.engine)
        self.Session = sessionmaker(bind=self.factory.engine)

class Message(object):
    def __init__(self, user_from, user_to, channel, text):
        self.user_from = user_from
        self.user_to = user_to
        self.channel = channel
        self.text = text

    def __repr__(self):
        return u'<Message(%s, %s, %s, %s)>' % (self.user_from, self.user_to, self.channel, self.text)
