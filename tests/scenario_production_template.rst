===================
Production Scenario
===================

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

Create Taxon::

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

    # Raim Blanc
    >>> template = ProductTemplate()
    >>> template.name = 'Raim Blanc'
    >>> template.default_uom = kg
    >>> template.type = 'goods'
    >>> template.producible = True
    >>> template.list_price = Decimal(0)
    >>> product, = template.products
    >>> product.cost_price = Decimal(10)
    >>> template.save()
    >>> product, = template.products
    >>> productA = Product()
    >>> productA.code = "A"
    >>> productA.template = template
    >>> productA.denominations_of_origin.append(catalunya)
    >>> productA.save()
    >>> catalunya, = DO.find([('name', '=', 'Catalunya')])
    >>> productB = Product()
    >>> productB.code = "B"
    >>> productB.template = template
    >>> productB.denominations_of_origin.append(catalunya)
    >>> productB.save()
    >>> catalunya, = DO.find([('name', '=' , 'Catalunya')])
    >>> productC = Product()
    >>> productC.code = "C"
    >>> productC.template = template
    >>> productC.denominations_of_origin.append(catalunya)
    >>> productC.save()

Create Variety::

    >>> Variety = Model.get('product.variety')
    >>> AM = Variety()
    >>> AM.variety = macabeu
    >>> AM.percent = 100.0
    >>> AM.product = productA
    >>> AM.save()

    >>> BM = Variety()
    >>> BM.variety = macabeu
    >>> BM.percent = 100.0
    >>> BM.product = productB
    >>> BM.save()

    >>> CP = Variety()
    >>> CP.variety = parellada
    >>> CP.percent = 100.0
    >>> CP.product = productC
    >>> CP.save()

    # Sulforos
    >>> template = ProductTemplate()
    >>> template.name = 'Sulforos'
    >>> template.default_uom = kg
    >>> template.type = 'goods'
    >>> template.producible = True
    >>> template.list_price = Decimal(0)
    >>> product2, = template.products
    >>> product2.cost_price = Decimal(10)
    >>> template.save()
    >>> product2, = template.products

    # Encims
    >>> template = ProductTemplate()
    >>> template.name = 'Encims'
    >>> template.default_uom = kg
    >>> template.type = 'goods'
    >>> template.producible = True
    >>> template.list_price = Decimal(0)
    >>> product3, = template.products
    >>> product3.cost_price = Decimal(10)
    >>> template.save()
    >>> product3, = template.products

    # Carbo actiu
    >>> template = ProductTemplate()
    >>> template.name = 'Carbo actiu'
    >>> template.default_uom = kg
    >>> template.type = 'goods'
    >>> template.producible = True
    >>> template.list_price = Decimal(0)
    >>> product4, = template.products
    >>> product4.cost_price = Decimal(10)
    >>> template.save()
    >>> product4, = template.products

    # Most flor
    >>> mostflor = ProductTemplate()
    >>> mostflor.name = 'Most Flor'
    >>> mostflor.default_uom = liter
    >>> mostflor.type = 'goods'
    >>> mostflor.producible = True
    >>> mostflor.list_price = Decimal(0)
    >>> mostflor.save()
    >>> product5, = mostflor.products
    >>> product5.cost_price = Decimal(0)
    >>> product5.save()

    # Most Primeres
    >>> mostprimeres = ProductTemplate()
    >>> mostprimeres.name = 'Most Primeres'
    >>> mostprimeres.default_uom = liter
    >>> mostprimeres.type = 'goods'
    >>> mostprimeres.producible = True
    >>> mostprimeres.list_price = Decimal(0)
    >>> mostprimeres.save()
    >>> product6, = mostprimeres.products
    >>> product6.cost_price = Decimal(0)
    >>> product6.save()

