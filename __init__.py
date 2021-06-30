# This file is part carviresa module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import party
from . import plot
from . import product


def register():
    Pool.register(
        party.Party,
        plot.Enclosure,
        plot.Crop,
        plot.DenominationOrigin,
        plot.MaxProductionAllowed,
        plot.Irrigation,
        plot.Plantation,
        plot.Ecological,
        plot.Parcel,
        plot.ParcelDo,
        plot.Beneficiaries,
        product.Certification,
        product.Container,
        product.Product,
        product.ProductCrop,
        product.ProductDO,
        product.ProductVariety,
        product.Template,
        module='agronomics', type_='model')
    Pool.register(
        module='agronomics', type_='wizard')
    Pool.register(
        module='agronomics', type_='report')
