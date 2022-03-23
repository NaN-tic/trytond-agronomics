# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime
from trytond.pool import PoolMeta, Pool
from trytond.model import fields, Model, ModelSQL, ModelView
from trytond.pyson import Eval, Id
from trytond.modules.agronomics.wine import _WINE_DIGITS
from trytond.transaction import Transaction

class ConfigurationCompany(ModelSQL):
    'Company Quality configuration'
    __name__ = 'quality.configuration.company'

    company = fields.Many2One('company.company', 'Company')
    sample_sequence = fields.Many2One('ir.sequence',
            'Sample Sequence', domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('sequence_type', '=', Id('agronomics',
                    'sequence_type_sample')),
                ])

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class Configuration(metaclass=PoolMeta):
    __name__ = 'quality.configuration'

    sample_sequence = fields.Function(fields.Many2One('ir.sequence',
            'Sample Sequence', domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('sequence_type', '=', Id('agronomics',
                    'sequence_type_sample')),
                ]),
        'get_company_config', setter='set_company_config')

    @classmethod
    def get_company_config(cls, configs, names):
        pool = Pool()
        CompanyConfig = pool.get('quality.configuration.company')
        res = dict.fromkeys(names, {configs[0].id: None})
        company_configs = CompanyConfig.search([], limit=1)
        if len(company_configs) == 1:
            company_config, = company_configs
            for field_name in set(names):
                value = getattr(company_config, field_name, None)
                if value:
                    res[field_name] = {configs[0].id: value.id}
        return res

    @classmethod
    def set_company_config(cls, configs, name, value):
        pool = Pool()
        CompanyConfig = pool.get('quality.configuration.company')
        company_configs = CompanyConfig.search([], limit=1)
        if len(company_configs) == 1:
            company_config, = company_configs
        else:
            company_config = CompanyConfig()
        setattr(company_config, name, value)
        company_config.save()


class QualitySample(ModelSQL, ModelView):
    'Quality Sample'
    __name__ = 'quality.sample'

    code = fields.Char('Code', select=True, readonly=True)
    reference = fields.Char('Reference')
    products = fields.Many2Many('product.product-quality.sample', 'sample',
        'product', "Products",
        context={
            'company': Eval('company'),
            },
        depends=['company'])
    collection_date = fields.DateTime('Collection Date', required=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        select=True)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_collection_date():
        return datetime.datetime.now()

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Config = pool.get('quality.configuration')

        sequence = Config(1).sample_sequence
        for value in vlist:
            if not value.get('code'):
                value['code'] = sequence.get()
        return super(QualitySample, cls).create(vlist)

    @classmethod
    def copy(cls, samples, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default['code'] = None
        return super(QualitySample, cls).copy(samples, default=default)

class ProductQualitySample(ModelSQL):
    'Product - Quality Sample'
    __name__ = 'product.product-quality.sample'

    product = fields.Many2One('product.product', 'Product', required=True,
        ondelete='CASCADE', select=True)
    sample = fields.Many2One('quality.sample', 'Sample', ondelete='CASCADE',
        required=True, select=True)


class QualityTest(metaclass=PoolMeta):
    __name__ = 'quality.test'

    @classmethod
    def confirmed(cls, tests):
        pool = Pool()
        Product = pool.get('product.product')
        ModelData = pool.get('ir.model.data')
        Date = pool.get('ir.date')

        super(QualityTest, cls).confirmed(tests)

        today = Date.today()

        # get all key from ir.model.data
        to_write = []
        proof_ids = []
        for test in tests:
            if not test.document or not isinstance(test.document, Product):
                continue

            proof_ids += [line.proof for line in test.quantitative_lines
                                    if line.proof]
        if not proof_ids:
            return

        datas = ModelData.search([
            ('module', '=', 'agronomics'),
            ('db_id', 'in', proof_ids),
            ('model', '=', 'quality.proof')
            ])
        data_key = dict((x.db_id, x.fs_id) for x in datas)

        # check all quantitative lines has key and update the product
        for test in tests:
            if not test.document or not isinstance(test.document, Product):
                continue

            values = {}
            for line in test.quantitative_lines:
                key = data_key.get(line.proof.id)
                if not key:
                    continue

                values[key] = round(line.value, _WINE_DIGITS)
                values[key + '_comment'] = line.internal_description
                values[key + '_confirm'] = today
                values[key + '_success'] = line.success

            if values:
                to_write.extend(([test.document], values))

        if to_write:
            Product.write(*to_write)


class TestLineMixin(Model):
    __slots__ = ()
    product = fields.Function(fields.Many2One('product.product', 'Product', select=True),
        'get_product', searcher='search_product')

    def get_product(self, name):
        Product = Pool().get('product.product')
        if isinstance(self.test.document, Product):
            return self.test.document.id

    @classmethod
    def search_product(cls, name, clause):
        Product = Pool().get('product.product')

        _, operator, value = clause[0:3]
        if isinstance(value, list):
            values = [('%s,%s' % ('product.product',
                v.id if isinstance(v, Product) else v)) for v in value]
        else:
            values = '%s,%s' % ('product.product',
                value.id if isinstance(value, Product) else value)
        return [('test.document', operator, values)]


class QuantitativeTestLine(TestLineMixin, metaclass=PoolMeta):
    __name__ = 'quality.quantitative.test.line'


class QualitativeTestLine(TestLineMixin, metaclass=PoolMeta):
    __name__ = 'quality.qualitative.test.line'
