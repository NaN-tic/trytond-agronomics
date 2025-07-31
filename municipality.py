from trytond.model import ModelSQL, ModelView, Unique, fields


class Municipality(ModelSQL, ModelView):
    'SIGPAC Municipality'
    __name__ = 'agronomics.sigpac.municipality'

    code = fields.Char('Cadastral Code', required=True, size=5)
    region = fields.Char('Region')
    province = fields.Char('Province')
    municipality = fields.Char('Municipality')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        cls._order.insert(0, ('code', 'ASC'))
        cls._sql_constraints += [
            ('code_unique', Unique(t, t.code), 'agronomics.msg_code_unique'),
            ('sequence_unique', Unique(t, t.region, t.province, t.municipality),
                'agronomics.msg_sequence_unique'),]

    def get_rec_name(self, name):
        return f'{self.municipality} ({self.code})'
