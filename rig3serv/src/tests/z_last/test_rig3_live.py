#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Rig3 site generation

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase
from rig3 import Rig3

_DEST_DIR = "live_dest"  # in testdat dir

#------------------------
class Rig3LiveTest(RigTestCase):

    def setUp(self):
        self._pwd = os.getcwd()
        self._testdata = self.getTestDataPath()
        # all paths are relative to the testdata dir
        os.chdir(self._testdata)
        # cleanup output and make sure it's not there anymore
        self.RemoveDir(_DEST_DIR)
        self.assertFalse(os.path.exists(_DEST_DIR))
        os.mkdir(_DEST_DIR)
        self.assertTrue(os.path.exists(_DEST_DIR))
        self.m = Rig3()

    def tearDown(self):
        os.chdir(self._pwd)
        self.m = None

    def testLive(self):
        t = self._testdata
        d = os.path.join(t, _DEST_DIR)
        rc = os.path.join(t, "z_last_rig3_live.rc")
        args = [ "rig3", "-c", rc ]
        self.m.ParseArgs(args)
        self.m.Run()
        self.m.Close()
        
        self.assertTrue(os.path.exists(os.path.join(d, "items", "2007-10-07_Folder-1-index_izu")))
        self.assertTrue(os.path.exists(os.path.join(d, "index.html")))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
