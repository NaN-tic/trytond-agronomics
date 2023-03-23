# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from sql.aggregate import Sum
from trytond.model import fields, ModelSQL, ModelView
from trytond.pool import Pool
from trytond.wizard import (Wizard, StateView, Button, StateTransition)


class Enclosure(ModelSQL, ModelView):
    "Enclosure"
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
    "Crop"
    __name__ = 'agronomics.crop'

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)

    def copy_parcels(self, next_crop):
        pool = Pool()
        Parcel = pool.get('agronomics.parcel')
        parcels = Parcel.search([('crop' ,'=', self.id)])
        Parcel.copy(parcels, {'crop': next_crop})


class DenominationOrigin(ModelSQL, ModelView):
    "Denomination of Origin"
    __name__ = 'agronomics.denomination_of_origin'

    name = fields.Char('Name', required=True)


class MaxProductionAllowed(ModelSQL, ModelView):
    "Max Production Allowed"
    __name__ = 'agronomics.max.production.allowed'

    crop = fields.Many2One('agronomics.crop', 'Crop', required=True)
    product = fields.Many2One('product.product', 'Product', required=True)
    denomination_origin = fields.Many2One('agronomics.denomination_of_origin',
        'Denomination of Origin', required=True)
    variety = fields.Many2One('product.taxon', 'Variety',
        domain=[('rank', '=', 'variety')], required=True,
        depends=['variety'])
    max_production = fields.Numeric('Max Production (kg/ha)', required=True)


class Irrigation(ModelSQL, ModelView):
    "Irrigation"
    __name__ = 'agronomics.irrigation'

    name = fields.Char('Name', required=True)


class Plantation(ModelSQL, ModelView):
    "Plantation"
    __name__ = 'agronomics.plantation'

    code = fields.Char("Code", required=True)
    party = fields.Many2One('party.party', "Party", required=True)
    enclosures = fields.One2Many('agronomics.enclosure', 'plantation',
        "Enclosure")
    parcels = fields.One2Many('agronomics.parcel', 'plantation', "Parcel")
    plantation_year = fields.Integer("Plantation Year")
    plantation_owner = fields.Many2One('party.party', "Plantation Owner")
    varieties = fields.Function(fields.Char('Varieties'), 'get_varieties',
        searcher='search_varieties')
    do = fields.Function(fields.Char('DO'), 'get_do', searcher='search_do')
    remaining_quantity = fields.Function(
        fields.Float("Remainig Quantity", digits=(16, 2)),
        'get_remaining_quantity', searcher='search_remaining_quantity')

    def get_rec_name(self, name):
        if self.code:
            return self.code
        return self.name

    def get_do(self, name):
        do = []
        for y in self.parcels:
            do += [x.name for x in y.denomination_origin]
        return ",".join(list(set(do)))

    def get_varieties(self, name):
        if not self.parcels:
            return []
        varieties = [y.variety.name for y in self.parcerls if y.variety]
        return ",".join(list(set(varieties)))

    def get_remaining_quantity(self, name):
        return sum([y.remaining_quantity or 0 for y in self.parcels])

    @classmethod
    def search_varieties(cls, name, clause):
        pool = Pool()
        Variety = pool.get('product.taxon')
        Parcel = pool.get('agronomics.parcel')

        variety = Variety.__table__()
        parcel = Parcel.__table__()
        Operator = fields.SQL_OPERATORS[clause[1]]
        query = parcel.join(variety, condition=parcel.variety == variety.id)
        _, operator, value = clause
        query = query.select(parcel.plantation)
        query.where = Operator(variety.name, value)
        return [('id', 'in', query)]

    @classmethod
    def search_do(cls, name, clause):
        pool = Pool()
        DO = pool.get('agronomics.denomination_of_origin')
        PARCEL_DO = pool.get('agronomics.parcel-agronomics.do')
        Parcel = pool.get('agronomics.parcel')

        do = DO.__table__()
        parcel = Parcel.__table__()
        parcel_do = PARCEL_DO.__table__()
        Operator = fields.SQL_OPERATORS[clause[1]]
        query = parcel.join(parcel_do, condition=parcel.id == parcel_do.parcel)
        query = query.join(do, condition=parcel_do.do==parcel_do.do)
        _, operator, value = clause
        query = query.select(parcel.plantation)
        query.where = Operator(do.name, value)
        return [('id', 'in', query)]

    @classmethod
    def search_remaining_quantity(cls, name, clause):
        pool = Pool()
        PARCEL_DO = pool.get('agronomics.parcel-agronomics.do')
        Parcel = pool.get('agronomics.parcel')
        Weighing = pool.get('agronomics.weighing-agronomics.parcel')
        MaxProductionAllowed = pool.get('agronomics.max.production.allowed')
        parcel = Parcel.__table__()
        parcel_do = PARCEL_DO.__table__()
        weighing = Weighing.__table__()
        max_production = MaxProductionAllowed.__table__()

        _, operator, value = clause
        Operator = fields.SQL_OPERATORS[operator]

        join1 = weighing.join(parcel, type_='RIGHT',
            condition=((weighing.parcel==parcel.id) &
                (weighing.table != True)))
        join2 = join1.join(parcel_do, type_= 'LEFT',
            condition=parcel.id==parcel_do.parcel)
        join3 = join2.join(max_production, type_='LEFT',
                condition=((max_production.crop == parcel.crop) &
                    (max_production.variety == parcel.variety)))
        query2 = join3.select(parcel.plantation,
            Sum(max_production.max_production*parcel.surface -
                weighing.netweight).as_('remaining_quantity'),
            group_by=parcel.plantation)
        query = query2.select(query2.plantation)
        query.where = Operator(query2.remaining_quantity, value)
        return [('id' , 'in', query)]


