#!/usr/bin/python

from twisted.internet import protocol, reactor

class SpykeeClient(protocol.Protocol):
    authenticated = False
    name = []
    docked = False

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
                    if nameLength + curpos - 1 < len(data):
                        self.name.append(data[curpos+1:nameLength+curpos+1])
                    else:
                        self.transport.loseConnection()
                        return
                    curpos = curpos + nameLength + 1
                    nameLength = ord(data[curpos])
                    if nameLength + curpos - 1 < len(data):
                        self.name.append(data[curpos+1:nameLength+curpos+1])
                    else:
                        self.transport.loseConnection()
                        return
                    curpos = curpos + nameLength + 1
                    self.docked = (ord(data[curpos]) == 0)
                    self.authenticated = True
                    self.setSoundVolume(85)
                    self.activateVideo()
                    self.activateSound()
                    print "I am authenticated to %r" % self.name
        else:
            if data[0:2] == "PK":
                if data[2] == chr(1):
                    print "Start of audio %d bytes" % (data[3] * 256 + data[4])
                elif data[2] == chr(2):
                    print "Start of video %d bytes" % (data[3] * 256 + data[4])
                elif data[2] == chr(3):
                    print "Battery: %d" % data[5]
                elif data[2] == chr(16):
                    if data[3] == chr(0) and data[4] == chr(1):
                        if data[5] == 2:
                            print "Docked"
                        elif data[5] == 1:
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

    def sendNames(self):
        str = "PK\x0b...%s%s%s%s%s%s%s" % (chr(len(self.factory.name[0])),
            self.factory.name[0], chr(len(self.factory.name[1])),
            self.factory.name[1], chr(len(self.factory.name[2])),
            self.factory.name[2], chr(0))
        self.transport.write(str)

if __name__ == "__main__":
    sf = protocol.Factory()
    sf.protocol = SpykeeServer
    sf.username = "user"
    sf.password = "test"
    sf.docked = True
    sf.name = ["myname", "is", "spykee"]
    reactor.listenTCP(9000, sf)
    cf = SpykeeClientFactory("user", "test")
    reactor.connectTCP("localhost", 9000, cf)
    reactor.run()
