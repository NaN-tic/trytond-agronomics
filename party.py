# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    plantations = fields.One2Many('agronomics.plantation', 'party',
        'Plantation')
    parcels = fields.One2Many('agronomics.parcel', 'producer', 'Parcels')

    @classmethod
    def copy(cls, parties, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('plantations', None)
        default.setdefault('parcels', None)
        return super().copy(parties, default=default)
