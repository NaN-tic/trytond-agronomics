# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView, Workflow, sequence_ordered
from trytond.pyson import Id, Eval, If, Bool
from trytond.pool import Pool
from trytond.i18n import gettext
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from datetime import date, datetime
from decimal import Decimal


def merge_location_lots(company, product, location):
    pool = Pool()
    Product = pool.get('product.product')
    Lot = pool.get('stock.lot')
    Move = pool.get('stock.move')
    Production = pool.get('production')

    quantities = Product.products_by_location(
        [location.id], grouping=('product', 'lot'))
    sources = [
        (Lot(lot_id), quantity)
        for (_location_id, product_id, lot_id), quantity
        in quantities.items()
        if product_id == product.id and quantity and lot_id]

    first_lot, _quantity = sources[0]
    for existing_lot, _quantity in sources[1:]:
        if (set(c.id for c in existing_lot.crop)
                != set(c.id for c in first_lot.crop)
                or set(d.id for d in existing_lot.denominations_of_origin)
                != set(d.id for d in first_lot.denominations_of_origin)
                or set(e.id for e in existing_lot.ecologicals)
                != set(e.id for e in first_lot.ecologicals)
                or set(v.variety.id for v in existing_lot.varieties)
                != set(v.variety.id for v in first_lot.varieties)):
            raise UserError(gettext(
                'agronomics.msg_weighing_location_lot_mismatch',
                location=location.rec_name))

    LotVariety = pool.get('agronomics.lot.variety')
    lot = Lot(product=product)
    lot.number = product.lot_sequence.get()
    lot.crop = first_lot.crop
    lot.denominations_of_origin = first_lot.denominations_of_origin
    lot.ecologicals = first_lot.ecologicals
    lot.varieties = [
        LotVariety(variety=v.variety, percent=v.percent)
        for v in first_lot.varieties]
    Lot.save([lot])

    uom = product.template.default_uom
    total_quantity = sum(quantity for _lot, quantity in sources)
    production, = Production.create([{
        'company': company.id,
        'warehouse': location.warehouse.id,
        'location': location.warehouse.production_location.id,
        'type': 'disassembly',
        'product': product.id,
        'unit': uom.id,
        'quantity': total_quantity,
        'planned_start_date': date.today(),
        'planned_date': date.today(),
        }])

    input_moves = []
    for source_lot, quantity in sources:
        move = production._move('input', product, uom, quantity)
        move.from_location = location
        move.to_location = production.location
        move.lot = source_lot
        input_moves.append(move)
    Move.save(input_moves)
    production = Production(production.id)

    output_move = production._move('output', product, uom, total_quantity)
    output_move.production_output = production
    output_move.from_location = production.location
    output_move.to_location = location
    output_move.lot = lot
    Move.save([output_move])

    with Transaction().set_context(production_mobile_manual_outputs=True):
        Production.wait([production])
    production = Production(production.id)
    Production.assign_force([production])
    production = Production(production.id)
    if production.state != 'assigned':
        raise UserError()
    Production.run([production])
    Production.do([Production(production.id)])


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


