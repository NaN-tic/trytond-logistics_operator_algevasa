# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import json

from trytond.pool import Pool, PoolMeta
from trytond.model import ModelView, fields
from trytond.pyson import Eval
from itertools import groupby
from trytond.rpc import RPC
from trytond.config import config
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserError
from .algevasa import _requests, parse_xml


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
    not_synch_algevasa = fields.Boolean('Not Synch Algevasa',
        states={
            'invisible': ~Eval('algevasa_warehouse')
            })
    algevasa_synch_message = fields.Text('Algevasa Synch Message', readonly=True,
        states={
            'invisible': ~Eval('algevasa_warehouse')
            })
    algevasa_number = fields.Char('Algevasa Number', readonly=True)
    algevasa_status = fields.Text('Algevasa Status', readonly=True,
        states={
            'invisible': ~Eval('algevasa_warehouse')
            })
    algevasa_message = fields.Text('Algevasa Message', readonly=True,
        states={
            'invisible': ~Eval('algevasa_warehouse')
            })

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.__rpc__.update({
                'algevasa_response': RPC(readonly=False),
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
        if self.warehouse and self.warehouse.algevasa:
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
            if (warehouse and warehouse.algevasa
                    and warehouse.algevasa_shipment_format):
                ships = []
                for shipment in shipments:
                    if shipment.not_synch_algevasa:
                        continue
                    ships.append(shipment)
                result.update(warehouse.algevasa_shipment_format.export_file(
                        list(ships)))
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
        pool = Pool()
        ShipmentOut = pool.get('stock.shipment.out')

        if not data:
            return {
                'response': 'KO',
                'answer': 'There are no date to process',
                }
        company = Transaction().context.get('company', None)
        if not company:
            return {
                'response': 'KO',
                'answer': ('There request has not the company in the '
                    'context and it is required'),
                }
        result = parse_xml(data.get('data'))
        number = result.get('NUMDOC')
        if (not result.get('OPERACION', None) == 'ALBARANVENTA'
                or not number):
            return {
                'response': 'KO',
                'answer': ('This file is not a ALVARANVENTA type or has not a '
                    'correct NUMDOC'),
                }
        # If for example the sequence of the Shipment is repeted for each year,
        # try to get the newest shipment to compare the values.
        shipments = ShipmentOut.search([
                ('company.id', '=', company),
                ('number', '=', number),
                ('state', '=', 'done'),
                ], order=[('effective_date', 'DESC')], limit=1)
        shipment = shipments[0] if shipments else None
        if not shipment:
            return {
                'response': 'KO',
                'answer': ('The shipment number %s does not exist or is not '
                    'process yet.' % number),
                }
        if not shipment.algevasa_synched:
            return {
                'response': 'KO',
                'answer': ('The shipment reference exist, but It is not '
                    'check as as synched')
                }
        status = ''
        response = ''
        answer = ''
        lines = {x.id: {
            'code': x.product.code,
            'qty': x.quantity,
            } for x in shipment.outgoing_moves}
        items = result.get('ITEMS', {}).get('ITEM', [])
        if not items:
            response = 'KO'
            answer += 'There is not ITEMS.'
        for item in items:
            code = str(item.get('CODART', None))
            qty = (float(item['CANTIDAD_PED'])
                if item.get('CANTIDAD_PED', None) else 0)
            qty_served = (float(item['CANTIDAD_SER'])
                if item.get('CANTIDAD_SER', None) else 0)

            key = next((k for k, v in lines.items()
                    if v['code'] == code and v['qty'] == qty), None)
            if key is not None:
                lines.pop(key)
            else:
                response = 'KO'
                answer += (f'The ITEM with values CODART = {code} and '
                    f'CANTIDAD_PED = {qty} and CANTIDAD_SER = '
                    f'{qty_served} is not found in the shipment.\n')
                status += ('There is a line served that it is not in '
                    'the shipment: %s\n\n' % item)
                continue
            if qty != qty_served:
                status += (f'Line with product code {code} and quantity {qty} '
                    f'has serverd only {qty_served}\n\n')
        if lines:
            status += ('There are lines not served:'
                '%s\n\n' % '\n'.join([
                        'Product: %s, Qty: %s' % (
                            x.product.code, x.quantity)
                        for x in lines]))

        if not response:
            response = 'OK'
            answer = 'Shipment updated'
        if not status:
            status = 'OK'
        shipment.algevasa_status = status
        shipment.algevasa_number = result.get('NUMALB', '')
        shipment.algevasa_message = json.dumps(result, indent=4)
        shipment.save()
        return {
            'response': response,
            'answer': answer
            }
