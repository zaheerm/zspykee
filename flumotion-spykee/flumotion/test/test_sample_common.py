# -*- Mode: Python; test-case-name: flumotion.test.test_sample_common -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Flumotion - a streaming media server
# Copyright (C) 2004,2005 Fluendo, S.L. (www.fluendo.com). All rights reserved.
# flumotion-ground-control - Advanced Administration

# Licensees having purchased or holding a valid Flumotion Advanced
# Streaming Server license may use this file in accordance with the
# Flumotion Advanced Streaming Server Commercial License Agreement.
# See "LICENSE.Flumotion" in the source distribution for more information.

# Headers in this file shall remain intact.

import common

from twisted.trial import unittest

from flumotion.component.sample import common

class SampleTest(unittest.TestCase):
    def testGetMethod(self):
        self.assertEquals(common.getMethod(False, False), 0)
        self.assertRaises(IndexError, common.getMethod, 'true', 'false')

    def testGetBooleans(self):
        self.assertEquals(common.getBooleans(0), (False, False))
