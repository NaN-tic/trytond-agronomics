# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Bool, If
from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.modules.product import round_price
from trytond.model.exceptions import ValidationError
from decimal import Decimal


class ProductionTemplate(ModelSQL, ModelView):
    "Produciton Template"
    __name__ = 'production.template'

    name = fields.Char('Name', required=True)
    uom = fields.Many2One('product.uom', 'Uom', required=True)
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
    cost_distribution_template = fields.Many2One(
        'production.cost_price.distribution.template',
        "Default cost distribution template",
        domain=[
            ('production_template', '=', Eval('id', 0)),
        ], depends=['id'])
    cost_distribution_templates = fields.One2Many(
        'production.cost_price.distribution.template',
        'production_template', "Cost Distribution Templates")

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

        output_templates = set([o for o in self.outputs])
        for c in self.cost_distribution_template.cost_distribution_templates:
            if c.template not in output_templates:
                raise ValidationError(
                    gettext('agronomics.msg_check_cost_distribution_template',
                        production=self.rec_name))


class ProductionTemplateInputsProductTemplate(ModelSQL):
    'Production Template Inputs- Product Template'
    __name__ = 'production.template.inputs-product.template'
    production_template = fields.Many2One('production.template',
        'Production Template', ondelete='CASCADE', required=True, select=True)
    template = fields.Many2One('product.template', 'Template',
        ondelete='CASCADE', required=True, select=True)


class ProductionTemplateOutputsProductTemplate(ModelSQL):
    'Production Template Inputs- Product Template'
    __name__ = 'production.template.outputs-product.template'
    production_template = fields.Many2One('production.template',
        'Production Template', ondelete='CASCADE', required=True, select=True)
    template = fields.Many2One('product.template', 'Product',
        ondelete='CASCADE', required=True, select=True)


