# This file is part carviresa module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import plot

def register():
    Pool.register(
        plot.Enclosure,
        plot.Crop,
        plot.DenominationOrigin,
        plot.MaxProductionAllowed,
        plot.Irrigation,
        plot.Plantation,
        plot.Ecological,
        plot.Parcel,
        plot.Beneficiaries,
        module='agronomics', type_='model')
    Pool.register(
        module='agronomics', type_='wizard')
    Pool.register(
        module='agronomics', type_='report')
