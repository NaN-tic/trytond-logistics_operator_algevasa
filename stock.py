# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import ModelView, fields
from trytond.pyson import Eval
from itertools import groupby
from trytond.rpc import RPC
from trytond.config import config
from trytond.i18n import gettext
from trytond.exceptions import UserError
from .algevasa import _requests, _process_response


class ShipmentOut(metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'

    algevasa_warehouse = fields.Function(fields.Boolean('Algevasa Warehouse',
                states={
                    'invisible': ~Eval('algevasa_warehouse')
                }), 'on_change_with_algevasa_warehouse')
    algevasa_synched = fields.Boolean('Algevasa Synched', readonly=True,
        states={
            'invisible': ~Eval('algevasa_warehouse')
            })
    algevasa_synch_message = fields.Text('Algevasa Synch Message', readonly=True,
        states={
            'invisible': ~Eval('algevasa_warehouse')
            })
    algevasa_status = fields.Text('Algevasa Status', readonly=True,
        states={
            'invisible': ~Eval('algevasa_warehouse')
            })

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.__rpc__.update({
                'algevasa_response': RPC(),
                })
        cls._buttons.update({
                'sync_with_algevasa': {
                    'invisible': Eval('state') != 'done',
                    },
                })

    @fields.depends('warehouse')
    def on_change_with_algevasa_warehouse(self, name=None):
        return self.warehouse.algevasa if self.warehouse else False

    @property
    def algevasa_owner(self):
        return config.get('algevasa', 'owner') or ''

    @property
    def algevasa_key(self):
        return config.get('algevasa', 'key') or ''

    def check_shipment_product_algevasa(self):
        for move in self.outgoing_moves:
            if not move.product.algevasa_synched:
                raise UserError(
                    gettext(
                        'logistics_operator_algevasa.'
                        'msg_product_without_algevasa',
                        product=move.product.rec_name,
                        shipment=move.shipment.rec_name))

    @classmethod
    def generate_algevasa_shipment_file(cls, shipments):
        result = {}
        for warehouse, shipments in groupby(shipments,
                key=lambda m: m.warehouse):
            if warehouse and warehouse.algevasa_shipment_format:
                result.update(warehouse.algevasa_shipment_format.export_file(
                        list(shipments)))
        return result

    @classmethod
    def sync_algevasa_shipment(cls, shipments):
        ships = cls.generate_algevasa_shipment_file(shipments)
        for ship, data in ships.items():
            response = _requests('POST', data=data)
            ship.algevasa_synch_message = response.get('message', '')
            if (response.get('code') == 200 
                    and response.get('answer') == 'TRUE'):
                ship.algevasa_synched = True
            ship.save()

    @classmethod
    def done(cls, shipments):
        super().done(shipments)

        for shipment in shipments:
            shipment.check_shipment_product_algevasa()
        cls.sync_algevasa_shipment(shipments)

    @classmethod
    @ModelView.button
    def sync_with_algevasa(cls, shipments):
        for shipment in shipments:
            shipment.check_shipment_product_algevasa()
        cls.sync_algevasa_shipment(shipments)

    @classmethod
    def algevasa_response(cls, data=None):
        if not data:
            return
        result = _process_response(data)