class ProductionTemplateLine(ModelSQL, ModelView):
    "Production Template Line"
    __name__ = 'production.template.line'

    product = fields.Many2One('product.product', 'Producte', required=True)
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
            },
        depends=['state'])
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
            'readonly': ~Eval('state').in_(['request', 'draft', 'waiting']),
        }, depends=['allowed_enology_products', 'state'])
    output_distribution = fields.One2Many('production.output.distribution',
        'production', "Output Distribution",
        # domain=[('product', 'in', Eval('allowed_ouput_products'))],
        states={
            'invisible': ~Bool(Eval('production_template')),
            'readonly': Eval('state') == 'done',
        }, depends=['allowed_output_products', 'state'])
    allowed_enology_products = fields.Function(fields.One2Many(
        'product.product', None, 'Allowed Enology Products', readonly=True),
        'on_change_with_allowed_enology_products',
        setter='set_allowed_products')
    allowed_output_products = fields.Function(fields.One2Many(
        'product.template', None, 'Allowed Output Products', readonly=True),
        'on_change_with_allowed_output_products',
        setter='set_allowed_products')
    cost_distributions = fields.Many2Many(
        'production-production.distribution.cost_price',
        'production', 'cost_distribution', "Cost Distributions",
        states={
            'readonly': Eval('state').in_(['cancelled', 'done']),
        }, domain=[
            If(Bool(Eval('cost_distribution_template')),
                ('id', 'in', Eval('cost_distribution_templates')),
                ()),
        ], depends=['state', 'cost_distribution_template',
            'cost_distribution_templates'])
    cost_distribution_template = fields.Many2One(
        'production.cost_price.distribution.template',
        "Cost Distribution Template",
        domain=[
            ('id', 'in', Eval('production_template_cost_distribution_templates'))
        ], states={
            'readonly': Eval('state').in_(['cancelled', 'done']),
        }, depends=['state', 'production_template_cost_distribution_templates'])
    cost_distribution_templates = fields.Function(
        fields.Many2Many('production.cost_price.distribution',
        None, None, "Cost Distribution Templates"),
        'on_change_with_cost_distribution_templates')

    @classmethod
    def set_allowed_products(cls, productions, name, value):
        pass

    @fields.depends('production_template')
    def on_change_production_template(self):
        if self.production_template and self.production_template.cost_distribution_template:
            self.cost_distribution_template = self.production_template.cost_distribution_template

    @fields.depends('production_template')
    def on_change_with_allowed_enology_products(self, name=None):
        products = []
        if not self.production_template:
            return []
        for template in self.production_template.inputs:
            products += template.products
        return [x.id for x in products]

    @fields.depends('production_template')
    def on_change_with_allowed_output_products(self, name=None):
        if not self.production_template:
            return []
        return [x.id for x in self.production_template.outputs]

    @fields.depends('production_template',
        '_parent_production_template.cost_distribution_templates')
    def on_change_with_production_template_cost_distribution_templates(self, name=None):
        if self.production_template:
            return [s.id for s in self.production_template.cost_distribution_templates]

    @fields.depends('cost_distribution_template',
        '_parent_cost_distribution_template.cost_distribution_templates')
    def on_change_with_cost_distribution_templates(self, name=None):
        if self.cost_distribution_template:
            return [s.cost_distribution.id for s in self.cost_distribution_template.cost_distribution_templates]

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
        distribution_templates = set([c.cost_distribution.template
            for c in self.cost_distribution_template.cost_distribution_templates])
        for c in self.cost_distributions:
            if c.template not in distribution_templates:
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

        moves = []
        delete = []
        outputs = []
        delete_outputs = []
        to_write = []

        for production in productions:
            if not production.production_template:
                continue

            delete += [x for x in production.inputs]
            input_quantity = 0
            template_qty = production.production_template.quantity
            for enology in production.enology_products:
                move = production._move(production.picking_location,
                    production.location,
                    production.company,
                    enology.product,
                    enology.uom.id,
                    enology.quantity)
                move.production_input = production
                moves.append(move)
                input_quantity += Uom.compute_qty(enology.uom, enology.quantity,
                    production.production_template.uom, round=True)
            enology_products = (production.production_template and
                production.production_template.enology_products or [])
            for enology in enology_products:
                quantity = Uom.compute_qty(enology.uom, enology.quantity,
                    production.production_template.uom, round=True)
                qty = quantity * (input_quantity or 1) / template_qty
                qty = enology.uom.round(qty)
                move = production._move(production.picking_location,
                    production.location,
                    production.company,
                    enology.product,
                    enology.uom.id,
                    float(qty))
                move.production_input = production
                moves.append(move)

            for output_product in production.production_template.outputs:
                delete_outputs += [x for x in production.output_distribution]
                od = OutputDistribution()
                od.product = output_product
                od.uom = od.on_change_with_uom()
                od.production = production
                outputs.append(od)

            values = {}
            if (not production.cost_distribution_template
                    and production.production_template
                    and production.production_template.cost_distribution_template):
                values['cost_distribution_template'] = production.production_template.cost_distribution_template
            if not production.cost_distributions:
                if production.cost_distribution_template:
                    cost_distribution_template = production.cost_distribution_template
                elif production.production_template:
                    cost_distribution_template = production.production_template.cost_distribution_template
                else:
                    cost_distribution_template = None
                if cost_distribution_template:
                    cost_distributions = []
                    for c in cost_distribution_template.cost_distribution_templates:
                        cost_distributions.append(c.cost_distribution)
                    if cost_distributions:
                        values['cost_distributions'] = [('add', cost_distributions)]
            if values:
                to_write.extend(([production], values))

        OutputDistribution.delete(delete_outputs)
        OutputDistribution.save(outputs)
        Move.save(moves)
        Move.delete(delete)

        if to_write:
            cls.write(*to_write)

        super().wait(productions)

    def create_variant(self, template, pass_feature):
        Product = Pool().get('product.product')
        product = Product()
        product.template = template
        return product

    def pass_feature(self, product):
        Variety = Pool().get('product.variety')
        Uom = Pool().get('product.uom')
        total_output = sum([Uom.compute_qty(x.uom, x.quantity,
            x.product.default_uom)
            for x in self.inputs if x.product.template in
                self.production_template.inputs])
        vintages = []
        do = []
        ecologicals = []
        for input in self.inputs:
            vintages += input.product.vintages
            do += input.product.denominations_of_origin
            ecologicals = input.product.ecologicals

        product.denominations_of_origin = list(set(do))
        product.ecologicals = list(set(ecologicals))
        product.vintages = list(set(vintages))
        varieties = {}
        for input in self.inputs:
            percent = round(input.quantity/total_output, 6)
            for variety in input.product.varieties:
                new_variety = varieties.get(variety.variety)
                if not new_variety:
                    new_variety = Variety()
                    new_variety.percent = 0
                new_variety.variety = variety.variety
                new_variety.percent += variety.percent/100.0*percent
                varieties[new_variety.variety] = new_variety
        for key, variety in varieties.items():
            variety.percent = "%.4f" % round(100.0*variety.percent, 4)
        product.varieties = varieties.values()
        return product

    @classmethod
    def done(cls, productions):
        Move = Pool().get('stock.move')
        moves = []
        for production in productions:
            for distrib in production.output_distribution:
                product = production.create_variant(distrib.product,
                    production.production_template.pass_feature)
                product = production.pass_feature(product)
                move = production._move(
                    production.location,
                    distrib.location,
                    production.company,
                    product,
                    distrib.uom,
                    distrib.produced_quantity)
                move.production_output = production
                move.unit_price = Decimal(0)
                moves.append(move)
        Move.save(moves)
        super().done(productions)

    @classmethod
    def set_cost(cls, productions):
        pool = Pool()
        Move = pool.get('stock.move')

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
                for cdist in production.cost_distributions:
                    products = cdist.template.products
                    if output.product not in products:
                        continue
                    has_product = True
                    cost = production_cost * (1 + cdist.percentatge) - production_cost
                    quantity = Decimal(str(output.quantity))
                    output_cost += round_price(cost / quantity)

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
    product = fields.Many2One('product.template', 'Template', required=True)
    location = fields.Many2One('stock.location', 'Location',
        states={
            'required': Eval('production_state').in_(['done'])
        }, depends=['production_state'])
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
            quantities = Product.get_quantity(self.product.products, 'quantity')
        self.initial_quantity = sum(quantities.values())

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
        context = Transaction().context
        context['locations'] = [self.location.id]
        with Transaction().set_context(context):
            quantities = Product.get_quantity(self.product.products, 'quantity')
        return sum(quantities.values())

    @fields.depends('final_quantity', 'initial_quantity')
    def on_change_with_produced_quantity(self, name=None):
        return ((self.final_quantity or 0) -
            (self.initial_quantity or 0))


