import unittest

from statsdhandler.tests import test_statsdhandler


def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_statsdhandler.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
