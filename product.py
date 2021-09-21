# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.modules.agronomics.wine import WineMixin


class Certification(ModelSQL, ModelView):
    "Certification"
    __name__ = 'agronomics.certification'
    _rec_name = 'number'

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
            ('do-wort', "DO Wort"),
            ('not-do-wort', "Not DO Wort"),
            ('unfiltered-wine', 'Unfiltered Wine'),
            ('filtered-wine', 'Filtered Wine'),
            ('clarified-wine', 'Clarified Wine'),
            ('wine', "Wine"),
            ('bottled-wine', "Bottled Wine"),
            ], "Agronomic Type", select=True)
    container = fields.Many2One('agronomics.container', 'Container',
        states={
            'invisible': Eval('agronomic_type') != 'bottled-wine',
        }, depends=['agronomic_type'])
    capacity = fields.Function(fields.Numeric('Capacity', digits=(16, 2),
        states={
            'invisible': Eval('agronomic_type') != 'bottled-wine',
        }, depends=['agronomic_type']), 'get_capacity',
        searcher='search_capacity')

    quality_weighting = fields.Many2One('quality.template', 'Quality Weighting')

    def get_capacity(self, name):
        if self.container:
            return self.container.capacity

    @classmethod
    def search_capacity(cls, name, clause):
        return [('container.capacity',) + tuple(clause[1:])]


class Product(WineMixin, metaclass=PoolMeta):
    __name__ = 'product.product'

    vintages = fields.Many2Many('product.product-agronomics.crop', 'product',
        'crop', 'Vintages')
    varieties = fields.Many2Many('product.product-product.taxon', 'product',
        'variety', 'Varieties')
    denominations_of_origin = fields.Many2Many(
        'product.product-agronomics.denomination_of_origin', 'product',
        'do', 'DOs',
        states={
            'invisible': Eval('agronomic_type').in_(
                ['not-do-wort']
            )
        }, depends=['agronomic_type'])
    ecologicals = fields.Many2Many('product.product-agronomics.ecological',
        'product', 'ecological', 'Ecologicals')
    quality_sample = fields.Many2One('quality.sample', 'Quality Sample',
        states={
            'invisible': ~ Eval('agronomic_type').in_(
                ['wine', 'unfiltered-wine', 'filtered-wine', 'clarified-wine',
                    'bottled-wine']
            )
        }, depends=['agronomic_type'])
    certification = fields.Many2One('agronomics.certification',
        'Certification', states={
            'invisible': ~ Eval('agronomic_type').in_(
                ['wine', 'unfiltered-wine', 'filtered-wine', 'clarified-wine',
                    'bottled-wine']
            )
        }, depends=['agronomic_type'])
    alcohol_volume = fields.Function(fields.Numeric('Alcohol Volume', digits=(16, 2), states={
            'invisible': ~ Eval('agronomic_type').in_(
                ['wine', 'unfiltered-wine', 'filtered-wine', 'clarified-wine',
                    'bottled-wine']
            )}, depends=['agronomic_type']), 'get_alcohol_volume')

    @classmethod
    def validate(cls, products):
        for product in products:
            if (product.agronomic_type in
                    ['grape', 'do-wort', 'not-do-wort', 'bottled-wine']):
                if len(product.vintages) > 1:
                    raise UserError(gettext('agronomics.msg_vintage_limit',
                    product=product.rec_name))
            if product.agronomic_type == 'grape':
                if len(product.varieties) > 1:
                    raise UserError(gettext('agronomics.msg_variety_limit',
                    product=product.rec_name))

    def get_alcohol_volume(self, name):
        if self.template.capacity and self.wine_alcohol_content:
            return Decimal(
                (float(self.template.capacity) * float(self.wine_alcohol_content))
                    / 100).quantize(
                        Decimal(str(10 ** -self.__class__.alcohol_volume.digits[1])))


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


class ProductEcological(ModelSQL):
    "Product - Ecological"
    __name__ = 'product.product-agronomics.ecological'
    product = fields.Many2One('product.product', 'Product',
        ondelete='CASCADE', select=True, required=True)
    ecological = fields.Many2One('agronomics.ecological', 'Ecological',
        ondelete='CASCADE', select=True, required=True)
