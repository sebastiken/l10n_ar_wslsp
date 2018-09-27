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

class RanchExpensesType(models.Model):
    _inherit = "ranch.expenses.type"

    afip_code_id = fields.Many2one("wslsp.expenses.codes",string="AFIP code")
    code = fields.Char('Code', related="afip_code_id.code")

    _sql_constraints = [('uniq_AFIP_code', 'UNIQUE(afip_code_id)',
        _("There is another specie with same AFIP code"))]

    @api.multi
    @api.depends('code', 'name')
    def name_get(self):
        res = []
        for record in self:
            name = ('' if not record.code else str(record.code) + ' ') + record.name
            res.append((record.id, name))
        return res

    @api.multi
    def get_afip_expense_code(self):
        self.ensure_one()
        if not self.afip_code_id:
            raise except_orm(_("Error!"),
                    _("Expense %s does not have configured afip expense")%(self.name))
        code = self.afip_code_id.code
        return code
