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
import sys
import gst
import gobject
gobject.threads_init()

#from flumotion.component.spykee import twistedprotocol
from twisted.internet import glib2reactor
glib2reactor.install()
from twisted.internet import reactor

import twistedprotocol

class SpykeeSource(gst.Bin):
    __gstdetails__ = ('SpykeeSrc', 'Source/Video',
        'Spykee Robot Source', 'Zaheer Merali')

    __gsttemplates__ = (
        gst.PadTemplate("video",
                        gst.PAD_SRC,
                        gst.PAD_ALWAYS,
                        gst.caps_from_string(
                            "video/x-raw-yuv,format=(fourcc)I420,width=320,"
                            "height=240,framerate=15/1")
                        ),
        gst.PadTemplate("audio",
                        gst.PAD_SRC,
                        gst.PAD_ALWAYS,
                        gst.caps_from_string(
                            "audio/x-raw-int,channels=1,rate=16000,width=16,"
                            "depth=16,signed=true,endianness=1234")
                        )
    )

    def __init__(self):
        gst.Bin.__init__(self)
        self.vsrc = gst.element_factory_make("appsrc", "vsrc")
        self.vsrc.set_property('caps',
            gst.caps_from_string("image/jpeg, width=320, height=240"))
        self.vsrc.set_property("do-timestamp", True)
        self.vqueue = gst.element_factory_make("queue2", "vqueue")
        self.jpegdec = gst.element_factory_make("jpegdec")
        self.vrate = gst.element_factory_make("videorate")
        self.vcapsfilter = gst.element_factory_make("capsfilter")
        self.vcapsfilter.set_property("caps", gst.caps_from_string(
            "video/x-raw-yuv,framerate=15/1"))
        self.add(self.vsrc, self.vqueue, self.jpegdec, self.vrate, 
            self.vcapsfilter)
        self.vsrc.link(self.vqueue)
        self.vqueue.link(self.jpegdec)
        self.jpegdec.link(self.vrate)
        self.vrate.link(self.vcapsfilter)
        self.vsrcpad = gst.GhostPad("video", self.vcapsfilter.get_pad("src"))
        self.add_pad(self.vsrcpad)
        self.asrc = gst.element_factory_make("appsrc", "asrc")
        self.asrc.set_property('caps',
            gst.caps_from_string("audio/x-raw-int,rate=16000,channels=1,"
                "width=16,depth=16,endianness=1234,signed=true"))
        self.asrc.set_property('do-timestamp', True)
        self.aqueue = gst.element_factory_make("queue2", "aqueue")
        self.audiorate = gst.element_factory_make("audiorate")
        self.acapsfilter = gst.element_factory_make("capsfilter")
        self.acapsfilter.set_property("caps",
             gst.caps_from_string("audio/x-raw-int,rate=16000,channels=1,"
                "width=16,depth=16,endianness=1234,signed=true"))
        self.add(self.asrc, self.aqueue, self.audiorate, self.acapsfilter)
        self.asrc.link(self.aqueue)
        self.aqueue.link(self.audiorate)
        self.audiorate.link(self.acapsfilter)
        self.asrcpad = gst.GhostPad("audio", self.acapsfilter.get_pad("src"))
        self.add_pad(self.asrcpad)
        # defaults
        self._hostname = "172.17.6.1"
        self._port = 9000
        self._username = "admin"
        self._password = "admin"
        self.vcapsfilter.get_pad("src").add_event_probe(self.event_probe)

    def do_change_state(self, transition):
        if transition == gst.STATE_CHANGE_READY_TO_PAUSED:
            # connect to spykee
            self.cf = twistedprotocol.SpykeeClientFactory(self._username,
                self._password, self)
            reactor.connectTCP(self._hostname, self._port, self.cf)
            self.debug("connecting to spykee robot at %s:%d with %s:%s" % (self._hostname, self._port, self._username, self._password))

            pass
        res = gst.Bin.do_change_state(self, transition)
        return res

    def set_property(self, name, value):
        print "Property set: %s = %s" % (name, value)
        if name == "hostname":
            self._hostname = value
        elif name == "username":
            self._username = value
        elif name == "password":
            self._password = value

    def videoFrame(self, frame):
        buf = gst.Buffer(frame)
        self.vsrc.emit("push-buffer", buf)

    def audioSample(self, sample):
        buf = gst.Buffer(sample)
        self.asrc.emit("push-buffer", buf)

    def batteryLevel(self, level):
        pass

    def connectionLost(self, reason):
        self.warning("Connection lost: %r" % (reason,))

    def connectionFailed(self, reason):
        self.warning("Connection failed: %r" % (reason,))

    def isDocked(self, docked):
        self.debug("Connection succeeded: docked - %d" % (docked,))
        if docked:
            self.cf.currentProtocol.undock()
        self.cf.currentProtocol.setSoundVolume(85)
        self.cf.currentProtocol.activateVideo()
        self.cf.currentProtocol.activateSound()

    def event_probe(self, pad, event):
        if event.type == gst.EVENT_NAVIGATION:
            s = event.get_structure()
            if s.get_name() == "application/x-gst-navigation":
                if "event" in s.keys():
                    if s["event"] == "key-press":
                        if "key" in s.keys():
                            if s["key"] == "Up":
                                self.cf.currentProtocol.motorForward(50)
                            elif s["key"] == "Down":
                                self.cf.currentProtocol.motorBack(50)
                            elif s["key"] == "Right":
                                self.cf.currentProtocol.motorRight()
                            elif s["key"] == "Left":
                                self.cf.currentProtocol.motorLeft()
                            elif s["key"] == "d":
                                self.cf.currentProtocol.dock()
        return True

gobject.type_register(SpykeeSource)
gst.element_register(SpykeeSource, 'spykeesrc', gst.RANK_MARGINAL)

if __name__ == '__main__':
    print sys.argv
    p = gst.parse_launch("spykeesrc name=src  ! xvimagesink sync=false src. ! alsasink sync=false")
    if len(sys.argv) >= 4:
        hostname = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]
        src = p.get_by_name("src")
        src.set_property("hostname", hostname)
        src.set_property("username", username)
        src.set_property("password", password)
    p.set_state(gst.STATE_PLAYING)
    reactor.run()
