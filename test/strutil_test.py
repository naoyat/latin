#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from latin.strutil import *

class StringTestCase(unittest.TestCase):
    def test_ends_with(self):
        self.assertTrue(ends_with("bc", "abc"))
        self.assertTrue(ends_with("bc", "bc"))
        self.assertFalse(ends_with("bc", "c"))
        self.assertFalse(ends_with("bc", ""))
        self.assertTrue(ends_with("", "abc"))
        self.assertTrue(ends_with("", ""))

if __name__ == '__main__':
    unittest.main()
