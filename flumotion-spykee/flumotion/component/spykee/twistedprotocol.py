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
from socket import SOL_SOCKET, SO_BROADCAST

from twisted.internet import protocol, reactor, task, defer

class SpykeeClient(protocol.Protocol):
    authenticated = False
    name = []
    docked = False
    buffer = ""
    settings = {}
    wifi = []
    log = ""

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
                    if self.factory.app:
                        self.factory.app.isDocked(self.docked)
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
        elif self.buffer[2] == chr(16):
            if self.buffer[3] == chr(0) and self.buffer[4] == chr(1):
                if self.buffer[5] == 2:
                    print "Docked"
                elif self.buffer[5] == 1:
                    print "Undocked"
        elif self.buffer[2] == chr(0x0d):
            self.settingsReceived()
        elif self.buffer[2] == chr(0x11):
            self.logReceived()
        elif self.buffer[2] == chr(0x0e):
            self.visibleWifiReceived()
        else:
            print "Unknown command %d" % ord(self.buffer[2])

    def sendCommand(self, command, data):
        lenstr = ""
        if len(data) <= 255:
            lenstr = "\x00%s" % chr(len(data))
        else:
            multiple = int(len(data) / 256)
            lenstr = "%s%s" % (multiple, len(data) % 256)
        str = "PK%s%s%s" % (chr(command), lenstr, data)
        self.transport.write(str)

    def getCurrentCommandLength(self):
        if len(self.buffer) > 5:
            length = ord(self.buffer[3]) * 256 + ord(self.buffer[4])
            return length
        else:
            return 0

    def activateVideo(self):
        self.sendCommand(15, "\x01\x01")

    def activateSound(self):
        self.sendCommand(15, "\x02\x01")

    def setSoundVolume(self, volume):
        if volume >= 0 and volume < 256:
            self.sendCommand(9, chr(volume))

    def undock(self):
        self.sendCommand(16, "\x05")
        self.docked = False

    def dock(self):
        self.sendCommand(16, "\x06")
        self.docked = True

    def cancelDock(self):
        self.sendCommand(16, "\x07")
        self.docked = False

    def playSound(self, soundNumber):
        if soundNumber >= 0 and soundNumber < 256:
            self.sendCommand(7, chr(soundNumber))

    def motorStop(self):
        self.sendCommand(5, "\x00\x00")

    def motorForward(self, motorSpeed, time=0.2):
        if motorSpeed < 128 and motorSpeed >= 0:
            self.motorCommand(motorSpeed, motorSpeed, time)

    def motorBack(self, motorSpeed, time=0.2):
        if motorSpeed < 128 and motorSpeed >= 0:
            self.motorCommand(-motorSpeed, -motorSpeed, time)

    def motorLeft(self, time=0.2):
        self.motorCommand(0x96, 0x64, time)

    def motorRight(self, time=0.2):
        self.motorCommand(0x64, 0x96, time)

    def motorCommand(self, leftMotor, rightMotor, time=0.2):
        self.sendCommand(5, "%s%s" % (chr(leftMotor), chr(rightMotor)))
        reactor.callLater(time, self.motorStop)

    def light(self, led, on=True):
        onstr = "\x00"
        if on:
            onstr="\x01"
        self.sendCommand(4, "%s%s" % (chr(led), onstr))

    def audioSample(self):
        if self.factory.app:
            length = self.getCurrentCommandLength()
            self.factory.app.audioSample(self.buffer[5:5+length])

    def videoFrame(self):
        if self.factory.app:
            length = self.getCurrentCommandLength()
            self.factory.app.videoFrame(self.buffer[5:5+length])

    def batteryLevel(self):
        if self.factory.app:
            level = ord(self.buffer[5])
            self.factory.app.batteryLevel(level)
        else:
            print "Battery level: %d" % ord(self.buffer[5])

    def settingsReceived(self):
        length = self.getCurrentCommandLength()
        settingsStr = self.buffer[5:5+length]
        import string
        keyvalues = string.split(settingsStr, '&')
        for kv in keyvalues:
            key, value = string.split(kv, '=')
            self.settings[key] = value

    def logReceived(self):
        length = self.getCurrentCommandLength()
        self.log = self.buffer[5:5+length]
        print self.log

    def visibleWifiReceived(self):
        length = self.getCurrentCommandLength()
        wifi = self.buffer[5:5+length]
        import string
        networks = string.split(wifi, ';')
        for n in networks:
            essid, encryption, strength = string.split(n, ":")
            self.wifi.append((essid, encryption, int(strength)))
        print repr(self.wifi)

    def audioToSpykeeOn(self):
        self.sendCommand(15, "\x03\x01")

    def audioToSpykeeOff(self):
        self.sendCommand(15, "\x03\x00")

    def audioToSpykeeSample(self, sample):
        self.sendCommand(1, sample)

    def getSettings(self):
        self.sendCommand(0xd, "")

    def getLog(self):
        self.sendCommand(0x11, "")

    def getVisibleWifi(self):
        self.sendCommand(0xe, "")

    def applySettings(self):
        settingsStr = ""
        self.sendCommand(0xd, settingsStr)

