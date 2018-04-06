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
    "depends": [
        "base", "l10n_ar_point_of_sale", "l10n_ar_wsaa",
    ],
    "data": [
        "data/wslsp_data.xml",
        "views/wslsp_view.xml",
    ],
    
    "installable": True,
    "application": True,
}
