# This file is part agronomics module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest


from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import suite as test_suite


class AgronomicsTestCase(ModuleTestCase):
    'Test Agronomics module'
    module = 'agronomics'


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            AgronomicsTestCase))
    return suite
