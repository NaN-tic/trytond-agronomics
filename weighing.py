# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView, Workflow, sequence_ordered
from trytond.pyson import Id, Eval, If
from trytond.pool import Pool
from trytond.i18n import gettext
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from trytond.wizard import (Wizard, StateView, StateTransition, StateAction,
    Button)
from datetime import datetime

class WeighingCenter(ModelSQL, ModelView):
    """ Weighing Center """
    __name__ = 'agronomics.weighing.center'

    name = fields.Char('Name', required=True)
    weighing_sequence = fields.Many2One('ir.sequence', 'Weighing Sequence',
        domain=[
            ('sequence_type', '=', Id('agronomics', 'sequence_type_weighing'))
        ])


READONLY = ['processing', 'distributed', 'in_analysis', 'done', 'cancelled']
READONLY2 = ['draft', 'distributed', 'in_analysis', 'done', 'cancelled']

class Weighing(Workflow, ModelSQL, ModelView):
    """ Weighing """
    __name__ = 'agronomics.weighing'
    _rec_name = 'number'

    number = fields.Char('Number', readonly=True, select=True)
    weighing_date = fields.Date('Date', states={
            'readonly': Eval('state').in_(READONLY),
            'required': True
            }, depends=['state'])
    weighing_center = fields.Many2One('agronomics.weighing.center',
        'Weighing Center', states={
            'readonly': Eval('state').in_(READONLY),
            'required': True
        }, depends=['state'])

    purchase_contract = fields.Many2One('purchase.contract',
        'Purchase Contract', states={
            'readonly': Eval('state').in_(READONLY),
            'required': True
        }, depends=['state'])

    crop = fields.Many2One('agronomics.crop', 'Crop', states={
            'readonly': Eval('state').in_(READONLY),
            'required': Eval('state') == 'in_analysis',
            }, depends=['state'])
    product = fields.Many2One('product.template', 'Product', states={
            'readonly': Eval('state').in_(READONLY),
            'required': Eval('state') == 'in_analysis',
            }, depends=['state'])
    variety = fields.Many2One('product.taxon', 'Variety', states={
            'readonly': Eval('state').in_(READONLY2),
            'required': Eval('state') == 'in_analysis',
            }, depends=['state'])
    table = fields.Boolean('Table', states={
            'readonly': Eval('state').in_(READONLY2),
            }, depends=['state'])
    ecological = fields.Many2One('agronomics.ecological', 'Ecological',
        states={
            'readonly': Eval('state').in_(READONLY2),
            'required': Eval('state') == 'in_analysis',
            }, depends=['state'])
    weight = fields.Float('Weight', states={
            'readonly': Eval('state').in_(READONLY2),
            'required': Eval('state') == 'in_analysis',
            })
    tara = fields.Float('Tara', states={
            'readonly': Eval('state').in_(READONLY2),
            'required': Eval('state') == 'in_analysis',
            })
    netweight = fields.Float('Net Weight', states={
            'readonly': Eval('state').in_(READONLY2),
            'required': Eval('state') == 'in_analysis',
            })
    beneficiaries = fields.One2Many('agronomics.beneficiary', 'weighing',
        'Beneficiaries', states={
                'readonly': Eval('state').in_(READONLY2),
                'required': Eval('state') == 'in_analysis',
                })
    denomination_origin = fields.Many2Many('agronomics.weighing-agronomics.do',
        'weighing', 'do', 'Denomination of Origin', states={
            'readonly': Eval('state').in_(READONLY2),
            'required': Eval('state') == 'in_analysis',
            })
    plantations = fields.One2Many('agronomics.weighing-agronomics.plantation',
        'weighing', 'plantations', states={
            'readonly': Eval('state').in_(READONLY),
            'required': Eval('state') == 'process',
            }, size=4)
    state = fields.Selection([
                ('draft', "Draft"),
                ('processing', "Processing"),
                ('distributed', "Distributed"),
                ('in_analysis', "In Analysis"),
                ('done', "Done"),
                ('cancelled', "Cancelled"),
                ], "State", readonly=True, required=True)
    state_string = state.translated('state')
    all_do = fields.Function(fields.Char('All DO'), 'get_all_do')
    quality_test = fields.Function(fields.Many2One('quality.test', 'Test',
        states={
            'readonly': Eval('state').in_(['done', 'cancelled']),
        }),
        'get_quality_test', 'set_quality_test')
    product_created = fields.Many2One('product.product', 'Product Created',
        readonly=True)
    parcels = fields.One2Many('agronomics.weighing-agronomics.parcel',
        'weighing', 'Parcels', readonly=True)
    not_assigned_weight = fields.Function(
        fields.Float('Not Assigned Weight'), 'get_not_assigned_weight')
    forced_analysis = fields.Boolean('Forced Analysis', readonly=True)

    @classmethod
    def __setup__(cls):
        super(Weighing, cls).__setup__()
        cls._order = [
            ('weighing_date', 'DESC NULLS FIRST'),
            ('id', 'DESC'),
            ]
        cls._transitions |= set((
                ('draft', 'processing'),
                ('processing', 'draft'),
                ('processing', 'distributed'),
                ('distributed', 'in_analysis'),
                ('distributed', 'draft'),
                ('processing', 'in_analysis'),
                ('draft', 'cancelled'),
                ('processing', 'cancelled'),
                ('in_analysis', 'done'),
                ))
        cls._buttons.update({
                'done': {
                    'invisible': ~Eval('state').in_(['in_analysis']),
                    'depends': ['state'],
                    },
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft']),
                    'depends': ['state'],
                    },
                'draft': {
                    'invisible': ~Eval('state').in_(['processing', 'distributed']),
                    'icon': If(Eval('state') == 'cancelled',
                        'tryton-undo',
                        'tryton-back'),
                    'depends': ['state'],
                    },
                'process': {
                    'invisible': Eval('state') != 'draft',
                    'depends': ['state'],
                    },
                'distribute': {
                    'invisible': Eval('state') != 'processing',
                    'depends': ['state'],
                    },
                'force_analysis': {
                    'invisible': Eval('state') != 'distributed',
                    'depends': ['state'],
                    },
                })

    @staticmethod
    def default_weighing_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_state():
        return 'draft'

    def get_all_do(self, name):
        return ",".join([x.name for x in self.denomination_origin])

    def get_quality_test(self, name):
        if not self.product_created:
            return
        tests = self.product_created.quality_tests
        return tests and tests[0] and tests[0].id

    @classmethod
    def set_quality_test(cls, weighings, name, value):
        Test = Pool().get('quality.test')
        if not value:
            return

    @fields.depends('weighing_date')
    def on_change_with_crop(self):
        Crop = Pool().get('agronomics.crop')
        crop = Crop.search([('start_date', '<=', self.weighing_date),
            ('end_date', '>=', self.weighing_date)], limit=1)
        if not crop:
            return
        return crop[0].id

    def get_parcel(self):
        if not self.plantations:
            return
        plantation = self.plantations[0].plantation
        if not plantation or not plantation.parcels:
            return
        return plantation.parcels[0]

    @fields.depends('plantations')
    def on_change_with_variety(self):
        parcel = self.get_parcel()
        if not parcel:
            return
        return parcel.variety and parcel.variety.id

    @fields.depends('plantations')
    def on_change_with_denomination_origin(self):
        parcel = self.get_parcel()
        if not parcel:
            return []

        return [x.id for x in parcel.denomination_origin]

    @fields.depends('plantations')
    def on_change_with_table(self):
        parcel = self.get_parcel()
        if not parcel:
            return
        return parcel.table

    @fields.depends('plantations')
    def on_change_with_ecological(self):
        parcel = self.get_parcel()
        if not parcel:
            return
        return parcel.ecological and parcel.ecological.id

    @fields.depends('plantations')
    def on_change_with_product(self):
        parcel = self.get_parcel()
        if not parcel:
            return
        return parcel.product and parcel.product.id

    @fields.depends('plantations')
    def on_change_with_purchase_contract(self):
        parcel = self.get_parcel()
        if not parcel:
            return

        producer = parcel.producer and parcel.producer.id
        if not producer:
            return
        Contract = Pool().get('purchase.contract')
        contracts = Contract.search([('party', '=', producer)], limit=1)
        if not contracts:
            return

        contract, = contracts
        return contract and contract.id

    @fields.depends('weight', 'tara')
    def on_change_with_netweight(self):
        return (self.weight or 0) - (self.tara or 0)

    @classmethod
    @Workflow.transition('in_analysis')
    def analysis(cls, weighings):
        pool = Pool()
        Product = pool.get('product.product')
        Quality = pool.get('quality.test')
        Variety = Pool().get('product.variety')
        default_product_values = Product.default_get(Product._fields.keys(),
            with_rec_name=False)
        product = Product(**default_product_values)
        for weighing in weighings:
            if weighing.not_assigned_weight and not weighing.forced_analysis:
                raise UserError(gettext('agronomics.msg_not_assigned_weight',
                    weighing=weighing.rec_name))
            product.template = weighing.product
            product.denominations_of_origin = weighing.denomination_origin
            if weighing.ecological:
                product.ecologicals = [weighing.ecological]
            if weighing.variety:
                new_variety = Variety()
                new_variety.percent = 100
                new_variety.variety = weighing.variety
                product.varieties = [new_variety]
            product.vintages = [weighing.crop.id]
            weighing.product_created = product

        cls.save(weighings)
        tests = []
        for weighing in weighings:
            tests.append(weighing.create_quality_test())
        Quality.save(tests)

    @classmethod
    @ModelView.button
    @Workflow.transition('distributed')
    def distribute(cls, weighings):
        pool = Pool()
        WeighingParcel = pool.get('agronomics.weighing-agronomics.parcel')
        weighing_parcel_to_save = []
        to_analysis = []
        for weighing in weighings:
            if not weighing.table:
                if weighing.parcels:
                    WeighingParcel.delete(weighing.parcels)
                allowed_parcels = []
                remaining_weight = weighing.netweight
                for wp in weighing.plantations:
                    plantation = wp.plantation
                    if plantation:
                        for parcel in plantation.parcels:
                            if parcel.crop == weighing.crop:
                                allowed_parcels.append(parcel)
                                break
                for parcel in allowed_parcels:
                    if not remaining_weight:
                        break
                    weighing_parcel = WeighingParcel()
                    weighing_parcel.parcel = parcel
                    weighing_parcel.weighing = weighing
                    if parcel.remaining_quantity - remaining_weight >= 0:
                        weighing_parcel.netweight = remaining_weight
                        remaining_weight = 0
                    else:
                        remaining_weight -= parcel.remaining_quantity
                        weighing_parcel.netweight = parcel.remaining_quantity
                    if weighing_parcel.netweight:
                        weighing_parcel_to_save.append(weighing_parcel)
                if remaining_weight == 0:
                    to_analysis.append(weighing)
            else:
                parcel = weighing.get_parcel()
                weighing_parcel = WeighingParcel()
                weighing_parcel.parcel = parcel
                weighing_parcel.weighing = weighing
                weighing_parcel.netweight = weighing.netweight
                weighing_parcel.table = True
                weighing_parcel_to_save.append(weighing_parcel)
                to_analysis.append(weighing)
        WeighingParcel.save(weighing_parcel_to_save)
        cls.save(weighings)
        cls.analysis(to_analysis)

    def get_not_assigned_weight(self, name):
        return self.netweight - sum([p.netweight for p in self.parcels])

    @classmethod
    @ModelView.button
    def force_analysis(cls, weighings):
        to_copy_values = {}
        for weighing in weighings:
            to_copy_values[weighing.id] = {
                'netweight': weighing.not_assigned_weight}
        cls.copy(weighings, default={
                            'netweight': lambda d: (
                                to_copy_values[d['id']]['netweight']),
                            'weight': None,
                            'tara': None,
                            })
        for weighing in weighings:
            weighing.forced_analysis = True
            weighing.netweight -= weighing.not_assigned_weight
        cls.save(weighings)
        cls.analysis(weighings)

    def create_quality_test(self):
        pool = Pool()
        QualityTest = pool.get('quality.test')

        with Transaction().set_context(_check_access=False):
            if not (self.product and self.product.quality_weighing):
                return
            template = self.product.quality_weighing
            test = QualityTest(
                test_date=datetime.now(),
                templates=[template],
                document=str(self.product_created))
            test.apply_template_values()

        return test

    @classmethod
    @Workflow.transition('draft')
    def draft(cls, weighings):
        pass

    @classmethod
    @Workflow.transition('done')
    def done(cls, weighings):
        pass

    @classmethod
    @Workflow.transition('processing')
    def process(cls, weighings):
        Beneficiary = Pool().get('agronomics.beneficiary')
        to_save = []

        for weighing in weighings:
            if weighing.beneficiaries:
                Beneficiary.delete([x for x in weighing.beneficiaries])

            parcel = weighing.get_parcel()
            if not parcel:
                continue

            for ben in parcel.beneficiaries:
                b = Beneficiary()
                b.party = ben.party
                b.weighing = weighing
                b.product_price_list_type = ben.product_price_list_type
                to_save.append(b)

        if to_save:
            Beneficiary.save(to_save)

    @classmethod
    @Workflow.transition('cancel')
    def cancel(cls, weighings):
        pass

    @classmethod
    def set_number(cls, weighing_center):
        WeighingCenter = Pool().get('agronomics.weighing.center')
        weighing_center = WeighingCenter(weighing_center)
        return (weighing_center.weighing_sequence and
            weighing_center.weighing_sequence.get())

    @classmethod
    def create(cls, vlist):
        vlist = [v.copy() for v in vlist]
        for values in vlist:
            if not values.get('number'):
                values['number'] = cls.set_number(values.get('weighing_center'))
        return super().create(vlist)

    @classmethod
    def copy(cls, weighings, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('beneficiaries', None)
        default.setdefault('product_created', None)
        default.setdefault('number', None)
        default.setdefault('parcels', None)
        return super().copy(weighings, default=default)


class WeighingDo(ModelSQL):
    'Weighing - Denomination Origin'
    __name__ = 'agronomics.weighing-agronomics.do'

    weighing = fields.Many2One('agronomics.weighing', 'Weighing')
    do = fields.Many2One('agronomics.denomination_of_origin',
        'Denomination Origin')


class WeighingPlantation(sequence_ordered(), ModelSQL, ModelView):
    'Weighing - Plantations'
    __name__ = 'agronomics.weighing-agronomics.plantation'

    weighing = fields.Many2One('agronomics.weighing', 'Weighing')
    plantation = fields.Many2One('agronomics.plantation',
        'Plantation')
    party = fields.Function(fields.Many2One('party.party', 'Party'), 'get_party')

    def get_party(self, name):
        if self.plantation:
            return self.plantation.party.id


class WeighingParcel(ModelSQL, ModelView):
    "Weighing-Parcel"
    __name__ = 'agronomics.weighing-agronomics.parcel'

    weighing = fields.Many2One('agronomics.weighing', 'Weighing',
        ondelete='CASCADE')
    parcel = fields.Many2One('agronomics.parcel', 'Parcel')
    netweight = fields.Float('Net Weight')
    table = fields.Boolean('Table')
