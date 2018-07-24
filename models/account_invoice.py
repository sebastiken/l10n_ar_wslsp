# -*- coding: utf-8 -*-
##############################################################################

#   Copyright (c) 2017 Rafaela Alimentos (Eynes - Ingenieria del software)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

##############################################################################


from openerp import _, api, exceptions, fields, models
from openerp.exceptions import except_orm
from openerp.addons.decimal_precision import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class AccountInvocie(models.Model):
    _inherit = 'account.invoice.line'

    def get_ranch_purchase_data(self):
        purchase_data_obj = self.env['ranch.purchase.data']
        query = """
            SELECT purchase_data_id
            FROM ranch_purchase_data_invoice_rel
            WHERE invoice_id = %s
            LIMIT 1
        """
        self.env.cr.execute(query, (self.id,))
        try:
            res = self.env.cr.fetchone()[0]
            purchase_data = purchase_data_obj.browse(res)
        except (TypeError, IndexError):
            purchase_data = purchase_data_obj
        return purchase_data

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