class Ecological(ModelSQL, ModelView):
    "Ecological"
    __name__ = 'agronomics.ecological'

    name = fields.Char('Name', required=True)


class Parcel(ModelSQL, ModelView):
    "Parcel"
    __name__ = 'agronomics.parcel'

    plantation = fields.Many2One('agronomics.plantation', 'Plantation',
        required=True)
    crop = fields.Many2One('agronomics.crop', 'Crop', required=True)
    product = fields.Many2One('product.template', 'Product') #, required=True)
    species = fields.Many2One('product.taxon', 'Spices',
        domain=[('rank', '=', 'species')], required=True,
        depends=['species'])
    variety = fields.Many2One('product.taxon', 'Variety',
        domain=[('rank', '=', 'variety')], required=True,
        depends=['variety'])
    ecological = fields.Many2One('agronomics.ecological', 'Ecological')
    denomination_origin = fields.Many2Many('agronomics.parcel-agronomics.do',
        'parcel', 'do', 'Denomination of Origin')
    table = fields.Boolean('Table')
    premium = fields.Boolean('Premium')
    plant_number = fields.Integer('Plant number')
    surface = fields.Float('Surface', digits=(16, 2), required=True)
    producer = fields.Many2One('party.party', 'Party')
    irrigation = fields.Many2One('agronomics.irrigation', 'Irrigation')
    max_production = fields.Function(fields.Float("Max Production",
        digits=(16, 2)), 'get_max_production')
    tenure_regime = fields.Char('Teneru Regime')
    beneficiaries = fields.One2Many('agronomics.beneficiary', 'parcel',
        'Beneficiaries')
    all_do = fields.Function(fields.Char('All DO'), 'get_all_do')
    weighings = fields.One2Many('agronomics.weighing-agronomics.parcel',
        'parcel', 'Weighings')
    purchased_quantity = fields.Function(
        fields.Float("Bought Quantity", digits=(16, 2)),
        'get_purchased_quantity')
    remaining_quantity = fields.Function(
        fields.Float("Remainig Quantity", digits=(16, 2)),
        'get_remaining_quantity')

    def get_rec_name(self, name):
        if self.plantation and self.crop:
            return self.plantation.code + ' - ' + self.crop.rec_name

    def get_all_do(self, name):
        return ",".join([x.name for x in self.denomination_origin])

    def get_max_production(self, name):
        MaxProduction = Pool().get('agronomics.max.production.allowed')
        max_production = MaxProduction.search([('crop', '=', self.crop.id),
            ('variety', '=', self.variety.id), ('denomination_origin', 'in',
                self.denomination_origin)])
        if not max_production:
            return None
        return round(float(min([x.max_production for x in max_production])
            )*self.surface, 2)

    def get_purchased_quantity(self, name):
        return sum([(w.netweight or 0) for w in self.weighings if not w.table])

    def get_remaining_quantity(self, name):
        return (self.max_production or 0) - (self.purchased_quantity or 0)


class ParcelDo(ModelSQL):
    "Parcel - Denomination Origin"
    __name__ = 'agronomics.parcel-agronomics.do'

    parcel = fields.Many2One('agronomics.parcel', 'Parcel')
    do = fields.Many2One('agronomics.denomination_of_origin',
        'Denomination Origin')


class Beneficiaries(ModelSQL, ModelView):
    "Beneficiaries"
    __name__ = 'agronomics.beneficiary'

    party = fields.Many2One('party.party', "Beneficiary", required=True)
    parcel = fields.Many2One('agronomics.parcel', "Parcel")
    weighing = fields.Many2One('agronomics.weighing', "Weighing")
    product_price_list_type = fields.Many2One('product.price_list.type',
        "Product Price List Type")

    @classmethod
    def __register__(cls, module_name):
        table = cls.__table_handler__(module_name)

        # Migration from #047773
        if table.column_exist('percent'):
            table.not_null_action('percent', 'remove')
            table.drop_column('percent')

        super(Beneficiaries, cls).__register__(module_name)


class CreateNewParcels(Wizard):
    'New Version'
    __name__ = 'agronomics.create_new_parcels'

    start = StateView('agronomics.create_new_parcels.start',
        'agronomics.create_new_parcels_start_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'copy_parcels', 'tryton-accept', default=True),
            ])
    copy_parcels = StateTransition()

    def transition_copy_parcels(self):
        crop = self.start.previous_crop
        crop.copy_parcels(self.start.next_crop)
        return 'end'


class CreateNewParcelsStart(ModelView):
    "Create New Parcels - Start"
    __name__ = 'agronomics.create_new_parcels.start'

    previous_crop = fields.Many2One('agronomics.crop', "Previous Crop",
        required=True)
    next_crop = fields.Many2One('agronomics.crop', "Next Crop",
        required=True)
