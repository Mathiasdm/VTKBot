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

class Plugin(object):

    def __init__(self, factory):
        self.factory = factory
        self.channel_message_rule = ""
        self.channel_kick_rule = ""
        self.user_join_rule = ""
        self.connected_rule = ""

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        pass

    def on_user_join(self, vtkbot, nick, nickmask, hostmask, channel):
        pass

    def on_connected(self, vtkbot):
        pass

    def on_kick(self, vtkbot, nick, nickmask, hostmask, channel, target):
        pass

    def create_database_tables(self):
        pass
