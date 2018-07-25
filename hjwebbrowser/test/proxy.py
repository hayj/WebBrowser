# coding: utf-8
# pew in webbrowser-venv python ./test/proxy.py

import os
import sys
sys.path.append('../')

import unittest
import doctest
from hjwebbrowser import proxy
from hjwebbrowser.proxy import *

# The level allow the unit test execution to choose only the top level test
mini = 0
maxi = 4
assert mini <= maxi

print("==============\nStarting unit tests...")

if mini <= 0 <= maxi:
    class DocTest(unittest.TestCase):
        def testDoctests(self):
            """Run doctests"""
            doctest.testmod(proxy)

if mini <= 1 <= maxi:
    class Test1(unittest.TestCase):
        def testToScheme(self):
            p1 = Proxy("107.150.77.161")
            self.assertTrue(p1.toScheme() == "http://107.150.77.161:80")
            p2 = Proxy("107.150.77.161:8:a:b:socks")
            self.assertTrue(p2.toScheme() == "socks://a:b@107.150.77.161:8")

            p3 = Proxy(p2)
            self.assertTrue(p3.toScheme() == p2.toScheme())
            self.assertTrue(p1.toScheme() != p2.toScheme())

        def testStrRepr(self):
            p1 = Proxy("107.150.77.161:80")
            self.assertTrue(str(p1) == repr(p1))
            p2 = Proxy("107.150.77.161:8:a:b:socks")
            self.assertTrue(str(p2) != repr(p2))
            p3 = Proxy("107.150.77.161::::::")
            self.assertTrue(repr(p1) != repr(p3))

        def testAttr(self):
            p1 = Proxy("107.150.77.161:80")
            p2 = Proxy("107.150.77.161:8:a:b:socks")
            p3 = Proxy("107.150.77.1::::::")

            self.assertTrue(p1.ip == p2.ip)
            self.assertTrue(p1["ip"] == p2["ip"])
            self.assertTrue(p1.ip != p3.ip)
            self.assertTrue(p1.port == p3.port)
            self.assertTrue(p1.user is None)
            self.assertTrue("user" not in p1)
            self.assertTrue("user" in p2)
            self.assertTrue(p1.type == "http")
            self.assertTrue(p2.user == "a")

            p2.ip = "e"
            self.assertTrue(p1.ip != p2.ip)

        def testEquality(self):
            p1 = Proxy("107.150.77.161:80:a:b")
            p2 = Proxy("107.150.77.161:80:a:b:socks")
            self.assertTrue(p1 != p2)
            p3 = Proxy(p2)
            self.assertTrue(p3 == p2)
            p4 = Proxy("107.150.77.161:80:a:b")
            self.assertTrue(p4 != p2)
            self.assertTrue(p4 == p1)
            p5 = Proxy("107.150.77.161:80:a:c")
            self.assertTrue(p4 == p5)
            p6 = Proxy("107.150.77.161:80:a:d", equalityExclude=None)
            self.assertTrue(p6 != p5)
            p8 = Proxy("106.150.77.161:80:a:b")
            self.assertTrue(p8 != p1)

        def testWellFormated(self):
            ok = True
            try:
                p1 = Proxy("107.150.77.161:80:a:b::::")
            except:
                ok = False
            self.assertTrue(ok)

        def testMalformated(self):
            ok = False
            try:
                p1 = Proxy(":::::")
            except:
                ok = True
            self.assertTrue(ok)



if __name__ == '__main__':
    unittest.main() # Or execute as Python unit-test in eclipse


print("Unit tests done.\n==============")