# -*- coding: utf-8 -*-
##############################################################################

#
#    Copyright (c) 2018 Eynes (Eynes)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

##############################################################################

{
    "name": "l10n_ar_wslsp",
    'category': "Others",
    'version': "8.0.1.0.0",
    "author": "Eynes",
    "description": "AFIP livestock sector liquidation webservice (LSLWS - WSLSP) management",
    "depends": ["rafalim_cattle_account",
                "l10n_ar_wsfe",
                "rafalim_payment_system"],
    "data": [
        "data/wslsp_data.xml",
        "data/groups_data.xml",
        "views/company_view.xml",
        "views/wslsp_view.xml",
        "views/ranch_expenses_type_view.xml",
        "views/ranch_species_view.xml",
        "views/account_invoice_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
}
