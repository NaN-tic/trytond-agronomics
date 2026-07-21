# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta, Pool


class PriceList(metaclass=PoolMeta):
    __name__ = 'product.price_list'

    def get_context_formula(self, product, quantity, uom, pattern=None):
        pool = Pool()
        Product = pool.get('product.product')

        res = super().get_context_formula(product, quantity, uom, pattern)

        lot_id = (pattern or {}).get('lot')
        lot = None
        if lot_id:
            lot = pool.get('stock.lot')(lot_id)
        if lot:
            product = lot.product
        if not product:
            product, = Product.search([], limit=1)

        res['names']['ecological'] = None
        source = lot or product
        if hasattr(source, 'ecologicals'):
            ecologicals = None
            if len(source.ecologicals) == 1:
                ecologicals = source.ecologicals[0].name
            res['names']['ecological'] = ecologicals

        res['names']['variety'] = None
        if hasattr(source, 'varieties'):
            varieties = None
            if len(source.varieties) == 1:
                varieties = source.varieties[0].variety.name
            res['names']['variety'] = varieties

        res['names']['do'] = None
        if hasattr(source, 'denominations_of_origin'):
            dos = []
            for do in source.denominations_of_origin:
                dos.append(do.name)
            res['names']['do'] = dos

        res['names']['vintages'] = None
        if hasattr(source, 'crop'):
            vintages = None
            if len(source.crop) == 1:
                vintages = source.crop[0].name
            res['names']['vintages'] = vintages

        res['names']['biotritis'] = 0
        if hasattr(source, 'wine_botrytis'):
            res['names']['biotritis'] = (source.wine_botrytis or 0)

        res['names']['likely_alcohol_content'] = 0
        if hasattr(source, 'wine_likely_alcohol_content'):
            res['names']['likely_alcohol_content'] = (
                source.wine_likely_alcohol_content or 0)

        res['names']['ph'] = 0
        if hasattr(source, 'wine_ph'):
            res['names']['ph'] = (source.wine_ph or 0)

        res['names']['tartaric_acidity'] = 0
        if hasattr(source, 'wine_tartaric_acidity'):
            res['names']['tartaric_acidity'] = (source.wine_tartaric_acidity
                or 0)

        res['names']['glucose_fructose'] = 0
        if hasattr(source, 'wine_glucose_fructose'):
            res['names']['glucose_fructose'] = (source.wine_glucose_fructose
                or 0)

        res['names']['overall_impression'] = 0
        if hasattr(source, 'wine_overall_impression'):
            res['names']['overall_impression'] = (
                source.wine_overall_impression or 0)

        return res


class PriceListLine(metaclass=PoolMeta):
    __name__ = 'product.price_list.line'

    def match(self, pattern):
        pattern = pattern.copy()
        pattern.pop('lot', None)
        return super().match(pattern)
