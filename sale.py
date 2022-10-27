# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval, Id, If


def default_func(field_name):
    @classmethod
    def default(cls, **pattern):
        return getattr(
            cls.multivalue_model(field_name),
            'default_%s' % field_name, lambda: None)()
    return default


class Configuration(metaclass=PoolMeta):
    __name__ = 'sale.configuration'
    maquila_sale_sequence = fields.MultiValue(fields.Many2One(
            'ir.sequence', "Maquila Sale Sequence", required=True,
            domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('sequence_type', '=', Id('agronomics', 'sequence_type_maquila_sale')),
                ]))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'maquila_sale_sequence':
            return pool.get('sale.configuration.sequence')
        return super(Configuration, cls).multivalue_model(field)

    default_maquila_sale_sequence = default_func('maquila_sale_sequence')


class ConfigurationSequence(metaclass=PoolMeta):
    __name__ = 'sale.configuration.sequence'
    maquila_sale_sequence = fields.Many2One(
        'ir.sequence', "Maquila Sale Sequence", required=True,
        domain=[
            ('company', 'in', [Eval('company', -1), None]),
            ('sequence_type', '=', Id('agronomics', 'sequence_type_maquila_sale')),
            ],
        depends=['company'])

    @classmethod
    def default_maquila_sale_sequence(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('agronomics', 'sequence_maquila_sale')
        except KeyError:
            return None


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'
    is_maquila = fields.Boolean("Is Maquila",
        states={
            'readonly': ((Eval('state') != 'draft') | (Eval('lines', [0]))),
            },
        depends=['state'])

    @fields.depends('is_maquila')
    def on_change_is_maquila(self):
        self.invoice_method = 'order' if self.is_maquila else self.default_invoice_method()

    @fields.depends('is_maquila')
    def on_change_party(self):
        super().on_change_party()
        if self.is_maquila:
            self.on_change_is_maquila()

    @classmethod
    def set_number(cls, sales):
        pool = Pool()
        Config = pool.get('sale.configuration')

        config = Config(1)
        for sale in sales:
            if sale.number:
                continue
            if sale.is_maquila:
                sale.number = config.get_multivalue(
                'maquila_sale_sequence', company=sale.company.id).get()
        super().set_number(sales)


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'
    maquila = fields.Many2One('agronomics.maquila.product_year', "Maquila",
        domain=[
            ('product', '=', Eval('product')),
            ('party', '=', Eval('_parent_sale', {}).get('party')),
        ],
        states={
            'invisible': ~Bool(Eval('_parent_sale', {}).get('is_maquila')),
            'required': Bool(Eval('_parent_sale', {}).get('is_maquila')),
            'readonly': Eval('sale_state') != 'draft',
        })
    liter_uom = fields.Function(fields.Many2One('product.uom', "Liter Uom"),
        'get_liter_uom')

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        cls.product.domain += [If( Bool(Eval('_parent_sale', {}).get('is_maquila')),
            ('sale_uom', '=', Eval('liter_uom')),
            ())]
        cls.product.depends += ['liter_uom']

    @classmethod
    def default_liter_uom(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')

        uom_liter_id = ModelData.get_id('product', 'uom_liter')
        return uom_liter_id

    @classmethod
    def get_liter_uom(cls, lines, name):
        uom_liter_id = cls.default_liter_uom()
        return dict((x.id, uom_liter_id) for x in lines)
