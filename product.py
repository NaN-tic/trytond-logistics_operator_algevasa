# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import ModelView, fields
from trytond.pyson import Eval
from trytond.config import config
from .algevasa import _requests


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'

    algevasa = fields.Boolean('Algevasa',
        states={
            'invisible': Eval('type') == 'service',
            },
        help="Work with Algevasa, a Logitiscs Operator")
    algevasa_synched = fields.Boolean('Algevasa Synched', readonly=True,
        states={
            'invisible': ~Eval('algevasa'),
            },)
    algevasa_synch_message = fields.Text('Algevasa Synch Message', readonly=True,
        states={
            'invisible': ~Eval('algevasa'),
            },)

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._buttons.update({
                'sync_with_algevasa': {
                    'invisible': ~Eval('algevasa', False)
                    },})

    @property
    def algevasa_owner(self):
        return config.get('algevasa', 'owner') or ''

    @property
    def algevasa_key(self):
        return config.get('algevasa', 'key') or ''

    @staticmethod
    def default_algevasa():
        return False

    @classmethod
    def generate_algevasa_product_file(cls, products):
        pool = Pool()
        Location = pool.get('stock.location')

        result = {}
        warehouses = Location.search([
                ('type', '=', 'warehouse'),
                ('active', '=', True),
                ('algevasa', '=', True),
                ('algevasa_product_format', '!=', None),
                ])
        products = [product for product in products if product.algevasa]
        for warehouse in warehouses:
            result.update(warehouse.algevasa_product_format.export_file(
                    products))
        return result

    @classmethod
    def update_algevasa_product(cls, products):
        prods = cls.generate_algevasa_product_file(products)
        for prod, data in prods.items():
            response = _requests('POST', data=data)
            prod.algevasa_synch_message = response.get('message', '')
            if (response.get('code') == 200
                and response.get('answer') == 'TRUE'):
                    prod.algevasa_synched = True
            prod.save()

    @classmethod
    @ModelView.button
    def sync_with_algevasa(cls, products):
        cls.update_algevasa_product(products)

