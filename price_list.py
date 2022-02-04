# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta, Pool


class PriceList(metaclass=PoolMeta):
    __name__ = 'product.price_list'

    def get_context_formula(self, party, product, unit_price, quantity, uom,
            pattern=None):
        pool = Pool()
        Product = pool.get('product.product')
        res = super().get_context_formula(party, product, unit_price, quantity,
            uom, pattern)

        if not product:
            product, = Product.search([], limit=1)

        res['names']['ecological'] = None
        if hasattr(product, 'ecologicals'):
            ecologicals = None
            if len(product.ecologicals) == 1:
                ecologicals = product.ecologicals[0].name
            res['names']['ecological'] = ecologicals

        res['names']['variety'] = None
        if hasattr(product, 'varieties'):
            varieties = None
            if len(product.varieties) == 1:
                varieties = product.varieties[0].variety.name
            res['names']['variety'] = varieties

        res['names']['do'] = None
        if hasattr(product, 'denominations_of_origin'):
            dos = []
            for do in product.denominations_of_origin:
                dos.append(do.name)
            res['names']['do'] = dos

        res['names']['vintages'] = None
        if hasattr(product, 'vintages'):
            vintages = None
            if len(product.vintages) == 1:
                vintages = product.vintages[0].name
            res['names']['vintages'] = vintages

        res['names']['biotritis'] = None
        if hasattr(product, 'wine_botrytis'):
            res['names']['biotritis'] = (product.wine_botrytis or 0)

        res['names']['likely_alcohol_content'] = None
        if hasattr(product, 'wine_likely_alcohol_content'):
            res['names']['likely_alcohol_content'] = (
                product.wine_likely_alcohol_content or 0)

        res['names']['ph'] = None
        if hasattr(product, 'wine_ph'):
            res['names']['ph'] = (product.wine_ph or 0)

        res['names']['tartaric_acidity'] = None
        if hasattr(product, 'wine_tartaric_acidity'):
            res['names']['tartaric_acidity'] = (product.wine_tartaric_acidity
                or 0)

        res['names']['glucose_fructose'] = None
        if hasattr(product, 'wine_glucose_fructose'):
            res['names']['glucose_fructose'] = (product.wine_glucose_fructose
                or 0)

        res['names']['overall_impression'] = None
        if hasattr(product, 'wine_overall_impression'):
            res['names']['overall_impression'] = (
                product.wine_overall_impression or 0)

        return res
