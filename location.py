# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields
from trytond.pyson import Eval

class Location(metaclass=PoolMeta):
    __name__ = 'stock.location'

    algevasa = fields.Boolean('Algevasa',
        states={
            'invisible': Eval('type') != 'warehouse',
            },
        help="Work with Algevasa, a Logitiscs Operator")
    algevasa_product_format = fields.Many2One('file.format',
        'Algevasa Product File Format',
        states={
            'invisible': ~Eval('algevasa', False),
            'required': Eval('algevasa', False),
            },
        help="The template file useded to synch products to Algevasa")
    algevasa_shipment_format = fields.Many2One('file.format',
        'Algevasa Shipment File Format',
        states={
            'invisible': ~Eval('algevasa', False),
            'required': Eval('algevasa', False),
            },
        help="The template file useded to synch shipments to Algevasa")
    algevasa_on_done = fields.Boolean('Algevasa On Done',
        states={
            'invisible': Eval('type') != 'warehouse',
            },
        help="If checked the shipment is synched with Algevasa when 'Done' "
        "the shipment. If unchecked the synched happens in the 'Assign'")

    @staticmethod
    def default_algevasa():
        return False

    @staticmethod
    def default_algevasa_on_done():
        return False
