# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
from trytond.i18n import gettext
from trytond.exceptions import UserError
from trytond.transaction import Transaction


class Move(metaclass=PoolMeta):
    __name__ = 'stock.move'

    @classmethod
    def validate(cls, moves):
        pool = Pool()
        Product = pool.get('product.product')
        super(Move, cls).validate(moves)
        for move in moves:
            if move.to_location.tank:
                #Same unit move and to location
                if move.uom != move.to_location.uom:
                    raise UserError(gettext(
                        'agronomics.msg_move_unit_not_match'))
                #Do not exceed the amount
                context = Transaction().context
                with Transaction().set_context(context):
                    location_quantity = sum(Product.products_by_location(
                            [move.to_location.id]).values())
                if (move.to_location.max_capacity
                        and (location_quantity > move.to_location.max_capacity)):
                    raise UserError(gettext(
                            'agronomics.msg_move_amount_exceed'))
