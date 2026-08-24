import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.company.tests.tools import create_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class TestProductionQualityTests(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        activate_modules('agronomics')

        create_company()

        Sequence = Model.get('ir.sequence')
        IrModel = Model.get('ir.model')
        QualityConfiguration = Model.get('quality.configuration')
        quality_sequence, = Sequence.find([
            ('name', '=', 'Quality Control'),
        ])
        lot_model, = IrModel.find([('name', '=', 'stock.lot')])
        quality_configuration = QualityConfiguration(1)
        configuration_line = quality_configuration.allowed_documents.new()
        configuration_line.quality_sequence = quality_sequence
        configuration_line.document = lot_model
        quality_configuration.save()

        QualityTemplate = Model.get('quality.template')
        quality_template = QualityTemplate(name='Fermentation Quality')
        QualityProof = Model.get('quality.proof')
        ph_proof, = QualityProof.find([('name', '=', 'PH')])
        QualityProofMethod = Model.get('quality.proof.method')
        ph_method, = QualityProofMethod.find([
            ('proof', '=', ph_proof.id),
        ])
        ProductUom = Model.get('product.uom')
        kg, = ProductUom.find([('name', '=', 'Kilogram')])
        quality_line = quality_template.quantitative_lines.new()
        quality_line.name = 'PH'
        quality_line.proof = ph_proof
        quality_line.method = ph_method
        quality_line.unit = kg
        quality_line.min_value = 3
        quality_line.max_value = 4
        quality_line.internal_description = 'PH result'
        quality_template.save()

        SequenceType = Model.get('ir.sequence.type')
        lot_sequence_type, = SequenceType.find([
            ('name', '=', 'Stock Lot'),
        ])
        lot_sequence = Sequence(
            name='Agronomics Lot',
            sequence_type=lot_sequence_type,
            company=None)
        lot_sequence.save()

        ProductTemplate = Model.get('product.template')
        input_template = ProductTemplate(
            name='Grapes',
            default_uom=kg,
            type='goods',
            producible=True,
            list_price=Decimal(0))
        input_template.save()
        input_product, = input_template.products
        input_product.cost_price = Decimal(0)
        input_product.save()

        output_template = ProductTemplate(
            name='Must',
            default_uom=kg,
            type='goods',
            producible=True,
            list_price=Decimal(0),
            lot_sequence=lot_sequence)
        output_template.save()
        output_product, = output_template.products
        output_product.cost_price = Decimal(0)
        output_product.save()

        ProductionTemplate = Model.get('production.template')
        production_template = ProductionTemplate(
            name='Pressing',
            uom=kg,
            quantity=100)
        production_template.inputs.append(input_template)
        production_template.outputs.append(output_template)
        production_template.save()

        Location = Model.get('stock.location')
        storage, = Location.find([('code', '=', 'STO')])

        Lot = Model.get('stock.lot')
        input_lot = Lot(product=input_product, number='INPUT-1')
        input_lot.save()

        Inventory = Model.get('stock.inventory')
        InventoryLine = Model.get('stock.inventory.line')
        inventory = Inventory()
        inventory.location = storage
        inventory_line = InventoryLine()
        inventory.lines.append(inventory_line)
        inventory_line.product = input_product
        inventory_line.lot = input_lot
        inventory_line.quantity = 10
        inventory.click('confirm')
        self.assertEqual(inventory.state, 'done')

        Production = Model.get('production')
        EnologyProduct = Model.get('production.enology.product')
        production = Production()
        production.production_template = production_template
        production.save()
        line = EnologyProduct()
        line.product = input_product
        line.production = production
        line.quantity = 10
        line.save()
        production.reload()
        production.click('wait')
        self.assertEqual(production.state, 'waiting')

        input_move, = production.inputs
        input_move.lot = input_lot
        input_move.save()

        output_distribution, = production.output_distribution
        output_distribution.location = storage
        output_distribution.final_quantity = 10
        output_distribution.save()

        production.click('assign_try')
        production.reload()
        self.assertEqual(production.state, 'assigned')
        production.click('run')
        production.click('do')
        production.reload()
        self.assertEqual(production.state, 'done')

        output_move, = production.outputs
        output_lot = output_move.lot
        self.assertIsNotNone(output_lot)

        QualityTest = Model.get('quality.test')
        quality_test = QualityTest(document=output_lot)
        quality_test.templates.append(quality_template)
        quality_test.save()
        QualityTest.apply_templates([quality_test.id], {})
        quality_test.reload()
        test_line, = quality_test.quantitative_lines
        test_line.value = Decimal('3.5')
        quality_test.save()
        QualityTest.confirmed([quality_test.id], {})

        output_lot.reload()
        self.assertEqual(output_lot.wine_ph, 3.5)

        production.reload()
        self.assertIn(quality_test.id,
            [test.id for test in production.quality_tests])
