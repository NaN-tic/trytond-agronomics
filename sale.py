# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta, Pool


class WizardAddProduct(metaclass=PoolMeta):
    __name__ = 'sale_pos.add_product'

    def transition_scan_(self):
        pool = Pool()
        Product = pool.get('product.product')

        def qty(value):
            try:
                return float(value)
            except ValueError:
                return False

        product = None
        value = self.start.input_value
        quantity = qty(value)
        if len(value) > 4:
            quantity = None

        if not quantity:
            domain = [('salable', '=', True),
            ['OR', ('code','=', value),
                ('identifiers.code', '=', value),
                ('name', 'like', '%'+value+'%'),
                ('name', 'like', '%'+value.upper()+'%'),
                ('name', 'like', '%'+value.capitalize()+'%'),
                ('name', 'like', '%'+value.lower()+'%'),]]
            products = Product.search(domain)
            if not products:
                return 'start'

            if len(products) > 1:
                self.choose.products = [x.id for x in products]
                return 'choose'

            product,  = products

            self.start.last_product = product

        if quantity and self.start.last_product:
            product = self.start.last_product

        if not product:
            return 'start'

        lines = self.add_sale_line(self.start.lines, product, quantity)
        self.start.lines = lines
        self.add_lines()
        return 'start'
