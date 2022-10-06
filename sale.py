# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval, Id


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
            'readonly': Eval('state') != 'draft',
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

    @classmethod
    def process(cls, sales):
        pool = Pool()
        Maquila = pool.get('agronomics.maquila')
        Line = pool.get('sale.line')

        super().process(sales)

        to_save = []
        for sale in sales:
            if not sale.is_maquila:
                continue

            for line in sale.lines:
                if line.maquila or not line.maquila_product:
                    continue

                maquila = Maquila()
                maquila.contract = contract # TODO
                maquila.crop = weighing.crop # TODO
                maquila.party = sale.party # TODO
                maquila.quantity = -1 # TODO negatiu
                maquila.product = line.maquila_product
                maquila.unit = line.maquila_product.default_uom
                maquila.save()
                line.maquila = maquila
                to_save.append(line)

        Line.save(to_save)


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'
    maquila_product = fields.Many2One('product.product', "Maquila Product",
        ondelete='RESTRICT',
        states={
            'invisible': ~Bool(Eval('_parent_sale', {}).get('is_maquila')),
            'readonly': Eval('sale_state') != 'draft',
        }, depends=['sale_state'])
    maquila = fields.Many2One('agronomics.maquila', "Maquila", readonly=True,
        states={
            'invisible': ~Bool(Eval('_parent_sale', {}).get('is_maquila')),
        })
