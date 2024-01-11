# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Bool


tank_states = {'invisible': ~Bool(Eval('tank'))}

class LocationMaterial(ModelSQL, ModelView):
    "Location Material"
    __name__ = 'stock.location.material'

    name = fields.Char("Name", required=True)


class Location(metaclass=PoolMeta):
    __name__ = 'stock.location'

    tank = fields.Boolean("Tank",
        states={
            'invisible': Eval('type') != 'storage',
            })
    material = fields.Many2One('stock.location.material', "Material",
        states=tank_states)
    uom = fields.Many2One('product.uom', 'Uom',
        states=tank_states)
    unit_digits = fields.Function(fields.Integer("Unit Digits",
        states=tank_states),
        'on_change_with_unit_digits')
    max_capacity = fields.Float("Maximum capacity",
        digits=(16, Eval('unit_digits', 2)),
        states=tank_states)

    @fields.depends('uom')
    def on_change_with_unit_digits(self, name=None):
        if self.uom:
            return self.uom.digits
        return 2
