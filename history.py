# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from sql import Literal, Null
from sql.aggregate import Min, Sum
from sql.functions import CurrentTimestamp
from trytond.pool import Pool
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval
from trytond.transaction import Transaction


class WineAgingHistory(ModelSQL, ModelView):
    'Wine Aging History'
    __name__ = 'wine.wine_aging.history'
    production = fields.Many2One('production', "Production",
        required=True, readonly=True)
    location = fields.Many2One('stock.location', "Location", required=True,
        readonly=True)
    product = fields.Many2One('product.product', "Product", readonly=True)
    lot = fields.Many2One('stock.lot', "Lot", readonly=True)
    material = fields.Many2One('stock.location.material', "Material",
        readonly=True)
    date_start = fields.Date("Date Start", required=True, readonly=True)
    date_end = fields.Date("Date End", readonly=True,
        domain=[
                ['OR',
                    ('date_end', '=', None),
                    ('date_end', '>=', Eval('date_start')),
                    ],
                ])
    duration = fields.Integer("Duration")

    @classmethod
    def delete(cls, records):
        pass


class ProductWineAgingHistory(ModelSQL, ModelView):
    "Product Wine Aging History"
    __name__ = 'product.wine.wine_aging.history'

    product = fields.Many2One('product.product', "Product")
    material = fields.Many2One('stock.location.material', "Material")
    duration = fields.Integer("Duration")

    @classmethod
    def table_query(cls):
        pool = Pool()
        WineAgingHistory = pool.get('wine.wine_aging.history')

        wine_aging_history = WineAgingHistory.__table__()

        product_id = Transaction().context.get('product')
        sql_where = None
        if product_id:
            sql_where = (wine_aging_history.product == product_id)

        query = wine_aging_history.select(
            (Min(wine_aging_history.id * 2)).as_('id'),
            Literal(0).as_('create_uid'),
            CurrentTimestamp().as_('create_date'),
            cls.write_uid.sql_cast(Literal(Null)).as_('write_uid'),
            cls.write_date.sql_cast(Literal(Null)).as_('write_date'),
            wine_aging_history.product.as_('product'),
            wine_aging_history.material.as_('material'),
            Sum(wine_aging_history.date_end - wine_aging_history.date_start).as_('duration'),
            group_by=[wine_aging_history.product, wine_aging_history.material])
        if sql_where:
            query.where = sql_where

        return query


class LotWineAgingHistory(ModelSQL, ModelView):
    "Lot Wine Aging History"
    __name__ = 'stock.lot.wine_aging.history'

    lot = fields.Many2One('stock.lot', "Lot")
    material = fields.Many2One('stock.location.material', "Material")
    duration = fields.Integer("Duration")

    @classmethod
    def table_query(cls):
        pool = Pool()
        WineAgingHistory = pool.get('wine.wine_aging.history')

        wine_aging_history = WineAgingHistory.__table__()

        lot_id = Transaction().context.get('lot')
        sql_where = (wine_aging_history.lot != Null)
        if lot_id:
            sql_where &= (wine_aging_history.lot == lot_id)

        return wine_aging_history.select(
            (Min(wine_aging_history.id * 2)).as_('id'),
            Literal(0).as_('create_uid'),
            CurrentTimestamp().as_('create_date'),
            cls.write_uid.sql_cast(Literal(Null)).as_('write_uid'),
            cls.write_date.sql_cast(Literal(Null)).as_('write_date'),
            wine_aging_history.lot.as_('lot'),
            wine_aging_history.material.as_('material'),
            Sum(wine_aging_history.date_end
                - wine_aging_history.date_start).as_('duration'),
            where=sql_where,
            group_by=[wine_aging_history.lot,
                wine_aging_history.material])
