# -*- coding: utf-8 -*-
##############################################################################

#   Copyright (c) 2017 Organization (Eynes - Ingenieria del software)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

##############################################################################

import logging

from openerp import api, models

_logger = logging.getLogger(__name__)


class PurchaseDataPerformanceWizardd(models.TransientModel):
    _inherit = "ranch.purchase.data.invoice.wizardd"

    @api.multi
    def _finalize_invoice_vals(self, purchase_data, invoice_vals):
        res = super(PurchaseDataPerformanceWizardd, self).\
            _finalize_invoice_vals(purchase_data, invoice_vals)

        fiscal_position_model = self.env['account.fiscal.position']

        # Check if it has to be lsp
        is_lsp = False
        if not purchase_data.auction_id:
            is_lsp = True

            fiscal_position_id = invoice_vals['fiscal_position']
            fiscal_position = fiscal_position_model.browse(
                fiscal_position_id)
            invoice_vals['denomination_id'] = fiscal_position.denomination_id.id

        res['is_lsp'] = is_lsp
        return res

    @api.multi
    def open_invoice(self):
        res = super(PurchaseDataPerformanceWizardd, self).open_invoice()
        if res and isinstance(res, dict):
            invoice_id = res.get('res_id', False)
            if not invoice_id:
                return res
            invoice = self.env['account.invoice'].browse(invoice_id)
            #purchase_data = invoice.purchase_data_id
            #if purchase_data.ranch_type == 'cattle':
            if invoice.is_lsp:
                form_view = self.env.ref('l10n_ar_wslsp.view_invoice_wslsp_purchase_data_form')
                vals = {'view_id': form_view.id}
                res.update(vals)

        return res

    @api.multi
    def _adjust_invoice_lines(self, purchase_data, invoice_vals, inv_summary_line_ids):
        res = super(PurchaseDataPerformanceWizardd, self)._adjust_invoice_lines(
            purchase_data, invoice_vals, inv_summary_line_ids)
        purchase_data, invoice_vals, inv_summary_line_ids = res
        if invoice_vals.get("is_lsp", False):
            inv_lines = self.env["account.invoice.line"].browse(inv_summary_line_ids)
            for line in inv_lines:
                price_unit, quantity = line._round_qty_and_adjust_price(line.price_unit,
                                                                        line.quantity)
                line.write({"price_unit": price_unit, "quantity": quantity})

        return res


class PurchaseDataPerformanceWizard(models.TransientModel):
    _inherit = "ranch.purchase.data.invoice.wizard"

    @api.multi
    def _finalize_invoice_vals(self, purchase_data, invoice_vals):
        res = super(PurchaseDataPerformanceWizard, self).\
            _finalize_invoice_vals(purchase_data, invoice_vals)

        fiscal_position_model = self.env['account.fiscal.position']

        # Check if it has to be lsp
        is_lsp = False
        if not purchase_data.auction_id:
            is_lsp = True

            fiscal_position_id = invoice_vals['fiscal_position']
            fiscal_position = fiscal_position_model.browse(
                fiscal_position_id)
            invoice_vals['denomination_id'] = fiscal_position.denomination_id.id

        res['is_lsp'] = is_lsp
        return res

    @api.multi
    def open_invoice(self):
        res = super(PurchaseDataPerformanceWizard, self).open_invoice()
        if res and isinstance(res, dict):
            invoice_id = res.get('res_id', False)
            if not invoice_id:
                return res
            invoice = self.env['account.invoice'].browse(invoice_id)
            #purchase_data = invoice.purchase_data_id
            #if purchase_data.ranch_type == 'cattle':
            if invoice.is_lsp:
                form_view = self.env.ref('l10n_ar_wslsp.view_invoice_wslsp_purchase_data_form')
                vals = {'view_id': form_view.id}
                res.update(vals)
        return res

    @api.multi
    def _adjust_invoice_lines(self, purchase_data, invoice_vals, inv_summary_line_ids):
        res = super(PurchaseDataPerformanceWizard, self)._adjust_invoice_lines(
            purchase_data, invoice_vals, inv_summary_line_ids)
        purchase_data, invoice_vals, inv_summary_line_ids = res
        if invoice_vals.get("is_lsp", False):
            inv_lines = self.env["account.invoice.line"].browse(inv_summary_line_ids)
            for line in inv_lines:
                price_unit, quantity = line._round_qty_and_adjust_price(line.price_unit,
                                                                        line.quantity)
                line.write({"price_unit": price_unit, "quantity": quantity})

        return res
