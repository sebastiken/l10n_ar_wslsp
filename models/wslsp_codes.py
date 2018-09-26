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

import logging


class WSLSPCategoryCodes(models.Model):
    _name = "wslsp.category.codes"
    _description = "WSLSP Category Codes"
    _order = 'code'

    ranch_type = fields.Selection([('cattle','Cattle'),('pork','Pork')], 'Ranch Type')
    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPCutCodes(models.Model):
    _name = "wslsp.cut.codes"
    _description = "WSLSP Cut Codes"
    _order = 'code'

    ranch_type = fields.Selection([('cattle','Cattle'),('pork','Pork')], 'Ranch Type')
    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPParticipantCharacterCodes(models.Model):
    _name = "wslsp.participant_character.codes"
    _description = "WSLSP Participant Character Codes"
    _order = 'code'


    ranch_type = fields.Selection([('cattle','Cattle'),('pork','Pork')], 'Ranch Type')
    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPExpensesCodes(models.Model):
    _name = "wslsp.expenses.codes"
    _description = "WSLSP Expenses Codes"
    _order = 'code'

    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPMotiveCodes(models.Model):
    _name = "wslsp.motive.codes"
    _description = "WSLSP Motives Codes"
    _order = 'code'

    autoliquidation = fields.Boolean('Autoliquidation')
    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPOperationCodes(models.Model):
    _name = "wslsp.operation.codes"
    _description = "WSLSP Operation Codes"
    _order = 'code'

    ranch_type = fields.Selection([('cattle','Cattle'),('pork','Pork')], 'Ranch Type')
    autoliquidation = fields.Boolean('Autoliquidation')
    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPProvinceCodes(models.Model):
    _name = "wslsp.province.codes"
    _description = "WSLSP Province Codes"
    _order = 'code'

    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPBreedCodes(models.Model):
    _name = "wslsp.breed.codes"
    _description = "WSLSP Breed Codes"
    _order = 'code'

    ranch_type = fields.Selection([('cattle','Cattle'),('pork','Pork')], 'Ranch Type')
    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPVoucherTypeCodes(models.Model):
    _name = "wslsp.voucher_type.codes"
    _description = "WSLSP Voucher Type Codes"
    _order = 'code'

    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    is_direct = fields.Boolean('Is Direct?')
    document_type = fields.Selection([
        ('out_invoice', 'Client Invoice'),
        ('in_invoice', 'Supplier Invoice'),
    ], 'Document Type', select=True, readonly=False)
    denomination_id = fields.Many2one('invoice.denomination', 'Denomination')
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPLiquidationTypeCodes(models.Model):
    _name = "wslsp.liquidation_type.codes"
    _description = "WSLSP Liquidation Type Codes"
    _order = 'code'

    billing_type = fields.Selection([('alive_kilo','Alive Kilo'),
        ('performance','Performance')], 'Billing Type')
    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')

class WSLSPTaxCodes(models.Model):
    _name = "wslsp.tax.codes"
    _description = "WSLSP Tax Codes"
    _order = 'code'

    ranch_type = fields.Selection([('cattle','Cattle'),('pork','Pork')], 'Ranch Type')
    code = fields.Char('Code', required=True, size=8)
    name = fields.Char('Desc', required=True, size=64)
    wslsp_config_id = fields.Many2one('wslsp.config')
