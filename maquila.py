from trytond.model import (Workflow, ModelSingleton, ModelView, ModelSQL,
    fields, sequence_ordered)
from trytond.pyson import Id, If, Eval, Bool
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.modules.company.model import (
    CompanyMultiValueMixin, CompanyValueMixin)
from trytond.i18n import gettext
from trytond.exceptions import UserError


def default_func(field_name):
    @classmethod
    def default(cls, **pattern):
        return getattr(
            cls.multivalue_model(field_name),
            'default_%s' % field_name, lambda: None)()
    return default


class Configuration(ModelSingleton, ModelSQL, ModelView, CompanyMultiValueMixin):
    "Maquila Configuration"
    __name__ = 'agronomics.maquila.configuration'
    contract_sequence = fields.MultiValue(fields.Many2One(
            'ir.sequence', "Contract Sequence", required=True,
            domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('sequence_type', '=', Id('agronomics', 'sequence_type_maquila_contract')),
                ]))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'contract_sequence':
            return pool.get('agronomics.maquila.configuration.sequence')
        return super(Configuration, cls).multivalue_model(field)

    default_contract_sequence = default_func('contract_sequence')


class ConfigurationSequence(ModelSQL, CompanyValueMixin):
    "Maquila Configuration Sequence"
    __name__ = 'agronomics.maquila.configuration.sequence'
    contract_sequence = fields.Many2One(
        'ir.sequence', "Contract Sequence", required=True,
        domain=[
            ('company', 'in', [Eval('company', -1), None]),
            ('sequence_type', '=', Id('agronomics', 'sequence_type_maquila_contract')),
            ],
        depends=['company'])

    @classmethod
    def default_contract_sequence(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('agronomics', 'sequence_maquila_contract')
        except KeyError:
            return None


class Contract(sequence_ordered(), Workflow, ModelSQL, ModelView):
    "Maquila Contract"
    __name__ = 'agronomics.maquila.contract'
    _rec_name = 'number'
    company = fields.Many2One(
        'company.company', "Company", required=True, select=True,
        states={
            'readonly': (
                (Eval('state') != 'draft')
                | Eval('product_crops', [0])
                | Eval('product_percentages', [0])
                | Eval('product_years', [0])
                | Eval('party', True)),
            },
        depends=['state'])
    number = fields.Char('Number', readonly=True, select=True)
    reference = fields.Char('Reference')
    party = fields.Many2One('party.party', "Party", required=True,
        states={
            'readonly': Eval('state') != 'draft',
            },
        context={
            'company': Eval('company', -1),
            },
        depends=['state', 'company'])
    product = fields.Many2One('product.product', "Product", required=True,
        domain=[
            ('agronomic_type', '=', 'grape'),
        ], states={
            'readonly': Eval('state') != 'draft',
            },
        context={
            'company': Eval('company', -1),
            },
        depends=['state', 'company'])
    quantity = fields.Float('Quantity', required=True,
        digits=(16, Eval('unit_digits', 2)),
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state', 'unit_digits'])
    unit = fields.Many2One('product.uom', "Unit", required=True, ondelete='RESTRICT',
        domain=[
            If(Bool(Eval('product_uom_category')),
                ('category', '=', Eval('product_uom_category')),
                ('category', '!=', -1)),
            ],
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state', 'product_uom_category'])
    unit_digits = fields.Function(fields.Integer("Unit Digits"),
        'on_change_with_unit_digits')
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', "Product Uom Category"),
        'on_change_with_product_uom_category')
    product_crops = fields.One2Many('agronomics.maquila.contract.crop',
        'contract', "Product Crops",
        states={
            'readonly': Eval('state') != 'draft',
            'required': Eval('state') == 'active',
            },
        depends=['state'])
    product_percentages = fields.One2Many('agronomics.maquila.contract.product_percentage',
        'contract', "Product Percentatges",
        states={
            'readonly': Eval('state') != 'draft',
            'required': Eval('state') == 'active',
            },
        depends=['state'])
    table = fields.Boolean("Table",
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])
    state = fields.Selection([
            ('draft', "Draft"),
            ('active', "Active"),
            ('done', "Done"),
            ('cancelled', "Cancelled"),
            ], "State", readonly=True, required=True)

    @classmethod
    def __setup__(cls):
        super(Contract, cls).__setup__()
        cls._order = [
            ('number', 'DESC NULLS FIRST'),
            ('id', 'DESC'),
            ]
        cls._transitions |= set((
                ('draft', 'active'),
                ('draft', 'cancelled'),
                ('active', 'done'),
                ('cancelled', 'draft'),
                ))
        cls._buttons.update({
            'draft': {
                'invisible': Eval('state') != 'cancelled',
                'icon': If(Eval('state') == 'cancelled', 'tryton-undo',
                        'tryton-back'),
            },
            'active': {
                'invisible': Eval('state') != 'draft',
                'icon': 'tryton-forward',
                },
            'cancel': {
                'invisible': Eval('state') != 'draft',
                'icon': 'tryton-cancel',
                },
            'done': {
                'invisible': Eval('state') != 'active',
                'icon': 'tryton-ok',
                },
            })

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    def get_rec_name(self, name):
        items = []
        if self.number:
            items.append(self.number)
        if self.reference:
            items.append('[%s]' % self.reference)
        if not items:
            items.append('(%s)' % self.id)
        return ' '.join(items)

    @classmethod
    def search_rec_name(cls, name, clause):
        _, operator, value = clause
        if operator.startswith('!') or operator.startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        domain = [bool_op,
            ('number', operator, value),
            ('reference', operator, value),
            ]
        return domain

    @classmethod
    def copy(cls, contracts, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('number', None)
        default.setdefault('product_years', None)
        default.setdefault('maquilas', None)
        return super(Contract, cls).copy(contracts, default=default)

    @classmethod
    def delete(cls, contracts):
        # Cancel before delete
        cls.cancel(contracts)
        for contract in contracts:
            if contract.state != 'cancelled':
                raise AccessError(
                    gettext('agronomics.msg_contract_delete_cancel',
                        contract=contract.rec_name))
        super(Contract, cls).delete(contracts)

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if self.unit:
            return self.unit.digits
        return 2

    @fields.depends('product', 'unit')
    def on_change_product(self):
        if not self.product:
            return

        category = self.product.default_uom.category
        if not self.unit or self.unit.category != category:
            self.unit = self.product.default_uom
            self.unit_digits = self.product.default_uom.digits

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, contracts):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, contracts):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('active')
    def active(cls, contracts):
        for contract in contracts:
            contract.check_quantity()
            contract.create_contract_product_year()
            contract.create_maquila()
        cls.set_number(contracts)

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, contracts):
        pass

    @classmethod
    def set_number(cls, contracts):
        '''
        Fill the number field with the contracts sequence
        '''
        pool = Pool()
        Config = pool.get('agronomics.maquila.configuration')

        config = Config(1)
        for contract in contracts:
            if contract.number:
                continue
            contract.number = config.get_multivalue(
                'contract_sequence', company=contract.company.id).get()
        cls.save(contracts)

    def check_quantity(self):
        if sum(x.quantity for x in self.product_crops) != self.quantity:
            raise UserError(gettext('agronomics.msg_maquila_contract_quantity',
                contract=self.rec_name))

    def create_contract_product_year(self):
        MaquilaProductYear = Pool().get('agronomics.maquila.product_year')

        crops = set()
        products = set()
        for crop in self.product_crops:
            crops.add(crop.crop)
            for ppercentatge in self.product_percentages:
                products.add(ppercentatge.product)

        records = MaquilaProductYear.search([
            ('party', '=', self.party),
            ('crop', 'in', crops),
            ('product', 'in', products),
            ])
        product_years = dict(((x.party, x.crop, x.product), x) for x in records)

        new_product_years = []
        for crop in self.product_crops:
            for ppercentatge in self.product_percentages:
                key = (self.party, crop.crop, ppercentatge.product)
                if key in product_years:
                    product_year = product_years.get(key)
                    product_year.contract_crops += (crop,)
                    product_year.save()
                    new_product_years.append(product_year)
                else:
                    product_year = MaquilaProductYear()
                    product_year.company = self.company
                    product_year.party = self.party
                    product_year.crop = crop.crop
                    product_year.product = ppercentatge.product
                    product_year.unit = ppercentatge.product.default_uom
                    product_year.contract_crops = (crop,)
                    product_year.save()
                    new_product_years.append(product_year)
        return new_product_years

    def create_maquila(self):
        Maquila = Pool().get('agronomics.maquila')

        default_values = Maquila.default_get(Maquila._fields.keys(),
                with_rec_name=False)

        crops = set()
        products = set()
        for crop in self.product_crops:
            crops.add(crop.crop)
            products.add(self.product)

        records = Maquila.search([
            ('party', '=', self.party),
            ('crop', 'in', crops),
            ('product', 'in', products),
            ])
        maquilas = dict(((x.party, x.product, x.crop, x.table), x) for x in records)

        new_maquilas = []
        for crop in self.product_crops:
            key = (self.party, self.product, crop.crop, self.table)
            if key in maquilas:
                maquila = maquilas.get(key)
                maquila.contract_crops += (crop,)
                maquila.save()
                new_maquilas.append(maquila)
            else:
                maquila = Maquila(**default_values)
                maquila.company = self.company
                maquila.party = self.party
                maquila.crop = crop.crop
                maquila.party = self.party
                maquila.product = self.product
                maquila.unit = self.product.default_uom
                maquila.table = self.table
                maquila.contract_crops = (crop,)
                maquila.save()
                new_maquilas.append(maquila)
        return new_maquilas


