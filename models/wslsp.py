# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2017 E-MIPS (http://www.e-mips.com.ar)
#    Copyright (c) 2017 Eynes (http://www.eynes.com.ar)
#    All Rights Reserved. See AUTHORS for details.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import _, api, exceptions, fields, models
from openerp.exceptions import except_orm
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from  openerp.addons.l10n_ar_wslsp.wslsptools.wslsp_easywsy import WSLSP

import logging

_logger = logging.getLogger(__name__)

class WSLSPConfig(models.Model):
    _name = "wslsp.config"
    _description = "Configuration for WSLSP"

    _webservice_class = WSLSP

    name = fields.Char('Name', size=64, required=True)
    cuit = fields.Char(related='company_id.partner_id.vat', string='Cuit')
    url = fields.Char('URL for WSLSP', size=60, required=True)
    company_id = fields.Many2one('res.company', 'Company Name' , required=True)
    homologation = fields.Boolean('Homologation', default=False,
            help="If true, there will be some validations that are disabled, for example, invoice number correlativeness")
    point_of_sale_ids = fields.Many2many('pos.ar', 'pos_ar_wslsp_rel', 'wslsp_config_id', 'pos_ar_id', 'Points of Sale')
    wsaa_ticket_id = fields.Many2one('wsaa.ta', 'Ticket Access')

    categories_ids = fields.One2many('wslsp.category.codes', 'wslsp_config_id' , 'Categories')
    cut_ids = fields.One2many('wslsp.cut.codes', 'wslsp_config_id' , 'Cuts')
    participant_character_ids = fields.One2many('wslsp.participant_character.codes', 'wslsp_config_id' , 'Participant characters')
    expenses_ids = fields.One2many('wslsp.expenses.codes', 'wslsp_config_id' , 'Expenses')
    motive_ids = fields.One2many('wslsp.motive.codes', 'wslsp_config_id' , 'Motives')
    operation_ids = fields.One2many('wslsp.operation.codes', 'wslsp_config_id' , 'Operations')
    province_ids = fields.One2many('wslsp.province.codes', 'wslsp_config_id' , 'Provinces')
    breed_ids = fields.One2many('wslsp.breed.codes', 'wslsp_config_id' , 'Breeds')
    voucher_type_ids = fields.One2many('wslsp.voucher_type.codes', 'wslsp_config_id' , 'Voucher Types')
    liquidation_type_ids = fields.One2many('wslsp.liquidation_type.codes', 'wslsp_config_id' , 'Liquidation Types')
    tax_ids = fields.One2many('wslsp.tax.codes', 'wslsp_config_id' , 'Tax Types')

    #currency_ids = fields.One2many('wsfex.currency.codes', 'wsfex_config_id' , 'Currencies')

    _defaults = {
        'company_id' : lambda self, cr, uid, context=None: self.pool.get('res.users')._get_company(cr, uid, context=context),
        }

    @api.multi
    def create(self, vals):
        # Creamos tambien un TA para este servcio y esta compania
        ta_obj = self.env['wsaa.ta']
        wsaa_obj = self.env['wsaa.config']
        service_obj = self.env['afipws.service']

        # Buscamos primero el wsaa que corresponde a esta compania
        # porque hay que recordar que son unicos por compania
        wsaa_ids = wsaa_obj.search([('company_id','=', vals['company_id'])]).ids
        service_ids = service_obj.search([('name','=', 'wslsp')]).ids
        if wsaa_ids:
            ta_vals = {
                'name': service_ids[0],
                'company_id': vals['company_id'],
                'config_id' : wsaa_ids[0],
                }

            ta_id = ta_obj.create(ta_vals)
            vals['wsaa_ticket_id'] = ta_id

        return super(WSLSPConfig, self).create(vals)

    @api.model
    def get_config(self):
        # Obtenemos la compania que esta utilizando en este momento este usuario
        company_id = self.env.user.company_id.id
        if not company_id:
            raise except_orm(_('Company Error!'), _('There is no company being used by this user'))

        config = self.search([('company_id','=',company_id)])
        if not config:
            raise except_orm(_('WSLSP Config Error!'), _('There is no WSLSP configuration set to this company'))
        return config

    def get_motive_code(self, billing_type):
        motives = self.motive_ids.filtered(lambda x: x.billing_type == billing_type)
        if not motives:
            raise except_orm(_('WSLSP Config Error!'),
                    _('The wslsp does not have a configuration for the motives [%s]') %(billing_type))
        return motives[0].code

    def get_liquidation_type_code(self, billing_type):
        liquidation_types = self.liquidation_type_ids.filtered(lambda x: x.billing_type == billing_type)
        if not liquidation_types:
            raise except_orm(_('WSLSP Config Error!'),
                    _('The wslsp does not have a configuration for the liquidation types [%s]') %(billing_type))
        return liquidation_types[0].code

    def get_category_code(self, species):
        categories = self.categories_ids.filtered(lambda x: x.species_id.id == species.id)
        if not categories:
            raise except_orm(_('WSLSP Config Error!'),
                    _('The wslsp does not have a configuration for the categories [%s]') %(species.name))
        return categories[0].code

    def get_operation_code(self, billing_type):
        operations = self.operation_ids.filtered(lambda x: x.billing_type == billing_type)
        if not operations:
            raise except_orm(_('WSLSP Config Error!'),
                    _('The wslsp does not have a configuration for the operations [%s]') %(billing_type))
        return operations[0].code

    @api.multi
    def _get_wslsp_obj(self):
        self.ensure_one()
        ws = self._webservice_class(self, self.url)
        return ws

    #TODO: Arreglar esta funcion
    @api.multi
    def get_server_state(self):
        conf = self
        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(conf.cuit, token, sign, conf.url)
        res = _wslsp.dummy()
        return res

    @api.multi
    def get_wslsp_categories(self):
        ws = self._get_wslsp_obj()
        category_lst = ws.get_categories()
        for category in category_lst:
            res = self.categories_ids.filtered(lambda x: x.code ==  category['code'])
            if not res:
                self.write({'categories_ids' : [(0, False, category)]})
            else :
                self.write({'categories_ids' : [(1, res.id, category)]})
        return True

    @api.multi
    def get_wslsp_cuts(self):
        ws = self._get_wslsp_obj()
        cut_lst = ws.get_cuts()
        for cut in cut_lst:
            res = self.cut_ids.filtered(lambda x: x.code ==  cut['code'])
            if not res:
                self.write({'cut_ids' : [(0, False, cut)]})
            else:
                self.write({'cut_ids' : [(1, res.id, cut)]})
        return True

    @api.multi
    def get_wslsp_participant_characters(self):
        ws = self._get_wslsp_obj()
        part_lst = ws.get_participant_characters()
        for part in part_lst:
            res = self.participant_character_ids.filtered(lambda x: x.code ==  part['code'])
            if not res:
                self.write({'participant_character_ids' : [(0, False, part)]})
            else:
                self.write({'participant_character_ids' : [(1, res.id, part)]})
        return True

    @api.multi
    def get_wslsp_expenses(self):
        ws = self._get_wslsp_obj()
        expense_lst = ws.get_expenses()
        for expense in expense_lst:
            res = self.expenses_ids.filtered(lambda x: x.code ==  expense['code'])
            if not res:
                self.write({'expenses_ids' : [(0, False, expense)]})
            else:
                self.write({'expenses_ids' : [(1, res.id, expense)]})
        return True

    @api.multi
    def get_wslsp_motives(self):
        ws = self._get_wslsp_obj()
        motive_lst = ws.get_motives()
        for motive in motive_lst:
            res = self.motive_ids.filtered(lambda x: x.code ==  motive['code'])
            if not res:
                self.write({'motive_ids' : [(0, False, motive)]})
            else:
                self.write({'motive_ids' : [(1, res.id, motive)]})
        return True

    @api.multi
    def get_wslsp_operations(self):
        ws = self._get_wslsp_obj()
        operation_lst = ws.get_operations()
        for operation in operation_lst:
            res = self.operation_ids.filtered(lambda x: x.code ==  operation['code'])
            if not res:
                self.write({'operation_ids' : [(0, False, operation)]})
            else:
                self.write({'operation_ids' : [(1, res.id, operation)]})
        return True

    @api.multi
    def get_wslsp_provinces(self):
        ws = self._get_wslsp_obj()
        province_lst = ws.get_states()
        for province in province_lst:
            res = self.province_ids.filtered(lambda x: x.code ==  province['code'])
            if not res:
                self.write({'province_ids' : [(0, False, province)]})
            else:
                self.write({'province_ids' : [(1, res.id, province)]})
        return True

    @api.multi
    def get_wslsp_breeds(self):
        ws = self._get_wslsp_obj()
        breed_lst = ws.get_breeds()
        for breed in breed_lst:
            res = self.breed_ids.filtered(lambda x: x.code ==  breed['code'])
            if not res:
                self.write({'breed_ids' : [(0, False, breed)]})
            else:
                self.write({'breed_ids' : [(1, res.id, breed)]})
        return True

    @api.multi
    def get_wslsp_voucher_types(self):
        ws = self._get_wslsp_obj()
        voucher_type_lst = ws.get_voucher_type()
        for voucher_type in voucher_type_lst:
            res = self.voucher_type_ids.filtered(lambda x: x.code ==  voucher_type['code'])
            if not res:
                self.write({'voucher_type_ids' : [(0, False, voucher_type)]})
            else:
                self.write({'voucher_type_ids' : [(1, res.id, voucher_type)]})
        return True

    @api.multi
    def get_wslsp_liquidation_types(self):
        ws = self._get_wslsp_obj()
        liquidation_lst = ws.get_liquidation_type()
        for liquidation in liquidation_lst:
            res = self.liquidation_type_ids.filtered(lambda x: x.code ==  liquidation['code'])
            if not res:
                self.write({'liquidation_type_ids' : [(0, False, liquidation)]})
            else:
                self.write({'liquidation_type_ids' : [(1, res.id, liquidation)]})
        return True

    @api.multi
    def get_wslsp_taxes(self):
        ws = self._get_wslsp_obj()
        taxes_lst = ws.get_tributes()
        for taxes in taxes_lst:
            res = self.tax_ids.filtered(lambda x: x.code ==  taxes['code'])
            if not res:
                self.write({'tax_ids' : [(0, False, taxes)]})
            else:
                self.write({'tax_ids' : [(1, res.id, taxes)]})
        return True

    def get_last_voucher(self, pos, voucher_type):
        ws = self._get_wslsp_obj()
        data = {'puntoVenta' : pos,
                'tipoComprobante' : voucher_type
                }
        number = ws.get_last_voucher_number(pos, voucher_type)
        return number
