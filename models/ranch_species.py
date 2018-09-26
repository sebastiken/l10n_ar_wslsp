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


class RanchSpecies(models.Model):
    _inherit = "ranch.species"

    afip_code_id = fields.Many2one("wslsp.category.codes",string="AFIP code")

    _sql_constraints = [('uniq_AFIP_code', 'UNIQUE(afip_code_id)',
        _("There is another specie with same AFIP code"))]

    @api.multi
    def get_afip_specie_code(self):
        self.ensure_one()
        if not afip_code_id:
            raise except_orm(_("Error!"),
                    _("Specie %s does not have configured afip category")%(self.name))
        code = self.afip_code_id.code
        return code
