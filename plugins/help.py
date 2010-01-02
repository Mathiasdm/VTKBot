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
