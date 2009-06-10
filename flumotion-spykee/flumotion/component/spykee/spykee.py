# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Flumotion - a streaming media server
# Copyright (C) 2004,2005 Fluendo, S.L. (www.fluendo.com). All rights reserved.

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.

# Licensees having purchased or holding a valid Flumotion Advanced
# Streaming Server license may use this file in accordance with the
# Flumotion Advanced Streaming Server Commercial License Agreement.
# See "LICENSE.Flumotion" in the source distribution for more information.

# Headers in this file shall remain intact.
import gst

from flumotion.component import feedcomponent

from flumotion.component.spykee import twistedprotocol

from twisted.internet import reactor

class SpykeeMedium(feedcomponent.FeedComponentMedium):
    def remote_dock(self):
        self.comp.cf.currentProtocol.dock()

    def remote_undock(self):
        self.comp.cf.currentProtocol.undock()

    def remote_playSound(self, soundNumber):
        self.comp.cf.currentProtocol.playSound(soundNumber)

    def remote_forward(self, speed, time):
        if speed >= 25 and speed <= 123:
            self.comp.cf.currentProtocol.motorForward(speed, time)

    def remote_back(self, speed, time):
        if speed >=25 and speed <= 123:
            self.comp.cf.currentProtocol.motorBack(speed, time)

class SpykeeProducer(feedcomponent.ParseLaunchComponent):
    componentMediumClass = SpykeeMedium
    logCategory = "spykee"

    def init(self):
        self.uiState.addKey('battery-level', 0)

    def get_pipeline_string(self, properties):
        return "appsrc do-timestamp=true name=src ! jpegdec ! videorate ! video/x-raw-yuv,framerate=25/1"

    def configure_pipeline(self, pipeline, properties):
        self._source = self.pipeline.get_by_name("src")
        self._source.set_property('caps',
            gst.caps_from_string("image/jpeg, width=320, height=240"))
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
        self._source.emit("push-buffer", buf)

    def audioFrame(self, frame):
        pass

    def batteryLevel(self, level):
        self.uiState.set("battery-level", level)
