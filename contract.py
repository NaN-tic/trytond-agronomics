# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields, Workflow, ModelView
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from decimal import Decimal

_STATES = {
    'readonly': Eval('state') != 'draft',
    }
_DEPENDS = ['state']


class PurchaseContract(metaclass=PoolMeta):
    __name__ = 'purchase.contract'

    producer = fields.Many2One('party.party', "Producer",
        states=_STATES, depends=_DEPENDS)
    crop = fields.Many2One('agronomics.crop', "Crop",
        states=_STATES, depends=_DEPENDS)
    price_list_base = fields.Many2One('product.price_list', "Price List Base",
        states=_STATES, depends=_DEPENDS)
    price_list_complement = fields.Many2One('product.price_list',
        "Price List Complement", states=_STATES, depends=_DEPENDS)

    @classmethod
    def __setup__(cls):
        super(PurchaseContract, cls).__setup__()
        cls.state.selection += [('done', 'Done')]
        cls._transitions.add(('active', 'done'))
        cls._buttons.update({
            'done': {
                'invisible': Eval('state') != 'active',
                'icon': 'tryton-ok',
            }
        })

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, contracts):
        pass


class PurchaseContractLine(metaclass=PoolMeta):
    __name__ = 'purchase.contract.line'

    parcel = fields.Many2One('agronomics.parcel', "Parcel",
        domain=[
            ('producer', '=', Eval('_parent_contract.producer')),
            ('crop', '=', Eval('_parent_contract.crop'))
        ])
    parcel_product = fields.Many2One('product.template', "Parcel Product")
    purchased_quantity = fields.Float("Purchased Quantity", digits=(16, 2))
    remaining_quantity = fields.Float("Remaining Quantity", digits=(16, 2))

    @fields.depends('parcel', 'product', 'purchased_quantity',
        'remaining_quantity')
    def on_change_parcel(self, name=None):
        if self.parcel:
            if self.parcel.product:
                self.parcel_product = self.parcel.product
            if self.parcel.purchased_quantity:
                self.purchased_quantity = (self.parcel.purchased_quantity
                    or Decimal(0))
            if self.parcel.remaining_quantity:
                self.remaining_quantity = (self.parcel.remaining_quantity
                    or Decimal(0))
