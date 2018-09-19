# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-TODAY Eynes (<http://www.e-mips.com.ar>)
#
#    This is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import psycopg2


def update_lsp_invoices(cr):
    try:
        cr.execute(
            """
            UPDATE account_invoice SET is_lsp='t'
            WHERE purchase_data_type='performance'
            """)
    except (TypeError, IndexError, psycopg2.ProgrammingError):
        cr.rollback()

    return True

def migrate(cr, installed_version):
    return update_lsp_invoices(cr)
