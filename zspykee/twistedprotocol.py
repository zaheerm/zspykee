#!/usr/bin/python

import gobject
gobject.threads_init()
import gst

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
                    print "I am authenticated to %r" % self.name
                    print "Docked: %d" % self.docked
                    #if self.docked:
                    #    self.undock()
                    if not self.docked:
                        self.initGst()
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
            print "Battery: %d" % ord(self.buffer[5])
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

    def audioSample(self):
        print "Audio sample received"

    def videoFrame(self):
        print "Video frame received"
        if self.appsrc:
            length = ord(self.buffer[3]) * 256 + ord(self.buffer[4])
            print "length: %d whole buffer length: %d" % (length, len(self.buffer))
            buf = gst.Buffer(self.buffer[5:5+length])
            self.appsrc.emit("push-buffer", buf)

    def initGst(self):
        self.pipeline = gst.parse_launch("appsrc do-timestamp=true name=src ! jpegdec ! xvimagesink sync=false")
        self.appsrc = self.pipeline.get_by_name("src")
        self.appsrc.props.caps = gst.caps_from_string("image/jpeg, width=320, height=240")
        self.pipeline.set_state(gst.STATE_PLAYING)

class SpykeeClientFactory(protocol.ClientFactory):

    protocol = SpykeeClient

    def __init__(self, username, password):
        self.username = username
        self.password = password

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
    sf = protocol.Factory()
    sf.protocol = SpykeeServer
    sf.username = "user"
    sf.password = "test"
    sf.docked = True
    sf.name = ["myname", "is", "spykee", "1.2.3"]
    reactor.listenTCP(9000, sf)
    cf = SpykeeClientFactory("user", "test")
    reactor.connectTCP("localhost", 9000, cf)
    reactor.run()