class ContractCrop(ModelSQL, ModelView):
    "Maquila Contract Crop"
    __name__ = 'agronomics.maquila.contract.crop'
    contract = fields.Many2One('agronomics.maquila.contract', "Contract",
        ondelete='CASCADE', select=True, required=True)
    crop = fields.Many2One('agronomics.crop', "Crop", required=True)
    quantity = fields.Float("Quantity", digits=(16, 2), required=True)
    penality = fields.Numeric("Penality", digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'], required=True)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    product_years = fields.Many2Many(
        'agronomics.maquila.product_year-agronomics.maquila.contract.crop', 'contract_crop', 'product_year', "Product Years")
    maquilas = fields.Many2Many(
        'agronomics.maquila-agronomics.maquila.contract.crop',
        'contract_crop', 'maquila', "Maquila", readonly=True)

    def on_change_with_currency_digits(self, name=None):
        Company = Pool().get('company.company')

        company = Transaction().context.get('company')
        if company:
            return Company(company).currency.digits
        return 2


class ContractProductPercentage(ModelSQL, ModelView):
    "Maquila Contract Product Percentage"
    __name__ = 'agronomics.maquila.contract.product_percentage'
    contract = fields.Many2One('agronomics.maquila.contract', "Contract",
        ondelete='CASCADE', select=True, required=True)
    product = fields.Many2One('product.product', "Product", required=True)
    percentatge = fields.Float("Percentatge", digits=(16, 2), required=True)


