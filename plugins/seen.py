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
from sqlalchemy import create_engine, Table, Column, Integer, Unicode, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from datetime import datetime
import re

class Seen(Plugin):

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.channel_message_rule = ".*?"

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        session = self.Session()
        occurrence = session.query(Occurrence).filter_by(user=nick).first()
        if not occurrence:
            occurrence = Occurrence(nick, channel, datetime.now())
        else:
            occurrence.datetime = datetime.now()
        session.save_or_update(occurrence)
        session.commit()
        match = re.match("%s: seen ([^\s]*)" % self.factory.nickname, message)
        if match:
            occurrence = session.query(Occurrence).filter_by(user=match.group(1)).first()
            if occurrence:
                vtkbot.send_channel_message(channel, "Ik zag %s het laatst %s" % (occurrence.user, occurrence.datetime))
            else:
                vtkbot.send_channel_message(channel, "Ik heb %s nog nooit gezien!" % match.group(1))

    def create_database_tables(self):
        metadata = MetaData()
        #Create SQL tables
        occurrence_table = Table('seen', metadata,
            Column('id', Integer, primary_key=True),
            Column('user', Unicode(length=35)),
            Column('channel', Unicode(length=100)),
            Column('datetime', DateTime),
        )
        mapper(Occurrence, occurrence_table)
        metadata.create_all(self.factory.engine)
        self.Session = sessionmaker(bind=self.factory.engine)

    def on_help(self, vtkbot, channel):
        vtkbot.send_channel_message(channel, "Seen is handig als je wil weten wanneer een gebruiker laatst online was: '%s: seen Gebruiker'" % self.factory.nickname)

class Occurrence(object):
    def __init__(self, user, channel, datetime):
        self.user = user
        self.channel = channel
        self.datetime = datetime

    def __repr__(self):
        return u'<Occurrence(%s, %s, %s)>' % (self.user, self.channel, self.datetime)
