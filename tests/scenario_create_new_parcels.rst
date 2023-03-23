===========================
Create new Parcel Scenario
===========================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()
    >>> yesterday = today - relativedelta(days=1)
    >>> before_yesterday = yesterday - relativedelta(days=1)

Activate modules::

    >>> config = activate_modules('agronomics')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create party::

    >>> Party = Model.get('party.party')
    >>> party = Party(name='Party')
    >>> party.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> liter, = ProductUom.find([('name', '=', 'Liter')])
    >>> kg, = ProductUom.find([('name', '=', 'Kilogram')])

    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> Taxon = Model.get('product.taxon')
    >>> DO = Model.get('agronomics.denomination_of_origin')
    >>> Ecological = Model.get('agronomics.ecological')

Create Denomination Of Origin::

    >>> catalunya = DO()
    >>> catalunya.name = 'Catalunya'
    >>> catalunya.save()

    >>> barcelona = DO()
    >>> barcelona.name = 'Barcelona'
    >>> barcelona.save()

Create Specie::

    >>> species = Taxon()
    >>> species.rank = 'species'
    >>> species.name = 'Species'
    >>> species.save()

Create Variety::

    >>> macabeu = Taxon()
    >>> macabeu.rank = 'variety'
    >>> macabeu.name = 'Macabeu'
    >>> macabeu.save()

    >>> parellada = Taxon()
    >>> parellada.rank = 'variety'
    >>> parellada.name = 'Parellada'
    >>> parellada.save()

Create Ecological::

    >>> ecological = Ecological()
    >>> ecological.name = 'Ecological'
    >>> ecological.save()

Create Crop::

    >>> Crop = Model.get('agronomics.crop')
    >>> crop = Crop()
    >>> crop.name = str(today.year)
    >>> crop.code = str(today.year)
    >>> crop.start_date = datetime.date(today.year, 1, 1)
    >>> crop.end_date = datetime.date(today.year, 12, 31)
    >>> crop.save()

Create Next Crop::

    >>> next_crop = Crop()
    >>> next_crop.name = str(today.year + 1)
    >>> next_crop.code = str(today.year + 1)
    >>> next_crop.start_date = datetime.date(today.year +1 , 1, 1)
    >>> next_crop.end_date = datetime.date(today.year +1, 12, 31)
    >>> next_crop.save()

Create Plantation::

    >>> Plantation = Model.get('agronomics.plantation')
    >>> plantation = Plantation()
    >>> plantation.party = party
    >>> plantation.code = 'Plantation'
    >>> plantation.plantation_year = today.year
    >>> enclosure = plantation.enclosures.new()
    >>> enclosure = plantation.enclosures.new()
    >>> parcel = plantation.parcels.new()
    >>> parcel.crop = crop
    >>> parcel.species = species
    >>> parcel.variety = macabeu
    >>> parcel.ecological = ecological
    >>> parcel.surface = 100
    >>> parcel2 = plantation.parcels.new()
    >>> parcel2.crop = crop
    >>> parcel2.species = species
    >>> parcel2.variety = macabeu
    >>> parcel2.ecological = ecological
    >>> parcel2.surface = 200
    >>> plantation.save()

Search for parcels::

    >>> Parcel = Model.get('agronomics.parcel')
    >>> parcels = Parcel.find([])
    >>> len(parcels)
    2

Create New Parcels for next Year::

    >>> wizard = Wizard('agronomics.create_new_parcels')
    >>> wizard.form.previous_crop = crop
    >>> wizard.form.next_crop = next_crop
    >>> wizard.execute('copy_parcels')

Search for parcels::

    >>> Parcel = Model.get('agronomics.parcel')
    >>> parcels = Parcel.find([])
    >>> len(parcels)
    4

Search 2 parcels from next_crop::

    >>> Parcel = Model.get('agronomics.parcel')
    >>> parcels = Parcel.find([('crop', '=', next_crop.id)])
    >>> len(parcels)
    2
