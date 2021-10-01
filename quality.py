# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
from trytond.model import fields, Model
from trytond.modules.agronomics.wine import _WINE_DIGITS


class QualityTest(metaclass=PoolMeta):
    __name__ = 'quality.test'

    @classmethod
    def confirmed(cls, tests):
        pool = Pool()
        Product = pool.get('product.product')
        ModelData = pool.get('ir.model.data')
        Date = pool.get('ir.date')

        super(QualityTest, cls).confirmed(tests)

        today = Date.today()

        # get all key from ir.model.data
        to_write = []
        proof_ids = []
        for test in tests:
            if not test.document or not isinstance(test.document, Product):
                continue

            proof_ids += [line.proof for line in test.quantitative_lines
                                    if line.proof]
        if not proof_ids:
            return

        datas = ModelData.search([
            ('module', '=', 'agronomics'),
            ('db_id', 'in', proof_ids),
            ('model', '=', 'quality.proof')
            ])
        data_key = dict((x.db_id, x.fs_id) for x in datas)

        # check all quantitative lines has key and update the product
        for test in tests:
            if not test.document or not isinstance(test.document, Product):
                continue

            values = {}
            for line in test.quantitative_lines:
                key = data_key.get(line.proof.id)
                if not key:
                    continue

                values[key] = round(line.value, _WINE_DIGITS)
                values[key + '_comment'] = line.internal_description
                values[key + '_confirm'] = today
                values[key + '_success'] = line.success

            if values:
                to_write.extend(([test.document], values))

        if to_write:
            Product.write(*to_write)


class TestLineMixin(Model):
    __slots__ = ()
    product = fields.Function(fields.Many2One('product.product', 'Product', select=True),
        'get_product', searcher='search_product')

    def get_product(self, name):
        Product = Pool().get('product.product')
        if isinstance(self.test.document, Product):
            return self.test.document.id

    @classmethod
    def search_product(cls, name, clause):
        Product = Pool().get('product.product')

        _, operator, value = clause[0:3]
        if isinstance(value, list):
            values = [('%s,%s' % ('product.product',
                v.id if isinstance(v, Product) else v)) for v in value]
        else:
            values = '%s,%s' % ('product.product',
                value.id if isinstance(value, Product) else value)
        return [('test.document', operator, values)]


class QuantitativeTestLine(TestLineMixin, metaclass=PoolMeta):
    __name__ = 'quality.quantitative.test.line'


class QualitativeTestLine(TestLineMixin, metaclass=PoolMeta):
    __name__ = 'quality.qualitative.test.line'
