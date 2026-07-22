import json
import unittest

from trytond.pyson import PYSONDecoder, PYSONEncoder
from trytond.tests.test_tryton import drop_db
from trytond.modules.agronomics.tests.tools import setup
from trytond.transaction import Transaction


class TestProducibleProductLot(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        vars = setup()

        with Transaction().start(
                vars.config.database_name, vars.config.user,
                context=vars.config.context):
            Product = vars.config.pool.get('product.product')
            self.assertTrue(
                Product(vars.product.id).lot_is_required(None, None))

        location_types = {
            value for value, _label
            in vars.template_model.lot_required.selection}
        vars.template.reload()
        self.assertEqual(set(vars.template.lot_required), location_types)

        vars.template.producible = False
        vars.template.save()
        vars.template.lot_required = []
        vars.template.save()
        self.assertFalse(vars.template.lot_required)

        vars.template.producible = True
        vars.template.save()
        vars.template.reload()
        self.assertEqual(set(vars.template.lot_required), location_types)

        template_readonly = vars.template_model.lot_required.states['readonly']
        self.assertTrue(json.loads(
                json.dumps(template_readonly, cls=PYSONEncoder),
                cls=PYSONDecoder, context={'producible': True}))
        self.assertFalse(json.loads(
                json.dumps(template_readonly, cls=PYSONEncoder),
                cls=PYSONDecoder, context={'producible': False}))
