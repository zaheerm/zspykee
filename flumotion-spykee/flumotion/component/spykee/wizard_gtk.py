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

import gettext
import os
import math

from zope.interface import implements

from flumotion.admin.assistant.interfaces import IProducerPlugin
from flumotion.admin.assistant.models import AudioProducer, VideoProducer, \
     AudioEncoder, VideoEncoder, VideoConverter
from flumotion.common import errors, messages
from flumotion.common.i18n import N_, gettexter
from flumotion.admin.gtk.basesteps import AudioProducerStep, VideoProducerStep

_ = gettext.gettext
T_ = gettexter()


class SpykeeProducer(AudioProducer, VideoProducer):
    componentType = 'spykee-producer'

    def __init__(self):
        super(SpykeeProducer, self).__init__()
        self.properties.port = 9000
        self.properties.username = 'admin'
        self.properties.password = 'admin'

    def getFeederName(self, component):
        if isinstance(component, AudioEncoder):
            return 'audio'
        elif isinstance(component, (VideoEncoder, VideoConverter)):
            return 'video'
        else:
            raise AssertionError

    def getFramerate(self):
        return (15, 1)

    def getWidth(self):
        return 320

    def getHeight(self):
        return 240


class _SpykeeCommon:
    icon = 'firewire.png'
    gladeFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'wizard.glade')
    componentType = 'spykee'

    def __init__(self):
        pass

    # WizardStep

    def workerChanged(self, worker):
        self.model.worker = worker
        self._populateDevices()

    # Private

    def _setSensitive(self, is_sensitive):
        self.vbox_controls.set_sensitive(is_sensitive)
        self.wizard.blockNext(not is_sensitive)

    def _populateDevices(self):
        self._setSensitive(False)
        msg = messages.Info(T_(N_('Checking for Spykee robots...')),
            mid='spykee-check')
        self.wizard.add_msg(msg)
        d = self.runInWorker('flumotion.component.spykee.spykeechecks',
                             'checkSpykeeDevices', mid='spykee-check')

        def spykeeCheckDone(devices):
            self.wizard.clear_msg('spykee-check')
            # need to convert to list of tuples
            spykees = list(("%s at %s" % (k, v), v) for k, v in devices.items())
            self.hostname.prefill(spykees)
            self._setSensitive(True)

        def trapRemoteFailure(failure):
            failure.trap(errors.RemoteRunFailure)

        def trapRemoteError(failure):
            failure.trap(errors.RemoteRunError)

        d.addCallback(spykeeCheckDone)
        d.addErrback(trapRemoteError)
        d.addErrback(trapRemoteFailure)

        return d

    # Callbacks


class SpykeeVideoStep(_SpykeeCommon, VideoProducerStep):
    name = 'Spykee'
    title = _('Spykee Video')
    docSection = 'help-configuration-assistant-producer-video-spykee'
    docAnchor = ''
    docVersion = 'local'

    def __init__(self, wizard, model):
        VideoProducerStep.__init__(self, wizard, model)
        _SpykeeCommon.__init__(self)

    def setup(self):
        self.hostname.data_type = str
        self.username.data_type = str
        self.password.data_type = str
        self.add_proxy(self.model.properties,
                       ['hostname', 'username', 'password'])


class SpykeeAudioStep(_SpykeeCommon, AudioProducerStep):
    name = 'Spykee audio'
    title = _('Spykee Audio')
    docSection = 'help-configuration-assistant-producer-audio-spykee'
    docAnchor = ''
    docVersion = 'local'

    def __init__(self, wizard, model):
        AudioProducerStep.__init__(self, wizard, model)
        _SpykeeCommon.__init__(self)

    # WizardStep

    def setup(self):
        self.username_hbox.hide()
        self.password_hbox.hide()

    def getNext(self):
        return None


class SpykeeWizardPlugin(object):
    implements(IProducerPlugin)

    def __init__(self, wizard):
        self.wizard = wizard

    def getProductionStep(self, type):
        if type == 'audio':
            return SpykeeAudioStep(self.wizard, SpykeeProducer())
        elif type == 'video':
            return SpykeeVideoStep(self.wizard, SpykeeProducer())
