#!/usr/bin/env python
# -*- coding: utf-8 -*-

import strutil
import unittest

class StringTestCase(unittest.TestCase):
    def test_ends_with(self):
        self.assertTrue(strutil.ends_with("bc", "abc"))
        self.assertTrue(strutil.ends_with("bc", "bc"))
        self.assertFalse(strutil.ends_with("bc", "c"))
        self.assertFalse(strutil.ends_with("bc", ""))
        self.assertTrue(strutil.ends_with("", "abc"))
        self.assertTrue(strutil.ends_with("", ""))

if __name__ == '__main__':
    unittest.main()