class Weighing(Workflow, ModelSQL, ModelView):
    """ Weighing """
    __name__ = 'agronomics.weighing'
    _rec_name = 'number'

    number = fields.Char('Number', readonly=True)
    weighing_date = fields.Date('Date', states={
            'readonly': Eval('state') != 'draft',
            }, required=True)
    weighing_center = fields.Many2One('agronomics.weighing.center',
        'Weighing Center', states={
            'readonly': Eval('state') != 'draft',
            }, required=True)

    purchase_contract = fields.Many2One('agronomics.contract',
        'Purchase Contract', domain=[
            ('crop', '=', Eval('crop', -1)),
            ], states={
            'readonly': Eval('state') != 'draft',
            }, required=True)

    crop = fields.Many2One('agronomics.crop', 'Crop', required=True, domain=[
            ('start_date', '<=', Eval('weighing_date', None)),
            ('end_date', '>=', Eval('weighing_date', None)),
            ], states={
            'readonly': Eval('state') != 'draft',
            })
    product = fields.Many2One('product.product', 'Product', required=True,
        states={
            'readonly': True,
            })
    variety = fields.Many2One('product.taxon', 'Variety', required=True,
        states={
            'readonly': True,
            })
    table = fields.Boolean('Table', states={
            'readonly': Eval('state') != 'draft',
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
            'required': Eval('state') == 'in_analysis',
            })
    beneficiaries = fields.One2Many('agronomics.beneficiary', 'weighing',
        'Beneficiaries', states={
                'readonly': Eval('state') != 'processing',
                # TODO: Are beneficiaries required??
                #'required': Eval('state') == 'in_analysis',
                })
    denomination_origin = fields.Many2Many('agronomics.weighing-agronomics.do',
        'weighing', 'do', 'Denomination of Origin', states={
            'readonly': Eval('state').in_(['done', 'cancelled']) | Bool(Eval('table')),
            'required': Eval('state') == 'in_analysis',
            })
    beneficiaries_invoices_line = fields.One2Many('account.invoice.line',
        'origin', "Beneficiary Invoice Lines", readonly=True)
    plantations = fields.One2Many('agronomics.weighing-agronomics.plantation',
        'weighing', 'plantations', domain=[
            If(Bool(Eval('product')), ('plantation.product', '=', Eval('product', -1)),
                ()),
            If(Bool(Eval('variety')), ('plantation.variety', '=', Eval('variety', -1)),
                ()),
            ], states={
            'readonly': (Eval('state') != 'draft') | ~Bool(Eval('crop'))
                | ~Bool(Eval('weighing_center')),
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
    lot_created = fields.Many2One('stock.lot', 'Lot Created', readonly=True)
    parcels = fields.One2Many('agronomics.weighing-agronomics.parcel',
        'weighing', 'Parcels', readonly=True)
    not_assigned_weight = fields.Function(
        fields.Float('Not Assigned Weight'), 'get_not_assigned_weight')
    forced_analysis = fields.Boolean('Forced Analysis', readonly=True)
    inventory_move = fields.Many2One('stock.move', "Inventory Move",
        readonly=True)

    @classmethod
    def __register__(cls, module_name):
        table = cls.__table_handler__(module_name)
        if (table.column_exist('product')
                and not table.column_exist('product_template_legacy')):
            table.column_rename('product', 'product_template_legacy')
        if table.column_exist('product_template_legacy'):
            table.not_null_action('product_template_legacy', 'remove')
        super().__register__(module_name)

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
        if not self.lot_created:
            return
        tests = self.lot_created.quality_tests
        if not tests:
            return
        return tests and tests[0] and tests[0].id

    @classmethod
    def set_quality_test(cls, weighings, name, value):
        if not value:
            return

    @fields.depends('weighing_date')
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

        # if not self.plantations:
        #     self.product = None
        #     self.variety = None
        #     self.table = None
        #     self.ecological = None
        #     self.denomination_origin = []
        #     return

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
        Lot = pool.get('stock.lot')
        Quality = pool.get('quality.test')
        Move = pool.get('stock.move')
        Location = pool.get('stock.location')
        Company = pool.get('company.company')

        supplier_location = Location.search([('code', '=', 'SUP')], limit=1)
        if not supplier_location:
            #Supplier location not found
            raise UserError()
        supplier_location = supplier_location[0]

        default_move_values = Move.default_get(Move._fields.keys(),
            with_rec_name=False)

        company = Company(Transaction().context.get('company'))

        for weighing in weighings:
            if weighing.not_assigned_weight and not weighing.forced_analysis:
                raise UserError(gettext('agronomics.msg_not_assigned_weight',
                    weighing=weighing.rec_name))

            if weighing.table and weighing.denomination_origin:
                raise UserError(gettext('agronomics.msg_weighing_with_table_do',
                    weighing=weighing.rec_name))

            if not weighing.product:
                raise UserError()
            lot = Lot(product=weighing.product)
            if not lot.product.lot_sequence:
                raise UserError(gettext('agronomics.msg_lot_sequence_required',
                    product=lot.product.rec_name))
            lot.number = lot.product.lot_sequence.get()
            lot.crop = [weighing.crop]
            lot.denominations_of_origin = weighing.denomination_origin
            if weighing.ecological:
                lot.ecologicals = [weighing.ecological]
            if weighing.variety:
                new_variety = pool.get('agronomics.lot.variety')()
                new_variety.percent = 100
                new_variety.variety = weighing.variety
                lot.varieties = [new_variety]
            Lot.save([lot])
            weighing.lot_created = lot

            if not weighing.weighing_center:
                raise UserError()
            if not weighing.weighing_center.to_location:
                raise UserError(
                    gettext('agronomics.msg_location_no_configured',
                    center=weighing.weighing_center.name))
            destination = weighing.weighing_center.to_location

            move = Move(**default_move_values)
            move.from_location = supplier_location
            move.to_location = destination
            move.product = weighing.product
            move.lot = lot
            move.currency = company.currency
            move.unit = weighing.product.template.default_uom
            move.unit_price = Decimal(0)
            move.quantity = weighing.netweight or 0
            Move.save([move])
            weighing.inventory_move = move

            with Transaction().set_context(_skip_warnings=True):
                Move.do([move])
                merge_location_lots(company, weighing.product, destination)

        cls.save(weighings)
        tests = []
        for weighing in weighings:
            tests.append(weighing.create_quality_test())
        Quality.save([t for t in tests if t])

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
                            'weight': lambda d: (
                                to_copy_values[d['id']]['netweight']),
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
                document=str(self.lot_created))
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
        Move = pool.get('stock.move')

        default_invoice_line_values = InvoiceLine.default_get(
            InvoiceLine._fields.keys(), with_rec_name=False)
        invoice_line = InvoiceLine(**default_invoice_line_values)

        to_save = []
        to_save_moves = []
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
                invoice_line.product = weighing.product
                invoice_line.on_change_product()
                invoice_line.quantity = weighing.netweight or 0
                invoice_line.product_price_list_type = (
                    beneficiary.product_price_list_type)
                invoice_line.origin = weighing

                if hasattr(Product, 'get_purchase_price'):
                    unit_price = Product.get_purchase_price(
                        [weighing.product],
                        abs(weighing.netweight or 0))[
                            weighing.product.id]
                else:
                    unit_price = weighing.product.cost_price or Decimal(0)
                if price_list:
                    if price_list[0].price_list:
                        price_list = price_list[0].price_list
                    unit_price = price_list.compute(
                        weighing.product,
                        weighing.netweight or 0,
                        weighing.product.template.default_uom,
                        pattern={'lot': weighing.lot_created.id})
                unit_price = unit_price or Decimal(0)
                invoice_line.unit_price = unit_price
                cost_price += unit_price
                to_save.append(invoice_line)

            weighing.inventory_move.unit_price = cost_price
            weighing.inventory_move.unit_price_updated = True
            to_save_moves.append(weighing.inventory_move)

        InvoiceLine.save(to_save)
        Move.save(to_save_moves)

    @classmethod
    @Workflow.transition('processing')
    def process(cls, weighings):
        Beneficiary = Pool().get('agronomics.beneficiary')
        to_save = []

        for weighing in weighings:
            if weighing.beneficiaries:
                Beneficiary.delete([x for x in weighing.beneficiaries])

            if not weighing.plantations:
                continue

            seen = set()
            for plantation in weighing.plantations:
                plantation = plantation.plantation
                for parcel in plantation.parcels:
                    if parcel.crop == weighing.crop:
                        break
                else:
                    raise UserError(gettext('agronomics.msg_parcel_without_current_crop',
                        weighing=weighing.rec_name, plantation=plantation.code))

                for ben in parcel.beneficiaries:
                    key = (ben.party.id, ben.product_price_list_type
                        and ben.product_price_list_type.id)
                    if key in seen:
                        continue
                    seen.add(key)
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
        default.setdefault('lot_created', None)
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
