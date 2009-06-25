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
import gobject
gobject.threads_init()
import gst
import gtk

from kiwi.ui.delegates import Delegate
from kiwi.ui.objectlist import ObjectList, Column
from kiwi.ui.views import SlaveView

from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor

import twistedprotocol
import gstreamer

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
        self.connectinglabel.set_text("Connecting to %s at %s" % (robot.name,
            robot.ip))
        self.robot = robot

    def on_cancelbutton__clicked(self, *args):
        self.view.hide_and_quit()

    def on_authconnectbutton__clicked(self, *args):
        self.control = SpykeeControl(self.robot, self.username.get_text(),
            self.password.get_text())
        self.control.show()
        self.view.hide_and_quit()

class SpykeeControl(Delegate):
    widgets = ["quitbutton", "forwardbutton", "reversebutton", "leftbutton",
        "rightbutton", "dockbutton", "canceldockbutton", "undockbutton",
        "playsoundbutton", "manualmovebutton", "leftmotor", "rightmotor",
        "docked", "all", "viewlogbutton", "picture"]
    gladefile = "spykee"
    toplevel_name = "control"

    def __init__(self, robot, username, password):
        Delegate.__init__(self, delete_handler=self.quit_if_last)
        self.robot = robot
        self.username = username
        self.password = password
        print "connecting to %s (%s) with %s:%s" % (robot.name, 
            robot.ip, username, password)
        self.all.set_sensitive(False)
        self.cf = twistedprotocol.SpykeeClientFactory(self.username,
            self.password, self)
        self.pipeline = None
        reactor.connectTCP(self.robot.ip, 9000, self.cf)

    def on_viewlogbutton__clicked(self, *args):
        self.cf.currentProtocol.getLog()

    def on_forwardbutton__clicked(self, *args):
        self.cf.currentProtocol.motorForward(50)

    def on_reversebutton__clicked(self, *args):
        self.cf.currentProtocol.motorBack(50)

    def on_leftbutton__clicked(self, *args):
        self.cf.currentProtocol.motorLeft()

    def on_rightbutton__clicked(self, *args):
        self.cf.currentProtocol.motorRight()

    def on_manualmovebutton__clicked(self, *args):
        left = self.leftmotor.get_value_as_int()
        right = self.rightmotor.get_value_as_int()
        if left < 0:
            left += 128
        if right < 0:
            right += 128
        self.cf.currentProtocol.motorCommand(left, right, 0.5)

    def on_undockbutton__clicked(self, *args):
        self.cf.currentProtocol.undock()
        self.docked.set_markup("<b>Undocked</b>")
        self.startStreaming()
        
    def on_dockbutton__clicked(self, *args):
        self.cf.currentProtocol.dock()

    def on_canceldockbutton__clicked(self, *args):
        self.cf.currentProtocol.cancelDock()

    def on_quitbutton__clicked(self, *args):
        if self.pipeline:
            self.pipeline.set_state(gst.STATE_NULL)
        self.view.hide_and_quit()

    # protocol callbacks
    def isDocked(self, docked):
        self.all.set_sensitive(True)
        if docked:
            self.docked.set_markup("<b>Docked</b>")
        else:
            self.docked.set_markup("<b>Undocked</b>")
            self.startStreaming()
    
    def connectionLost(self, reason):
        d = gtk.Dialog("Connection to spykee lost: reason %r" % reason, 
            None, 0, (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        d.show()

    def connectionFailed(self, reason):
        d = gtk.Dialog("Connection to spykee failed: reason %r" % reason, 
            None, 0, (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        d.show()
    
    def videoFrame(self, frame):
        if self.src:
            self.src.videoFrame(frame)

    def audioSample(self, sample):
        if self.src:
            self.src.audioSample(sample)

    def batteryLevel(self, level):
        self.batterylevel.set_text("Battery: %d" % (level,))

    def logReceived(self, log):
        print "Log: %r" % log

    # pipeline stuff
    def startStreaming(self):
        self.cf.currentProtocol.setSoundVolume(85)
        self.cf.currentProtocol.activateVideo()
        self.cf.currentProtocol.activateSound()
        if self.pipeline:
            self.pipeline.set_state(gst.STATE_NULL)
            self.pipeline.get_state()
        self.pipeline = gst.parse_launch("spykeesrc name=src  ! xvimagesink sync=false")
        bus = self.pipeline.get_bus()
        bus.enable_sync_message_emission()
        bus.add_signal_watch()
        bus.connect("sync-message::element", self.on_sync_message)
        bus.connect("message", self.on_message)
        self.src = self.pipeline.get_by_name("src")
        self.src.set_property("connect", False)
        self.pipeline.set_state(gst.STATE_PLAYING)

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return None
        if message.structure.get_name() == 'prepare-xwindow-id':
            gtk.gdk.display_get_default().sync()
            message.src.set_xwindow_id(self.picture.window.xid)
            message.src.set_property('force-aspect-ratio', True)

    def on_message(self, bus, message):
        pass

    
delegate = Discoverer()
delegate.show()
reactor.run()
