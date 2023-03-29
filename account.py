# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields
from trytond.pool import PoolMeta


class Statement(metaclass=PoolMeta):
    __name__ = 'account.statement'

    @fields.depends('journal', 'state', 'lines', 'number_of_lines',
        'total_amount')
    def on_change_journal(self):
        super().on_change_journal()
        if not self.journal:
            return
        if (self.journal.validation == 'amount' and not self.total_amount):
            self.total_amount = Decimal(0)
        elif (self.journal.validation == 'number_of_lines' and not
                self.number_of_lines):
            self.number_of_lines = 0
        else:
            return
