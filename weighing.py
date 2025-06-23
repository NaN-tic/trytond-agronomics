# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView, Workflow, sequence_ordered
from trytond.pyson import Id, Eval, If, Bool
from trytond.pool import Pool
from trytond.i18n import gettext
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from datetime import datetime
from decimal import Decimal


class WeighingCenter(ModelSQL, ModelView):
    """ Weighing Center """
    __name__ = 'agronomics.weighing.center'

    name = fields.Char('Name', required=True)
    weighing_sequence = fields.Many2One('ir.sequence', 'Weighing Sequence',
        domain=[
            ('sequence_type', '=', Id('agronomics', 'sequence_type_weighing'))
        ])
    warehouse = fields.Many2One('stock.location', "Warehouse",
        domain=[('type', '=', 'warehouse')])
    to_location = fields.Many2One('stock.location', "To Location")

READONLY = ['processing', 'distributed', 'in_analysis', 'done', 'cancelled']
READONLY2 = ['draft', 'distributed', 'in_analysis', 'done', 'cancelled']


class Weighing(Workflow, ModelSQL, ModelView):
    """ Weighing """
    __name__ = 'agronomics.weighing'
    _rec_name = 'number'

    number = fields.Char('Number', readonly=True)
    weighing_date = fields.Date('Date', states={
            'readonly': Eval('state').in_(READONLY),
            }, required=True)
    weighing_center = fields.Many2One('agronomics.weighing.center',
        'Weighing Center', states={
            'readonly': Eval('state').in_(READONLY),
            }, required=True)

    purchase_contract = fields.Many2One('agronomics.contract',
        'Purchase Contract', domain=[
            ('crop', '=', Eval('crop', -1)),
            ], states={
            'readonly': Eval('state').in_(READONLY),
            }, required=True)

    crop = fields.Many2One('agronomics.crop', 'Crop', required=True, domain=[
            ('start_date', '<=', Eval('weighing_date')),
            ('end_date', '>=', Eval('weighing_date')),
            ], states={
            'readonly': Eval('state').in_(READONLY),
            })
    product = fields.Many2One('product.template', 'Product', required=True,
        states={
            'readonly': True,
            })
    variety = fields.Many2One('product.taxon', 'Variety', required=True,
        states={
            'readonly': True,
            })
    table = fields.Boolean('Table', states={
            'readonly': Eval('state').in_(READONLY2),
            })
    ecological = fields.Many2One('agronomics.ecological', 'Ecological',
        required=True, states={
            'readonly': Eval('state').in_(['done', 'cancelled']),
            'required': Eval('state') == 'in_analysis',
            })
    weight = fields.Float('Weight', required=True, domain=[
            If(Bool(Eval('weight')), ('weight', '>', 0), ()),
            ], states={
            'readonly': ~Eval('state').in_(['draft']),
            })
    tara = fields.Function(fields.Float('Tara', required=True, states={
            'readonly': ~Eval('state').in_(['draft']),
            }), 'on_change_with_tara', setter='set_tara')
    netweight = fields.Float('Net Weight', required=True, domain=[
            If(Bool(Eval('netweight')), [
                   ('netweight', '>', 0),
                   ('netweight', '<=', Eval('weight')),
               ], ()),
            ], states={
            'readonly': ~Eval('state').in_(['draft']),
            })
    grade = fields.Float('Grade', digits=(16, 1), required=True, states={
            #'readonly': Eval('state').in_(READONLY),
            'required': Eval('state') == 'in_analysis',
            })
    beneficiaries = fields.One2Many('agronomics.beneficiary', 'weighing',
        'Beneficiaries', states={
                'readonly': Eval('state').in_(READONLY2),
                # TODO: Are beneficiaries required??
                #'required': Eval('state') == 'in_analysis',
                })
    denomination_origin = fields.Many2Many('agronomics.weighing-agronomics.do',
        'weighing', 'do', 'Denomination of Origin', states={
            'readonly': Eval('state').in_(['done', 'cancelled']) | Bool(Eval('table')),
            'required': Eval('state') == 'in_analysis',
            })
    beneficiaries_invoices_line = fields.Many2Many(
        'agronomics.weighing-account.invoice.line', 'weighing', 'invoice_line',
        "Beneficiaries Invoices", readonly=True)
    plantations = fields.One2Many('agronomics.weighing-agronomics.plantation',
        'weighing', 'plantations', domain=[
            If(Bool(Eval('product')), ('plantation.product', '=', Eval('product', -1)),
                ()),
            If(Bool(Eval('variety')), ('plantation.variety', '=', Eval('variety', -1)),
                ()),
            ], states={
            'readonly': (Eval('state').in_(READONLY) | ~Bool(Eval('crop'))
                | ~Bool(Eval('weighing_center'))),
            'required': Eval('state') == 'process',
            }, size=4)
    state = fields.Selection([
                ('draft', "Draft"),
                ('processing', "Processing"),
                ('distributed', "Distributed"),
                ('in_analysis', "In Analysis"),
                ('done', "Done"),
                ('cancelled', "Cancelled"),
                ], "State", readonly=True, required=True)
    state_string = state.translated('state')
    all_do = fields.Function(fields.Char('All DO'), 'get_all_do')
    quality_test = fields.Function(fields.Many2One('quality.test', 'Test',
        states={
            'readonly': Eval('state').in_(['done', 'cancelled']),
        }),
        'get_quality_test', 'set_quality_test')
    product_created = fields.Many2One('product.product', 'Product Created',
        readonly=True)
    parcels = fields.One2Many('agronomics.weighing-agronomics.parcel',
        'weighing', 'Parcels', readonly=True)
    not_assigned_weight = fields.Function(
        fields.Float('Not Assigned Weight'), 'get_not_assigned_weight')
    forced_analysis = fields.Boolean('Forced Analysis', readonly=True)
    inventory_move = fields.Many2One('stock.move', "Inventory Move",
        readonly=True)

    @classmethod
    def __setup__(cls):
        super(Weighing, cls).__setup__()
        cls._order = [
            ('weighing_date', 'DESC NULLS FIRST'),
            ('id', 'DESC'),
            ]
        cls._transitions |= set((
                ('draft', 'processing'),
                ('processing', 'draft'),
                ('processing', 'distributed'),
                ('distributed', 'in_analysis'),
                ('distributed', 'draft'),
                ('processing', 'in_analysis'),
                ('draft', 'cancelled'),
                ('processing', 'cancelled'),
                ('in_analysis', 'done'),
                ))
        cls._buttons.update({
                'do': {
                    'invisible': ~Eval('state').in_(['in_analysis']),
                    'depends': ['state'],
                    'icon': 'tryton-forward',
                    },
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft']),
                    'depends': ['state'],
                    'icon': 'tryton-cancel',
                    },
                'draft': {
                    'invisible': ~Eval('state').in_(['processing', 'distributed']),
                    'icon': If(Eval('state') == 'cancelled',
                        'tryton-undo',
                        'tryton-back'),
                    'depends': ['state'],
                    },
                'process': {
                    'invisible': Eval('state') != 'draft',
                    'depends': ['state'],
                    'icon': 'tryton-forward',
                    },
                'distribute': {
                    'invisible': Eval('state') != 'processing',
                    'depends': ['state'],
                    'icon': 'tryton-forward',
                    },
                'force_analysis': {
                    'invisible': Eval('state') != 'distributed',
                    'depends': ['state'],
                    'icon': 'tryton-forward',
                    },
                })

    @staticmethod
    def default_weighing_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_state():
        return 'draft'

    def get_all_do(self, name):
        return ",".join([x.name for x in self.denomination_origin])

    def get_quality_test(self, name):
        if not self.product_created:
            return
        tests = self.product_created.quality_tests
        if not tests:
            return
        return tests and tests[0] and tests[0].id

    @classmethod
    def set_quality_test(cls, weighings, name, value):
        if not value:
            return

    fields.depends('weighing_date')
    def on_change_weighing_date(self):
        Crop = Pool().get('agronomics.crop')
        crops = Crop.search([
                ('start_date', '<=', self.weighing_date),
                ('end_date', '>=', self.weighing_date),
                ])
        if len(crops) == 1:
            self.crop = crops[0]

    @fields.depends('plantations', 'crop')
    def get_parcel(self):
        if not self.plantations:
            return
        plantation = self.plantations[0].plantation
        if not plantation:
            return
        res = None
        for parcel in plantation.parcels:
            if parcel.crop == self.crop:
                res = parcel
                break
        return res

    @fields.depends('plantations', 'ecological', 'denomination_origin',
        methods=['get_parcel'])
    def on_change_plantations(self):
        pool = Pool()
        ContractLine = pool.get('agronomics.contract.line')

        parcel = self.get_parcel()
        if not parcel:
            return
        self.product = parcel.product
        self.variety = parcel.variety
        self.table = parcel.table
        if not self.ecological:
            self.ecological = parcel.ecological
        self.denomination_origin = [x.id for x in parcel.denomination_origin]
        if parcel.producer:
            contract_lines = ContractLine.search([
                    ('parcel', '=', parcel),
                    ('contract.party', '=', parcel.producer),
                    ('contract.state', '=', 'active'),
                    ], limit=1)
            if contract_lines:
                self.purchase_contract = contract_lines[0].contract

    @fields.depends('weight', 'netweight')
    def on_change_with_tara(self, name=None):
        return (self.weight or 0) - (self.netweight or 0)

    @classmethod
    def set_tara(cls, weighings, name, value):
        pass

    @fields.depends('weight', 'tara')
    def on_change_with_netweight(self, name=None):
        return (self.weight or 0) - (self.tara or 0)

    @classmethod
    @Workflow.transition('in_analysis')
    def analysis(cls, weighings):
        pool = Pool()
        Product = pool.get('product.product')
        Quality = pool.get('quality.test')
        Variety = pool.get('product.variety')
        Move = pool.get('stock.move')
        Location = pool.get('stock.location')
        Company = pool.get('company.company')

        supplier_location = Location.search([('code', '=', 'SUP')], limit=1)
        if not supplier_location:
            #Supplier location not found
            raise UserError()

        default_product_values = Product.default_get(Product._fields.keys(),
            with_rec_name=False)
        product = Product(**default_product_values)
        default_move_values = Move.default_get(Move._fields.keys(),
                with_rec_name=False)
        move = Move(**default_move_values)

        company = Company(Transaction().context.get('company'))

        to_done = []
        for weighing in weighings:
            if weighing.not_assigned_weight and not weighing.forced_analysis:
                raise UserError(gettext('agronomics.msg_not_assigned_weight',
                    weighing=weighing.rec_name))

            if weighing.table and weighing.denomination_origin:
                raise UserError(gettext('agronomics.msg_weighing_with_table_do',
                    weighing=weighing.rec_name))

            product.template = weighing.product
            product.denominations_of_origin = weighing.denomination_origin
            if weighing.ecological:
                product.ecologicals = [weighing.ecological]
            if weighing.variety:
                new_variety = Variety()
                new_variety.percent = 100
                new_variety.variety = weighing.variety
                product.varieties = [new_variety]
            product.vintages = [weighing.crop.id]
            weighing.product_created = product

            if not weighing.weighing_center:
                raise UserError()

            # Create Move
            move.from_location = supplier_location[0]
            if not weighing.weighing_center.to_location:
                raise UserError(
                    gettext('agronomics.msg_location_no_configured',
                    center=weighing.weighing_center.name))
            move.to_location = weighing.weighing_center.to_location
            move.product = weighing.product_created
            move.currency = company.currency
            move.unit = weighing.product_created.template.default_uom
            # TODO: Price should be based on price list of the supplier
            #move.unit_price = weighing.product_created.template.list_price
            move.unit_price = Decimal(0)
            move.quantity = weighing.netweight or 0

            weighing.inventory_move = move
            to_done.append(move)

        cls.save(weighings)
        with Transaction().set_context(_skip_warnings=True):
            Move.do(to_done)
        tests = []
        for weighing in weighings:
            tests.append(weighing.create_quality_test())
        Quality.save(tests)

    @classmethod
    @ModelView.button
    @Workflow.transition('distributed')
    def distribute(cls, weighings):
        pool = Pool()
        WeighingParcel = pool.get('agronomics.weighing-agronomics.parcel')
        weighing_parcel_to_save = []
        to_analysis = []
        for weighing in weighings:
            if not weighing.table:
                if weighing.parcels:
                    WeighingParcel.delete(weighing.parcels)
                allowed_parcels = []
                for wp in weighing.plantations:
                    plantation = wp.plantation
                    if plantation:
                        for parcel in plantation.parcels:
                            if parcel.crop == weighing.crop:
                                allowed_parcels.append(parcel)
                                break
                remaining_weight = weighing.netweight
                for parcel in allowed_parcels:
                    if not remaining_weight:
                        break
                    weighing_parcel = WeighingParcel()
                    weighing_parcel.parcel = parcel
                    weighing_parcel.weighing = weighing
                    if parcel.remaining_quantity - remaining_weight >= 0:
                        weighing_parcel.netweight = remaining_weight
                        remaining_weight = 0
                    else:
                        remaining_weight -= parcel.remaining_quantity
                        weighing_parcel.netweight = parcel.remaining_quantity
                    if weighing_parcel.netweight:
                        weighing_parcel_to_save.append(weighing_parcel)
                if remaining_weight == 0:
                    to_analysis.append(weighing)
            else:
                parcel = weighing.get_parcel()
                weighing_parcel = WeighingParcel()
                weighing_parcel.parcel = parcel
                weighing_parcel.weighing = weighing
                weighing_parcel.netweight = weighing.netweight
                weighing_parcel.table = True
                weighing_parcel_to_save.append(weighing_parcel)
                to_analysis.append(weighing)
        WeighingParcel.save(weighing_parcel_to_save)
        cls.save(weighings)
        cls.analysis(to_analysis)

    def get_not_assigned_weight(self, name):
        return (self.netweight or 0) - sum([(p.netweight or 0)
            for p in self.parcels])

    @classmethod
    @ModelView.button
    def force_analysis(cls, weighings):
        to_copy_values = {}
        for weighing in weighings:
            to_copy_values[weighing.id] = {
                'netweight': weighing.not_assigned_weight}
        cls.copy(weighings, default={
                            'netweight': lambda d: (
                                to_copy_values[d['id']]['netweight']),
                            'weight': None,
                            'tara': None,
                            })
        for weighing in weighings:
            weighing.forced_analysis = True
            weighing.netweight -= weighing.not_assigned_weight
        cls.save(weighings)
        cls.analysis(weighings)

    def create_quality_test(self):
        pool = Pool()
        QualityTest = pool.get('quality.test')

        with Transaction().set_context(_check_access=False):
            if not (self.product and self.product.quality_weighing):
                return
            template = self.product.quality_weighing
            test = QualityTest(
                test_date=datetime.now(),
                templates=[template],
                document=str(self.product_created))
            test.apply_template_values()

        return test

    @classmethod
    @Workflow.transition('draft')
    def draft(cls, weighings):
        pass

    @classmethod
    @Workflow.transition('done')
    def do(cls, weighings):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')
        Product = pool.get('product.product')
        Company = pool.get('company.company')
        context = Transaction().context
        ContractProductPriceListTypePriceList = pool.get(
            'agronomics.contract-product.price_list.type-product.price_list')
        WeighingInvoiceLine = pool.get(
            'agronomics.weighing-account.invoice.line')
        RecomputeCostPrice = pool.get('product.recompute_cost_price',
            type='wizard')
        Move = pool.get('stock.move')

        default_invoice_line_values = InvoiceLine.default_get(
            InvoiceLine._fields.keys(), with_rec_name=False)
        invoice_line = InvoiceLine(**default_invoice_line_values)

        to_save = []
        to_save_moves = []
        to_recompute_products = []
        for weighing in weighings:
            cost_price = Decimal(0)
            for beneficiary in weighing.beneficiaries:
                price_list = ContractProductPriceListTypePriceList.search([
                        ('contract', '=', weighing.purchase_contract),
                        ('price_list_type', '=',
                            beneficiary.product_price_list_type),
                        ])

                invoice_line = InvoiceLine()
                invoice_line.type = 'line'
                invoice_line.invoice_type = 'in'
                invoice_line.party = beneficiary.party
                invoice_line.currency = (
                    Company(context['company']).currency)
                invoice_line.company = Company(context['company'])
                invoice_line.description = ''
                invoice_line.product = weighing.product_created
                invoice_line.on_change_product()
                invoice_line.quantity = weighing.netweight or 0
                invoice_line.product_price_list_type = (
                    beneficiary.product_price_list_type)

                unit_price = Product.get_purchase_price(
                    [weighing.product_created],
                    abs(weighing.netweight or 0))[
                        weighing.product_created.id]
                if price_list:
                    if price_list[0].price_list:
                        price_list = price_list[0].price_list
                    unit_price = price_list.compute(
                        weighing.product_created,
                        weighing.netweight or 0,
                        weighing.product_created.template.default_uom)
                    unit_price = unit_price
                invoice_line.unit_price = unit_price
                cost_price += unit_price

                weighing_invoice = WeighingInvoiceLine(
                    weighing=weighing,
                    invoice_line=invoice_line
                )
                to_save.append(weighing_invoice)

            weighing.inventory_move.unit_price = cost_price
            weighing.inventory_move.unit_price_updated = True
            weighing.product_created.cost_price = cost_price
            to_save_moves.append(weighing.inventory_move)
            to_recompute_products.append(weighing.product_created)
            Product.save([weighing.product_created])

            session_id, _, _ = RecomputeCostPrice.create()
            with Transaction().set_context(active_model='product.product',
                    active_ids=[weighing.product_created.id]):
                recompute_cost_price = RecomputeCostPrice(session_id)
                default_values = recompute_cost_price.default_start({})
                recompute_cost_price.start.from_ = default_values['from_']
                recompute_cost_price.transition_recompute()

        WeighingInvoiceLine.save(to_save)
        Move.save(to_save_moves)

    @classmethod
    @Workflow.transition('processing')
    def process(cls, weighings):
        Beneficiary = Pool().get('agronomics.beneficiary')
        to_save = []

        for weighing in weighings:
            if weighing.beneficiaries:
                Beneficiary.delete([x for x in weighing.beneficiaries])

            # Check if all plantations has a parcel in the weighing's crop
            for plantation in weighing.plantations:
                plantation = plantation.plantation
                for parcel in plantation.parcels:
                    if parcel.crop == weighing.crop:
                        break
                else:
                    raise UserError(gettext('agronomics.msg_parcel_without_current_crop',
                        weighing=weighing.rec_name, plantation=plantation.code))

            if not parcel:
                continue

            for ben in parcel.beneficiaries:
                b = Beneficiary()
                b.party = ben.party
                b.weighing = weighing
                b.product_price_list_type = ben.product_price_list_type
                to_save.append(b)

        if to_save:
            Beneficiary.save(to_save)

    @classmethod
    @Workflow.transition('cancel')
    def cancel(cls, weighings):
        pass

    @classmethod
    def set_number(cls, weighing_center):
        WeighingCenter = Pool().get('agronomics.weighing.center')
        weighing_center = WeighingCenter(weighing_center)
        return (weighing_center.weighing_sequence and
            weighing_center.weighing_sequence.get())

    @classmethod
    def create(cls, vlist):
        vlist = [v.copy() for v in vlist]
        for values in vlist:
            if not values.get('number'):
                values['number'] = cls.set_number(values.get('weighing_center'))
        return super().create(vlist)

    @classmethod
    def copy(cls, weighings, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('beneficiaries', None)
        default.setdefault('beneficiaries_invoices_line', None)
        default.setdefault('product_created', None)
        default.setdefault('number', None)
        default.setdefault('parcels', None)
        default.setdefault('inventory_move', None)
        return super().copy(weighings, default=default)


class WeighingDo(ModelSQL):
    'Weighing - Denomination Origin'
    __name__ = 'agronomics.weighing-agronomics.do'

    weighing = fields.Many2One('agronomics.weighing', 'Weighing')
    do = fields.Many2One('agronomics.denomination_of_origin',
        'Denomination Origin')


class WeighingInvoice(ModelSQL):
    "Weighing - Invoice"
    __name__ = 'agronomics.weighing-account.invoice.line'

    weighing = fields.Many2One('agronomics.weighing', "Weighing")
    invoice_line = fields.Many2One('account.invoice.line', "Invoice Line")


class WeighingPlantation(sequence_ordered(), ModelSQL, ModelView):
    'Weighing - Plantations'
    __name__ = 'agronomics.weighing-agronomics.plantation'

    weighing = fields.Many2One('agronomics.weighing', 'Weighing', required=True)
    plantation = fields.Many2One('agronomics.plantation', 'Plantation',
        required=True)
    party = fields.Function(fields.Many2One('party.party', 'Party'), 'on_change_with_party')
    purchased_quantity = fields.Function(fields.Float('Purchased Quantity'),
        'on_change_with_purchased_quantity')
    remaining_quantity = fields.Function(fields.Float('Remaining Quantity'),
        'on_change_with_remaining_quantity')

    @fields.depends('plantation')
    def on_change_with_party(self, name=None):
        if self.plantation:
            return self.plantation.party.id

    @fields.depends('plantation')
    def on_change_with_purchased_quantity(self, name=None):
        if self.plantation:
            return self.plantation.purchased_quantity

    @fields.depends('plantation')
    def on_change_with_remaining_quantity(self, name=None):
        if self.plantation:
            return self.plantation.remaining_quantity


class WeighingParcel(ModelSQL, ModelView):
    "Weighing-Parcel"
    __name__ = 'agronomics.weighing-agronomics.parcel'

    weighing = fields.Many2One('agronomics.weighing', 'Weighing',
        ondelete='CASCADE')
    parcel = fields.Many2One('agronomics.parcel', 'Parcel')
    netweight = fields.Float('Net Weight')
    table = fields.Boolean('Table')
