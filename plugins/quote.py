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
from random import choice
import re

class Quote(Plugin):

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.channel_message_rule = "%s: quote" % self.factory.nickname

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        print 'MATCH!'
        session = self.Session()
        match = re.match("%s: quote$" % self.factory.nickname, message)
        if match:
            #Random quote
            quotes = session.query(Quote).all()
            if (quotes == None) or (len(quotes) == 0):
                vtkbot.send_channel_message(channel, "Geen quotes gevonden.")
                return
            quote = choice(quotes)
            vtkbot.send_channel_message(channel, "<%s> %s" % (quote.user, quote.text))
            return

        match = re.match("%s: quote ([^\s]*)$" % self.factory.nickname, message)
        if match:
            #Random quote from user
            quotes = session.query(Quote).filter_by(user=match.group(1)).all()
            if (quotes == None) or (len(quotes) == 0):
                vtkbot.send_channel_message(channel, "Geen quotes van %s gevonden." % match.group(1))
                return
            quote = choice(quotes)
            vtkbot.send_channel_message(channel, "<%s> %s" % (quote.user, quote.text))
            return

        match = re.match("%s: quote ([^\s]*) (.*)" % self.factory.nickname, message)
        if match:
            #Add quote
            user = match.group(1)
            text = match.group(2)
            quote = Quote(user, channel, text)
            session.save_or_update(quote)
            session.commit()
            vtkbot.send_channel_message(channel, "Quote toegevoegd.")
            return

    def on_help(self, vtkbot, channel):
        vtkbot.send_channel_message(channel, "Quote biedt de mogelijkheid mensen te citeren. Typ '%s: quote' om quotes weer te geven." % self.factory.nickname)

    def create_database_tables(self):
        metadata = MetaData()
        #Create SQL tables
        quotes_table = Table('quotes', metadata,
            Column('id', Integer, primary_key=True),
            Column('user', Unicode(length=35)),
            Column('channel', Unicode(length=100)),
            Column('text', Unicode(length=150)),
        )
        try:
            mapper(Quote, quotes_table)
        except: #This is for mapper reloads -- unloading the mappers doesn't seem to work
            pass
        metadata.create_all(self.factory.engine)
        self.Session = sessionmaker(bind=self.factory.engine)

class Quote(object):
    def __init__(self, user, channel, text):
        self.user = user
        self.channel = channel
        self.text = text

    def __repr__(self):
        return u'<Quote(%s, %s, %s)>' % (self.user, self.channel, self.text)
