# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields, Workflow, ModelView, ModelSQL
from trytond.pyson import Eval
from decimal import Decimal
from trytond.pyson import If
from trytond.exceptions import UserError
from trytond.pool import Pool
from trytond.i18n import gettext

_STATES = {
    'readonly': Eval('state') != 'draft',
    }
_DEPENDS = ['state']


class AgronomicsContractProductPriceListTypePriceList(ModelSQL, ModelView):
    "Agronomics Contract Product Price List Type Price List"
    __name__ = 'agronomics.contract-product.price_list.type-product.price_list'

    contract = fields.Many2One('agronomics.contract', "Contract")
    price_list_type = fields.Many2One(
        'product.price_list.type', "Price List Type")
    price_list = fields.Many2One('product.price_list', "Price List")


class AgronomicsContract(Workflow, ModelSQL, ModelView):
    "Agronomics Contract"
    __name__ = 'agronomics.contract'

    reference = fields.Char('Reference')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('cancelled', "Cancelled"),
            ('done', 'Done'),
            ], 'State', readonly=True, required=True)
    crop = fields.Many2One(
        'agronomics.crop', "Crop", states=_STATES, depends=_DEPENDS,
        required=True)
    start_date = fields.Function(
        fields.Date('Start Date'), 'on_change_with_start_date')
    end_date = fields.Function(
        fields.Date('End Date'), 'on_change_with_start_date')
    producer = fields.Many2One(
        'party.party', "Producer", states=_STATES, depends=_DEPENDS,
        required=True)
    price_list_types = fields.One2Many(
        'agronomics.contract-product.price_list.type-product.price_list',
        'contract', "Price List Types", states=_STATES, depends=_DEPENDS)
    lines = fields.One2Many(
        'agronomics.contract.line', 'contract', "Lines", states=_STATES,
        depends=_DEPENDS)
    weighings = fields.One2Many('agronomics.weighing', 'purchase_contract',
        "Weighings", readonly=True)

    @classmethod
    def __setup__(cls):
        super(AgronomicsContract, cls).__setup__()
        cls._transitions |= set((
                ('draft', 'active'),
                ('active', 'cancelled'),
                ('active', 'done'),
                ('active', 'draft'),
                ('cancelled', 'draft'),
                ))
        cls._buttons.update({
            'draft': {
                'invisible': ~Eval('state').in_(['cancelled', 'active']),
                'icon': If(Eval('state') == 'cancelled', 'tryton-undo',
                        'tryton-back'),
            },
            'active': {
                'invisible': Eval('state') != 'draft',
                'icon': 'tryton-forward',
                },
            'cancel': {
                'invisible': Eval('state') != 'active',
                'icon': 'tryton-cancel',
                },
            'done': {
                'invisible': Eval('state') != 'active',
                'icon': 'tryton-ok',
                },
            })

    @staticmethod
    def default_state():
        return 'draft'

    def get_rec_name(self, name):
        ret = self.producer.rec_name
        if self.start_date:
            ret += ' - %s' % (self.start_date)
        return ret

    @fields.depends('crop')
    def on_change_with_start_date(self, name=None):
        if self.crop:
            return self.crop.start_date
        return None

    @fields.depends('crop')
    def on_change_with_end_date(self, name=None):
        if self.crop:
            return self.crop.end_date
        return None

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, contracts):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('active')
    def active(cls, contracts):
        pool = Pool()
        ContractLine = pool.get('agronomics.contract.line')

        for contract in contracts:
            for line in contract.lines:
                active_lines = ContractLine.search([
                    ('contract.crop', '=', contract.crop),
                    ('parcel', '=', line.parcel),
                    ('contract.state', '=', 'active'),
                ])
                if active_lines:
                    raise UserError(gettext(
                        'agronomics.msg_cant_active_contract',
                        contract=contract.rec_name,
                        parcel=line.parcel.rec_name))
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, contracts):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, contracts):
        pass


class AgronomicsContractLine(ModelSQL, ModelView):
    "Agronomics Contract Line"
    __name__ = 'agronomics.contract.line'

    contract = fields.Many2One('agronomics.contract', 'Contract', required=True,
        ondelete='CASCADE')
    parcel = fields.Many2One('agronomics.parcel', "Parcel",
        domain=[
            ('producer', '=', Eval('_parent_contract.producer')),
            ('crop', '=', Eval('_parent_contract.crop'))
        ])
    product = fields.Function(
        fields.Many2One('product.template', "Product"),
        'on_change_with_product')
    unit = fields.Function(fields.Many2One('product.uom', "Unit"),
        'on_change_with_unit')
    unit_digits = fields.Function(fields.Integer("Unit Digits"),
        'on_change_with_unit_digits')
    agreed_quantity = fields.Float("Agreed Quantity",
        digits=(16, Eval('unit_digits', 2)), depends=['unit_digits'])
    purchased_quantity = fields.Function(
        fields.Float("Purchased Quantity", digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits']),'on_change_with_purchased_quantity')
    remaining_quantity = fields.Function(
        fields.Float("Remaining Quantity", digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits']), 'on_change_with_remaining_quantity')

    @fields.depends('parcel')
    def on_change_with_product(self, name=None):
        if self.parcel:
            return self.parcel.product.id
        return None

    @fields.depends('product', methods=['on_change_with_product'])
    def on_change_with_unit(self, name=None):
        if self.product:
            return self.product.purchase_uom.id
        return None

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if self.unit:
            return self.unit.digits
        return 2

    @fields.depends('parcel')
    def on_change_with_purchased_quantity(self, name=None):
        if self.parcel:
            if self.parcel.purchased_quantity:
                return self.parcel.purchased_quantity
        return Decimal(0)

    @fields.depends('agreed_quantity', 'purchased_quantity')
    def on_change_with_remaining_quantity(self, name=None):
        if self.agreed_quantity:
            if self.purchased_quantity:
                return self.agreed_quantity - self.purchased_quantity
            else:
                return self.agreed_quantity
        return None
