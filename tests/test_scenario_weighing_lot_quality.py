import datetime
import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.account.tests.tools import create_chart, get_accounts
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class TestWeighingLotQuality(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        activate_modules('agronomics')

        create_company()
        company = get_company()
        create_chart(company)
        accounts = get_accounts(company)
        today = datetime.date.today()

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
        quality_template = QualityTemplate(name='Weighing Quality')
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
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(
            name='Account Category',
            accounting=True,
            account_expense=accounts['expense'],
            account_revenue=accounts['revenue'])
        account_category.save()
        product_template = ProductTemplate(
            name='Table Grapes',
            default_uom=kg,
            type='goods',
            list_price=Decimal(0),
            account_category=account_category,
            lot_sequence=lot_sequence,
            quality_weighing=quality_template)
        product_template.save()
        product, = product_template.products
        product.cost_price = Decimal(0)
        product.save()

        PriceList = Model.get('product.price_list')
        price_list = PriceList(name='Lot Analysis', company=company)
        price_line = price_list.lines.new()
        price_line.formula = 'Decimal(ph)'
        price_list.save()
        PriceListType = Model.get('product.price_list.type')
        price_list_type = PriceListType(name='Lot Analysis')
        price_list_type.save()

        Taxon = Model.get('product.taxon')
        species = Taxon(name='Grape', rank='species')
        species.save()
        variety = Taxon(name='Macabeu', rank='variety')
        variety.save()

        DenominationOrigin = Model.get(
            'agronomics.denomination_of_origin')
        denomination_origin = DenominationOrigin(name='Catalunya')
        denomination_origin.save()
        denomination_origin_id = denomination_origin.id
        Ecological = Model.get('agronomics.ecological')
        ecological = Ecological(name='Ecological')
        ecological.save()
        Crop = Model.get('agronomics.crop')
        crop = Crop(
            name=str(today.year),
            code=str(today.year),
            start_date=datetime.date(today.year, 1, 1),
            end_date=datetime.date(today.year, 12, 31))
        crop.save()

        Party = Model.get('party.party')
        producer = Party(name='Producer')
        producer.save()
        Plantation = Model.get('agronomics.plantation')
        plantation = Plantation(
            party=producer,
            code='Plantation',
            plantation_year=today.year)
        parcel = plantation.parcels.new()
        parcel.crop = crop
        parcel.product = product
        parcel.species = species
        parcel.variety = variety
        parcel.ecological = ecological
        parcel.denomination_origin.append(denomination_origin)
        parcel.surface = 1
        beneficiary = parcel.beneficiaries.new()
        beneficiary.party = producer
        beneficiary.product_price_list_type = price_list_type
        plantation.save()

        MaxProductionAllowed = Model.get(
            'agronomics.max.production.allowed')
        max_production = MaxProductionAllowed(
            crop=crop,
            product=product,
            denomination_origin=DenominationOrigin(denomination_origin_id),
            variety=variety,
            max_production=Decimal(1000))
        max_production.save()

        Contract = Model.get('agronomics.contract')
        contract = Contract(party=producer, crop=crop)
        contract_price_list = contract.price_list_types.new()
        contract_price_list.price_list_type = price_list_type
        contract_price_list.price_list = price_list
        contract.save()
        contract.click('active')

        Location = Model.get('stock.location')
        storage, = Location.find([('code', '=', 'STO')])
        weighing_sequence, = Sequence.find([('name', '=', 'Weighing')])
        WeighingCenter = Model.get('agronomics.weighing.center')
        weighing_center = WeighingCenter(
            name='Weighing Center',
            weighing_sequence=weighing_sequence,
            to_location=storage)
        weighing_center.save()

        Weighing = Model.get('agronomics.weighing')
        weighing = Weighing(
            weighing_date=today,
            weighing_center=weighing_center,
            purchase_contract=contract,
            crop=crop,
            product=product,
            variety=variety,
            ecological=ecological,
            weight=100,
            netweight=100,
            grade=10)
        weighing.denomination_origin.append(
            DenominationOrigin(denomination_origin_id))
        weighing_plantation = weighing.plantations.new()
        weighing_plantation.plantation = plantation
        weighing.save()

        second_weighing = Weighing(
            weighing_date=today,
            weighing_center=weighing_center,
            purchase_contract=contract,
            crop=crop,
            product=product,
            variety=variety,
            ecological=ecological,
            weight=50,
            netweight=50,
            grade=10)
        second_weighing.denomination_origin.append(
            DenominationOrigin(denomination_origin_id))
        second_plantation = second_weighing.plantations.new()
        second_plantation.plantation = plantation
        second_weighing.save()

        Weighing.click([weighing, second_weighing], 'process')
        weighing.reload()
        second_weighing.reload()
        self.assertEqual(weighing.state, 'processing')
        self.assertEqual(second_weighing.state, 'processing')
        Weighing.click([weighing, second_weighing], 'distribute')
        weighing.reload()
        second_weighing.reload()

        self.assertEqual(weighing.state, 'in_analysis')
        self.assertEqual(second_weighing.state, 'in_analysis')
        self.assertIsNotNone(weighing.lot_created)
        self.assertIsNotNone(second_weighing.lot_created)
        self.assertNotEqual(weighing.lot_created, second_weighing.lot_created)
        self.assertNotEqual(
            weighing.inventory_move, second_weighing.inventory_move)
        self.assertEqual(
            second_weighing.inventory_move.lot,
            second_weighing.lot_created)
        self.assertEqual(weighing.inventory_move.lot, weighing.lot_created)

        Lot = Model.get('stock.lot')
        with weighing._config.set_context(locations=[storage.id]):
            lots_in_stock = Lot.find([
                ('product', '=', product.id),
                ('quantity', '>', 0),
                ])
        self.assertEqual(len(lots_in_stock), 1)
        self.assertEqual(lots_in_stock[0].quantity, 150)
        self.assertNotIn(lots_in_stock[0].id,
            [weighing.lot_created.id, second_weighing.lot_created.id])

        QualityTest = Model.get('quality.test')
        quality_tests = QualityTest.find([
            ('document.id', '=', weighing.lot_created.id, 'stock.lot'),
        ])
        self.assertEqual(len(quality_tests), 1)
        quality_test, = quality_tests
        self.assertEqual(quality_test.document, weighing.lot_created)

        quality_line, = quality_test.quantitative_lines
        self.assertEqual(quality_line.product, product)
        QuantitativeTestLine = Model.get(
            'quality.quantitative.test.line')
        product_lines = QuantitativeTestLine.find([
            ('product', '=', product.id),
        ])
        self.assertIn(quality_line.id,
            [line.id for line in product_lines])
        quality_line.value = Decimal('3.5')
        quality_test.save()
        QualityTest.confirmed([quality_test.id], {})

        weighing.lot_created.reload()
        self.assertEqual(weighing.lot_created.wine_ph, 3.5)
        self.assertEqual(weighing.lot_created.wine_ph_comment, 'PH result')
        self.assertEqual(weighing.lot_created.wine_ph_confirm, today)
        self.assertTrue(weighing.lot_created.wine_ph_success)

        weighing.click('do')
        weighing.reload()
        invoice_line, = weighing.beneficiaries_invoices_line
        self.assertEqual(invoice_line.unit_price, Decimal('3.5'))

        price_list.lines.remove(price_list.lines[0])
        price_list.save()
        second_weighing.click('do')
        second_weighing.reload()
        invoice_line, = second_weighing.beneficiaries_invoices_line
        self.assertEqual(invoice_line.unit_price, Decimal(0))
