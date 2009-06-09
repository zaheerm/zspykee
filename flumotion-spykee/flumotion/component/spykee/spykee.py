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

from flumotion.component import feedcomponent

from flumotion.component.sample.common import getMethod


class SampleMedium(feedcomponent.FeedComponentMedium):
    def remote_setVideoFlip(self, method):
        self.comp.set_element_property('videoflip', 'method', method)
        
# this is a sample converter component for video that will use videoflip
# FIXME: check for videoflip plugin on worker
class Sample(feedcomponent.ParseLaunchComponent):
    componentMediumClass = SampleMedium

    def init(self):
        self.uiState.addKey('method', 0)

    def get_pipeline_string(self, properties):
        return "ffmpegcolorspace ! videoflip name=videoflip ! ffmpegcolorspace"

    def configure_pipeline(self, pipeline, properties):
        def notify_method(obj, pspec):
            self.uiState.set('method', int(obj.get_property('method')))

        hor = properties.get('horizontal', False)
        ver = properties.get('vertical', False)
        method = getMethod(hor, ver)
        
        source = self.get_element('videoflip')
        source.connect('notify::method', notify_method)
        source.set_property('method', method)
