from trytond.model import (Workflow, Model, ModelSingleton, ModelView, ModelSQL,
    fields, sequence_ordered)
from trytond.pyson import Id, If, Eval, Bool, PYSONEncoder
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


class Maquila(ModelSQL, ModelView):
    "Maquila"
    __name__ = 'agronomics.maquila'
    company = fields.Many2One(
        'company.company', "Company", required=True, select=True, readonly=True)
    contract = fields.Many2One('agronomics.maquila.contract', "Contract",
        ondelete='CASCADE', select=True, required=True, readonly=True)
    crop = fields.Many2One('agronomics.crop', "Crop", required=True, readonly=True)
    party = fields.Many2One('party.party', "Party", required=True, readonly=True,
        context={
            'company': Eval('company', -1),
            },
        depends=['company'])
    quantity = fields.Float("Quantity", digits=(16, Eval('unit_digits', 2)),
        required=True, readonly=True, depends=['unit_digits'])
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

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @fields.depends('product')
    def on_change_with_product_uom_category(self, name=None):
        if self.product:
            return self.product.default_uom_category.id

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if self.unit:
            return self.unit.digits
        return 2


class Contract(sequence_ordered(), Workflow, ModelSQL, ModelView):
    "Maquila Contract"
    __name__ = 'agronomics.maquila.contract'
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
            },
        depends=['state'])
    product_percentages = fields.One2Many('agronomics.maquila.contract.product_percentage',
        'contract', "Product Percentatges",
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])
    product_years = fields.One2Many('agronomics.maquila.contract.product_year',
        'contract', "Product Years", readonly=True,
        states={
            'readonly': Eval('state') != 'draft',
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
        cls._transitions |= set((
                ('draft', 'active'),
                ('active', 'cancelled'),
                ('active', 'done'),
                ('active', 'draft'),
                ('cancelled', 'draft'),

                ))
        cls._buttons.update({
            'draft': {
                'invisible': ~Eval('state').in_(['cancelled', 'active']),
                'icon': If(Eval('state') == 'cancelled', 'tryton-undo',
                        'tryton-back'),
            },
            'active': {
                'invisible': Eval('state') != 'draft',
                'icon': 'tryton-forward',
                },
            'cancel': {
                'invisible': Eval('state') != 'active',
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

    @classmethod
    def copy(cls, contracts, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('number', None)
        return super(Contract, cls).copy(contracts, default=default)

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
        for contract in contracts:
            contract.delete_contract_product_year()
            contract.delete_maquila()

    @classmethod
    @ModelView.button
    @Workflow.transition('active')
    def active(cls, contracts):
        for contract in contracts:
            contract.check_quantity()
            contract.create_contract_product_year()
            # TODO si active -> create_contract_product_year
            # also create_maquila from product_years that create_contract_product_year ?
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
        ContractProductYear = Pool().get('agronomics.maquila.contract.product_year')

        product_years = []
        for crop in self.product_crops:
            for ppercentatge in self.product_percentages:
                product_year = ContractProductYear()
                product_year.contract = self
                product_year.crop = crop.crop
                product_year.product = contract.product
                product_year.quantity = crop.quantity * ppercentatge.percentatge
                product_year.unit = contract.unit
                product_year.save()
                product_years.append(product_year)
        return product_years

    def delete_contract_product_year(self):
        ContractProductYear = Pool().get('agronomics.maquila.contract.product_year')

        product_years = ContractProductYear.search([
            ('contract', '=', self),
            ])
        ContractProductYear.delete(product_years)

    def create_maquila(self):
        Maquila = Pool().get('agronomics.maquila')

        default_values = Maquila.default_get(Maquila._fields.keys(),
                with_rec_name=False)

        maquilas = []
        for crop in self.product_years:
            for ppercentatge in self.product_percentages:
                maquila = Maquila(**default_values)
                maquila.contract = self
                maquila.crop = crop
                maquila.party = self.party
                maquila.product = contract.product
                maquila.quantity = crop.quantity * ppercentatge.percentatge
                maquila.unit = contract.unit
                maquila.save()
                maquilas.append(maquila)
        return maquilas

    def delete_maquila(self):
        Maquila = Pool().get('agronomics.maquila')

        maquilas = Maquila.search([
            ('contract', '=', self),
            ])
        Maquila.delete(maquilas)


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
    percentatge = fields.Float("Percentatge", digits=(16, 4), required=True)


class ContractProductYear(ModelSQL, ModelView):
    "Maquila Contract Product Year"
    __name__ = 'agronomics.maquila.contract.product_year'
    contract = fields.Many2One('agronomics.maquila.contract', "Contract",
        ondelete='CASCADE', select=True, required=True, readonly=True)
    crop = fields.Many2One('agronomics.crop', "Crop", required=True,
        readonly=True)
    product = fields.Many2One('product.product', "Product", required=True,
        readonly=True)
    quantity = fields.Float('Quantity', required=True, readonly=True,
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits'])
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
