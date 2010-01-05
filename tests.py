import os
import settings
import unittest
from timeit import Timer
from datetime import datetime
from twisted.internet import reactor
from sqlalchemy import create_engine
from sets import Set
from random import randint

from core import VTKBot, VTKBotFactory
from plugin import Plugin
from plugins.quote import QuoteObject

def generate_random_word(min_length, max_length):
    length = randint(min_length, max_length)
    word_chars = []
    for i in range(length):
        word_chars.append(chr(randint(ord('a'), ord('z'))))
    return u''.join(word_chars)

def generate_random_sentence(min_words, max_words, min_word_length, max_word_length):
    length = randint(min_words, max_words)
    words = []
    for i in range(length):
        words.append(generate_random_word(min_word_length, max_word_length))
    return u' '.join(words)

class MockVTKBot(VTKBot):
    """ A mock VTKBot for debugging purposes: this way we can save messages and study them. """

    def send_channel_message(self, channel, message):
        if not hasattr(self, 'message_list'):
            self.message_list = []
        self.message_list.append(message)

class MockVTKBotFactory(VTKBotFactory):
    """ A mock VTKBotFactory that creates a MockVTKBot. """

    protocol = MockVTKBot

    def __init__(self, realname="RealName", host="localhost", server="localhost", port=9999, nickname="NickName", username="UserName",
            databasefile="sqlite:///test.db", channels=["#test", "#test2"]):
        self.nickname = nickname
        self.username = username
        self.realname = realname
        self.host = host
        self.server = server
        self.port = port
        self.databasefile = "test.db"
        self.engine = create_engine("sqlite:///%s" % self.databasefile, echo=False)
        self.channels = channels
        self.load_plugins()

class TestVTKBotFactory(unittest.TestCase):

    def setUp(self):
        settings.plugin_list = ["ping.py", "help.py", "say.py"]
        self.factory = MockVTKBotFactory(nickname=settings.core_nickname, server=settings.core_server, channels=settings.core_channels)

    def tearDown(self):
        try:
            os.remove(self.factory.databasefile)
        except:
            pass

    def testPluginReload(self):
        "Make sure the plugin classes are only loaded once."
        for i in range(1,5):
            self.factory.load_plugins()

        plugin_set = Set(Plugin.__subclasses__())

        self.assertEquals(len(plugin_set), len(Plugin.__subclasses__()))
        #Note: we can't compare the lenght of the list of Plugin subclasses to the length of settings.plugin_list,
        #because the other unit tests will also load Plugin subclasses.
        #This should actually be fixed in the future :)

    def testEndswith(self):
        plugin_list_1 = ["abc", "def", "ghijklm", ""]
        plugin_list_2 = ["test.py", "blah.py"]
        plugin_list_3 = []
        name_1 = "abcd"
        name_2 = "klm"
        name_3 = "test.py"
        self.assertEquals(True, self.factory.endswith(name_1, plugin_list_1)) #Every plugin is accepted if you add ""
        self.assertEquals(True, self.factory.endswith(name_2, plugin_list_1))
        self.assertEquals(False, self.factory.endswith(name_2, plugin_list_2))
        self.assertEquals(True, self.factory.endswith(name_3, plugin_list_2))
        self.assertEquals(False, self.factory.endswith(name_3, plugin_list_3))

class TestPingPlugin(unittest.TestCase):
    def setUp(self):
        settings.plugin_list = ["ping.py"]
        self.factory = MockVTKBotFactory(nickname=settings.core_nickname, server=settings.core_server, channels=settings.core_channels)
        self.vtkbot = self.factory.buildProtocol(('localhost', 9999))
        self.sender_nick = "blah"

    def tearDown(self):
        try:
            os.remove(self.factory.databasefile)
        except:
            pass

    def runPing(self):
        "Basic method to receive a ping message."
        self.vtkbot.lineReceived(":%s!blih@bloeh PRIVMSG #test :%s: ping" % (self.sender_nick, self.factory.nickname))

    def testPingContents(self):
        "Make sure we get the correct ping response."
        #Clear message list
        self.vtkbot.message_list = []

        self.runPing()

        self.assertEquals(1, len(self.vtkbot.message_list))

    def testPingSpeed(self):
        "Make sure pings are very fast."
        before = datetime.now()
        for i in range(1, 100):
            self.runPing()
        after = datetime.now()
        diff = after - before
        self.assert_(diff.seconds < 1)

