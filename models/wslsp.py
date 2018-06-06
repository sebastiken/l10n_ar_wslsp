# -*- coding: utf-8 -*-
##############################################################################

#   Copyright (c) 2017 Rafaela Alimentos (Eynes - Ingenieria del software)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

##############################################################################

from openerp import _, api, exceptions, fields, models
from openerp.exceptions import except_orm
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare

from wslsp_tools.wslsp_suds import WSLSP as wslsp

import logging

_logger = logging.getLogger(__name__)

class WSLSPConfig(models.Model):
    _name = "wslsp.config"
    _description = "Configuration for WSLSP"

    name = fields.Char('Name', size=64, required=True)
    cuit = fields.Char(related='company_id.partner_id.vat', string='Cuit')
    url = fields.Char('URL for WSLSP', size=60, required=True)
    company_id = fields.Many2one('res.company', 'Company Name' , required=True)
    homologation = fields.Boolean('Homologation', default=False,
            help="If true, there will be some validations that are disabled, for example, invoice number correlativeness")
    point_of_sale_ids = fields.Many2many('pos.ar', 'pos_ar_wslsp_rel', 'wslsp_config_id', 'pos_ar_id', 'Points of Sale')
    wsaa_ticket_id = fields.Many2one('wsaa.ta', 'Ticket Access')

    categories_ids = fields.One2many('wslsp.category.codes', 'wslsp_config_id' , 'Categories')
    cut_ids = fields.One2many('wslsp.cut.codes', 'wslsp_config_id' , 'Cuts')
    participant_character_ids = fields.One2many('wslsp.participant_character.codes', 'wslsp_config_id' , 'Participant characters')
    expenses_ids = fields.One2many('wslsp.expenses.codes', 'wslsp_config_id' , 'Expenses')
    motive_ids = fields.One2many('wslsp.motive.codes', 'wslsp_config_id' , 'Motives')
    operation_ids = fields.One2many('wslsp.operation.codes', 'wslsp_config_id' , 'Operations')
    province_ids = fields.One2many('wslsp.province.codes', 'wslsp_config_id' , 'Provinces')
    breed_ids = fields.One2many('wslsp.breed.codes', 'wslsp_config_id' , 'Breeds')
    voucher_type_ids = fields.One2many('wslsp.voucher_type.codes', 'wslsp_config_id' , 'Voucher Types')
    liquidation_type_ids = fields.One2many('wslsp.liquidation_type.codes', 'wslsp_config_id' , 'Liquidation Types')
    tax_ids = fields.One2many('wslsp.tax.codes', 'wslsp_config_id' , 'Tax Types')
    
    #currency_ids = fields.One2many('wsfex.currency.codes', 'wsfex_config_id' , 'Currencies')

    _defaults = {
        'company_id' : lambda self, cr, uid, context=None: self.pool.get('res.users')._get_company(cr, uid, context=context),
        }

    def create(self, cr, uid, vals, context):
        # Creamos tambien un TA para este servcio y esta compania
        ta_obj = self.pool.get('wsaa.ta')
        wsaa_obj = self.pool.get('wsaa.config')
        service_obj = self.pool.get('afipws.service')

        # Buscamos primero el wsaa que corresponde a esta compania
        # porque hay que recordar que son unicos por compania
        wsaa_ids = wsaa_obj.search(cr, uid, [('company_id','=', vals['company_id'])], context=context)
        service_ids = service_obj.search(cr, uid, [('name','=', 'wslsp')], context=context)
        if wsaa_ids:
            ta_vals = {
                'name': service_ids[0],
                'company_id': vals['company_id'],
                'config_id' : wsaa_ids[0],
                }

            ta_id = ta_obj.create(cr, uid, ta_vals, context)
            vals['wsaa_ticket_id'] = ta_id

        return super(WSLSPConfig, self).create(cr, uid, vals, context)

    def get_config(self):
        # Obtenemos la compania que esta utilizando en este momento este usuario
        company_id = self.env.user.company_id.id
        if not company_id:
            raise osv.except_osv(_('Company Error!'), _('There is no company being used by this user'))

        ids = self.search([('company_id','=',company_id)])
        if not ids:
            raise osv.except_osv(_('WSLSP Config Error!'), _('There is no WSLSP configuration set to this company'))

        return ids

    @api.one
    def get_server_state(self):
        conf = self
        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(conf.cuit, token, sign, conf.url)
        res = _wslsp.dummy()
        return res

    @api.one
    def get_wslsp_categories(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarCategorias()

        wslsp_category_model = self.env['wslsp.category.codes']

        # Armo un lista con los codigos de los Impuestos
        for category in res['response']:
            res_c = wslsp_category_model.search([('code','=', category.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_category_model.create({'code': category.codigo, 'name': category.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': category.descripcion, 'wslsp_config_id': self.id})

        return True
        
    @api.one
    def get_wslsp_cuts(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarCortes()

        wslsp_cut_model = self.env['wslsp.cut.codes']

        # Armo un lista con los codigos de los Impuestos
        for cut in res['response']:
            res_c = wslsp_cut_model.search([('code','=', cut.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_cut_model.create({'code': cut.codigo, 'name': cut.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': cut.descripcion, 'wslsp_config_id': self.id})

        return True
        
    @api.one
    def get_wslsp_participant_characters(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarCaracteresParticipante()

        wslsp_participant_characters_model = self.env['wslsp.participant_character.codes']

        # Armo un lista con los codigos de los Impuestos
        for participant_character in res['response']:
            res_c = wslsp_participant_characters_model.search([('code','=', participant_character.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_participant_characters_model.create({'code': participant_character.codigo, 'name': participant_character.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': participant_character.descripcion, 'wslsp_config_id': self.id})

        return True
        
    @api.one
    def get_wslsp_expenses(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarGastos()

        wslsp_expenses_model = self.env['wslsp.expenses.codes']

        # Armo un lista con los codigos de los Impuestos
        for expenses in res['response']:
            res_c = wslsp_expenses_model.search([('code','=', expenses.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_expenses_model.create({'code': expenses.codigo, 'name': expenses.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': expenses.descripcion, 'wslsp_config_id': self.id})

        return True
        
    @api.one
    def get_wslsp_motives(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarMotivos()

        wslsp_motive_model = self.env['wslsp.motive.codes']

        # Armo un lista con los codigos de los Impuestos
        for motive in res['response']:
            res_c = wslsp_motive_model.search([('code','=', motive.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_motive_model.create({'code': motive.codigo, 'name': motive.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': motive.descripcion, 'wslsp_config_id': self.id})

        return True
        
    @api.one
    def get_wslsp_operations(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarOperaciones()

        wslsp_operation_model = self.env['wslsp.operation.codes']

        # Armo un lista con los codigos de los Impuestos
        for operation in res['response']:
            res_c = wslsp_operation_model.search([('code','=', operation.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_operation_model.create({'code': operation.codigo, 'name': operation.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': operation.descripcion, 'wslsp_config_id': self.id})

        return True
        
    @api.one
    def get_wslsp_provinces(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarProvincias()

        wslsp_province_model = self.env['wslsp.province.codes']

        # Armo un lista con los codigos de los Impuestos
        for province in res['response']:
            res_c = wslsp_province_model.search([('code','=', province.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_province_model.create({'code': province.codigo, 'name': province.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': province.descripcion, 'wslsp_config_id': self.id})

        return True
        
    @api.one
    def get_wslsp_breeds(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarRazas()

        wslsp_breed_model = self.env['wslsp.breed.codes']

        # Armo un lista con los codigos de los Impuestos
        for breed in res['response']:
            res_c = wslsp_breed_model.search([('code','=', breed.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_breed_model.create({'code': breed.codigo, 'name': breed.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': breed.descripcion, 'wslsp_config_id': self.id})

        return True

    @api.one
    def get_wslsp_voucher_types(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarTiposComprobante()

        wslsp_voucher_type_model = self.env['wslsp.voucher_type.codes']

        # Armo un lista con los codigos de los Impuestos
        for voucher_type in res['response']:
            res_c = wslsp_voucher_type_model.search([('code','=', voucher_type.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_voucher_type_model.create({'code': voucher_type.codigo, 'name': voucher_type.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': voucher_type.descripcion, 'wslsp_config_id': self.id})

        return True

    @api.one
    def get_wslsp_liquidation_types(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarTiposLiquidacion()

        wslsp_liquidation_type_model = self.env['wslsp.liquidation_type.codes']

        # Armo un lista con los codigos de los Impuestos
        for liquidation_type in res['response']:
            res_c = wslsp_liquidation_type_model.search([('code','=', liquidation_type.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_liquidation_type_model.create({'code': liquidation_type.codigo, 'name': liquidation_type.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': liquidation_type.descripcion, 'wslsp_config_id': self.id})

        return True

    @api.one
    def get_wslsp_taxes(self):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)
        res = _wslsp.consultarTributos()

        wslsp_tax_model = self.env['wslsp.tax.codes']

        # Armo un lista con los codigos de los Impuestos
        for tax in res['response']:
            res_c = wslsp_tax_model.search([('code','=', tax.codigo )])

            # Si no tengo los codigos de esos Impuestos en la db, los creo
            if not len(res_c):
                wslsp_tax_model.create({'code': tax.codigo, 'name': tax.descripcion, 'wslsp_config_id': self.id})
            # Si los codigos estan en la db los modifico
            else :
                res_c.write({'name': tax.descripcion, 'wslsp_config_id': self.id})

        return True

    def check_error(self, res, raise_exception=True):
        msg = ''
        #TODO MANY ERRORS NOT 1
        if 'errors' in res:
            error = res['error'].msg
            err_code = str(res['error'].code)
            msg = 'Codigo/s Error: %s[%s]' % (error, err_code)

            if msg != '' and raise_exception:
                raise osv.except_osv(_('WSLSP Error!'), msg)

        return msg
    
    def get_last_voucher(self, pos, voucher_type):
        conf = self

        token, sign = conf.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(conf.cuit, token, sign, conf.url)
        res = _wslsp.consultarUltimoNroComprobantePorPtoVta(pos, voucher_type)

        self.check_error(res)
        last = res['response']
        return last

    def _parse_result(self, invoices, result):

        invoices_approbed = {}

        # Verificamos el resultado de la Operacion
        # Si no fue aprobado
        if 'error' in result:

            msg = result['error'].msg
            if self._context.get('raise-exception', True):
                raise osv.except_osv(_('AFIP Web Service Error'),
                                     _('La factura no fue aprobada. \n%s') % msg)

        # Igualmente, siempre va a ser una para FExp
        for inv in invoices:
            invoice_vals = {}

            comp = result['response']

            # Chequeamos que se corresponda con la factura que enviamos a validar
#            doc_num = comp['Cuit'] == int(inv.partner_id.vat)
            cbte = True
            if inv.internal_number:
                cbte = comp['Cbte_nro'] == int(inv.internal_number.split('-')[1])
            else:
                # TODO: El nro de factura deberia unificarse para que se setee en una funcion
                # o algo asi para que no haya posibilidad de que sea diferente nunca en su formato
                invoice_vals['internal_number'] = '%04d-%08d' % (result['PtoVta'], comp['CbteHasta'])

#            if not all([cbte]):
#                raise osv.except_osv(_("WSFE Error!"), _("Validated invoice that not corresponds!"))

            invoice_vals['cae'] = comp['Cae']
            invoice_vals['cae_due_date'] = comp['Fch_venc_Cae']
            invoices_approbed[inv.id] = invoice_vals

        return invoices_approbed

    # TODO: Migrar a v8
    def _log_wsfe_request(self, cr, uid, ids, pos, voucher_type_code, detail, res, context=None):

        wsfex_req_obj = self.pool.get('wsfex.request.detail')
        voucher_type_obj = self.pool.get('wsfe.voucher_type')
        voucher_type_ids = voucher_type_obj.search(cr, uid, [('code','=',voucher_type_code)])
        #voucher_type_name = voucher_type_obj.read(cr, uid, voucher_type_ids, ['name'])[0]['name']

        error = 'error' in res

        # Esto es para fixear un bug que al hacer un refund, si fallaba algo con la AFIP
        # se hace el rollback por lo tanto el refund que se estaba creando ya no existe en
        # base de datos y estariamos violando una foreign key contraint. Por eso,
        # chequeamos que existe info de la invoice_id, sino lo seteamos en False
        read_inv = self.pool.get('account.invoice').read(cr, uid, detail['invoice_id'], ['id', 'internal_number'], context=context)

        if not read_inv:
            invoice_id = False
        else:
            invoice_id = detail['invoice_id']

        vals = {
            'invoice_id': invoice_id,
            'request_id': detail['Id'],
            'voucher_number': '%04d-%08d' % (pos, detail['Cbte_nro']),
            'voucher_type_id': voucher_type_ids[0],
            'date': detail['Fecha_cbte'],
            'detail': str(detail),
            'error': 'error' in res and res['error'] or '',
            'event': 'event' in res and res['event'] or '',
        }

        if not error:
            comp = res['response']
            vals['cae'] = comp['Cae']
            vals['cae_duedate'] = comp['Fch_venc_Cae']
            vals['result'] = comp['Resultado']
            vals['reprocess'] = comp['Reproceso']
        else:
            vals['result'] = 'R'

        return wsfex_req_obj.create(cr, uid, vals)


    def prepare_details(self, invoices):
        company = self.env.user.company_id
        obj_precision = self.env['decimal.precision']
        voucher_type_obj = self.env['wsfe.voucher_type']
        invoice_obj = self.env['account.invoice']
        currency_code_obj = self.env['wsfex.currency.codes']
        uom_code_obj = self.env['wsfex.uom.codes']

        if len(invoices) > 1:
            raise osv.except_osv(_("WSFEX Error!"), _("You cannot inform more than one invoice to AFIP WSFEX"))

        first_num = self._context.get('first_num', False)
        Id = int(datetime.strftime(datetime.now(), '%Y%m%d%H%M%S'))
        cbte_nro = 0

        for inv in invoices:

            # Obtenemos el numero de comprobante a enviar a la AFIP teniendo en
            # cuenta que inv.number == 000X-00000NN o algo similar.
            if not inv.internal_number:
                if not first_num:
                    raise osv.except_osv(_("WSFE Error!"), _("There is no first invoice number declared!"))
                inv_number = first_num
            else:
                inv_number = inv.internal_number

            if not cbte_nro:
                cbte_nro = inv_number.split('-')[1]
                cbte_nro = int(cbte_nro)
            else:
                cbte_nro = cbte_nro + 1

            date_invoice = datetime.strptime(inv.date_invoice, '%Y-%m-%d')
            formatted_date_invoice = date_invoice.strftime('%Y%m%d')
            #date_due = inv.date_due and datetime.strptime(inv.date_due, '%Y-%m-%d').strftime('%Y%m%d') or formatted_date_invoice

            cuit_pais = inv.dst_cuit_id and int(inv.dst_cuit_id.code) or 0
            inv_currency_id = inv.currency_id.id
            curr_codes = currency_code_obj.search([('currency_id', '=', inv_currency_id)])

            if curr_codes:
                curr_code = curr_codes[0].code
                curr_rate = company.currency_id.id==inv_currency_id and 1.0 or inv.currency_rate
            else:
                raise osv.except_osv(_("WSFEX Error!"), _("Currency %s has not code configured") % inv.currency_id.name)

            # Items
            items = []
            for i, line in enumerate(inv.invoice_line):
                product_id = line.product_id
                product_code = product_id and product_id.default_code or i
                uom_id = line.uos_id.id
                uom_codes = uom_code_obj.search([('uom_id','=',uom_id)])
                if not uom_codes:
                    raise osv.except_osv(_("WSFEX Error!"), _("There is no UoM Code defined for %s in line %s") % (line.uos_id.name, line.name))

                uom_code = uom_codes[0].code

                items.append({
                    'Pro_codigo' : i,#product_code,
                    'Pro_ds' : line.name.encode('ascii', errors='ignore'),
                    'Pro_qty' : line.quantity,
                    'Pro_umed' : uom_code,
                    'Pro_precio_uni' : line.price_unit,
                    'Pro_total_item' : line.price_subtotal,
                    'Pro_bonificacion' : 0,
                })

            Cmps_asoc = []
            for associated_inv in inv.associated_inv_ids:
                tipo_cbte = voucher_type_obj.get_voucher_type(associated_inv)
                pos, number = associated_inv.internal_number.split('-')
                Cmp_asoc = {
                    'Cbte_tipo': tipo_cbte,
                    'Cbte_punto_vta': int(pos),
                    'Cbte_nro': int(number),
                }

                Cmps_asoc.append(Cmp_asoc)

            # TODO: Agregar permisos
            shipping_perm = 'S' and inv.shipping_perm_ids or 'N'

            Cmp = {
                'invoice_id' : inv.id,
                'Id' : Id,
                #'Tipo_cbte' : cbte_tipo,
                'Fecha_cbte' : formatted_date_invoice,
                #'Punto_vta' : pto_venta,
                'Cbte_nro' : cbte_nro,
                'Tipo_expo' : inv.export_type_id.code, #Exportacion de bienes
                'Permiso_existente' : shipping_perm,
                'Dst_cmp' : inv.dst_country_id.code,
                'Cliente' : inv.partner_id.name.encode('ascii', errors='ignore'),
                'Domicilio_cliente' : inv.partner_id.contact_address.encode('ascii', errors='ignore'),
                'Cuit_pais_cliente' : cuit_pais,
                'Id_impositivo' : inv.partner_id.vat,
                'Moneda_Id' : curr_code,
                'Moneda_ctz' : curr_rate,
                'Imp_total' : inv.amount_total,
                'Idioma_cbte' : 1,
                'Items' : items
            }

            # Datos No Obligatorios
            if inv.incoterm_id:
                Cmp['Incoterms'] = inv.incoterm_id.code
                Cmp['Incoterms_Ds'] = inv.incoterm_id.name

            if Cmps_asoc:
                Cmp['Cmps_Asoc'] = Cmps_asoc

        return Cmp

    def get_liquidation(self, purchase_data):
        company = self.env.user.company_id

        token, sign = self.wsaa_ticket_id.get_token_sign()

        _wslsp = wslsp(self.cuit, token, sign, self.url)

        _wslsp.set_codOperacion(purchase_data['operationCode'])
        _wslsp.set_emisorSolicitud(purchase_data['emisor']) #nroComprobante
        _wslsp.set_receptorSolicitud(purchase_data['receptor']) #operador
        _wslsp.set_datosLiquidacionSolicitud(purchase_data['datosLiquidacion'])
        for itemDetalleLiquidacion in purchase_data['itemDetalleLiquidacion']:
            _wslsp.add_itemDetalleLiquidacion(itemDetalleLiquidacion) #raza
        for gasto in purchase_data['gastos']:
            _wslsp.add_Gasto(gasto)
        for dte in purchase_data['dtes']:
            _wslsp.add_DTE(dte)
        for guia in purchase_data['guias']:
            _wslsp.add_Guia(guia)
        for tributo in purchase_data['tributos']:
            _wslsp.add_Tributo(tributo)

        res = _wslsp.generarLiquidacion()
        return res
