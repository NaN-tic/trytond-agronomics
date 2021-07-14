# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
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

        # get all key from ir.model.data
        to_write = []
        proof_templates = []
        for test in tests:
            if not test.document or test.document.__name__ != 'product.product':
                continue

            proof_templates += [line.proof.template
                                    for line in test.quantitative_lines
                                        if line.proof and line.proof.template]

        datas = ModelData.search([
            ('module', '=', 'agronomics'),
            ('db_id', 'in', [pt.id for pt in proof_templates]),
            ('model', '=', 'quality.proof.template')
            ])
        data_key = dict((x.db_id, x.fs_id) for x in datas)

        # check all quantitative lines has key and update the product
        for test in tests:
            if not test.document or test.document.__name__ != 'product.product':
                continue

            values = {}
            for line in test.quantitative_lines:
                if not line.proof.template:
                    continue

                key = data_key.get(line.proof.template.id)
                if not key:
                    continue

                values[key] = round(line.value, _WINE_DIGITS)
                values[key + '_comment'] = line.internal_description

            if values:
                values['wine_quality_confirm'] = Date.today()
                values['wine_quality_success'] = test.success

                to_write.extend(([test.document], values))

        if to_write:
            Product.write(*to_write)
