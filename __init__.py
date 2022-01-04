# This file is part agronomics module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import party
from . import plot
from . import product
from . import weighing
from . import quality
from . import production
from . import location
from . import move

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
        product.ProductEcological,
        product.ProductVariety,
        product.Template,
        weighing.WeighingCenter,
        weighing.Weighing,
        weighing.WeighingPlantation,
        weighing.WeighingDo,
        quality.QualityTest,
        quality.QuantitativeTestLine,
        quality.QualitativeTestLine,
        production.ProductionTemplate,
        production.ProductionTemplateLine,
        production.ProductionTemplateInputsProductTemplate,
        production.ProductionTemplateOutputsProductTemplate,
        production.Production,
        production.OutputDistribution,
        production.ProductionEnologyProduct,
        production.ProductionCostPriceDistribution,
#        production.ProductionProductionCostPriceDistribution,
        production.ProductionCostPriceDistributionTemplate,
        production.ProductionCostPriceDistributionTemplateProductionTemplateAsk,
        location.LocationMaterial,
        location.Location,
        move.Move,
        module='agronomics', type_='model')
    Pool.register(
        production.ProductionCostPriceDistributionTemplateProductionTemplate,
        module='agronomics', type_='wizard')
    Pool.register(
        module='agronomics', type_='report')
