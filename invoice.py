from trytond.report import Report
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.model import fields
from trytond.pyson import Eval, Bool
from decimal import Decimal


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    product_price_list_type = fields.Many2One('product.price_list.type',
        "Product Price List Type")
