# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval
from trytond.exceptions import UserError
from trytond.i18n import gettext


class Certification(ModelSQL, ModelView):
    "Certification"
    __name__ = 'agronomics.certification'

    number = fields.Char('Number')
    date = fields.Date('Date')

    def get_rec_name(self, name):
        return self.number


class Container(ModelSQL, ModelView):
    "Container"
    __name__ = 'agronomics.container'

    name = fields.Char('Name')
    capacity = fields.Numeric('Capacity', digits=(16, 2))


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    agronomic_type = fields.Selection([
            (None, ''),
            ('grape', "Grape"),
            ('flower-wort', "Flower Wort"),
            ('firs-and-third-wort', "First and Third Wort"),
            ('wine', "Wine"),
            ('bottled-wine', "Bottled Wine"),
            ], "Agronomic Type", select=True, required=True,)
    container = fields.Many2One('agronomics.container', 'Container',
        states={
            'invisible': Eval('agronomic_type') != 'bottled-wine',
        }, depends=['agronomic_type'])
    capacity = fields.Function(fields.Numeric('Capacity', digits=(16, 2),
        states={
            'invisible': Eval('agronomic_type') != 'bottled-wine',
        }, depends=['agronomic_type']), 'get_capacity',
        searcher='search_capacity')

    def get_capacity(self, name):
        if self.container:
            return self.container.capacity

    @classmethod
    def search_capacity(cls, name, clause):
        return [('container.capacity',) + tuple(clause[1:])]


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'

    vintage = fields.Many2Many('product.product-agronomics.crop', 'product',
        'crop', 'Vintage')
    variety = fields.Many2Many('product.product-product.taxon', 'product',
        'variety', 'Variety')
    do = fields.Many2Many('product.product-agronomics.denomination_of_origin',
        'product', 'do', 'DO',
        states={
            'invisible': Eval('agronomic_type').in_(
                ['firs-and-third-wort']
            )
        }, depends=['agronomic_type'])
    ecological = fields.Many2One('agronomics.ecological', 'Ecological')
    quality_sample = fields.Many2One('quality.sample', 'Quality Sample',
        states={
            'invisible': ~ Eval('agronomic_type').in_(
                ['wine', 'bottled-wine']
            )
        }, depends=['agronomic_type'])
    certification = fields.Many2One('agronomics.certification',
        'Certification', states={
            'invisible': ~ Eval('agronomic_type').in_(
                ['wine', 'bottled-wine']
            )
        }, depends=['agronomic_type'])
    alcohol_volume = fields.Numeric('Alcohol Volume', digits=(16, 2), states={
            'invisible': ~ Eval('agronomic_type').in_(
                ['wine', 'bottled-wine']
            )}, depends=['agronomic_type'])

    @classmethod
    def validate(cls, products):
        for product in products:
            if (product.agronomic_type in
                    ['grape', 'flower-wort', 'firsts-wort', 'bottled-wine']):
                if len(product.vintage) > 1:
                    raise UserError(gettext('agronomics.msg_vintage_limit'))
            if (product.agronomic_type in
                    ['grape']):
                if len(product.variety) > 1:
                    raise UserError(gettext('agronomics.msg_variety_limit'))


class ProductCrop(ModelSQL):
    "Product - Crop"
    __name__ = 'product.product-agronomics.crop'
    product = fields.Many2One('product.product', 'Product',
        ondelete='CASCADE', select=True, required=True)
    crop = fields.Many2One('agronomics.crop', 'Crop',
        ondelete='CASCADE', select=True, required=True)


class ProductVariety(ModelSQL):
    "Product - Variety"
    __name__ = 'product.product-product.taxon'
    product = fields.Many2One('product.product', 'Product',
        ondelete='CASCADE', select=True, required=True)
    variety = fields.Many2One('product.taxon', 'Variety',
        ondelete='CASCADE', select=True, required=True)


class ProductDO(ModelSQL):
    "Product - DO"
    __name__ = 'product.product-agronomics.denomination_of_origin'
    product = fields.Many2One('product.product', 'Product',
        ondelete='CASCADE', select=True, required=True)
    do = fields.Many2One('agronomics.denomination_of_origin', 'DO',
        ondelete='CASCADE', select=True, required=True)
