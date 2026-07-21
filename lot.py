# This file is part of agronomics module for Tryton.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from .wine import WineMixin


class Lot(WineMixin, metaclass=PoolMeta):
    __name__ = 'stock.lot'

    crop = fields.Many2Many('agronomics.lot-agronomics.crop', 'lot', 'crop',
        'Vintages')
    varieties = fields.One2Many('agronomics.lot.variety', 'lot', 'Varieties')
    denominations_of_origin = fields.Many2Many(
        'agronomics.lot-agronomics.denomination_of_origin', 'lot', 'do',
        'DOs')
    ecologicals = fields.Many2Many('agronomics.lot-agronomics.ecological',
        'lot', 'ecological', 'Ecologicals')
    certification = fields.Many2One('agronomics.certification',
        'Certification')
    quality_samples = fields.Many2Many('stock.lot-quality.sample', 'lot',
        'sample', 'Quality Samples')
    wine_aging = fields.One2Many('stock.lot.wine_aging.history', 'lot',
        "Wine Aging", readonly=True,
        context={
            'lot': Eval('id', -1),
            },
        depends=['id'])
    agronomic_type = fields.Function(fields.Char('Agronomic Type'),
        'on_change_with_agronomic_type')

    @fields.depends('product')
    def on_change_with_agronomic_type(self, name=None):
        if self.product:
            return self.product.template.agronomic_type


class LotVariety(ModelSQL, ModelView):
    __name__ = 'agronomics.lot.variety'
    lot = fields.Many2One('stock.lot', 'Lot', required=True,
        ondelete='CASCADE')
    variety = fields.Many2One('product.taxon', 'Variety', required=True)
    percent = fields.Float('Percent', digits=(16, 4), required=True)


class LotCrop(ModelSQL):
    __name__ = 'agronomics.lot-agronomics.crop'
    lot = fields.Many2One('stock.lot', 'Lot', required=True,
        ondelete='CASCADE')
    crop = fields.Many2One('agronomics.crop', 'Crop', required=True,
        ondelete='CASCADE')


class LotDO(ModelSQL):
    __name__ = 'agronomics.lot-agronomics.denomination_of_origin'
    lot = fields.Many2One('stock.lot', 'Lot', required=True,
        ondelete='CASCADE')
    do = fields.Many2One('agronomics.denomination_of_origin', 'DO',
        required=True, ondelete='CASCADE')


class LotEcological(ModelSQL):
    __name__ = 'agronomics.lot-agronomics.ecological'
    lot = fields.Many2One('stock.lot', 'Lot', required=True,
        ondelete='CASCADE')
    ecological = fields.Many2One('agronomics.ecological', 'Ecological',
        required=True, ondelete='CASCADE')
