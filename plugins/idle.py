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
import settings

class Idle(Plugin):
    """ A plugin for idle RPG """

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.connected_rule = ".*?"

    def on_connected(self, vtkbot):
        vtkbot.send_private_message(settings.plugins_idle_nick, "login %s %s" % (settings.plugins_idle_own_name, settings.plugins_idle_password))
