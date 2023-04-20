# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from datetime import datetime
from sql.operators import (Less, Greater, LessEqual,
    GreaterEqual, Equal, NotEqual)
from sql import Null
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.modules.agronomics.wine import WineMixin
from trytond.transaction import Transaction


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


class ProductConfiguration(metaclass=PoolMeta):
    __name__ = 'product.configuration'

    variant_deactivation_time = fields.TimeDelta("Variant Deactivation Time")


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    needs_sample = fields.Boolean('Needs Samples')
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

    quality_weighing = fields.Many2One('quality.template', 'Quality Weighing')

    variant_deactivate_stock_zero = fields.Boolean("Variant Deactivate Stock 0")

    def get_capacity(self, name):
        if self.container:
            return self.container.capacity

    @classmethod
    def search_capacity(cls, name, clause):
        return [('container.capacity',) + tuple(clause[1:])]


class ProductVariety(ModelSQL, ModelView):
    'Product Variety'
    __name__ = 'product.variety'

    variety = fields.Many2One('product.taxon', 'Variety', required=True)
    percent = fields.Float('Percent', digits=(16, 4), required=True)
    product = fields.Many2One('product.product', 'Product', required=True)


class Product(WineMixin, metaclass=PoolMeta):
    __name__ = 'product.product'

    vintages = fields.Many2Many('product.product-agronomics.crop', 'product',
        'crop', 'Vintages')
    varieties = fields.One2Many('product.variety', 'product', 'Varieties')
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
    certification = fields.Many2One('agronomics.certification',
        'Certification', states={
            'invisible': ~ Eval('agronomic_type').in_(
                ['wine', 'unfiltered-wine', 'filtered-wine', 'clarified-wine',
                    'bottled-wine']
            )
        }, depends=['agronomic_type'])
    alcohol_volume = fields.Function(fields.Numeric('Alcohol Volume',
            digits=(16, 2), states={
            'invisible': ~ Eval('agronomic_type').in_(
                ['wine', 'unfiltered-wine', 'filtered-wine', 'clarified-wine',
                    'bottled-wine']
            )}, depends=['agronomic_type']), 'get_alcohol_volume')
    quality_tests = fields.One2Many('quality.test', 'document', 'Quality Tests')
    quality_samples = fields.Many2Many('product.product-quality.sample',
        'product', 'sample', 'Quality Samples')
    wine_aging = fields.One2Many('product.wine.wine_aging.history', 'product',
        "Wine Aging", readonly=True,
        context={
            'product': Eval('id'),
        }, depends=['id'])
    wine_history_material = fields.Function(fields.Text("History Material"),
        'get_wine_history', searcher='search_wine_history')
    wine_history_duration = fields.Function(fields.Text("History Duration"),
        'get_wine_history', searcher='search_wine_history')
    vintages_str = fields.Function(fields.Char("Vintage"), 'get_vintages_str')

    def get_vintages_str(self, name):
        return ', '.join([v.name for v in self.vintages])


    @classmethod
    def deactivate_no_stock_variants_cron(cls):
        pool = Pool()
        Location = pool.get('stock.location')
        ProductConfiguration = pool.get('product.configuration')
        WineAgingHistory = pool.get('wine.wine_aging.history')
        Date = pool.get('ir.date')

        today = Date.today()
        config = ProductConfiguration(1)
        locations = Location.search(['type', '=', 'warehouse'])
        locations = [location.id for location in locations]
        with Transaction().set_context(locations=locations, with_childs=True):
            if config.variant_deactivation_time is not None:
                products = cls.search(
                    [
                        ('quantity', '=', 0),
                        ('template.variant_deactivate_stock_zero', '=', True),
                        ('create_date', '<',
                            (datetime.now() - config.variant_deactivation_time))
                    ])
                if products:
                    cls.write(products, {'active': False})
                    histories = WineAgingHistory.search([
                        ('product', 'in', products),
                        ('date_end', '=', None),
                        ])
                    if histories:
                        WineAgingHistory.write(histories, {'date_end': today})

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

    def get_wine_history(self, name):
        # not implemented
        pass

    @classmethod
    def search_wine_history(cls, name, clause):
        pool = Pool()
        WineAgingHistory = pool.get('wine.wine_aging.history')
        Material = pool.get('stock.location.material')

        wineaginghistory = WineAgingHistory.__table__()
        material =  Material.__table__()

        Operator = fields.SQL_OPERATORS[clause[1]]
        value = clause[2]

        join1 = wineaginghistory.join(material,
            condition=wineaginghistory.material == material.id)
        query = join1.select(wineaginghistory.product)

        if name == 'wine_history_material':
            query.where = (Operator(material.name, clause[2])
                            & (wineaginghistory.material != Null)
                            & (wineaginghistory.duration != Null))
        elif name == 'wine_history_duration':
            operator = clause[1]
            try:
                value = int(value)
            except ValueError:
                value = None
            if value:
                if operator == '=':
                    query.where = Equal(wineaginghistory.duration, value)
                elif operator == '!=':
                    query.where = NotEqual(wineaginghistory.duration, value)
                elif operator == '>':
                    query.where = Greater(wineaginghistory.duration, value)
                elif operator == '>=':
                    query.where = GreaterEqual(wineaginghistory.duration, value)
                elif operator == '<':
                    query.where = Less(wineaginghistory.duration, value)
                elif operator == '<=':
                    query.where = LessEqual(wineaginghistory.duration, value)

        return [('id', 'in', query)]


    def get_rec_name(self, name):
        rec_name = super().get_rec_name(name)
        if not self.vintages:
            return rec_name

        aging = ",".join(x.name for x in self.vintages)
        rec_name = rec_name + "-" + aging
        return rec_name

class Cron(metaclass=PoolMeta):
    __name__ = 'ir.cron'

    @classmethod
    def __setup__(cls):
        super(Cron, cls).__setup__()
        cls.method.selection.append(
            ('product.product|deactivate_no_stock_variants_cron',
                "Deactivate Variants"),
            )


class ProductCrop(ModelSQL):
    "Product - Crop"
    __name__ = 'product.product-agronomics.crop'
    product = fields.Many2One('product.product', 'Product',
        ondelete='CASCADE', select=True, required=True)
    crop = fields.Many2One('agronomics.crop', 'Crop',
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


class ProductPriceListType(ModelSQL, ModelView):
    "Product Price List Type"
    __name__ = 'product.price_list.type'
    name = fields.Char("Name", required=True)


class PriceList(metaclass=PoolMeta):
    __name__ = 'product.price_list'
    product_price_list_type = fields.Many2One('product.price_list.type',
        "Product Price List Type")
