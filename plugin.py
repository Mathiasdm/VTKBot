class Plugin(object):

    def __init__(self, factory):
        self.factory = factory
        self.channel_message_rule = ""
        self.user_join_rule = ""

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        pass

    def on_user_join(self, vtkbot, nick, nickmask, hostmask, channel):
        pass

    def create_database_tables(self):
        pass
