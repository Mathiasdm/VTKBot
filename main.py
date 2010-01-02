from core import *

from twisted.internet import reactor

factory = VTKBotFactory(nickname="VTKBot", server="vtk.ugent.be", channels=["#vtk"])
reactor.connectTCP("vtk.ugent.be", 6667, factory)
reactor.run()