class ProductYear(ModelSQL, ModelView):
    "Maquila Product Year"
    __name__ = 'agronomics.maquila.product_year'
    company = fields.Many2One(
        'company.company', "Company", required=True, select=True, readonly=True)
    party = fields.Many2One('party.party', "Party", required=True, readonly=True,
        context={
            'company': Eval('company', -1),
            },
        depends=['company'])
    crop = fields.Many2One('agronomics.crop', "Crop", required=True,
        readonly=True)
    product = fields.Many2One('product.product', "Product", required=True,
        readonly=True)
    quantity = fields.Function(fields.Float("Quantity",
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits']), 'get_quantity')
    delivered_quantity = fields.Function(fields.Float("Delivered Quantity",
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits']), 'get_delivered_quantity')
    unit = fields.Many2One('product.uom', "Unit", required=True, readonly=True,
        ondelete='RESTRICT', domain=[
            If(Bool(Eval('product_uom_category')),
                ('category', '=', Eval('product_uom_category')),
                ('category', '!=', -1)),
            ],
        depends=['product_uom_category'])
    unit_digits = fields.Function(fields.Integer("Unit Digits"),
        'on_change_with_unit_digits')
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', "Product Uom Category"),
        'on_change_with_product_uom_category')
    contract_crops = fields.Many2Many(
        'agronomics.maquila.product_year-agronomics.maquila.contract.crop',
        'product_year', 'contract_crop', "Contract Crops", readonly=True)
    contracts = fields.Function(fields.One2Many('agronomics.maquila.contract',
        None, "Contracts"), 'get_contracts', searcher='search_contracts')

    @classmethod
    def __setup__(cls):
        super(ProductYear, cls).__setup__()
        cls._order = [
            ('id', 'DESC'),
            ]

    def get_rec_name(self, name):
        items = []
        items.append(self.party.rec_name)
        items.append('[%s]' % self.crop.rec_name)
        return ' '.join(items)

    @classmethod
    def search_rec_name(cls, name, clause):
        _, operator, value = clause
        if operator.startswith('!') or operator.startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        domain = [bool_op,
            ('party', operator, value),
            ('crop', operator, value),
            ]
        return domain

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if self.unit:
            return self.unit.digits
        return 2

    @fields.depends('product', 'unit')
    def on_change_product(self):
        if not self.product:
            return

        category = self.product.default_uom.category
        if not self.unit or self.unit.category != category:
            self.unit = self.product.default_uom
            self.unit_digits = self.product.default_uom.digits

    @classmethod
    def get_quantity(cls, product_years, name):
        res = dict((x.id, 0) for x in product_years)
        for product_year in product_years:
            _sum = 0
            for crop in product_year.contract_crops:
                for ppercentatge in crop.contract.product_percentages:
                    if ppercentatge.product == product_year.product:
                        _sum += crop.quantity * ppercentatge.percentatge
            res[product_year.id] = _sum
        return res

    @classmethod
    def get_delivered_quantity(cls, product_years, name):
        pool = Pool()
        SaleLine = pool.get('sale.line')
        Uom = pool.get('product.uom')

        res = dict((x.id, 0) for x in product_years)
        for product_year in product_years:
            lines = SaleLine.search([
                ('maquila', '=', product_year),
                ('product', '=', product_year.product),
                ('sale.state', 'not in', ['cancelled', 'draft', 'quotation']),
                ])

            _sum = 0
            for line in lines:
                for move in line.moves:
                    if not move.state == 'done':
                        continue
                    _sum += Uom.compute_qty(move.uom, move.quantity, product_year.unit, False)
            res[product_year.id] = _sum
        return res

    @classmethod
    def get_contracts(cls, product_years, name):
        res = dict((x.id, None) for x in product_years)
        for product_year in product_years:
            contracts = [crop.contract.id for crop in product_year.contract_crops]
            res[product_year.id] = contracts
        return res

    @classmethod
    def search_contracts(cls, name, clause):
        return [('contract_crops.contract',) + tuple(clause[1:])]


class Maquila(ModelSQL, ModelView):
    "Maquila"
    __name__ = 'agronomics.maquila'
    company = fields.Many2One(
        'company.company', "Company", required=True, select=True, readonly=True)
    crop = fields.Many2One('agronomics.crop', "Crop", required=True, readonly=True)
    party = fields.Many2One('party.party', "Party", required=True, readonly=True,
        context={
            'company': Eval('company', -1),
            },
        depends=['company'])
    quantity = fields.Function(fields.Float("Quantity",
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits']), 'get_quantity')
    pending_quantity = fields.Function(fields.Float("Pending Quantity",
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits']), 'get_pending_quantity')
    product = fields.Many2One('product.product', "Product", required=True,
        readonly=True,
        context={
            'company': Eval('company', -1),
            },
        depends=['company'])
    unit = fields.Many2One('product.uom', "Unit", required=True, readonly=True,
        ondelete='RESTRICT', domain=[
            If(Bool(Eval('product_uom_category')),
                ('category', '=', Eval('product_uom_category')),
                ('category', '!=', -1)),
            ],
        depends=['product_uom_category'])
    unit_digits = fields.Function(fields.Integer("Unit Digits"),
        'on_change_with_unit_digits')
    product_uom_category = fields.Function(
        fields.Many2One('product.uom.category', "Product Uom Category"),
        'on_change_with_product_uom_category')
    weighings = fields.One2Many('agronomics.weighing', 'maquila',
        "Weighings", readonly=True)
    product_year = fields.Many2One('agronomics.maquila.product_year',
        "Product Year", readonly=True)
    table = fields.Boolean("Table", readonly=True)
    contract_crops = fields.Many2Many(
        'agronomics.maquila-agronomics.maquila.contract.crop',
        'maquila', 'contract_crop', "Contract Crops", readonly=True)
    contracts = fields.Function(fields.One2Many('agronomics.maquila.contract',
        None, "Contracts"), 'get_contracts', searcher='search_contracts')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def __setup__(cls):
        super(Maquila, cls).__setup__()
        cls._order = [
            ('id', 'DESC'),
            ]

    def get_rec_name(self, name):
        items = []
        items.append(self.party.rec_name)
        items.append('[%s]' % self.crop.rec_name)
        return ' '.join(items)

    @classmethod
    def search_rec_name(cls, name, clause):
        _, operator, value = clause
        if operator.startswith('!') or operator.startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        domain = [bool_op,
            ('party', operator, value),
            ('crop', operator, value),
            ]
        return domain

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if self.unit:
            return self.unit.digits
        return 2

    @classmethod
    def get_quantity(cls, maquilas, name):
        res = dict((x.id, 0) for x in maquilas)
        for maquila in maquilas:
            _sum = 0
            for crop in maquila.contract_crops:
                if crop.contract.product == maquila.product:
                    _sum += crop.quantity
            res[maquila.id] = _sum
        return res

    @classmethod
    def get_pending_quantity(cls, maquilas, name):
        pool = Pool()
        Weighing = pool.get('agronomics.weighing')
        Uom = pool.get('product.uom')

        res = dict((x.id, 0) for x in maquilas)
        for maquila in maquilas:
            weighings = Weighing.search([
                ('maquila', '=', maquila),
                ('product', '=', maquila.product),
                ('state', '=', 'done'),
                ])

            _sum = 0
            for weighing in weighings:
                move = weighing.inventory_move
                if move:
                    _sum += Uom.compute_qty(move.uom, move.quantity, maquila.unit, False)
            res[maquila.id] = maquila.quantity - _sum
        return res

    @classmethod
    def get_contracts(cls, maquilas, name):
        res = dict((x.id, None) for x in maquilas)
        for maquila in maquilas:
            contracts = [crop.contract.id for crop in maquila.contract_crops]
            res[maquila.id] = contracts
        return res

    @classmethod
    def search_contracts(cls, name, clause):
        return [('contract_crops.contract',) + tuple(clause[1:])]


class MaquilaProductYearContractCrop(ModelSQL):
    'Party - Category'
    __name__ = 'agronomics.maquila.product_year-agronomics.maquila.contract.crop'
    _table = 'agronomics_maquila_product_year_contract_crop_rel'
    product_year = fields.Many2One('agronomics.maquila.product_year', "Product Year", ondelete='CASCADE',
            required=True, select=True)
    contract_crop = fields.Many2One('agronomics.maquila.contract.crop', "Contract Crop",
        ondelete='CASCADE', required=True, select=True)


class MaquilaContractCrop(ModelSQL):
    'Party - Category'
    __name__ = 'agronomics.maquila-agronomics.maquila.contract.crop'
    _table = 'agronomics_maquila_contract_crop_rel'
    maquila = fields.Many2One('agronomics.maquila', "Maquila", ondelete='CASCADE',
            required=True, select=True)
    contract_crop = fields.Many2One('agronomics.maquila.contract.crop', "Contract Crop",
        ondelete='CASCADE', required=True, select=True)
