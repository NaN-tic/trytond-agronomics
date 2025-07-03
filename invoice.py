from trytond.pool import PoolMeta
from trytond.model import fields


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    product_price_list_type = fields.Many2One('product.price_list.type',
        "Product Price List Type")

    @classmethod
    def _get_origin(cls):
        return ['agronomics.weighing']

