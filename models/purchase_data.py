# -*- coding: utf-8 -*-
##############################################################################

#   Copyright (c) 2017 Rafaela Alimentos (Eynes - Ingenieria del software)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

##############################################################################


from openerp import _, api, exceptions, fields, models
from openerp.exceptions import except_orm
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare

import logging

_logger = logging.getLogger(__name__)


class PurchaseData(models.Model):
    _inherit = 'ranch.purchase.data'

    @api.multi
    def view_invoices(self):
        res = super(PurchaseData, self).view_invoices()
        if not res or not isinstance(res, dict):
            return res

        act_type = res.get('type', False)
        if act_type != 'ir.actions.act_window':
            return res


        invoice = self.invoice_ids and self.invoice_ids[0]

        if invoice.is_lsp and self.ranch_type == 'cattle':
            form_view = self.env.ref('l10n_ar_wslsp.view_invoice_wslsp_purchase_data_form')
            tree_view = self.env.ref('account.invoice_tree')
            res_id = res.get('res_id', False)
            vals = {'views': [(form_view.id, 'form')]}
            if not res_id:
                vals = {
                    'views': [(tree_view.id ,'tree'),(form_view.id, 'form')]
                }
            res.update(vals)
        return res

