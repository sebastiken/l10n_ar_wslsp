# -*- coding: utf-8 -*-
##############################################################################

#   Copyright (c) 2017 Organization (Eynes - Ingenieria del software)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

##############################################################################


from openerp import _, api, exceptions, fields, models
from openerp.exceptions import except_orm
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare

import logging

_logger = logging.getLogger(__name__)

class PurchaseDataPerformanceWizardd(models.TransientModel):
    _inherit = "ranch.purchase.data.invoice.wizardd"

    @api.multi
    def _finalize_invoice_vals(self, purchase_data, invoice_vals):
        res = super(PurchaseDataPerformanceWizardd, self).\
            _finalize_invoice_vals(purchase_data,invoice_vals)

        # Check if it has to be lsp
        is_lsp = False
        if not purchase_data.auction_id:
            is_lsp = True

        invoice_vals['is_lsp'] = is_lsp
        return invoice_vals

    @api.multi
    def open_invoice(self):
        res = super(PurchaseDataPerformanceWizardd, self).open_invoice()
        if res and isinstance(res, dict):
            invoice_id = res.get('res_id', False)
            if not invoice_id:
                return res
            invoice = self.env['account.invoice'].browse(invoice_id)
            purchase_data = invoice.purchase_data_id
            #if purchase_data.ranch_type == 'cattle':
            if invoice.is_lsp:
                form_view = self.env.ref('l10n_ar_wslsp.view_invoice_wslsp_purchase_data_form')
                vals = {'view_id': form_view.id}
                res.update(vals)
        return res


class PurchaseDataPerformanceWizard(models.TransientModel):
    _inherit = "ranch.purchase.data.invoice.wizard"

    @api.multi
    def _finalize_invoice_vals(self, purchase_data, invoice_vals):
        res = super(PurchaseDataPerformanceWizard, self).\
            _finalize_invoice_vals(purchase_data,invoice_vals)

        # Check if it has to be lsp
        is_lsp = False
        if not purchase_data.auction_id:
            is_lsp = True

        invoice_vals['is_lsp'] = is_lsp
        return invoice_vals

    @api.multi
    def open_invoice(self):
        res = super(PurchaseDataPerformanceWizard, self).open_invoice()
        if res and isinstance(res, dict):
            invoice_id = res.get('res_id', False)
            if not invoice_id:
                return res
            invoice = self.env['account.invoice'].browse(invoice_id)
            purchase_data = invoice.purchase_data_id
            #if purchase_data.ranch_type == 'cattle':
            if invoice.is_lsp:
                form_view = self.env.ref('l10n_ar_wslsp.view_invoice_wslsp_purchase_data_form')
                vals = {'view_id': form_view.id}
                res.update(vals)
        return res
