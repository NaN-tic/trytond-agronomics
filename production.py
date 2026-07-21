# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Bool, If
from trytond.exceptions import UserWarning, UserError
from trytond.i18n import gettext
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.modules.product import round_price
from trytond.model.exceptions import ValidationError


class ProductionTemplate(ModelSQL, ModelView):
    "Production Template"
    __name__ = 'production.template'

    name = fields.Char('Name', required=True)
    uom = fields.Many2One('product.uom', 'Uom',
        states = {
            'required': True
        })
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')
    quantity = fields.Float('Quantity',
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits'])
    inputs = fields.Many2Many('production.template.inputs-product.template',
        'production_template', 'template', "Inputs")
    outputs = fields.Many2Many('production.template.outputs-product.template',
        'production_template', 'template', "Outputs")
    enology_products = fields.One2Many('production.template.line',
        'production_template', 'Complementary Products')
    pass_feature = fields.Boolean('Pass on Feature')
    pass_quality = fields.Boolean('Pass Quality')
    pass_certification = fields.Boolean('Pass Certification')
    pass_quality_sample = fields.Boolean('Pass Quality Sample')
    cost_distribution_template = fields.Many2One(
        'production.cost_price.distribution.template',
        "Default cost distribution template",
        domain=[
            ('production_template', '=', Eval('id', 0)),
        ])
    cost_distribution_templates = fields.One2Many(
        'production.cost_price.distribution.template',
        'production_template', "Cost Distribution Templates")
    transfer_wine_aging = fields.Boolean("Transfer Wine Aging")
    inputs_products = fields.Function(fields.Many2Many('product.product', None,
         None, 'Products'), 'get_products', searcher='search_input_products')

    def get_products(self, name=None):
        products = []
        for template in self.inputs:
            products.extend(template.products)
        return [product.id for product in products]

    @classmethod
    def search_input_products(cls, name, clause):
        return [('inputs.products.id',) + tuple(clause[1:])]

    @fields.depends('uom')
    def on_change_with_unit_digits(self, name=None):
        if self.uom:
            return self.uom.digits
        return 2

    @classmethod
    def validate(cls, records):
        super().validate(records)
        for record in records:
            record.check_input_uoms()
            record.check_cost_distribution()

    def check_input_uoms(self):
        if not self.uom:
            return
        category_uom = self.uom.category
        uoms = [i.default_uom.category for i in self.inputs]
        uoms.append(category_uom)
        if len(list(set(uoms))) > 1:
            raise UserError(gettext('agronomics.msg_uom_not_fit',
                production=self.rec_name,
                uom=self.uom.rec_name,
                uoms=",".join([x.rec_name for x in set(uoms)])))

    def check_cost_distribution(self):
        if not self.cost_distribution_template:
            return

        output_templates = set(self.outputs)
        for cost in self.cost_distribution_template.cost_distribution_templates:
            if cost.product.template not in output_templates:
                raise ValidationError(
                    gettext('agronomics.msg_check_cost_distribution_template',
                        production=self.rec_name))


class ProductionTemplateInputsProductTemplate(ModelSQL):
    'Production Template Inputs- Product Template'
    __name__ = 'production.template.inputs-product.template'
    production_template = fields.Many2One('production.template',
        'Production Template', ondelete='CASCADE', required=True)
    template = fields.Many2One('product.template', 'Template',
        ondelete='CASCADE', required=True)


class ProductionTemplateOutputsProductTemplate(ModelSQL):
    'Production Template Inputs- Product Template'
    __name__ = 'production.template.outputs-product.template'
    production_template = fields.Many2One('production.template',
        'Production Template', ondelete='CASCADE', required=True)
    template = fields.Many2One('product.template', 'Product',
        ondelete='CASCADE', required=True)


class ProductionTemplateLine(ModelSQL, ModelView):
    "Production Template Line"
    __name__ = 'production.template.line'

    product = fields.Many2One('product.product', 'Product', required=True)
    uom = fields.Many2One('product.uom', 'Uom')
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')
    quantity = fields.Float('Quantity',
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits'])
    production_template = fields.Many2One('production.template',
        'Production Template')

    @fields.depends('uom')
    def on_change_with_unit_digits(self, name=None):
        if self.uom:
            return self.uom.digits
        return 2

    @fields.depends('product')
    def on_change_with_uom(self):
        if not self.product:
            return
        return self.product.default_uom and self.product.default_uom.id


class Production(metaclass=PoolMeta):
    __name__ = 'production'

    production_template = fields.Many2One('production.template',
        "Production Template",
        states={
            'readonly': ~Eval('state').in_(['request', 'draft']),
            })
    production_template_cost_distribution_templates = fields.Function(
        fields.Many2Many('production.cost_price.distribution.template',
        None, None, "Cost Distribution Templates"),
        'on_change_with_production_template_cost_distribution_templates')
    enology_products = fields.One2Many('production.enology.product',
        'production', "Enology Products",
        domain=[('product', 'in', Eval('allowed_enology_products')),
                If((Eval('state').in_(['waiting', 'draft'])),
                    ('product.quantity', '>', 0), ())],
        states={
            'invisible': ~Bool(Eval('production_template')),
            'readonly': ~Eval('state').in_(['request', 'draft']),
        })
    output_distribution = fields.One2Many('production.output.distribution',
        'production', "Output Distribution",
        # domain=[('product', 'in', Eval('allowed_ouput_products'))],
        states={
            'invisible': ~Bool(Eval('production_template')),
            'readonly': Eval('state').in_(['cancelled', 'done']),
        })
    allowed_enology_products = fields.Function(fields.Many2Many(
        'product.product', None, None, 'Allowed Enology Products',
        readonly=True, context={
            'company': Eval('company', -1),
            },
        depends=['company']), 'on_change_with_allowed_enology_products',
        setter='set_allowed_products')
    allowed_output_products = fields.Function(fields.Many2Many(
            'product.product', None, None, 'Allowed Output Products',
            readonly=True, context={
                'company': Eval('company', -1),
                },
            depends=['company']),
        'on_change_with_allowed_output_products', setter='set_allowed_products')
    cost_distributions = fields.One2Many(
        'production.cost_price.distribution',
        'origin', "Cost Distributions",
        domain=[
            ('product', 'in', Eval('cost_distribution_products')),
            ],
        states={
            'readonly': Eval('state').in_(['cancelled', 'done']),
            },
        context={
            'company': Eval('company', -1),
            },
        depends=['company'])
    cost_distribution_template = fields.Many2One(
        'production.cost_price.distribution.template',
        "Cost Distribution Template",
        domain=[
            ('id', 'in',
                Eval('production_template_cost_distribution_templates'))
                ],
        states={
            'readonly': Eval('state').in_(['cancelled', 'done']),
            },
        context={
            'company': Eval('company', -1),
            },
        depends=['company'])
    cost_distribution_products = fields.Function(
        fields.Many2Many('product.product',
        None, None, "Cost Products",
        context={
            'company': Eval('company', -1),
            },
        depends=['company']),
        'on_change_with_cost_distribution_products')
    pass_quality = fields.Boolean('Pass Quality')
    pass_certification = fields.Boolean('Pass Certification')
    pass_quality_sample = fields.Boolean('Pass Quality Sample')

    @classmethod
    def set_allowed_products(cls, productions, name, value):
        pass

    @fields.depends('production_template')
    def on_change_with_pass_quality(self):
        if self.production_template:
            return self.production_template.pass_quality

    @fields.depends('production_template')
    def on_change_with_pass_certification(self):
        if self.production_template:
            return self.production_template.pass_certification

    @fields.depends('production_template')
    def on_change_with_pass_quality_sample(self):
        if self.production_template:
            return self.production_template.pass_quality_sample

    @fields.depends('production_template')
    def on_change_production_template(self):
        if (self.production_template and
                self.production_template.cost_distribution_template):
            self.cost_distribution_template = \
                self.production_template.cost_distribution_template

    @fields.depends('production_template')
    def on_change_with_allowed_enology_products(self, name=None):
        if not self.production_template:
            return []
        return [product.id
            for template in self.production_template.inputs
            for product in template.products]

    @fields.depends('production_template')
    def on_change_with_allowed_output_products(self, name=None):
        if not self.production_template:
            return []
        return [product.id
            for template in self.production_template.outputs
            for product in template.products]

    @fields.depends('production_template',
        '_parent_production_template.cost_distribution_templates')
    def on_change_with_production_template_cost_distribution_templates(self,
            name=None):
        if self.production_template:
            return [s.id for s in
                self.production_template.cost_distribution_templates]

    @fields.depends('production_template')
    def on_change_with_cost_distribution_products(self, name=None):
        if self.production_template:
            return [product.id
                for template in self.production_template.outputs
                for product in template.products]

    @classmethod
    def validate(cls, productions):
        super(Production, cls).validate(productions)
        for production in productions:
            production.check_cost_distribution()
            production.check_percentatge()

    def check_cost_distribution(self):
        if (self.state in ('cancelled', 'done')
                or not self.cost_distribution_template
                or not self.cost_distributions):
            return
        distribution_products = set(c.product
            for c in self.cost_distribution_template.cost_distribution_templates)
        for c in self.cost_distributions:
            if c.product not in distribution_products:
                raise ValidationError(
                    gettext('agronomics.msg_check_cost_distribution',
                        production=self.rec_name))

    def check_percentatge(self):
        if not self.cost_distributions:
            return

        percentatge = sum(template.percentatge
            for template in self.cost_distributions)
        if percentatge != 1:
            raise ValidationError(
                gettext('agronomics.msg_check_production_percentatge',
                    production=self.rec_name,
                    percentatge=percentatge * 100,
                ))

    @classmethod
    def wait(cls, productions):
        pool = Pool()
        Move = pool.get('stock.move')
        Uom = pool.get('product.uom')
        OutputDistribution = pool.get('production.output.distribution')
        CostDistribution = pool.get('production.cost_price.distribution')

        moves = []
        delete = []
        outputs = []
        costs = []
        delete_outputs = []

        for production in productions:
            if not production.production_template:
                continue

            delete += [x for x in production.inputs]
            input_quantity = 0
            template_qty = production.production_template.quantity
            for enology in production.enology_products:
                move = production._move('input',
                    enology.product,
                    enology.uom,
                    enology.quantity)
                move.production_input = production
                moves.append(move)
                input_quantity += Uom.compute_qty(enology.uom, enology.quantity,
                    production.production_template.uom, round=True)
            enology_products = (production.production_template and
                production.production_template.enology_products or [])
            for enology in enology_products:
                quantity = enology.quantity
                qty = quantity * (input_quantity or 1) / template_qty
                qty = enology.uom.round(qty)
                move = production._move('input',
                    enology.product,
                    enology.uom,
                    float(qty))
                move.production_input = production
                moves.append(move)

            for output_template in production.production_template.outputs:
                output_products = [product
                    for product in output_template.products if product.active]
                if len(output_products) != 1:
                    raise UserError(gettext(
                        'agronomics.msg_output_product_required',
                        template=output_template.rec_name))
                output_product, = output_products
                delete_outputs += [x for x in production.output_distribution]
                output_distribution = OutputDistribution()
                output_distribution.product = output_product
                output_distribution.uom = (
                            output_distribution.on_change_with_uom())
                output_distribution.production = production
                outputs.append(output_distribution)

            if not production.cost_distributions:
                if production.cost_distribution_template:
                    cost_distribution_template = production.cost_distribution_template
                elif production.production_template:
                    cost_distribution_template = production.production_template.cost_distribution_template
                else:
                    cost_distribution_template = None
                if cost_distribution_template:
                    for c in cost_distribution_template.cost_distribution_templates:
                        cost = CostDistribution()
                        cost.product = c.product
                        cost.percentatge = c.percentatge
                        cost.origin = str(production)
                        costs.append(cost)

        CostDistribution.save(costs)
        OutputDistribution.delete(delete_outputs)
        OutputDistribution.save(outputs)
        Move.save(moves)
        Move.delete(delete)

        super().wait(productions)

    def copy_certification(self, new_lot):
        lots = {
            move.lot for move in self.inputs
            if move.lot and move.lot.certification
            }
        if not self.pass_certification or len(lots) != 1:
            return new_lot
        lot, = lots
        new_lot.certification = lot.certification
        return new_lot

    def copy_quality_samples(self, new_lot):
        LotSample = Pool().get('stock.lot-quality.sample')
        lots = {
            move.lot for move in self.inputs
            if move.lot and move.lot.quality_samples
            }
        if not self.pass_quality_sample or len(lots) != 1:
            return new_lot
        lot, = lots
        samples = lot.quality_samples
        new_samples = []
        for sample in samples:
            lot_sample = LotSample()
            lot_sample.lot = new_lot
            lot_sample.sample = sample
            new_samples.append(lot_sample)
        LotSample.save(new_samples)
        return new_lot

    def copy_quality(self, new_lot):
        Quality = Pool().get('quality.test')
        if not self.pass_quality:
            return new_lot
        lots = {
            move.lot for move in self.inputs
            if move.lot and move.lot.quality_tests
            }
        if len(lots) != 1:
            return new_lot
        lot, = lots
        new_tests = Quality.copy(lot.quality_tests, {
                'document': str(new_lot),
                'state': 'draft',
                'confirmed_by': None,
                'confirmed_date': None,
                'validated_by': None,
                'validated_date': None,
                })
        Quality.confirmed(new_tests)
        Quality.manager_validate(new_tests)
        return new_lot

    def pass_feature(self, lot):
        Variety = Pool().get('agronomics.lot.variety')
        Uom = Pool().get('product.uom')
        inputs = [move for move in self.inputs
            if move.product.template in self.production_template.inputs]
        total_output = sum(Uom.compute_qty(
                move.unit, move.quantity, self.production_template.uom)
            for move in inputs)
        vintages = []
        do = []
        ecologicals = []
        for input in inputs:
            vintages += input.lot.crop
            do += input.lot.denominations_of_origin
            ecologicals += input.lot.ecologicals

        lot.denominations_of_origin = list(set(do))
        lot.ecologicals = list(set(ecologicals))
        lot.crop = list(set(vintages))
        varieties = {}
        for input in inputs:
            quantity = Uom.compute_qty(
                input.unit, input.quantity, self.production_template.uom)
            percent = round(quantity / total_output, 6)
            for variety in input.lot.varieties:
                new_variety = varieties.get(variety.variety)
                if not new_variety:
                    new_variety = Variety()
                    new_variety.percent = 0
                new_variety.variety = variety.variety
                new_variety.percent += variety.percent / 100.0 * percent
                varieties[new_variety.variety] = new_variety
        for key, variety in varieties.items():
            variety.percent = "%.4f" % round(100.0 * variety.percent, 4)
        lot.varieties = list(varieties.values())
        return lot

    def create_wine_aged_history(self, input, outputs):
        pool = Pool()
        WineAgingHistory = pool.get('wine.wine_aging.history')
        Date = pool.get('ir.date')

        effective_date = (input.production_input.effective_date
            or Date.today())
        histories = WineAgingHistory.search([
            ('lot', '=', input.lot),
            ('date_end', '=', None),
            ])
        if histories:
            to_write = []
            for history in histories:
                to_write.extend(([history], {
                    'date_end': effective_date,
                    'duration': (effective_date - history.date_start).days,
                    }))
            WineAgingHistory.write(*to_write)

        new_histories = []
        for output in outputs:
            new_histories += WineAgingHistory.create([{
                'production': output.production_output,
                'location': output.to_location,
                'material': output.to_location.material,
                'lot': output.lot,
                'date_start': effective_date,
                'date_end': None
                }])
            if histories:
                new_histories += WineAgingHistory.copy(histories, {
                    'production': output.production_output,
                    'product': None,
                    'lot': output.lot,
                    })
        return new_histories

    @classmethod
    def do(cls, productions):
        pool = Pool()
        Move = pool.get('stock.move')
        Warning = pool.get('res.user.warning')

        for production in productions:
            if any(move.quantity and not move.lot
                    for move in production.inputs):
                raise UserError(gettext('agronomics.msg_input_lot_required',
                    production=production.rec_name))
            if (production.production_template
                    and production.production_template.transfer_wine_aging):
                if len(production.inputs) > 1:
                    warning_name = 'transfer_wine_aging_input_%s' % production.id
                    if Warning.check(warning_name):
                        raise UserWarning(warning_name,
                            gettext('agronomics.msg_transfer_wine_aging_inputs',
                                production=production.rec_name))

        moves = []
        for production in productions:
            for distrib in production.output_distribution:
                if distrib.distribution_state == 'draft' and distrib.location:
                    pass_feature = bool(production.production_template
                        and production.production_template.pass_feature)
                    product = distrib.product
                    Lot = pool.get('stock.lot')
                    lot = Lot(product=product)
                    if not product.lot_sequence:
                        raise UserError(gettext(
                            'agronomics.msg_lot_sequence_required',
                            product=product.rec_name))
                    lot.number = product.lot_sequence.get()
                    if pass_feature:
                        lot = production.pass_feature(lot)
                    lot = production.copy_certification(lot)
                    Lot.save([lot])
                    move = production._move(
                        'output',
                        product,
                        distrib.uom,
                        distrib.produced_quantity)
                    move.production_output = production
                    move.lot = lot
                    move.unit_price = Decimal(0)
                    moves.append(move)

        Move.save(moves)
        for production in productions:
            output_moves = Move.search([
                    ('production_output', '=', production.id),
                    ('quantity', '!=', 0),
                    ])
            if any(not move.lot for move in output_moves):
                raise UserError(gettext('agronomics.msg_output_lot_required',
                    production=production.rec_name))
        super().do(productions)

        for production in productions:
            for output in production.outputs:
                production.copy_quality(output.lot)
                production.copy_quality_samples(output.lot)
            if (production.production_template
                    and production.production_template.transfer_wine_aging):
                inputs = production.inputs
                if len(inputs) == 1:
                    input, = inputs
                    outputs = production.outputs
                    production.create_wine_aged_history(input, outputs)

    @classmethod
    def set_cost(cls, productions):
        pool = Pool()
        Move = pool.get('stock.move')
        Uom = pool.get('product.uom')

        not_cost_distribution = []
        moves = []
        for production in productions:
            if not production.cost_distributions:
                not_cost_distribution.append(production)
                continue

            production_cost = production.cost
            for output in production.outputs:
                has_product = False
                output_cost = Decimal(0)
                total_output = sum([Uom.compute_qty(x.unit, x.quantity,
                    x.product.default_uom) for x in production.outputs
                        if x.product == output.product])

                for cdist in production.cost_distributions:
                    if output.product != cdist.product:
                        continue
                    has_product = True
                    cost = (production_cost * (1 + cdist.percentatge) -
                        production_cost)
                    output_cost += round_price(cost / Decimal(total_output))

                output_cost = output_cost if has_product else Decimal(0)
                if output.unit_price != output_cost:
                    output.unit_price = output_cost
                    moves.append(output)

        if moves:
            Move.save(moves)

        if not_cost_distribution:
            super(Production, cls).set_cost(not_cost_distribution)


class OutputDistribution(ModelSQL, ModelView):
    'Output Distribution'
    __name__ = 'production.output.distribution'

    production = fields.Many2One('production', 'Production',
        required=True)
    product = fields.Many2One('product.product', 'Product', required=True)
    location = fields.Many2One('stock.location', 'Location',
        states={
            'required': Eval('production_state').in_(['done'])
        })
    uom = fields.Many2One('product.uom', 'Uom')
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')
    initial_quantity = fields.Float('Initial Quantity',
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits'])
    initial_quantity_readonly = fields.Function(fields.Float('Initial Quantity',
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits']), 'on_change_with_initial_quantity_readonly')
    final_quantity = fields.Float('Final Quantity',
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits'])
    produced_quantity = fields.Function(fields.Float('Produced Quantity',
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits']), 'on_change_with_produced_quantity')
    production_state = fields.Function(fields.Selection([
        ('request', 'Request'), ('draft', 'Draft'), ('waiting', 'Waiting'),
        ('assigned', 'Assigned'), ('running', 'Running'), ('done', 'Done'),
        ('cancelled', 'Cancelled')], 'State'),
        'on_change_with_production_state')
    distribution_state = fields.Selection([
        ('draft', 'Draft'), ('done', 'Done')], 'Distribution State',
        readonly=True)

    @classmethod
    def __register__(cls, module_name):
        table = cls.__table_handler__(module_name)
        if (table.column_exist('product')
                and not table.column_exist('product_template_legacy')):
            table.column_rename('product', 'product_template_legacy')
        super().__register__(module_name)

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._buttons.update({
            'done': {
                'readonly': Eval('distribution_state') != 'draft',
                'depends': ['distribution_state']
                }
        })

    @classmethod
    def default_distribution_state(cls):
        return 'draft'

    @fields.depends('production', '_parent_production.state')
    def on_change_with_production_state(self, name=None):
        return self.production and self.production.state

    @fields.depends('product')
    def on_change_with_uom(self):
        if not self.product:
            return
        return self.product.default_uom and self.product.default_uom.id

    @fields.depends('uom')
    def on_change_with_unit_digits(self, name=None):
        if self.uom:
            return self.uom.digits
        return 2

    @fields.depends('initial_quantity', 'final_quantity', 'produced_quantity',
        'location', 'product')
    def on_change_product(self):
        Product = Pool().get('product.product')
        if not self.product:
            self.initial_quantity = 0
            return
        if not self.location:
            return
        context = Transaction().context
        context['locations'] = [self.location.id]
        with Transaction().set_context(context):
            quantities = Product.get_quantity([self.product], 'quantity')
        self.initial_quantity = quantities[self.product.id]

    @fields.depends('location', methods=['on_change_product'])
    def on_change_location(self):
        if not self.location:
            return
        self.on_change_product()

    @fields.depends('product', 'location', 'initial_quantity')
    def on_change_with_initial_quantity_readonly(self, name=None):
        Product = Pool().get('product.product')
        if not self.product or not self.location:
            return
        if self.initial_quantity:
            return self.initial_quantity
        context = Transaction().context.copy()
        context['locations'] = [self.location.id]
        with Transaction().set_context(context):
            quantities = Product.get_quantity([self.product], 'quantity')
        return quantities[self.product.id]

    @fields.depends('final_quantity', 'initial_quantity')
    def on_change_with_produced_quantity(self, name=None):
        return ((self.final_quantity or 0) -
            (self.initial_quantity or 0))

    @classmethod
    @ModelView.button
    def done(cls, distributions):
        pool = Pool()
        Move = pool.get('stock.move')

        moves = []
        for distribution in distributions:
            move = distribution.production._move(
                'input',
                distribution.product,
                distribution.uom,
                distribution.produced_quantity)
            move.production_output = distribution.production
            move.unit_price = Decimal(0)
            moves.append(move)
            distribution.distribution_state = 'done'
        Move.save(moves)
        Move.do(moves)
        cls.save(distributions)


class ProductionEnologyProduct(ModelSQL, ModelView):
    'Production Enology Product'
    __name__ = 'production.enology.product'
    production = fields.Many2One('production', 'Production')
    product = fields.Many2One('product.product', 'Product', required=True)
    uom = fields.Many2One('product.uom', 'Uom')
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')
    quantity = fields.Float('Quantity',
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits'])

    @fields.depends('uom')
    def on_change_with_unit_digits(self, name=None):
        if self.uom:
            return self.uom.digits
        return 2

    @fields.depends('product')
    def on_change_with_uom(self):
        if not self.product:
            return
        return self.product.default_uom and self.product.default_uom.id

    @fields.depends('product')
    def on_change_product(self):
        if not self.product:
            return
        self.quantity = self.product.quantity


class ProductionCostPriceDistribution(ModelSQL, ModelView):
    "Production Distribution Cost Price"
    __name__ = 'production.cost_price.distribution'
    product = fields.Many2One('product.product', "Product", required=True,
        ondelete='RESTRICT')
    origin = fields.Reference('Origin', selection='_get_models', required=True)
    percentatge = fields.Numeric("Percentatge", digits=(16, 4), required=True)

    @classmethod
    def __register__(cls, module_name):
        table = cls.__table_handler__(module_name)
        if (table.column_exist('template')
                and not table.column_exist('product_template_legacy')):
            table.column_rename('template', 'product_template_legacy')
        super().__register__(module_name)

    @classmethod
    def __setup__(cls):
        BOMInput = Pool().get('production.bom.input')
        super(ProductionCostPriceDistribution, cls).__setup__()
        cls.product.domain = [('type', 'in', BOMInput.get_product_types())]

    @staticmethod
    def _get_models():
        return [
            ('production', 'Production'),
            ('production.cost_price.distribution.template', 'Templates'),
            ]


class ProductionCostPriceDistributionTemplate(ModelSQL, ModelView):
    "Production Cost Price Distribution Template"
    __name__ = 'production.cost_price.distribution.template'
    name = fields.Char("Name", required=True)
    production_template = fields.Many2One('production.template',
        "Production Template", required=True)
    cost_distribution_templates = fields.One2Many(
        'production.cost_price.distribution',
        'origin', "Cost Distribution")

    @classmethod
    def validate(cls, templates):
        super(ProductionCostPriceDistributionTemplate, cls).validate(templates)
        for template in templates:
            template.check_percentatge()
            template.check_products()

    def check_products(self):
        for cost in self.cost_distribution_templates:
            if cost.product.template not in self.production_template.outputs:
                raise ValidationError(gettext(
                    'agronomics.msg_check_cost_templates',
                    cost=cost.rec_name,
                    product=cost.product.rec_name,
                    ))


    def check_percentatge(self):
        percentatge = sum(t.percentatge
            for t in self.cost_distribution_templates)
        if percentatge != 1:
            raise ValidationError(
                gettext(
                    'agronomics.msg_check_cost_distribution_template_percentatge',
                    distribution=self.rec_name,
                    percentatge=percentatge * 100,
                    ))


class ProductionCostPriceDistributionTemplateProductionTemplateAsk(ModelView):
    'Production Cost Price Distribution Template from Production Template Ask'
    __name__ = 'production.cost_price.distribution.template.ask'
    name = fields.Char("Name", required=True)
    cost_distribution_templates = fields.One2Many(
        'production.cost_price.distribution',
        None, "Cost Distributions")


class ProductionCostPriceDistributionTemplateProductionTemplate(Wizard):
    "Production Cost Price Distribution Template from Production Template"
    __name__ = 'production.cost_price.distribution.template.from.production.template'
    start_state = 'ask'
    ask = StateView('production.cost_price.distribution.template.ask',
        'agronomics.create_cost_price_distribution_from_production_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create', 'create_cost_distributions', 'tryton-ok', True),
            ])
    create_cost_distributions = StateAction(
            'agronomics.act_production_cost_distribution_template_tree')

    def do_create_cost_distributions(self, action):
        pool = Pool()
        Template = pool.get('production.cost_price.distribution.template')
        Distribution = pool.get('production.cost_price.distribution')

        to_create = []
        for record in self.records:
            tpl = Template()
            tpl.name = self.ask.name
            tpl.production_template = record
            cost_distributions = []
            for cost_distribution in self.ask.cost_distribution_templates:
                dt = Distribution()
                dt.product = cost_distribution.product
                dt.percentatge = cost_distribution.percentatge
                cost_distributions.append(dt)
            if cost_distributions:
                tpl.cost_distribution_templates = cost_distributions
            to_create.append(tpl._save_values())
        tpls = Template.create(to_create)

        data = {'res_id': [tpl.id for tpl in tpls]}
        if len(tpls) == 1:
            action['views'].reverse()
        return action, data

    def default_ask(self, fields):
        pool = Pool()
        ProductionTemplate = pool.get('production.template')

        default = {}
        context = Transaction().context

        active_id = context.get('active_id')
        if active_id:
            ptpl = ProductionTemplate(active_id)
            cost_distributions = []
            for output in ptpl.outputs:
                for product in output.products:
                    if product.active:
                        cost_distributions.append({
                                'product': product.id,
                                'product.': {'rec_name': product.rec_name},
                                })
            default['cost_distribution_templates'] = cost_distributions
        return default
