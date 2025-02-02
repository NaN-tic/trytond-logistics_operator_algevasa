# This file is part product_variant module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta


class Configuration(metaclass=PoolMeta):
    __name__ = 'product.configuration'

    auto_algevasa = fields.Boolean('Algevasa Automatic',
        help="Set Algevasa check automatically when create a Goods product.")

    @staticmethod
    def default_auto_algevasa():
        return False
