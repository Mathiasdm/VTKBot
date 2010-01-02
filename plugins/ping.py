from plugin import Plugin
import re

class Ping(Plugin):

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.channel_message_rule = "(?i)%s: ping" % factory.nickname

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        vtkbot.send_channel_message(channel, "pong %s" % nick)

    def on_help(self, vtkbot, channel):
        vtkbot.send_channel_message(channel, "Ping helpt om te controleren of je nog verbonden bent met de server. Typ '%s: ping' en je krijgt meteen reactie." % self.factory.nickname)
