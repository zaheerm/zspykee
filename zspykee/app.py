# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Flumotion Spykee component
# Copyright (C) 2009 Zaheer Abbas Merali. All rights reserved.

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.

# Headers in this file shall remain intact.
import gtk

from kiwi.ui.delegates import Delegate
from kiwi.ui.objectlist import ObjectList, Column
from kiwi.ui.views import SlaveView

from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor

import twistedprotocol

class SpykeeRobot:
    def __init__(self, name, ip):
        self.name, self.ip = name, ip

class SpykeeListView(SlaveView):
    def __init__(self):
        self.robots = ObjectList([Column("name", "Name",),
                            Column("ip", "IP Address")])
        d = twistedprotocol.discover(5)
        d.addCallback(self.discovered)
        SlaveView.__init__(self, toplevel=self.robots)

    def discovered(self, spykees):
        if spykees:
            for s in spykees:
                r = SpykeeRobot(s, spykees[s])
                self.robots.append(r)

class Discoverer(Delegate):
    widgets = ["quitbutton", "connectbutton"]
    gladefile = "spykee"
    toplevel_name = "discoverer"

    def __init__(self):
        Delegate.__init__(self, delete_handler=self.quit_if_last)
        self.spykees = SpykeeListView()
        self.attach_slave("my_placeholder", self.spykees)
        self.spykees.show_all()
        self.spykees.focus_toplevel()

    def on_quitbutton__clicked(self, *args):
        self.view.hide_and_quit()

    def on_connectbutton__clicked(self, *args):
        robot = self.spykees.robots.get_selected()
        if robot:
            print "Connect to %s at %s" % (robot.name, robot.ip)
            logindelegate = Login(robot)
            logindelegate.show()
            self.view.hide_and_quit()

class Login(Delegate):
    widgets = ["cancelbutton", "authconnectbutton", "username", "password",
        "connectinglabel"]
    gladefile = "spykee"
    toplevel_name = "login"

    def __init__(self, robot):
        Delegate.__init__(self, delete_handler=self.quit_if_last)
        #self.connectinglabel.set_text("Connecting to %s at %s" % (robot.name,
        #    robot.ip))

    def on_cancelbutton__clicked(self, *args):
        self.view.hide_and_quit()

delegate = Discoverer()
delegate.show()
reactor.run()
