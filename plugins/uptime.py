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
from datetime import datetime
import re

class Uptime(Plugin):

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.channel_message_rule = "(?i)%s: uptime" % factory.nickname
        self.load_time = datetime.now()

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        uptime = datetime.now() - self.load_time
        if uptime.days > 1:
            vtkbot.send_channel_message(channel, "Ik ben al online gedurende %s dagen." % uptime.days)
        elif uptime.days > 0:
            vtkbot.send_channel_message(channel, "Ik ben al online gedurende %s dag." % uptime.days)
        elif uptime.seconds > 7200:
            vtkbot.send_channel_message(channel, "Ik ben al online gedurende %s uren." % (uptime.seconds/3600))
        elif uptime.seconds > 3600:
            vtkbot.send_channel_message(channel, "Ik ben al online gedurende %s uur." % (uptime.seconds/3600))
        elif uptime.seconds > 120:
            vtkbot.send_channel_message(channel, "Ik ben al online gedurende %s minuten." % (uptime.seconds/60))
        elif uptime.seconds > 60:
            vtkbot.send_channel_message(channel, "Ik ben al online gedurende %s minuut." % (uptime.seconds/60))
        else:
            vtkbot.send_channel_message(channel, "Ik ben al online gedurende %s seconden." % uptime.seconds)

    def on_help(self, vtkbot, channel):
        vtkbot.send_channel_message(channel, "Met uptime kan je weten hoe lang %s al online is. Typ '%s: uptime' om zijn uptime te weten." % (self.factory.nickname, self.factory.nickname))
