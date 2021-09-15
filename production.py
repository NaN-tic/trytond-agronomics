# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Bool, If
from trytond.exceptions import UserError
from trytond.i18n import gettext
from decimal import Decimal
from trytond.transaction import Transaction

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

    @fields.depends('uom')
    def on_change_with_unit_digits(self, name=None):
        if self.uom:
            return self.uom.digits
        return 2

    @classmethod
    def check_input_uoms(cls, records):
        for record in records:
            category_uom = record.uom.category
            uoms = [i.default_uom.category for i in record.inputs]
            uoms.append(category_uom)
            if len(list(set(uoms))) > 1:
                raise UserError(gettext('agronomics.msg_uom_not_fit',
                    production=record.rec_name,
                    uom=record.uom.rec_name,
                    uoms=",".join([x.rec_name for x in set(uoms)])))

    @classmethod
    def validate(cls, records):
        super().validate(records)
        cls.check_input_uoms(records)


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
        'Production Template')
    enology_products = fields.One2Many('production.enology.product',
        'production', "Enology Products",
        domain=[('product', 'in', Eval('allowed_enology_products')),
                If((Eval('state').in_(['waiting', 'draft'])),
                    ('product.quantity', '>', 0), ())],
        states={
            'invisible': ~Bool(Eval('production_template'))
        }, depends=['allowed_enology_products', 'state'])
    output_distribution = fields.One2Many('production.output.distribution',
        'production', 'Output Distribution',
        # domain=[('product', 'in', Eval('allowed_ouput_products'))],
        states={
            'invisible': ~Bool(Eval('production_template'))
        }, depends=['allowed_output_products'])
    allowed_enology_products = fields.Function(fields.One2Many(
        'product.product', None, 'Allowed Enology Products', readonly=True),
        'on_change_with_allowed_enology_products',
        setter='set_allowed_products')
    allowed_output_products = fields.Function(fields.One2Many(
        'product.template', None, 'Allowed Output Products', readonly=True),
        'on_change_with_allowed_output_products',
        setter='set_allowed_products')

    @classmethod
    def set_allowed_products(cls, productions, name, value):
        pass

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

    @classmethod
    def wait(cls, productions):
        Move = Pool().get('stock.move')
        Uom = Pool().get('product.uom')
        OutputDistribution = Pool().get('production.output.distribution')
        moves = []
        delete = []
        outputs = []
        delete_outputs = []
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

        OutputDistribution.delete(delete_outputs)
        OutputDistribution.save(outputs)
        Move.save(moves)
        Move.delete(delete)
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
