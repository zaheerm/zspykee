# -*- Mode: Python; -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Flumotion Spykee Component
# Copyright (C) 2009 Zaheer Abbas Merali. All rights reserved.

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.

# Headers in this file shall remain intact.

import gettext
import os

from flumotion.common.i18n import gettexter
from flumotion.component.base.admin_gtk import BaseAdminGtk
from flumotion.component.base.baseadminnode import BaseAdminGtkNode

_ = gettext.gettext

class MotorAdminGtkNode(BaseAdminGtkNode):
    gladeFile = os.path.join('flumotion', 'component', 'spykee',
        'spykee.glade')
    gettextDomain = "flumotion-template"

    _buttons = {}
    uiStateHandlers = None

    def haveWidgetTree(self):
        self._buttons["forward"] = self.getWidget('forward_button')
        self._buttons["reverse"] = self.getWidget('reverse_button')
        self._buttons["left"] = self.getWidget('left_button')
        self._buttons["right"] = self.getWidget('right_button')
        self._dock = self.getWidget('dock_button')

        for b in self._buttons:
            self._buttons[b].connect("clicked", self.button_clicked)

        # necessary to set self.widget
        self.widget = self.getWidget('table1')

    def button_clicked(self, button):
        name = button.get_name()
        if name == "forward_button":
            self.callRemote("forward", 50, 0.2)
        elif name == "reverse_button":
            self.callRemote("reverse", 50, 0.2)
        elif name == "left_button":
            self.callRemote("left")
        elif name == "right_button":
            self.callRemote("right")
        elif name == "dock_button":
            self.callRemote("dock")

    def stateSet(self, state, key, value):
        handler = self.uiStateHandlers.get(key, None)
        if handler:
            handler(value)

    def setUIState(self, state):
        BaseAdminGtkNode.setUIState(self, state)
        if not self.uiStateHandlers:
            self.uiStateHandlers = {'battery-level': self.batterySet}
        for k, handler in self.uiStateHandlers.items():
            handler(state.get(k))

    def batterySet(self, value):
        self.debug("battery level changed to %r" % value)

class SpykeeAdminGtk(BaseAdminGtk):
    gettext_domain = 'flumotion-spykee'

    def setup(self):
        self.nodes['Motor'] = MotorAdminGtkNode(self.state,
                                                  self.admin,
                                                  title=_('Movement'))
        return BaseAdminGtk.setup(self)

GUIClass = SpykeeAdminGtk
