# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval


class WineAgingHistory(ModelSQL, ModelView):
    'Wine Aging History'
    __name__ = 'wine.wine_aging.history'
    production = fields.Many2One('production', "Production",
        required=True, readonly=True)
    location = fields.Many2One('stock.location', "Location", required=True,
        readonly=True)
    product = fields.Many2One('product.product', "Product", required=True,
        readonly=True)
    material = fields.Many2One('stock.location.material', "Material",
        readonly=True)
    date_start = fields.Date("Date Start", required=True, readonly=True)
    date_end = fields.Date("Date End", readonly=True,
        domain=[
                ['OR',
                    ('date_end', '=', None),
                    ('date_end', '>=', Eval('date_start')),
                    ],
                ],
        depends=['date_start'])
    duration = fields.Function(fields.Integer("Duration"),
        'get_duration')

    @classmethod
    def get_duration(cls, records, name):
        res = dict((x.id, None) for x in records)
        for record in records:
            if record.date_end:
                res[record.id] = (record.date_end - record.date_start).days
        return res

    @classmethod
    def delete(cls, records):
        pass