class SpykeeClientFactory(protocol.ClientFactory):

    protocol = SpykeeClient

    def __init__(self, username, password, app=None):
        self.username = username
        self.password = password
        self.app = app
        self.currentProtocol = None

    def clientConnectionLost(self, connector, reason):
        if self.app:
            self.app.connectionLost(reason)
        else:
            print "Connection lost because of %r" % (reason,)
            reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        if self.app:
            self.app.connectionFailed(reason)
        else:
            print "Connection failed because of %r" % (reason,)
            reactor.stop()

class SpykeeDiscoveryProtocol(protocol.DatagramProtocol):

    port = 9000
    bcastaddresses = []
    spykees = {}

    def startProtocol(self):
        import netifaces
        self.interfaces = netifaces.interfaces()
        for i in self.interfaces:
            addresses = netifaces.ifaddresses(i)
            for item in addresses:
                a = addresses[item]
                for eacha in a:
                    if "broadcast" in eacha:
                        # crude way to remove ipv6 bcast addresses
                        import string
                        if string.upper(eacha["broadcast"]) == \
                           eacha["broadcast"]:
                            self.bcastaddresses.append(eacha["broadcast"])
        self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
        self.call = task.LoopingCall(self.discover)
        self.dcall = self.call.start(1.0)

    def stopProtocol(self):
        self.call.stop()

    def discover(self):
        for i in self.bcastaddresses:
            self.transport.write("DSCV\01", (i, self.port))

    def datagramReceived(self, data, addr):
        if len(data) > 5: # length 5 means we receive our own bcast
            if data[0:4] == "DSCV":
                import string
                spykee_id = string.split(data[6:],"=")
                if spykee_id[0] == "uid":
                    if spykee_id[1] not in self.spykees:
                        self.spykees[spykee_id[1]] = addr[0]

def discover(wait=10):
    returnd = defer.Deferred()
    discover_protocol = SpykeeDiscoveryProtocol()
    listener = reactor.listenUDP(9000, discover_protocol)
    def stopDiscovery():
        listener.stopListening()
        returnd.callback(discover_protocol.spykees)
    reactor.callLater(wait, stopDiscovery)
    return returnd

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

if __name__ == "__main__":
    def discovered(spykees):
        if not spykees:
            print "You poor thing, you need to buy yourself a Spykee at http://www.redstore.com/MECIMG001"
        for name in spykees:
            print "Spykee %s discovered at IP %s" % (name, spykees[name])
        reactor.stop()
    d = discover(2)
    d.addCallback(discovered)
    reactor.run()
    class a:
        cf = None
        def isDocked(self, docked):
            print "docked:%d" % docked
            self.cf.currentProtocol.getSettings()
            self.cf.currentProtocol.getLog()
            self.cf.currentProtocol.getVisibleWifi()
            self.cf.currentProtocol.activateVideo()
            self.cf.currentProtocol.activateSound()

        def videoFrame(self, frame):
            print "video frame"

        def audioSample(self, sample):
            print "audio sample"

        def connectionLost(self, reason):
            print "connection lost"

        def connectionFailed(self, reason):
            print "connection failed"

        def batteryLevel(self, level):
            print "battery level: %d" % level
    ao = a()
    cf = SpykeeClientFactory("admin", "admin", ao)
    ao.cf = cf
    reactor.connectTCP("172.17.6.1", 9000, cf)
    reactor.run()

