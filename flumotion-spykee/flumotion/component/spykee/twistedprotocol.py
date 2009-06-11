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

from twisted.internet import protocol, reactor

class SpykeeClient(protocol.Protocol):
    authenticated = False
    name = []
    docked = False
    buffer = ""

    def connectionMade(self):
        # PK<10><0><len(username)+len(password)+2><len(username)username
        # len(password)password
        str = "PK\x0a\x00%s%s%s%s%s" % (chr(len(self.factory.username) +
            len(self.factory.password) + 2), chr(len(self.factory.username)),
            self.factory.username, chr(len(self.factory.password)),
            self.factory.password)
        self.transport.write(str)

    def dataReceived(self, data):
        if not self.authenticated:
            # should get at least 8 characters, otherwise it has not
            # authenticated successfully
            if len(data) < 8:
                self.transport.loseConnection()
            else:
                if data[0:3] == "PK\x0b":
                    nameLength = ord(data[6])
                    if nameLength + 6 < len(data):
                        self.name.append(data[7:nameLength+7])
                    else:
                        self.transport.loseConnection()
                        return
                    curpos = nameLength + 7
                    nameLength = ord(data[curpos])
                    curpos = curpos + 1
                    if nameLength + curpos <= len(data):
                        self.name.append(data[curpos:nameLength+curpos])
                    else:
                        self.transport.loseConnection()
                        return
                    curpos = curpos + nameLength
                    nameLength = ord(data[curpos])
                    curpos = curpos + 1
                    if nameLength + curpos <= len(data):
                        self.name.append(data[curpos:nameLength+curpos])
                    else:
                        self.transport.loseConnection()
                        return
                    curpos = curpos + nameLength
                    nameLength = ord(data[curpos])
                    curpos = curpos + 1
                    if nameLength + curpos <= len(data):
                        self.name.append(data[curpos:nameLength+curpos])
                    else:
                        self.transport.loseConnection()
                        return
                    curpos = curpos + nameLength
                    self.docked = (ord(data[curpos]) == 0)
                    self.authenticated = True
                    self.factory.currentProtocol = self
                    print "I am authenticated to %r" % self.name
                    print "Docked: %d" % self.docked
                    if self.docked:
                        self.undock()
                    if not self.docked:
                        self.setSoundVolume(85)
                        self.activateVideo()
                        self.activateSound()
        else:
            if not self.buffer:
                self.buffer = data
            else:
                self.buffer = "%s%s" % (self.buffer, data)
            if self.buffer[0:2] == "PK":
                length_needed = ord(self.buffer[3]) * 256 + ord(self.buffer[4])
                if length_needed > len(self.buffer) - 5:
                    # have to wait until we have enough data
                    pass
                else:
                    self.commandReceived()
                    self.buffer = self.buffer[length_needed+5:]

    def commandReceived(self):
        if self.buffer[2] == chr(1):
            self.audioSample()
        elif self.buffer[2] == chr(2):
            self.videoFrame()
        elif self.buffer[2] == chr(3):
            self.batteryLevel()
            #print "Battery: %d" % ord(self.buffer[5])
        elif self.buffer[2] == chr(16):
            if self.buffer[3] == chr(0) and self.buffer[4] == chr(1):
                if self.buffer[5] == 2:
                    print "Docked"
                elif self.buffer[5] == 1:
                    print "Undocked"

    def activateVideo(self):
        str = "PK\x0f\x00\x02\x01\x01"
        self.transport.write(str)

    def activateSound(self):
        str = "PK\x0f\x00\x02\x02\x01"
        self.transport.write(str)

    def setSoundVolume(self, volume):
        str = "PK\x09\x00\x01%s" % chr(volume)
        self.transport.write(str)

    def undock(self):
        str = "PK\x10\x00\x01\x05"
        self.transport.write(str)
        self.docked = False

    def dock(self):
        str = "PK\x10\x00\x01\x06"
        self.transport.write(str)
        self.docked = True

    def cancelDock(self):
        str = "PK\x10\x00\x01\x07"
        self.transport.write(str)
        self.docked = False

    def playSound(self, soundNumber):
        str = "PK\x07\x00\x01%s" % chr(soundNumber)
        self.transport.write(str)

    def motorStop(self):
        str = "PK\x05\x00\x02\x00\x00"
        self.transport.write(str)

    def motorForward(self, motorSpeed, time=0.2):
        str = "PK\x05\x00\x02%s%s" % (chr(125 - motorSpeed),
            chr(125 - motorSpeed))
        self.transport.write(str)
        reactor.callLater(time, self.motorStop)

    def motorBack(self, motorSpeed, time=0.2):
        str = "PK\x05\x00\x02%s%s" % (chr(125 + motorSpeed),
            chr(125 + motorSpeed))
        self.transport.write(str)
        reactor.callLater(time, self.motorStop)

    def motorLeft(self, time=0.2):
        str = "PK\x05\x00\x02\x96\x64"
        self.transport.write(str)
        reactor.callLater(time, self.motorStop)

    def motorRight(self, time=0.2):
        str = "PK\x05\x00\x02\x64\x96"
        self.transport.write(str)
        reactor.callLater(time, self.motorStop)

    def light(self, led, on=True):
        onstr = "\x00"
        if on:
            onstr="\x01"
        str = "PK\x04\x00\x02%s%s" % (chr(led), onstr)
        self.transport.write(str)

    def audioSample(self):
        if self.factory.app:
            length = ord(self.buffer[3]) * 256 + ord(self.buffer[4])
            self.factory.app.audioSample(self.buffer[5:5+length])

    def videoFrame(self):
        if self.factory.app:
            length = ord(self.buffer[3]) * 256 + ord(self.buffer[4])
            self.factory.app.videoFrame(self.buffer[5:5+length])

    def batteryLevel(self):
        if self.factory.app:
            level = ord(self.buffer[5])
            self.factory.app.batteryLevel(level)

