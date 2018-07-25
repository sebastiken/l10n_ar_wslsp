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
import logging

_logger = logging.getLogger(__name__)


class AccountInvocie(models.Model):
    _inherit = 'account.invoice'

    def get_wslsp_config(self):
        config_obj = self.env['wslsp.config']
        config = config_obj.get_config()
        return config

    @api.multi
    def _check_ranch_purchase(self):
        self.ensure_one()
        if not self.purchase_data_id:
            raise except_orm(_('WSLSP Error!'),
                    _("Invoice does not have a ranch purchase data associated"))
        return purchase_data

    @api.multi
    def get_wslsp_voucher_type(self, purchase_data=False):
        self.ensure_one()
        config = self.get_wslsp_config()
        if not purchase_data:
            purchase_data = self._check_ranch_purchase()
        billing_type = purchase_data.billing_type
        if billing_type == 'performance':
            is_direct = True
        else:
            is_direct = False
        voucher_type = config.voucher_type_ids.filtered(
                lambda x: x.is_direct == is_direct and \
                        x.document_type == self.type and \
                        x.denomination_id.id = self.denomination_id.id)
        if not voucher_type:
            raise except_orm(_('WSLSP Error!'),
                    _('There is not configured voucher type with document[%s] Is Direct[%s] Denomination[%s]') %
                    (self.type, is_direct, self.denomination_id.name))
        if len(voucher_type) > 1:
            raise except_orm(_('WSLSP Error!'), _('There are duplicated voucher types')
        return voucher_type.code

    @api.multi
    def _get_next_wslsp_number(self, conf=False):
        self.ensure_one()
        inv = self
        if not conf:
            conf = self.get_wslsp_config()
        tipo_cbte = self._get_wslsp_voucher_type()
        pos_ar = self.split_number()[0]
        last = conf.get_last_voucher(pto_vta, tipo_cbte)
        return int(last + 1)

    # @api.multi
    # def action_aut_cae(self):
    #     res = super(AccountInvocie, self).action_aut_cae()
    #     for inv in self:
    #         purchase_data = inv.purchase_data_id
    #         if not purchase_data:
    #             return res
    #         conf = inv.get_wslsp_config()
    #         ws = conf._get_wslsp_obj()
    #         invoice_vals = ws.generate_liquidation(inv)
    #         if invoice_vals:
    #             inv.write(invoice_vals)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def get_romaneo_summary_line(self):
        summary_line_obj = self.env['ranch.purchase.romaneo.summary.line']
        query = """
            SELECT romaneo_summary_line_id
            FROM purchase_romaneo_summary_line_invoice_rel
            WHERE invoice_id = %s
            LIMIT 1
        """
        self.env.cr.execute(query, (self.id,))
        try:
            res = self.env.cr.fetchone()[0]
            summary_line = summary_line_obj.browse(res)
        except (TypeError, IndexError):
            summary_line = summary_line_obj
        return summary_line

    def _check_romaneo_summary_line(self):
        self.ensure_one()
        summary_line = self.get_romaneo_summary_line()
        if not summary_line:
            raise except_orm(_('WSLSP Error!'),
                    _("Line Invoice [%s] does not have a ranch purchase data associated") %(self.name))
        return summary_line
