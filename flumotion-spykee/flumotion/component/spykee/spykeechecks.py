# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Flumotion - a streaming media server
# Copyright (C) 2009 Zaheer Abbas Merali
# All rights reserved.

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.

# Headers in this file shall remain intact.

from twisted.internet import defer

from flumotion.common import messages
from flumotion.common.i18n import N_, gettexter
from flumotion.worker.checks import check

from flumotion.component.spykee import twistedprotocol

T_ = gettexter()


def checkSpykeeDevices(mid):
    """
    Fetch the available Spykee devices.

    Return a deferred firing a result.

    The result is either:
     - succesful, with a list of tuples of guid and device-name
     - failed

    @param mid: the id to set on the message.

    @rtype: L{twisted.internet.defer.Deferred} of
            L{flumotion.common.messages.Result}
    """
    result = messages.Result()

    def discovered(spykees):
        if not spykees:
            m = messages.Error(T_(
                N_("You poor thing, you need to buy yourself a Spykee robot.")))
            m.id = mid
            result.add(m)
            return defer.succeed(result)
        else:
            result.succeed(spykees)
            return defer.succeed(result)

    d = twistedprotocol.discover(5)
    d.addCallback(discovered)
    return d