class SpykeeClientFactory(protocol.ClientFactory):

    protocol = SpykeeClient

    def __init__(self, username, password, app=None):
        self.username = username
        self.password = password
        self.app = app
        self.currentProtocol = None

class SpykeeServer(protocol.Protocol):

    authenticated = False

    def connectionMade(self):
        print "We have a connection to our Spykee"

    def dataReceived(self, data):
        commands = data.split('PK')
        for c in commands:
            self.commandReceived("PK%s" % c)

    def commandReceived(self, data):
        if data[0:4] == "PK\x0a\x00":
            rest_length = data[4]
            username_length = ord(data[5])
            username = data[6:(6+username_length)]
            password_length = ord(data[6+username_length])
            password = data[7+username_length:(7+username_length+password_length)]
            if username == self.factory.username and password == self.factory.password:
                print "Username and password correct"
                self.authenticated = True
                self.sendNames()
            else:
                print "Username and password incorrect"
        else:
            if self.authenticated:
                if data[0:7] == "PK\x0f\x00\x02\x01\x01":
                    print "Video activated"
                elif data[0:7] == "PK\x0f\x00\x02\x02\x01":
                    print "Audio activated"
                elif data[0:5] == "PK\x09\x00\x01":
                    print "Sound volume set to %d" % ord(data[5])
                elif data[0:6] == "PK\x10\x00\x01\x05":
                    print "Undocked"

    def sendNames(self):
        docked_str = chr(1)
        if self.factory.docked:
            docked_str = chr(0)
        str = "PK\x0b...%s%s%s%s%s%s%s%s%s" % (chr(len(self.factory.name[0])),
            self.factory.name[0], chr(len(self.factory.name[1])),
            self.factory.name[1], chr(len(self.factory.name[2])),
            self.factory.name[2], chr(len(self.factory.name[3])),
            self.factory.name[3], docked_str)
        self.transport.write(str)
