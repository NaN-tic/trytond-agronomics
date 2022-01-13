# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Bool


tank_states = {'invisible': ~Bool(Eval('tank'))}
tank_depends = ['tank']

class LocationMaterial(ModelSQL, ModelView):
    "Location Material"
    __name__ = 'stock.location.material'

    name = fields.Char("Name", required=True)


class Location(metaclass=PoolMeta):
    __name__ = 'stock.location'

    tank = fields.Boolean("Tank",
        states={
            'invisible': Eval('type') != 'storage',
            },
        depends=['type'])
    material = fields.Selection('get_materials', "Material",
        states=tank_states, depends=tank_depends)
    uom = fields.Many2One('product.uom', 'Uom',
        states=tank_states, depends=tank_depends)
    unit_digits = fields.Function(fields.Integer("Unit Digits",
        states=tank_states, depends=tank_depends),
        'on_change_with_unit_digits')
    max_capacity = fields.Float("Maximum capacity",
        digits=(16, Eval('unit_digits', 2)),
        states=tank_states, depends=['unit_digits', 'tank'])

    @classmethod
    def get_materials(field_name):
        pool = Pool()
        LocationMaterial = pool.get('stock.location.material')
        materials = [(None, "")]
        for material in LocationMaterial.search([]):
            materials.append((material.name, material.name))
        return materials

    @fields.depends('uom')
    def on_change_with_unit_digits(self, name=None):
        if self.uom:
            return self.uom.digits
        return 2
