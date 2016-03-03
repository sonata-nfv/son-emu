#!/usr/bin/env python

"""
Run all tests
 -v : verbose output
 -e : emulator test only (no API tests)
 -a : API tests only
"""

from unittest import defaultTestLoader, TextTestRunner, TestSuite
import os
import sys
from mininet.util import ensureRoot
from mininet.clean import cleanup
from mininet.log import setLogLevel


def runTests( testDir, verbosity=1, emuonly=False, apionly=False ):
    "discover and run all tests in testDir"
    # ensure inport paths work
    sys.path.append("%s/.." % testDir)
    # ensure root and cleanup before starting tests
    ensureRoot()
    cleanup()
    # discover all tests in testDir
    testSuite = defaultTestLoader.discover( testDir )
    if emuonly:
        testSuiteFiltered = [s for s in testSuite if "Emulator" in str(s)]
        testSuite = TestSuite()
        testSuite.addTests(testSuiteFiltered)
    if apionly:
        testSuiteFiltered = [s for s in testSuite if "Api" in str(s)]
        testSuite = TestSuite()
        testSuite.addTests(testSuiteFiltered)

    # run tests
    TextTestRunner( verbosity=verbosity ).run( testSuite )


def main(thisdir):
    setLogLevel( 'warning' )
    # get the directory containing example tests
    vlevel = 2 if '-v' in sys.argv else 1
    emuonly = ('-e' in sys.argv)
    apionly = ('-a' in sys.argv)
    runTests(
        testDir=thisdir, verbosity=vlevel, emuonly=emuonly, apionly=apionly)


if __name__ == '__main__':
    thisdir = os.path.dirname( os.path.realpath( __file__ ) )
    main(thisdir)