class TestQuotePlugin(unittest.TestCase):
    def setUp(self):
        settings.plugin_list = ["quote.py"]
        self.factory = MockVTKBotFactory(nickname=settings.core_nickname, server=settings.core_server, channels=settings.core_channels)
        self.vtkbot = self.factory.buildProtocol(('localhost', 9999))
        self.sender_nick = "blah"
        self.sender_nickmask = "blih"
        self.sender_host = "somehost.com"
        self.channel = "#test"

        for plugin in self.factory.plugins:
            if plugin.__class__.__name__ == "Quote":
                self.quote_plugin = plugin

    def tearDown(self):
        try:
            os.remove(self.factory.databasefile)
        except:
            pass

    def runQuote(self, quotetext):
        self.vtkbot.on_channel_message(self.sender_nick, self.sender_nickmask, self.sender_host, self.channel, quotetext)

    def testQuotes(self):
        "Make sure quotes are selected or a 'no quotes found' message is returned."
        #Variables
        user_name = []
        user_name.append("SomeName")
        user_name.append("SomeOtherName")
        user_quote = []
        user_quote.append("This is a quote!")
        user_quote.append("This is a second quote!")
        user_quote.append("This is a third quote!")
        session = self.quote_plugin.Session()

        #Remove previous state
        self.vtkbot.message_list = []

        #No quotes present yet
        quotes = session.query(QuoteObject).all()
        self.assertEquals(0, len(quotes))

        #Request a quote
        self.runQuote("%s: quote" % (self.factory.nickname))
        quotes = session.query(QuoteObject).all()

        self.assertEquals(0, len(quotes))
        self.assertEquals(1, len(self.vtkbot.message_list))
        for quote in user_quote:
            self.assert_(self.vtkbot.message_list[0].find(quote) < 0)

        #Add quotes
        for user in user_name:
            for quote in user_quote:
                self.runQuote("%s: quote %s %s" % (self.factory.nickname, user, quote))
        quotes = session.query(QuoteObject).all()

        self.assertEquals(len(user_name)*len(user_quote), len(quotes))
        self.assertEquals(1 + len(user_name)*len(user_quote), len(self.vtkbot.message_list))

        #Request a quote
        self.runQuote("%s: quote" % self.factory.nickname)
        quotes = session.query(QuoteObject).all()

        self.assertEquals(len(user_name)*len(user_quote), len(quotes))
        self.assertEquals(2 + len(user_name)*len(user_quote), len(self.vtkbot.message_list))

        quote_found = False
        for user in user_name:
            for quote in user_quote:
                if self.vtkbot.message_list[1 + len(user_name)*len(user_quote)].find(quote):
                    quote_found = True
        self.assert_(quote_found)

    def testUserQuotes(self):
        "Request quotes from a user."
        #Variables
        user_name = "SomeName"
        user_quote = "This is a quote!"
        session = self.quote_plugin.Session()

        #Remove previous state
        self.vtkbot.message_list = []

        #No quotes present yet
        quotes = session.query(QuoteObject).all()
        self.assertEquals(0, len(quotes))

        #Request a user quote
        self.runQuote("%s: quote %s" % (self.factory.nickname, user_name))
        quotes = session.query(QuoteObject).all()

        self.assertEquals(0, len(quotes))
        self.assertEquals(1, len(self.vtkbot.message_list))
        self.assert_(self.vtkbot.message_list[0].find(user_quote) < 0)

        #Add a user quote
        self.runQuote("%s: quote %s %s" % (self.factory.nickname, user_name, user_quote))
        quotes = session.query(QuoteObject).all()

        self.assertEquals(1, len(quotes))
        self.assertEquals(2, len(self.vtkbot.message_list))

        #Request a user quote
        self.runQuote("%s: quote %s" % (self.factory.nickname, user_name))
        quotes = session.query(QuoteObject).all()

        self.assertEquals(1, len(quotes))
        self.assertEquals(3, len(self.vtkbot.message_list))
        self.assert_(self.vtkbot.message_list[2].find(user_quote))

    def testQuoteSpeed(self):
        "Make sure adding and viewing quotes does not take too much time."

        #Prepare names and sentences
        names = []
        sentences = []
        for i in range(5):
            names.append(generate_random_word(10,30))
        for i in range(20):
            sentences.append(generate_random_sentence(5, 20, 10, 30))

        #Send quotes
        before = datetime.now()
        for name in names:
            for sentence in sentences:
                self.runQuote(u"%s: quote %s %s" % (self.factory.nickname, name, sentence))
        after = datetime.now()
        diff = after - before
        self.assert_(diff.seconds < len(names)*len(sentences)/10) #10 quotes/second

        #Request quotes
        before = datetime.now()
        for name in names:
            for sentence in sentences:
                self.runQuote(u"%s: quote" % (self.factory.nickname))
        after = datetime.now()
        diff = after - before
        self.assert_(diff.seconds < 10)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQuotePlugin)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestPingPlugin)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestVTKBotFactory)
    unittest.TextTestRunner(verbosity=2).run(suite)
