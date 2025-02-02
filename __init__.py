# This file is part logistics_operator_algevasa module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool

from . import configuration, location, stock, product

def register():
    Pool.register(
        configuration.Configuration,
        location.Location,
        stock.ShipmentOut,
        product.Product,
        module='logistics_operator_algevasa', type_='model')
