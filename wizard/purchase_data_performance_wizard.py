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

class PurchaseDataPerformanceWizard(models.TransientModel):
    _inherit = "ranch.purchase.data.invoice.wizardd"


    @api.multi
    def open_invoice(self):
        res = super(PurchaseDataPerformanceWizard, self).open_invoice()
        if res and isinstance(res, dict):
            invoice_id = res.get('res_id', False)
            if not invoice_id:
                return res
            invoice = self.env['account.invoice'].browse(invoice_id)
            purchase_data = invoice.purchase_data_id
            if purchase_data.ranch_type == 'cattle':
                form_view = self.env.ref('l10n_ar_wslsp.view_invoice_wslsp_purchase_data_form')
                vals = {'view_id': form_view.id}
                res.update(vals)
        return res




