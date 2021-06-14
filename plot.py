# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView


class Enclosure(ModelSQL, ModelView):
    """ Enclosure """
    __name__ = 'agronomics.enclosure'

    aggregate_sigpac = fields.Numeric('Aggragate Sigpac')
    municipality_sigpac = fields.Numeric('Municipality Sigpac')
    parcel_sigpac = fields.Numeric('Parcel Sigpac')
    province_sigpac = fields.Numeric('Province Sigpac')
    enclosure_sigpac = fields.Numeric('Enclosure Sigpac')
    polygon_sigpac = fields.Numeric('Polygon Sigpac')
    zone_sigpac = fields.Numeric('Zone Sigpac')
    surface_sigpac = fields.Numeric('Surface Sigpac')
    plantation = fields.Many2One('agronomics.plantation', 'Plantation')

class Crop(ModelSQL, ModelView):
    """ Crop """
    __name__ = 'agronomics.crop'

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)


class DenominationOrigin(ModelSQL, ModelView):
    """ Denomination Of Origin """
    __name__ = 'agronomics.denomination_of_origin'

    name = fields.Char('Name', required=True)


class MaxProductionAllowed(ModelSQL, ModelView):
    """ Max Production Allowed """
    __name__ = 'agronomics.max.production.allowed'

    crop = fields.Many2One('agronomics.crop', 'Crop', required=True)
    product = fields.Many2One('product.product', 'Product', required=True)
    denomination_origin = fields.Many2One('agronomics.denomination_of_origin',
        'Denomination of Origin', required=True)
    variety = fields.Many2One('product.taxon', 'Variety',
        domain=[('rank', '=', 'variety')], required=True,
        depends=['variety'])
    max_production = fields.Numeric('Max Production (kg/ha)')


class Irrigation(ModelSQL, ModelView):
    """ Irrigation """
    __name__ = 'agronomics.irrigation'

    name = fields.Char('Name', required=True)

class Plantation(ModelSQL, ModelView):
    """ Plantation """
    __name__ = 'agronomics.plantation'

    code = fields.Char('Code', required=True)
    party = fields.Many2One('party.party', 'Party', required=True)
    enclosures = fields.One2Many('agronomics.enclosure', 'plantation',
        'Enclosure')
    parcels = fields.One2Many('agronomics.parcel', 'plantation', 'Parcel')


class Ecological(ModelSQL, ModelView):
    """ Ecological """
    __name__ = 'agronomics.ecological'

    name = fields.Char('Name', required=True)


class Parcel(ModelSQL, ModelView):
    """ Parcel """
    __name__ = 'agronomics.parcel'

    plantation = fields.Many2One('agronomics.plantation', 'Plantation',
        required=True)
    crop = fields.Many2One('agronomics.crop', 'Crop', required=True)
    variety = fields.Many2One('product.taxon', 'Variety',
        domain=[('rank', '=', 'variety')], required=True,
        depends=['variety'])
    species = fields.Many2One('product.taxon', 'Spices',
        domain=[('rank', '=', 'species')], required=True,
        depends=['species'])
    ecological = fields.Many2One('agronomics.ecological', 'Ecological')
    denomination_origin = fields.Many2One('agronomics.denomination_of_origin',
        'Denomination of Origin', required=True)
    table = fields.Boolean('Table')
    premium = fields.Boolean('Premium')
    plant_number = fields.Integer('Plant number')
    surface = fields.Float('Surface', digits=(16, 2))
    producer = fields.Many2One('party.party', 'Party')
    irrigation = fields.Many2One('agronomics.irrigation', 'Irrigation')
    max_production = fields.Many2One('agronomics.max.production.allowed',
        'Max Production')
    tenure_regime = fields.Text('Teneru Regime')
    beneficiaries = fields.One2Many('agronomics.beneficiary', 'parcel',
        'Beneficiaries')

class Beneficiaries(ModelSQL, ModelView):
    """ Beneficiaries """
    __name__ = 'agronomics.beneficiary'

    party = fields.Many2One('party.party', 'Beneficiary', required=True)
    percent = fields.Float('Percent', digits=(16, 2), required=True)
    parcel = fields.Many2One('agronomics.parcel', 'Parcel', required=True)