class ProductionEnologyProduct(ModelSQL, ModelView):
    'Production Enology Product'
    __name__ = 'production.enology.product'
    production = fields.Many2One('production', 'Production',
        select=True)
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


class ProductionProductionCostPriceDistribution(ModelSQL):
    'Production - Production Cost Price Distribution'
    __name__ = 'production-production.distribution.cost_price'
    production = fields.Many2One('production', 'Production', ondelete='CASCADE',
        required=True, select=True)
    cost_distribution = fields.Many2One('production.cost_price.distribution',
        "Cost Distribution",
        ondelete='CASCADE', required=True, select=True)


class ProductionCostPriceDistribution(ModelSQL, ModelView):
    "Production Distribution Cost Price"
    __name__ = 'production.cost_price.distribution'
    template = fields.Many2One('product.template', "Template", required=True,
        ondelete='RESTRICT')
    percentatge = fields.Numeric("Percentatge", digits=(16, 4), required=True)

    @classmethod
    def __setup__(cls):
        BOMInput = Pool().get('production.bom.input')
        super(ProductionCostPriceDistribution, cls).__setup__()
        cls.template.domain = [('type', 'in', BOMInput.get_product_types())]

    def get_rec_name(self, name):
        return '%s - %s' % (self.template.rec_name, self.percentatge * 100)


class ProductionCostPriceDistributionTemplate(ModelSQL, ModelView):
    "Production Cost Price Distribution Template"
    __name__ = 'production.cost_price.distribution.template'
    name = fields.Char("Name", required=True)
    production_template = fields.Many2One('production.template',
        "Production Template", required=True)
    cost_distribution_templates = fields.One2Many(
        'production.cost_price.distribution.templates',
        'cost_distribution_template', "Cost Distribution Templates")

    @classmethod
    def validate(cls, templates):
        super(ProductionCostPriceDistributionTemplate, cls).validate(templates)
        for template in templates:
            template.check_percentatge()

    def check_percentatge(self):
        percentatge = sum(t.cost_distribution.percentatge
            for t in self.cost_distribution_templates)
        if percentatge != 1:
            raise ValidationError(
                gettext('agronomics.msg_check_cost_distribution_template_percentatge',
                    distribution=self.rec_name,
                    percentatge=percentatge * 100,
                    ))


class ProductionDistributionCostPriceTemplates(ModelSQL, ModelView):
    'Production Distribution Cost Price Templates'
    __name__ = 'production.cost_price.distribution.templates'
    cost_distribution_template = fields.Many2One(
        'production.cost_price.distribution.template',
        "Cost Distribution Template", ondelete='CASCADE',
        required=True, select=True)
    cost_distribution = fields.Many2One(
        'production.cost_price.distribution',
        "Cost Distribution",
        ondelete='CASCADE', required=True, select=True)


class ProductionCostPriceDistributionTemplateProductTemplate(ModelSQL, ModelView):
    "Production Cost Price Distribution Template - Product Template"
    __name__ = 'production.cost_price.distribution.template-product.template'
    _table = 'production_cost_price_dist_tpl-product_tpl_rel'
    distribution_template = fields.Many2One(
        'production.cost_price.distribution.template',
        "Distribution Template", ondelete='CASCADE', required=True, select=True)
    product_template = fields.Many2One('product.template',
        "Product Template", ondelete='CASCADE', required=True, select=True)


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
        Templates = pool.get('production.cost_price.distribution.templates')

        to_create = []
        for record in self.records:
            tpl = Template()
            tpl.name = self.ask.name
            tpl.production_template = record
            cost_distributions = []
            for cost_distribution in self.ask.cost_distribution_templates:
                template = Templates()
                dt = Distribution()
                dt.template = cost_distribution.template
                dt.percentatge = cost_distribution.percentatge
                template.cost_distribution = dt
                cost_distributions.append(template)
            if cost_distributions:
                tpl.cost_distribution_templates = cost_distributions
            to_create.append(tpl._save_values)
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
            if ptpl.cost_distribution_template:
                cost_distributions = []
                for c in ptpl.cost_distribution_template.cost_distribution_templates:
                    cost_distributions.append({
                        'template': c.cost_distribution.template.id,
                        'percentatge': c.cost_distribution.percentatge,
                        })
                default['cost_distribution_templates'] = cost_distributions
        return default
