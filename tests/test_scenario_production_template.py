import datetime
import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.company.tests.tools import create_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Activate modules
        activate_modules('agronomics')

        # Create company
        _ = create_company()

        # Create product
        ProductUom = Model.get('product.uom')
        liter, = ProductUom.find([('name', '=', 'Liter')])
        kg, = ProductUom.find([('name', '=', 'Kilogram')])
        gram, = ProductUom.find([('name', '=', 'Gram')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        Sequence = Model.get('ir.sequence')
        SequenceType = Model.get('ir.sequence.type')
        Taxon = Model.get('product.taxon')
        DO = Model.get('agronomics.denomination_of_origin')
        Ecological = Model.get('agronomics.ecological')

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

        # Create Denomination Of Origin
        catalunya = DO()
        catalunya.name = 'Catalunya'
        catalunya.save()
        barcelona = DO()
        barcelona.name = 'Barcelona'
        barcelona.save()

        # Create Taxon
        macabeu = Taxon()
        macabeu.rank = 'variety'
        macabeu.name = 'Macabeu'
        macabeu.save()
        parellada = Taxon()
        parellada.rank = 'variety'
        parellada.name = 'Parellada'
        parellada.save()

        # Create Ecological
        ecological = Ecological()
        ecological.name = 'Ecological'
        ecological.save()
        Certification = Model.get('agronomics.certification')
        certification = Certification(number='CERT-1')
        certification.save()

        # # Raim Blanc
        template = ProductTemplate()
        template.name = 'Raim Blanc'
        template.default_uom = kg
        template.type = 'goods'
        template.producible = True
        template.list_price = Decimal(0)
        product, = template.products
        product.cost_price = Decimal(10)
        template.save()
        product, = template.products
        productA = Product()
        productA.code = "A"
        productA.template = template
        productA.save()
        productB = Product()
        productB.code = "B"
        productB.template = template
        productB.save()
        productC = Product()
        productC.code = "C"
        productC.template = template
        productC.save()

        # # Sulforos
        template = ProductTemplate()
        template.name = 'Sulforos'
        template.default_uom = kg
        template.type = 'goods'
        template.producible = True
        template.list_price = Decimal(0)
        product2, = template.products
        product2.cost_price = Decimal(10)
        template.save()
        product2, = template.products

        # # Encims
        template = ProductTemplate()
        template.name = 'Encims'
        template.default_uom = kg
        template.type = 'goods'
        template.producible = True
        template.list_price = Decimal(0)
        product3, = template.products
        product3.cost_price = Decimal(10)
        template.save()
        product3, = template.products

        # # Carbo actiu
        template = ProductTemplate()
        template.name = 'Carbo actiu'
        template.default_uom = kg
        template.type = 'goods'
        template.producible = True
        template.list_price = Decimal(0)
        product4, = template.products
        product4.cost_price = Decimal(10)
        template.save()
        product4, = template.products

        # # Most flor
        mostflor = ProductTemplate()
        mostflor.name = 'Most Flor'
        mostflor.default_uom = liter
        mostflor.type = 'goods'
        mostflor.producible = True
        mostflor.list_price = Decimal(0)
        mostflor.save()
        product5, = mostflor.products
        product5.cost_price = Decimal(0)
        product5.save()
        product5 = Product(product5.id)

        # # Most Primeres
        mostprimeres = ProductTemplate()
        mostprimeres.name = 'Most Primeres'
        mostprimeres.default_uom = liter
        mostprimeres.type = 'goods'
        mostprimeres.producible = True
        mostprimeres.list_price = Decimal(0)
        mostprimeres.save()
        product6, = mostprimeres.products
        product6.cost_price = Decimal(0)
        product6.save()
        product5 = Product(product5.id)
        product6 = Product(product6.id)
        product6 = Product(product6.id)

        lot_sequence_type, = SequenceType.find([
            ('name', '=', 'Stock Lot'),
        ])
        lot_sequence = Sequence()
        lot_sequence.name = 'Lot'
        lot_sequence.sequence_type = lot_sequence_type
        lot_sequence.company = None
        lot_sequence.save()
        mostflor.lot_sequence = lot_sequence
        mostflor.save()
        mostprimeres.lot_sequence = lot_sequence
        mostprimeres.save()
        for product in [productA, product2, product3, product4]:
            product.template.lot_sequence = lot_sequence
            product.template.save()

        # Create Production Template
        ProductionTemplate = Model.get('production.template')
        ProductionTemplateLine = Model.get("production.template.line")
        production_template = ProductionTemplate()
        production_template.name = 'Premsat i desfangat de raim blanc'
        production_template.uom = kg
        production_template.quantity = 10000
        production_template.pass_feature = True
        production_template.inputs.append(productA.template)
        production_template.outputs.extend([mostflor, mostprimeres])
        production_template.pass_quality = True
        production_template.pass_quality_sample = True
        production_template.pass_certification = True
        line = ProductionTemplateLine()
        line.product = product2
        line.quantity = 100
        production_template.enology_products.append(line)
        line = ProductionTemplateLine()
        line.product = product3
        line.quantity = 50
        production_template.enology_products.append(line)
        line = ProductionTemplateLine()
        line.product = product4
        line.quantity = 150
        production_template.enology_products.append(line)
        production_template.save()

        CostDistributionTemplate = Model.get(
            'production.cost_price.distribution.template')
        cost_distribution_template = CostDistributionTemplate(
            name='Output Cost Distribution',
            production_template=production_template)
        cost_distribution = (
            cost_distribution_template.cost_distributions.new())
        cost_distribution.product = product5
        cost_distribution.percentatge = Decimal('0.4')
        cost_distribution = (
            cost_distribution_template.cost_distributions.new())
        cost_distribution.product = product6
        cost_distribution.percentatge = Decimal('0.6')
        cost_distribution_template.save()
        production_template.cost_distribution_template = (
            cost_distribution_template)
        production_template.save()

        # Create an Inventory
        Inventory = Model.get('stock.inventory')
        InventoryLine = Model.get('stock.inventory.line')
        Location = Model.get('stock.location')
        storage, = Location.find([
            ('code', '=', 'STO'),
        ])
        Lot = Model.get('stock.lot')
        inventory_lots = {}
        for input_product in [
                productA, productB, productC, product2, product3, product4]:
            lot = Lot(
                product=input_product,
                number=f'INPUT-{input_product.id}')
            lot.save()
            inventory_lots[input_product.id] = lot
        inventory = Inventory()
        inventory.location = storage
        inventory_line1 = InventoryLine()
        inventory.lines.append(inventory_line1)
        inventory_line1.product = productA
        inventory_line1.lot = inventory_lots[productA.id]
        inventory_line1.quantity = 5000
        inventory_line2 = InventoryLine()
        inventory.lines.append(inventory_line2)
        inventory_line2.product = productB
        inventory_line2.lot = inventory_lots[productB.id]
        inventory_line2.quantity = 10000
        inventory_line3 = InventoryLine()
        inventory.lines.append(inventory_line3)
        inventory_line3.product = productC
        inventory_line3.lot = inventory_lots[productC.id]
        inventory_line3.quantity = 3000
        inventory_line3 = InventoryLine()
        inventory.lines.append(inventory_line3)
        inventory_line3.product = product2
        inventory_line3.lot = inventory_lots[product2.id]
        inventory_line3.quantity = 1000
        inventory_line3 = InventoryLine()
        inventory.lines.append(inventory_line3)
        inventory_line3.product = product3
        inventory_line3.lot = inventory_lots[product3.id]
        inventory_line3.quantity = 1000
        inventory_line3 = InventoryLine()
        inventory.lines.append(inventory_line3)
        inventory_line3.product = product4
        inventory_line3.lot = inventory_lots[product4.id]
        inventory_line3.quantity = 1000
        inventory.click('confirm')
        self.assertEqual(inventory.state, 'done')

        # Create Production
        Production = Model.get('production')
        EnologyProduct = Model.get('production.enology.product')
        production = Production()
        production.production_template = production_template
        production.save()
        line = EnologyProduct()
        line.product = productA
        line.production = production
        line.quantity = 5000
        line.save()
        line = EnologyProduct()
        line.product = productB
        line.quantity = 10000
        line.production = production
        line.save()
        line = EnologyProduct()
        line.product = productC
        line.uom = gram
        line.quantity = 3000000
        line.production = production
        line.save()
        production.reload()
        production.click('wait')
        self.assertEqual(production.state, 'waiting')
        sample_lot = None
        for move in production.inputs:
            lot = inventory_lots[move.product.id]
            if move.product in [productA, productB, productC]:
                lot.denominations_of_origin.append(DO(catalunya.id))
                lot_variety = lot.varieties.new()
                lot_variety.variety = (
                    parellada if move.product == productC else macabeu)
                lot_variety.percent = 100.0
            lot.save()
            if move.product == productA:
                sample_lot = lot
                sample_lot.certification = certification
                sample_lot.save()
            move.lot = lot
            move.save()
        QualitySample = Model.get('quality.sample')
        quality_sample = QualitySample(reference='Input grape sample')
        quality_sample.save()
        sample_lot.quality_samples.append(quality_sample)
        sample_lot.save()
        QualityTest = Model.get('quality.test')
        input_quality_test = QualityTest(document=sample_lot)
        input_quality_test.save()
        QualityTest.confirmed([input_quality_test.id], {})
        QualityTest.manager_validate([input_quality_test.id], {})
        self.assertEqual(len(production.inputs), 6)
        input, = [i for i in production.inputs if i.product == product2]
        self.assertEqual(input.quantity, 180.0)
        input, = [i for i in production.inputs if i.product == product3]
        self.assertEqual(input.quantity, 90.0)
        input, = [i for i in production.inputs if i.product == product4]
        self.assertEqual(input.quantity, 270.0)
        input, = [i for i in production.inputs if i.product == productC]
        self.assertEqual(input.unit, gram)
        self.assertEqual(input.quantity, 3000000)
        (o1, o2) = production.output_distribution
        o1.location = storage
        o1.final_quantity = 5000
        o1.save()
        o2.location = storage
        o2.final_quantity = 10000
        o2.save()
        production.reload()
        self.assertEqual(len(production.output_distribution), 2)
        self.assertEqual(
            [x.name for x in production.allowed_enology_products],
            ['Raim Blanc', 'Raim Blanc', 'Raim Blanc', 'Raim Blanc'])
        self.assertEqual(
            [x.name for x in production.production_template.inputs],
            ['Raim Blanc'])
        self.assertEqual(
            {line.product.id: line.percentatge
                for line in production.cost_distributions},
            {product5.id: Decimal('0.4'), product6.id: Decimal('0.6')})
        input_lots = {move.product.id: move.lot.id
            for move in production.inputs}
        input_move_ids = {move.id for move in production.inputs}
        production.click('assign_try')
        production.click('wait')
        production.reload()
        self.assertEqual(production.state, 'waiting')
        self.assertTrue(input_move_ids.isdisjoint(
                move.id for move in production.inputs))
        for move in production.inputs:
            move.lot = Lot(input_lots[move.product.id])
            move.save()
        final_quantities = {
            product5.id: 5000,
            product6.id: 10000,
            }
        for distribution in production.output_distribution:
            distribution.location = storage
            distribution.final_quantity = final_quantities[
                distribution.product.id]
            distribution.save()
        production.click('assign_try')
        production.click('run')
        product_ids = [product.id for product in Product.find([])]
        production.click('do')
        production.reload()
        self.assertEqual(len(production.outputs), 2)
        self.assertEqual(
            {move.product.id for move in production.outputs},
            {product5.id, product6.id})
        self.assertEqual(
            [product.id for product in Product.find([])], product_ids)
        self.assertTrue(all(move.lot for move in production.outputs))
        self.assertEqual(
            len({move.lot.id for move in production.outputs}), 2)
        for output in production.outputs:
            self.assertEqual(output.product.quality_samples, [])
            self.assertEqual(output.lot.certification, certification)
            self.assertEqual(
                [sample.id for sample in output.lot.quality_samples],
                [quality_sample.id])
            quality_tests = QualityTest.find([
                ('document.id', '=', output.lot.id, 'stock.lot'),
            ])
            self.assertEqual(len(quality_tests), 1)
            self.assertEqual(quality_tests[0].state, 'successful')
            self.assertEqual(
                sorted((variety.variety.name, variety.percent)
                    for variety in output.lot.varieties),
                [('Macabeu', 83.3334), ('Parellada', 16.6667)])
            self.assertEqual(
                [do.name for do in output.lot.denominations_of_origin],
                ['Catalunya'])

        aging_input, = [move for move in production.outputs
            if move.product == product5]
        today = datetime.date.today()
        WineAgingHistory = Model.get('wine.wine_aging.history')
        input_history_id, = WineAgingHistory.create([{
            'production': production.id,
            'location': storage.id,
            'lot': aging_input.lot.id,
            'date_start': today - datetime.timedelta(days=10),
        }], {})
        input_history = WineAgingHistory(input_history_id)

        aging_template = ProductionTemplate(
            name='Age Most Flor',
            uom=liter,
            quantity=1,
            transfer_wine_aging=True)
        aging_template.inputs.append(product5.template)
        aging_template.outputs.append(product6.template)
        aging_template_line = aging_template.enology_products.new()
        aging_template_line.product = product5
        aging_template_line.quantity = 100
        aging_template.save()
        aging_production = Production(production_template=aging_template)
        aging_production.save()
        aging_production.reload()
        aging_production.click('wait')
        aging_input_move, = aging_production.inputs
        self.assertEqual(aging_input_move.product, product5)
        self.assertEqual(aging_input_move.quantity, 100)
        aging_input_move.lot = aging_input.lot
        aging_input_move.save()
        aging_distribution, = aging_production.output_distribution
        aging_distribution.location = storage
        aging_distribution.final_quantity = (
            aging_distribution.initial_quantity + 100)
        aging_distribution.save()
        aging_production.reload()
        aging_input_move, = aging_production.inputs
        aging_input_move.lot = None
        aging_input_move.save()
        aging_production.click('assign_try')
        self.assertEqual(aging_production.state, 'assigned')
        aging_production.click('wait')
        aging_production.reload()
        aging_input_move, = aging_production.inputs
        aging_input_move.lot = aging_input.lot
        aging_input_move.save()
        aging_distribution, = aging_production.output_distribution
        aging_distribution.location = storage
        aging_distribution.final_quantity = (
            aging_distribution.initial_quantity + 100)
        aging_distribution.save()
        aging_production.click('assign_try')
        aging_production.click('run')
        aging_production.click('do')
        aging_production.reload()

        input_history.reload()
        self.assertEqual(input_history.date_end, today)
        aging_output, = aging_production.outputs
        output_histories = WineAgingHistory.find([
            ('lot', '=', aging_output.lot.id),
        ])
        self.assertEqual(len(output_histories), 2)
        self.assertTrue(all(not history.product
            for history in output_histories))
        self.assertEqual(len(aging_output.lot.wine_aging), 1)
