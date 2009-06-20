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
import gst

from flumotion.common.i18n import N_, gettexter
from flumotion.common.planet import moods
from flumotion.component import feedcomponent

from flumotion.component.spykee import twistedprotocol

from twisted.internet import reactor

T_ = gettexter()

class SpykeeMedium(feedcomponent.FeedComponentMedium):
    def remote_dock(self):
        self.comp.cf.currentProtocol.dock()

    def remote_undock(self):
        self.comp.cf.currentProtocol.undock()

    def remote_canceldock(self):
        self.comp.cf.currentProtocol.cancelDock()

    def remote_playSound(self, soundNumber):
        self.comp.cf.currentProtocol.playSound(soundNumber)

    def remote_forward(self, speed, time):
        if speed >= 0 and speed < 128:
            self.comp.cf.currentProtocol.motorForward(speed, time)

    def remote_back(self, speed, time):
        if speed >= 0 and speed < 128:
            self.comp.cf.currentProtocol.motorBack(speed, time)

    def remote_left(self):
        self.comp.cf.currentProtocol.motorLeft()

    def remote_right(self):
        self.comp.cf.currentProtocol.motorRight()

    def remote_motor(self, leftMotor, rightMotor, time):
        self.comp.cf.currentProtocol.motorCommand(leftMotor, rightMotor, time)

    def remote_light(self, led, on):
        self.comp.cf.currentProtocol.light(led, on)

class SpykeeProducer(feedcomponent.ParseLaunchComponent):
    componentMediumClass = SpykeeMedium
    logCategory = "spykee-producer"

    def init(self):
        self.uiState.addKey('battery-level', 0)

    def get_pipeline_string(self, properties):
        return "appsrc do-timestamp=true name=vsrc ! queue ! jpegdec ! videorate ! video/x-raw-yuv,framerate=15/1 ! @feeder:video@ appsrc do-timestamp=true name=asrc ! queue ! audiorate ! audio/x-raw-int,rate=16000,channels=1,width=16,depth=16 ! @feeder:audio@"

    def configure_pipeline(self, pipeline, properties):
        self._vsource = self.pipeline.get_by_name("vsrc")
        self._vsource.set_property('caps',
            gst.caps_from_string("image/jpeg, width=320, height=240"))
        self._asource = self.pipeline.get_by_name("asrc")
        self._asource.set_property('caps',
            gst.caps_from_string("audio/x-raw-int,rate=16000,channels=1,width=16,depth=16,signed=true,endianness=1234"))
        self.debug("Configured pipeline")

    def check_properties(self, properties, addMessage):
        self._port = properties.get("port", 9000)
        self._hostname = properties.get("hostname", "localhost")
        self._username = properties.get("username", "admin")
        self._password = properties.get("password", "admin")
        self.debug("set properties")

    def do_setup(self):
        self.cf = twistedprotocol.SpykeeClientFactory(self._username,
            self._password, self)
        reactor.connectTCP(self._hostname, self._port, self.cf)
        self.debug("connecting to spykee robot at %s:%d with %s:%s", self._hostname, self._port, self._username, self._password)

    def videoFrame(self, frame):
        buf = gst.Buffer(frame)
        self._vsource.emit("push-buffer", buf)

    def audioSample(self, sample):
        buf = gst.Buffer(sample)
        self._asource.emit("push-buffer", buf)

    def batteryLevel(self, level):
        self.uiState.set("battery-level", level)

    def connectionLost(self, reason):
        m = messages.Error(T_(N_(
            "Connection to spykee lost: reason %r" % reason)), mid="lostconn")
        self.addMessage(m)
        self.setMood(moods.sad)

    def connectionFailed(self, reason):
        m = messages.Error(T_(N_(
            "Connection to spykee failed: reason %r" % reason)), 
            mid="failedconn")
        self.addMessage(m)
        self.setMood(moods.sad)

    def isDocked(self, docked):
        if docked:
            self.cf.currentProtocol.undock()
        self.cf.currentProtocol.setSoundVolume(85)
        self.cf.currentProtocol.activateVideo()
        self.cf.currentProtocol.activateSound()

