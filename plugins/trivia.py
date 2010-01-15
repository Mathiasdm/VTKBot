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
import re
from sqlalchemy import create_engine, func, select, Table, Column, Integer, Unicode, MetaData, DateTime, String, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.sql.expression import asc, desc
from random import randint
from twisted.internet import reactor
from twisted.internet import task
import codecs

def is_number(uni):
    try:
        int(uni)
        return True
    except:
        return False

class Trivia(Plugin):

    def __init__(self, factory):
        Plugin.__init__(self, factory)
        self.channel_message_rule = "(.*)"
        self.trivia_started = {} #Dict with channel name and boolean to see if the trivia is busy on that channel
        self.questions = {}
        self.answered = {}
        self.timers = {}
        for channel in self.factory.channels:
            self.trivia_started[channel] = False

    def on_channel_message(self, vtkbot, nick, nickmask, hostmask, channel, message, match):
        match = re.match("%s: trivia top$" % self.factory.nickname, message)
        if match:
            self.on_trivia_top(vtkbot, channel)
            return

        if self.trivia_started[channel]:
            match = re.match("%s: trivia stop" % self.factory.nickname, message)
            if match:
                self.on_trivia_stop(vtkbot, channel)
                return
            match = re.match("%s: trivia skip" % self.factory.nickname, message)
            if match:
                self.questions[channel].on_skip(vtkbot, channel, self)
                return
            elif (not channel in self.answered) or not self.answered[channel]:
                self.questions[channel].on_answer(vtkbot, nick, channel, message, self) #Somebody answered, the Question class will check if the answer's correct
                return
        else:
            match = re.match("%s: trivia start" % self.factory.nickname, message)
            if match:
                self.on_trivia_start(vtkbot, channel)
                return
            match = re.match("%s: trivia loaddump regular \"(.*?)\" \"(.*?)\"" % self.factory.nickname, message)
            if match:
                filename = match.group(1)
                dumpfile = codecs.open(filename, 'r', 'utf-8')
                session = self.Session()
                for line in dumpfile.readlines():
                    line = line.replace('\r', '').replace('\n', '')
                    linematch = re.match(u'(.*)¶(.*)', line)
                    if linematch:
                        question_string = (linematch.group(1))
                        answer_string = (linematch.group(2))
                        category_string = (match.group(2))
                        question = RegularQuestion(question = question_string, answer = answer_string, category = category_string)
                        session.save_or_update(question)
                session.commit()
                vtkbot.send_channel_message(channel, "Nieuwe vragen toegevoegd.")
                return

    def on_trivia_start(self, vtkbot, channel):
        self.trivia_started[channel] = True
        vtkbot.send_channel_message(channel, "Trivia gestart!", "BLUE")
        self.on_next_question(vtkbot, channel)

    def on_trivia_stop(self, vtkbot, channel):
        if channel in self.timers:
            for timer in self.timers[channel]:
                try:
                    timer.cancel()
                except:
                    pass
        self.trivia_started[channel] = False
        vtkbot.send_channel_message(channel, "Trivia gestopt!", "BLUE")

    def on_trivia_top(self, vtkbot, channel, count=10):
        vtkbot.send_channel_message(channel, "Top scores op %s:" % channel)
        session = self.Session()
        users = session.query(User).filter_by(channel=channel).order_by(desc('score'))[:count]
        for index, user in enumerate(users):
            vtkbot.send_channel_message(channel, "%s. %s: %s punten voor %s vragen" % (index + 1, user.nickname, user.score, user.questioncount))

    def on_point_change(self, vtkbot, channel, nick, change):
        session = self.Session()
        user = session.query(User).filter_by(channel=channel, nickname=nick).first()
        if not user:
            user = User(nick, channel, 0, 0)
        user.questioncount += 1
        user.score += change
        session.save_or_update(user)
        session.commit()
        vtkbot.send_channel_message(channel, "%s krijgt %s punten!" % (nick, change), bold=True)
        vtkbot.send_channel_message(channel, "%s heeft nu in totaal %s punten voor %s vragen!" % (nick, user.score, user.questioncount), bold=True)

    def on_next_question(self, vtkbot, channel):
        #Get a question from the database
        session = self.Session()
        max_question = session.query(Question).filter(Question.question_id == func.max(Question.question_id).select()).first()
        if max_question == None:
            vtkbot.send_channel_message(channel, "Ik heb geen vragen! :(")
            self.on_trivia_stop(vtkbot, channel)
        else:
            question_id = randint(1, max_question.question_id)
            question = session.query(Question).filter(Question.question_id >= question_id).order_by(asc('question_id')).first()
            self.questions[channel] = question
            reactor.callLater(0.1, self.questions[channel].start, vtkbot, channel, self)

    def on_help(self, vtkbot, channel):
        vtkbot.send_channel_message(channel, "Trivia is een spel waarbij je zo snel mogelijk de vragen juist moet beantwoorden.")
        vtkbot.send_channel_message(channel, "Om een spel te starten, typ je '%s: trivia start', om een te stoppen '%s: trivia stop'. Om een vraag over te slaan: '%s: trivia skip'." % (self.factory.nickname, self.factory.nickname))

    def create_database_tables(self):
        metadata = MetaData()
        #Create SQL tables
        questions = Table('questions', metadata,
            Column('question_id', Integer, primary_key=True),
            Column('question', Unicode(length=150)),
            Column('category', Unicode(length=50)),
            Column('type', Unicode(30), nullable=False)
        )
        regularquestions = Table('regularquestions', metadata,
            Column('regularquestion_id', Integer, ForeignKey('questions.question_id'), primary_key=True),
            Column('answer', Unicode(length=150)),
        )
        pimpampetquestions = Table('pimpampetquestions', metadata,
            Column('pimpampetquestion_id', Integer, ForeignKey('questions.question_id'), primary_key=True),
        )
        pimpampetanswers = Table('pimpampetanswers', metadata,
            Column('id', Integer, primary_key=True),
            Column('answer', Unicode(length=150)),
        )
        users = Table('users', metadata,
            Column('id', Integer, primary_key=True),
            Column('nickname', Unicode(length=35)),
            Column('channel', Unicode(length=150)),
            Column('score', Integer),
            Column('questioncount', Integer),
        )
        mapper(Question, questions, polymorphic_on=questions.c.type, polymorphic_identity='question')
        mapper(RegularQuestion, regularquestions, inherits=Question, polymorphic_identity='regularquestion')
        mapper(PimPamPetQuestion, pimpampetquestions, inherits=Question, polymorphic_identity='pimpampetquestion')
        mapper(PimPamPetAnswer, pimpampetanswers)
        mapper(User, users),
        metadata.create_all(self.factory.engine)
        self.Session = sessionmaker(bind=self.factory.engine)

