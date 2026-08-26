import datetime
import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.account.tests.tools import create_chart, get_accounts
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class TestWeighingMultiPlantationBeneficiaries(unittest.TestCase):

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

        ProductUom = Model.get('product.uom')
        kg, = ProductUom.find([('name', '=', 'Kilogram')])
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
            account_category=account_category)
        product_template.save()
        product, = product_template.products
        product.cost_price = Decimal(0)
        product.save()

        Taxon = Model.get('product.taxon')
        species = Taxon(name='Grape', rank='species')
        species.save()
        variety = Taxon(name='Macabeu', rank='variety')
        variety.save()

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
        owner = Party(name='Owner')
        owner.save()
        sharecropper = Party(name='Sharecropper')
        sharecropper.save()

        PriceListType = Model.get('product.price_list.type')
        owner_price_list_type = PriceListType(name='Grape')
        owner_price_list_type.save()
        sharecropper_price_list_type = PriceListType(name='Harvest service')
        sharecropper_price_list_type.save()

        Plantation = Model.get('agronomics.plantation')

        plantation_1 = Plantation(
            party=owner, code='Plantation-1', plantation_year=today.year)
        parcel_1 = plantation_1.parcels.new()
        parcel_1.crop = crop
        parcel_1.product = product
        parcel_1.species = species
        parcel_1.variety = variety
        parcel_1.ecological = ecological
        parcel_1.surface = 1
        beneficiary_1 = parcel_1.beneficiaries.new()
        beneficiary_1.party = owner
        beneficiary_1.product_price_list_type = owner_price_list_type
        plantation_1.save()

        plantation_2 = Plantation(
            party=owner, code='Plantation-2', plantation_year=today.year)
        parcel_2 = plantation_2.parcels.new()
        parcel_2.crop = crop
        parcel_2.product = product
        parcel_2.species = species
        parcel_2.variety = variety
        parcel_2.ecological = ecological
        parcel_2.surface = 1
        beneficiary_2 = parcel_2.beneficiaries.new()
        beneficiary_2.party = sharecropper
        beneficiary_2.product_price_list_type = (
            sharecropper_price_list_type)
        plantation_2.save()

        Contract = Model.get('agronomics.contract')
        contract = Contract(party=owner, crop=crop)
        contract.save()

        Location = Model.get('stock.location')
        storage, = Location.find([('code', '=', 'STO')])
        Sequence = Model.get('ir.sequence')
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
            weight=150,
            netweight=150,
            grade=10)
        wp1 = weighing.plantations.new()
        wp1.plantation = plantation_1
        wp2 = weighing.plantations.new()
        wp2.plantation = plantation_2
        weighing.save()

        weighing.click('process')
        weighing.reload()
        self.assertEqual(weighing.state, 'processing')

        beneficiary_parties = sorted(
            b.party.name for b in weighing.beneficiaries)
        self.assertEqual(beneficiary_parties, ['Owner', 'Sharecropper'])

        beneficiaries_by_party = {
            b.party.name: b for b in weighing.beneficiaries}
        self.assertEqual(
            beneficiaries_by_party['Owner'].product_price_list_type,
            owner_price_list_type)
        self.assertEqual(
            beneficiaries_by_party['Sharecropper'].product_price_list_type,
            sharecropper_price_list_type)
