from types import SimpleNamespace

from proteus import Model
from trytond.tests.tools import activate_modules


def setup():
    config = activate_modules('agronomics')

    Uom = Model.get('product.uom')
    Template = Model.get('product.template')
    kilogram, = Uom.find([('name', '=', 'Kilogram')])
    template = Template(
        name='Producible Product',
        default_uom=kilogram,
        type='goods',
        producible=True)
    template.save()
    product, = template.products

    return SimpleNamespace(
        config=config,
        product=product,
        template=template,
        template_model=config.pool.get('product.template'))