class Question(object):
    def __init__(self, question, category):
        self.question = question
        self.category = category

    def start(self, vtkbot, channel, trivia_plugin):
        pass #Schedule timers and post question

    def on_answer(self, vtkbot, nickname, channel, answer, trivia_plugin):
        pass

    def on_skip(self, vtkbot, channel, trivia_plugin):
        pass

    def get_dots(self, answer):
        answer_list = self.answer.split(" ")
        answer_dots = ""
        for answer in answer_list:
            answer_dots += '.' * len(answer) + ' '
        answer_dots = answer_dots[:-1]
        return answer_dots

    def get_lengths(self, answer):
        answer_list = self.answer.split(" ")
        answer_lengths = ""
        for answer in answer_list:
            answer_lengths += unicode(len(answer)) + '+'
        answer_lengths = answer_lengths[:-1]
        return answer_lengths

    def __repr__(self):
        return u'<Question(%s)>' % (self.question)

class RegularQuestion(Question):
    def __init__(self, question, category, answer):
        Question.__init__(self, question, category)
        self.answer = answer

    def start(self, vtkbot, channel, trivia_plugin):
        trivia_plugin.answered[channel] = False
        if is_number(self.answer):
            self.score = 50
            self.attempts = {}
            post_question = reactor.callLater(1, self.post_number_question, vtkbot, channel)
            next_question = reactor.callLater(21, self.next_question, vtkbot, channel, trivia_plugin)
            trivia_plugin.timers[channel] = [post_question, next_question]
        else:
            self.score = 100
            post_question = reactor.callLater(1, self.post_question, vtkbot, channel)
            first_hint = reactor.callLater(10, self.nth_hint, vtkbot, channel, 1, 4)
            second_hint = reactor.callLater(20, self.nth_hint, vtkbot, channel, 2, 4)
            third_hint = reactor.callLater(30, self.nth_hint, vtkbot, channel, 3, 4)
            fourth_hint = reactor.callLater(40, self.nth_hint, vtkbot, channel, 4, 4)
            next_question = reactor.callLater(50, self.next_question, vtkbot, channel, trivia_plugin)
            trivia_plugin.timers[channel] = [post_question, first_hint, second_hint, third_hint, fourth_hint, next_question]

    def post_question(self, vtkbot, channel):
        question = vtkbot.coloured_message("Gewone vraag", "BLUE")
        question += " %s: %s (%s: %s)" % (self.regularquestion_id, self.question, self.get_lengths(self.answer), self.get_dots(self.answer))
        vtkbot.send_channel_message(channel, question)

    def post_number_question(self, vtkbot, channel):
        question = vtkbot.coloured_message("Getallenvraag", "BLUE")
        question += " %s: %s (%s: %s)" % (self.regularquestion_id, self.question, self.get_lengths(self.answer), self.get_dots(self.answer))
        vtkbot.send_channel_message(channel, question)
        vtkbot.send_channel_message(channel, "Voor deze vraag heb je maar 20 seconden tijd en slechts 2 pogingen!", "RED")

    def nth_hint(self, vtkbot, channel, n, total_hints):
        self.score = self.score/2
        answer_hint = self.answer[:]
        for i in range(len(answer_hint)):
            if (i%total_hints != n-1) and (answer_hint[i] != ' '):
                answer_hint = answer_hint[:i] + '.' + answer_hint[i+1:]
        vtkbot.send_channel_message(channel, "Hint %s: %s" % (n, answer_hint))

    def next_question(self, vtkbot, channel, trivia_plugin):
        trivia_plugin.answered[channel] = True
        vtkbot.send_channel_message(channel, "Jammer, niemand kon het antwoord raden. Het juiste antwoord was: %s" % self.answer)
        reactor.callLater(1, trivia_plugin.on_next_question, vtkbot, channel)

    def on_skip(self, vtkbot, channel, trivia_plugin):
        trivia_plugin.answered[channel] = True
        for timer in trivia_plugin.timers[channel]:
            try:
                timer.cancel()
            except:
                pass
        vtkbot.send_channel_message(channel, "De vraag wordt overgeslaan. Het juiste antwoord was: %s" % self.answer)
        reactor.callLater(1, trivia_plugin.on_next_question, vtkbot, channel)

    def on_answer(self, vtkbot, nickname, channel, answer, trivia_plugin):
        if is_number(self.answer):
            try:
                self.attempts[nickname] += 1
            except:
                self.attempts[nickname] = 0

            if self.attempts[nickname] >= 2:    
                return

        if answer.lower() == self.answer.lower():
            trivia_plugin.answered[channel] = True
            for timer in trivia_plugin.timers[channel]:
                try:
                    timer.cancel()
                except:
                    pass
            vtkbot.send_channel_message(channel, "%s heeft het correcte antwoord (%s) gegeven!" % (nickname, self.answer))
            trivia_plugin.on_point_change(vtkbot, channel, nickname, self.score)
            reactor.callLater(1, trivia_plugin.on_next_question, vtkbot, channel)
        elif is_number(self.answer):
            if self.attempts[nickname] == 1:
                vtkbot.send_channel_message(channel, "%s is uitgeschakeld!" % nickname, "RED")

    def __repr__(self):
        return u'<Question(%s, %s)>' % (self.question, self.answer)

class PimPamPetQuestion(Question):
    def __init__(self, question, category):
        Question.__init__(self, question, category)

class PimPamPetAnswer(object):
    def __init__(self, answer, question):
        self.answer = answer
        self.question = question

class User(object):
    def __init__(self, nickname, channel, score, questioncount):
        self.nickname = nickname
        self.channel = channel
        self.score = score
        self.questioncount = questioncount
