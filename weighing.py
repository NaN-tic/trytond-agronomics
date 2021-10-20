# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView, Workflow
from trytond.pyson import Id, Eval, If
from trytond.pool import Pool
from trytond.i18n import gettext
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from datetime import datetime

class WeighingCenter(ModelSQL, ModelView):
    """ Weighing Center """
    __name__ = 'agronomics.weighing.center'

    name = fields.Char('Name', required=True)
    weighing_sequence = fields.Many2One('ir.sequence', 'Weighing Sequence',
        domain=[
            ('sequence_type', '=', Id('agronomics', 'sequence_type_weighing'))
        ])


READONLY = ['processing', 'in_analysis', 'done', 'cancelled']
READONLY2 = ['draft', 'in_analysis', 'done', 'cancelled']

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
    plantations = fields.Many2Many('agronomics.weighing-agronomics.plantation',
        'weighing', 'plantation', 'plantations', states={
            'readonly': Eval('state').in_(READONLY),
            'required': Eval('state') == 'process',
            }, size=4)
    state = fields.Selection([
                ('draft', "Draft"),
                ('processing', "Processing"),
                ('in_analysis', "In Analysis"),
                ('done', "Done"),
                ('cancelled', "Cancelled"),
                ], "State", readonly=True, required=True)
    state_string = state.translated('state')
    all_do = fields.Function(fields.Char('All DO'), 'get_all_do')
    quality_test = fields.Many2One('quality.test', 'Test')
    product_created = fields.Many2One('product.product', 'Product Created',
        readonly=True)

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
                    'invisible': ~Eval('state').in_(['processing']),
                    'icon': If(Eval('state') == 'cancelled',
                        'tryton-undo',
                        'tryton-back'),
                    'depends': ['state'],
                    },
                'process': {
                    'invisible': Eval('state') != 'draft',
                    'depends': ['state'],
                    },
                'analysis': {
                    'invisible': Eval('state') != 'processing',
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
        plantation = self.plantations[0]
        if not plantation.parcels:
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
            return

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
    def validate(cls, records):
        super().validate(records)
        cls.check_percent_beneficiaries(records)

    @classmethod
    def check_percent_beneficiaries(cls, records):
        for record in records:
            if record.state == 'draft':
                continue
            percent = sum([x.percent for x in record.beneficiaries])
            if record.beneficiaries and abs(100 - round(percent, 2)) > 0.0001:
                raise UserError(gettext('agronomics.msg_beneficiaris_percent',
                    crop=record.crop.rec_name,
                    plantation=record.plantations[0].rec_name))

    @classmethod
    @Workflow.transition('in_analysis')
    def analysis(cls, weighings):
        pool = Pool()
        Product = pool.get('product.product')
        default_product_values = Product.default_get(Product._fields.keys(),
            with_rec_name=False)
        product = Product(**default_product_values)
        for weighing in weighings:
            product.template = weighing.product
            product.denominations_of_origin = weighing.denomination_origin
            product.ecologicals = [weighing.ecological]
            product.varieties = [weighing.variety.id]
            product.vintages = [weighing.crop.id]
            weighing.product_created = product
            weighing.quality_test = weighing.create_quality_test()

        cls.save(weighings)

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
                document=str(self))
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
                b.percent = ben.percent
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
        return super().copy(weighings, default=default)


class WeighingDo(ModelSQL):
    'Weighing - Denomination Origin'
    __name__ = 'agronomics.weighing-agronomics.do'

    weighing = fields.Many2One('agronomics.weighing', 'Weighing')
    do = fields.Many2One('agronomics.denomination_of_origin',
        'Denomination Origin')


class WeighingPlantation(ModelSQL):
    'Weighing - Plantations'
    __name__ = 'agronomics.weighing-agronomics.plantation'

    weighing = fields.Many2One('agronomics.weighing', 'Weighing')
    plantation = fields.Many2One('agronomics.plantation',
        'Plantation')
