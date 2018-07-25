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
import logging
_logger = logging.getLogger(__name__)


class WSLSPRequest(models.Model):
    _name = "wslsp.request"
    _description = "WSLSP Request"

    pos_ar = fields.Char('POS', required=True, readonly=True, size=16)
    voucher_type = fields.Char('Voucher Type', required=True, readonly=True, size=64)
    date_request = fields.Datetime('Request Date', required=True)
    name = fields.Char('Desc', required=False, size=64)
    detail_ids = fields.One2many('wsfe.request.detail', 'request_id', 'Details', readonly=True)
    result = fields.Selection([('A', 'Approved'), ('R', 'Rejected'), ('P', 'Partial')], 'Result', readonly=True)
    reprocess = fields.Boolean('Reprocess', readonly=True, default=False)
    errors = fields.Text('Errors', readonly=True)

class WSLSPRequestDetail(models.Model):
    _name = "wslsp.request.detail"
    _description = "WSLSP Request Detail"

    name = fields.Many2one('account.invoice', 'Voucher', required=False, readonly=True)
    request_id = fields.Many2one('wsfe.request', 'Request', required=True)
    concept = fields.Selection([('1', 'Products'), ('2', 'Services'), ('3', 'Products&Services')], 'Concept', readonly=True)
    doctype = fields.Integer('Document Type', readonly=True)
    docnum = fields.Char('Document Number', size=32, readonly=True)
    voucher_number = fields.Integer('Voucher Number', readonly=True)
    voucher_date = fields.Date('Voucher Date', readonly=True)
    amount_total = fields.Char('Amount Total', size=64, readonly=True)
    cae = fields.Char('CAE', required=False, readonly=True, size=64)
    cae_duedate = fields.Date('CAE Due Date', required=False, readonly=True)
    result = fields.Selection([('A', 'Approved'), ('R', 'Rejected')], 'Result', readonly=True)
    observations = fields.Text('Observations', readonly=True)
    currency = fields.Char('Currency', required=False, readonly=True)
    currency_rate = fields.Float('Currency Rate', required=False, readonly=True)
