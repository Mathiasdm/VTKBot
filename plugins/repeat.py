from plugin import Plugin
import re

class Repeat(Plugin):

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.channel_message_rule = "(?i)%s: repeat (.*)" % factory.nickname

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        vtkbot.send_channel_message(channel, match.group(1))
