# -*- coding: utf-8 -*-
##############################################################################

#   Copyright (c) 2017 Rafaela Alimentos (Eynes - Ingenieria del software)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

##############################################################################


from openerp import _, api, exceptions, fields, models
from openerp.exceptions import except_orm

class RanchPurchaseRomaneoFromDataWizard(models.TransientModel):
    _inherit = 'ranch.purchase.romaneo.from.data.wizard'

    @api.model
    def _get_matched(self):
        romaneos = super(RanchPurchaseRomaneoFromDataWizard, self)._get_matched()
        purchase_data_id = self.env.context.get('active_ids')
        purchase_data_obj = self.env['ranch.purchase.data']
        purchase_data = purchase_data_obj.browse(purchase_data_id)
        auction = purchase_data.auction_id
        if purchase_data.billing_type == 'performance' or auction:
            return romaneos
        troop_number_lst = purchase_data.romaneo_ids.mapped('troop_number')
        troop_lst = list(set(troop_number_lst))
        if len(troop_lst) > 1:
            name = purchase.name
            raise except_orm(_("Error!"),
                    _("Purchase data %s has romaneos with different troop number")%(name))
        if troop_lst:
            romaneos = romaneos.filtered(lambda x: x.troop_number in troop_lst)
        return romaneos

    @api.multi
    def get_now(self):
        res = super(RanchPurchaseRomaneoFromDataWizard, self).get_now()
        purchase_data_id = self.env.context.get('active_ids')
        purchase_data_obj = self.env['ranch.purchase.data']
        purchase_data = purchase_data_obj.browse(purchase_data_id)
        auction = purchase_data.auction_id
        if purchase_data.billing_type == 'performance' or auction:
            return res
        troop_number_lst = self.pre_matched_lines.mapped('troop_number')
        troop_lst = list(set(troop_number_lst))
        if len(troop_lst) > 1:
            raise except_orm(_("Error!"),
                    _("There are romaneos with different troop number"))
        return res
