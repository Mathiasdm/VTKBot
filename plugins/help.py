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

class Help(Plugin):

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.channel_message_rule = "%s: help" % factory.nickname

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        plugins = "Er zijn %d plugins:" % len(self.factory.plugins)
        for plugin in self.factory.plugins:
            plugins += " %s," % plugin.__class__.__name__
        plugins = plugins[:-1]
        vtkbot.send_channel_message(channel, plugins)
        for plugin in self.factory.plugins:
            try:
                plugin.on_help(vtkbot, channel) #TODO: iets mooier doen, is er een has_method?
            except:
                pass