Create Production Template::

    >>> ProductionTemplate = Model.get('production.template')
    >>> ProductionTemplateLine = Model.get("production.template.line")
    >>> production_template = ProductionTemplate()
    >>> production_template.name = 'Premsat i desfangat de raim blanc'
    >>> production_template.uom = kg
    >>> production_template.quantity = 10000
    >>> production_template.pass_feature = True
    >>> production_template.inputs.append(productA.template)
    >>> production_template.outputs.append(mostflor)
    >>> production_template.outputs.append(mostprimeres)
    >>> production_template.pass_quality = True
    >>> line = ProductionTemplateLine()
    >>> line.product = product2
    >>> line.quantity = 100
    >>> production_template.enology_products.append(line)
    >>> line = ProductionTemplateLine()
    >>> line.product = product3
    >>> line.quantity = 50
    >>> production_template.enology_products.append(line)
    >>> line = ProductionTemplateLine()
    >>> line.product = product4
    >>> line.quantity =150
    >>> production_template.enology_products.append(line)
    >>> production_template.save()

Create Test:

    >>> QualityTest = Model.get('quality.test')
    >>> Test = QualityTest()

Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory_line1 = InventoryLine()
    >>> inventory.lines.append(inventory_line1)
    >>> inventory_line1.product = productA
    >>> inventory_line1.quantity = 5000
    >>> inventory_line2 = InventoryLine()
    >>> inventory.lines.append(inventory_line2)
    >>> inventory_line2.product = productB
    >>> inventory_line2.quantity = 10000
    >>> inventory_line3 = InventoryLine()
    >>> inventory.lines.append(inventory_line3)
    >>> inventory_line3.product = productC
    >>> inventory_line3.quantity = 3000

    >>> inventory_line3 = InventoryLine()
    >>> inventory.lines.append(inventory_line3)
    >>> inventory_line3.product = product2
    >>> inventory_line3.quantity = 1000

    >>> inventory_line3 = InventoryLine()
    >>> inventory.lines.append(inventory_line3)
    >>> inventory_line3.product = product3
    >>> inventory_line3.quantity = 1000

    >>> inventory_line3 = InventoryLine()
    >>> inventory.lines.append(inventory_line3)
    >>> inventory_line3.product = product4
    >>> inventory_line3.quantity = 1000

    >>> inventory.click('confirm')
    >>> inventory.state
    'done'

Create Production

  >>> Production = Model.get('production')
  >>> EnologyProduct = Model.get('production.enology.product')
  >>> production = Production()
  >>> production.production_template = production_template
  >>> production.save()
  >>> line = EnologyProduct()
  >>> line.product = productA
  >>> line.production = production
  >>> line.quantity = 5000
  >>> line.save()
  >>> # production.enology_products.append(productA)
  >>> line = EnologyProduct()
  >>> line.product = productB
  >>> line.quantity = 10000
  >>> line.production = production
  >>> line.save()
  >>> # production.enology_products.append(productB)
  >>> line = EnologyProduct()
  >>> line.product = productC
  >>> line.quantity = 3000
  >>> line.production = production
  >>> line.save()
  >>> # production.enology_products.append(productC)
  >>> production.reload()
  >>> production.click('wait')
  >>> production.state
  'waiting'
  >>> len(production.inputs)
  6
  >>> input, = [i for i in production.inputs if i.product == product2]
  >>> input.quantity
  180.0
  >>> input, = [i for i in production.inputs if i.product == product3]
  >>> input.quantity
  90.0
  >>> input, = [i for i in production.inputs if i.product == product4]
  >>> input.quantity
  270.0

  >>> (o1, o2) = production.output_distribution
  >>> o1.location = storage
  >>> o1.final_quantity = 5000
  >>> o1.save()

  >>> o2.location = storage
  >>> o2.final_quantity = 10000
  >>> o2.save()

  >>> production.reload()
  >>> len(production.output_distribution)
  2
  >>> [x.name for x in production.allowed_enology_products]
  ['Raim Blanc', 'Raim Blanc', 'Raim Blanc', 'Raim Blanc']
  >>> [x.name for x in production.production_template.inputs]
  ['Raim Blanc']
  >>> production.click('assign_try')
  >>> production.click('run')
  >>> production.click('do')
  >>> len(production.outputs)
  2
  >>> most = production.outputs[0]
  >>> len(most.product.varieties)
  2
  >>> sorted([(x.variety.name, x.percent) for x in most.product.varieties], key=lambda x: x[1])
  [('Parellada', 16.6667), ('Macabeu', 83.3334)]
  >>> [x.name for x in most.product.denominations_of_origin]
  ['Catalunya']
