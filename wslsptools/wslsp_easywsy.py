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

from easywsy import WebService, wsapi
from openerp import _, api, exceptions, fields, models
from openerp.exceptions import except_orm
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime
import time
import logging

_logger = logging.getLogger(__name__)


AFIP_DATE_FORMAT = '%Y-%m-%d'

NOCHECK = ['nroRenspa', 'nroRUCA', 'cuit', 'cuitAutorizado',
            'nroPlanta', 'nroDTE', 'cuitCliente', 'descripcion',
            'datosAdicionales','codCategoria']

NATURAL = ['codOperacion', 'codCaracter','tipoComprobante',
           'puntoVenta', 'cantidadKgVivo', 'cantidadAsociada',
           'codRaza', 'cantidad', 'cantidadCabezas',
           'nroTropa', 'codCorte', 'codGasto', 'codTributo',
           'tipoLiquidacion', 'codMotivo']

DATES = ['fechaInicioActividades', 'fechaComprobante']

POSITIVE_REALS = ['precioRecupero', 'baseImponible',
        'importe', 'alicuota', 'precioUnitario']

def check_afip_date_format(date, reraise=True):
    try:
        datetime.strptime(date, AFIP_DATE_FORMAT)
    except Exception:
        if reraise:
            raise except_orm(_("WSLSP Error!"), _("Invalid Date Format"))
        return False
    return True

class WSLSP(WebService):

    def __init__(self, conf, url, **kwargs):
        WebService.__init__(self, url, **kwargs)
        self.config = conf

    ###############################################################################
    # AFIP Data Validation Methods According to:
    # https://www.afip.gob.ar/ws/WSLSP/manual_wslsp_1.2.pdf
    @wsapi.check(NATURAL, sequence=1)
    def _check_natural_fields(value):
        try:
            value = int(value)
        except Exception:
            return False
        if value <= 0:
            return False
        return True

    @wsapi.check(POSITIVE_REALS, sequence=1)
    def validate_positive_reals(val):
        if not val or (isinstance(val, float) and val > 0):
            return True
        return False

    @wsapi.check(DATES, sequence=1)
    def _check_date(value):
        check = check_afip_date_format(value, reraise=False)
        return check

    @wsapi.check(['iibb'])
    def _check_iibb(value):
        try:
            value = int(value)
        except Exception:
            return False
        if not (1 <= int(value) <= 15):
            return False
        return True

    @wsapi.check(['nroGuia'])
    def _check_guia(value):
        if not isinstance(value, int):
            return False
        if not (1 <= value <= 15):
            return False
        return True

    @wsapi.check(['alicuotaIVA'])
    def _check_tax_amount(value):
        if not isinstance(value, float):
            return False
        if value not in (10.5, 21, 21.0):
            return False
        return True

    @wsapi.check(['fechaOperacion'], reraise=True, sequence=4)
    def _check_operation_date(value, fechaComprobante):
        if not value:
            raise except_orm(_("WSFE Error!"), _("Operation Date was not setted"))
        check_afip_date_format(value)
        operation_date = value.replace('-','')
        voucher_date = fechaComprobante.replace('-','')

        if voucher_date < operation_date:
            raise except_orm(_("WSFE Error!"),
                    _("Voucher Date is less that Operation Date"))
        return True

    @wsapi.check(['fechaRecepcion'], reraise=True, sequence=5) #Es opcional
    def _check_receipt_date(value, fechaOperacion, fechaComprobante):
        if not value:
            raise except_orm(_("WSFE Error!"), _("Reception Date was not setted"))
        check_afip_date_format(value)
        operation_date = fechaOperacion.replace('-','')
        voucher_date = fechaComprobante.replace('-','')
        receipt_date = value.replace('-','')

        if not (operation_date <= receipt_date <= voucher_date):
            raise except_orm(_("WSFE Error!"), _("Invalid Receipt Date"))
        return True

    @wsapi.check(['fechaFaena'], reraise=True, sequence=5) #Es opcional
    def _check_chore(value, fechaRecepcion):
        if not value:
            raise except_orm(_("WSFE Error!"), _("Chore Date was not setted"))
        check_afip_date_format(value)
        chore_date = value.replace('-','')
        receipt_date = fechaRecepcion.replace('-','')

        if not (receipt_date <= chore_date):
            raise except_orm(_("WSFE Error!"),
                    _("Chore Date is less than Receipt Date"))
        return True

    @wsapi.check(['nroComprobante'], reraise=True, sequence=20)
    def _check_invoice_number(value, invoice):
        conf = invoice.get_wslsp_config()
        wslsp_next_number = invoice.get_next_wslsp_number(conf=conf)
        # Si es homologacion, no hacemos el chequeo del numero
        if not conf.homologation:
            if int(wslsp_next_number) != int(value):
                raise except_orm(_("WSFE Error!"),
                        _("The next number in the system [%d] does not " +
                          "match the one obtained from AFIP WSLSP [%d]") %
                        (int(value), int(wslsp_next_number)))
        return True

    ###############################################################################

    #--------------------authentication-----------------------#
    def prepare_auth(self, key):
        if not hasattr(self, 'auth') or not self.auth or \
                self.auth.attrs['token'] == 'T':

            data_instance = getattr(self.data, key)
            if not data_instance:
                raise except_orm(_("WSLSP Error!"),
                        _("Error when getting instance with key %s")%(key))

            token, sign = self.config.wsaa_ticket_id.get_token_sign()

            auth = {
                'token': token,
                'sign': sign,
                'cuit': self.config.cuit
            }

            self.login('auth', auth)
            auth_instance = getattr(data_instance, self.auth._element_name)
            for k, v in self.auth.attrs.items():
                setattr(auth_instance, k, v)
        return True

    def auth_falsehood(self):
        #Le pasamos datos para poder hacer los
        #chequeos primero y luego agregarle el token verdadero
        auth = {
            'token': 'T',
            'sign': 'S',
            'cuit': 'C',
        }
        self.login('auth', auth)
        return True

    #-------------------End-Authentication-------------------#


    #------------------------Queries-------------------------#
    def wslsp_query(self, qry_data, operation):
        if not qry_data or not isinstance(qry_data, dict):
            raise except_orm(_("WSLSP Error!"),_("Invalid Query Data"))
        self.auth_falsehood()
        self.add(qry_data, no_check=NOCHECK) #no_check='all' or [fields]
        ref_key = qry_data.keys()[0]
        self.prepare_auth(ref_key)
        response = self.request(operation)
        return response

    def _check_error(self, response, raise_exception=True):
        errors = []
        #Error de campos incorrectos?
        if 'errores' in response:
            for e in response.errores.error:
                desc = e.descripcion#.encode('utf-8')
                e_msg = _("Error [%s] \n Description: %s \n\n") %(e.codigo, desc)
                errors.append(e_msg)

        #Es un error de los excepcionales?
        if 'faultcode' in response:
            e_msg = _('An unexpected error has occurred!! \n')
            e_msg += response.faultcode + '\n' + response.faultstring
            errors.append(e_msg)

        msg = ''.join(errors)
        if raise_exception:
            if errors:
                raise except_orm(_('WSLSP Error!'), msg)
        return msg

    def _parse_code_name(self, data_objects):
        data_lst = []
        for field in data_objects:
            vals = {
                'name' : field.descripcion.encode('ascii', errors='ignore'),
                'code' : field.codigo,
            }
            data_lst.append(vals)
        return data_lst

    def get_states(self):
        qry_data = {'ConsultarProvinciasReq' : {}}
        operation = 'consultarProvincias'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'provincia')
        states_lst = self._parse_code_name(data_objects)
        return states_lst

    def get_location_for_states(self, state_code):
        data = {'solicitud' : state_code}
        qry_data = {'ConsultarLocalidadesPorProvinciaReq' : data}
        operation = 'consultarLocalidadesPorProvincia'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'localidad')
        location_lst = self._parse_code_name(data_objects)
        return location_lst

    def get_point_of_sale(self):
        point_of_sale_lst = []
        qry_data = {'ConsultarPuntosVentaReq' : {}}
        operation = 'consultarPuntosVenta'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'puntoVenta')
        if data_objects:
            point_of_sale_lst = self._parse_code_name(data_objects)
        return point_of_sale_lst

    def get_last_voucher_number(self,point_of_sale, voucher_type):
        data = {'solicitud' : {
                    'puntoVenta' : point_of_sale,
                    'tipoComprobante' : voucher_type,
                    }
                }
        qry_data = {'ConsultarUltimoNroComprobantePorPtoVtaReq' : data}
        operation = 'consultarUltimoNroComprobantePorPtoVta'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        voucher_number = getattr(response, 'nroComprobante')
        return voucher_number

    def get_operations(self):
        qry_data = {'ConsultarOperacionesReq' : {}}
        operation = 'consultarOperaciones'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'operacion')
        operation_lst = self._parse_code_name(data_objects)
        return operation_lst

    def get_voucher_type(self):
        qry_data = {'ConsultarTiposComprobanteReq' : {}}
        operation = 'consultarTiposComprobante'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'tipoComprobante')
        voucher_type_lst = self._parse_code_name(data_objects)
        return voucher_type_lst

    def get_liquidation_type(self):
        qry_data = {'ConsultarTiposLiquidacionReq' : {}}
        operation = 'consultarTiposLiquidacion'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'tipoLiquidacion')
        liquidation_type_lst = self._parse_code_name(data_objects)
        return liquidation_type_lst

    def get_participant_characters(self):
        qry_data = {'ConsultarCaracteresParticipanteReq' : {}}
        operation = 'consultarCaracteresParticipante'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'caracter')
        participant_lst = self._parse_code_name(data_objects)
        return participant_lst

    def get_categories(self):
        qry_data = {'ConsultarCategoriasReq' : {}}
        operation = 'consultarCategorias'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'categoria')
        category_lst = self._parse_code_name(data_objects)
        return category_lst

    def get_motives(self):
        qry_data = {'ConsultarMotivosReq' : {}}
        operation = 'consultarMotivos'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'motivo')
        motive_lst = self._parse_code_name(data_objects)
        return motive_lst

    def get_breeds(self):
        qry_data = {'ConsultarRazasReq' : {}}
        operation = 'consultarRazas'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'raza')
        breed_lst = self._parse_code_name(data_objects)
        return breed_lst

    def get_cuts(self):
        qry_data = {'ConsultarCortesReq' : {}}
        operation = 'consultarCortes'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'corte')
        cut_lst = self._parse_code_name(data_objects)
        return cut_lst

    def get_expenses(self):
        qry_data = {'ConsultarGastosReq' : {}}
        operation = 'consultarGastos'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'gasto')
        expense_lst = self._parse_code_name(data_objects)
        return expense_lst

    def get_tributes(self):
        qry_data = {'ConsultarTributosReq' : {}}
        operation = 'consultarTributos'
        response = self.wslsp_query(qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'tributo')
        tribute_lst = self._parse_code_name(data_objects)
        return tribute_lst

    # def get_liquidation_for_voucher(self, point_of_sale, voucher_type, number):
    #     qry_data = {'ConsultarLiquidacionPorNroComprobanteReq' : {}}
    #     operation = 'consultarLiquidacionPorNroComprobante'
    #     response = self.wslsp_query(qry_data, operation)
    #     self._check_error(response)
    #     data_objects = getattr(response, 'provincia')
    #     states_lst = self._parse_code_name(data_objects)
    #     return states_lst
    #----------------------End-Queries-----------------------#

    def generate_liquidation(self, invoice):
        #Guardamos la factura
        self.data.invoice = invoice
        #Actualizamos fechas
        invoice.complete_date_invoice()

        invoice_data = self.parse_invoice()

        #Enviamos la liquidación
        response = self.wslsp_query(invoice_data, 'generarLiquidacion')

        #Parseamos la respuesta y guardamos los datos para los logs
        invoice_vals = self.parse_invoice_response(response)
        return invoice_vals

    def parse_invoice(self):
        invoice = self.data.invoice
        voucher_type = invoice._get_wslsp_voucher_type()
        pos = invoice._get_pos()

        operation_code = self._get_operation_code()
        emitter_data = self._get_emitter_data()
        receiver_data = self._get_receiver_data()
        liquidation_data = self._get_liquidation_data()
        items_data = self._get_items_to_liquidation()
        expense_data = self._get_expenses()
        tribute_data = self._get_tribute()
        guide_data = self._get_guide()
        dte_data = self._get_dte()

        data = {
            'GenerarLiquidacionReq': {
                'solicitud': {
                    'codOperacion' : operation_code,
                    'emisor' : emitter_data,
                    'receptor' : receiver_data,
                    'datosLiquidacion' : liquidation_data,
                    #'guia' : [guide],
                    #'dte' : [dte],
                    'itemDetalleLiquidacion' : items_data,
                    #'gasto' : expense_data or {},
                    #'tributo' : tribute_data or {},
                    'datosAdicionales' : ' ',#Optional
                },
            },
        }

        #Update no required data
        if dte_data:
            data['GenerarLiquidacionReq']['solicitud'].update(dte_data)
        # if guide_data:
        #     data['GenerarLiquidacionReq']['solicitud'].update(guide_data)
        # if expense_data:
        #     data['GenerarLiquidacionReq']['solicitud'].update(expense_data)
        if tribute_data:
            data['GenerarLiquidacionReq']['solicitud'].update(tribute_data)
        return data

    def _get_operation_code(self):
        invoice = self.data.invoice
        purchase_data = invoice._check_ranch_purchase()
        billing_type = purchase_data.billing_type
        operation_code = self.config.get_operation_code(billing_type)
        return operation_code

    def _get_emitter_data(self):
        invoice = self.data.invoice
        company = invoice.company_id
        pos_ar = invoice._get_pos()
        voucher_type = invoice._get_wslsp_voucher_type()
        date = company.partner_id.date
        number = invoice.split_number()[1]
        iibb = company.partner_id.nro_insc_iibb

        vals = {
            'puntoVenta' : pos_ar,
            'tipoComprobante' : voucher_type,
            'nroComprobante' : number,
            'invoice' : invoice, #Pass reference
            'codCaracter' : '4', #TODO
            'fechaInicioActividades' : date,
            'iibb' : iibb, #Opcional
            'nroRUCA' : '1011', #Opcional #VER EL CODIGO VERDADERO
            #'nroRenspa' : '22.123.1.12345/A4', #Opcional
            #'cuitAutorizado' : '30678155469', #Opcional
        }

        return vals

    def _get_receiver_data(self):
        invoice = self.data.invoice
        #partner = invoice.partner_id
        partner = invoice.company_id.partner_id
        partner_cuit = '30160000011' or partner.vat
        iibb = partner.nro_insc_iibb
        vals = {
            'codCaracter' : '4', #TODO
            'operador' : {
                'cuit' : partner_cuit,
                'iibb' : iibb,#Opcional
                'nroRUCA' : '1011', #Opcional
                #'nroRenspa' : '22.123.1.12345/A4', #Opcional
                #'cuitAutorizado' : '30678155469', #Opcional
            }
        }
        return vals

    def _get_liquidation_data(self):
        invoice = self.data.invoice
        invoice_date = invoice.date_invoice
        invoice_line = invoice.invoice_line[0]
        purchase_data = invoice._check_ranch_purchase()
        billing_type = purchase_data.billing_type
        motive_code = self.config.get_motive_code(billing_type)
        purchase_date = purchase_data.purchase_date
        summary_line = invoice_line.get_romaneo_summary_line()
        romaneo = summary_line.romaneo_id

        vals = {
            'fechaComprobante' : invoice_date,#'2018-07-26',#invoice_date,
            'fechaOperacion' : purchase_date,#'2018-07-23', #purchase_date
            #'lugarRealizacion' : False,#Opcional
            'codMotivo' : motive_code,
            'fechaRecepcion' : romaneo.date,#'2018-07-24', #Opcional TODO
            'fechaFaena' :romaneo.date,#'2018-07-25', #Opcional TODO
            #'frigorifico' : { #Opcional
            #    'cuit' : '30678155469',
            #    'nroPlanta' : '1',
            #},
        }
        return vals

    def _get_items_to_liquidation(self):
        invoice = self.data.invoice
        invoice_lines = invoice.invoice_line
        item_lst = []
        for line in invoice_lines:
            partner = invoice.company_id.partner_id
            summary_line = line.get_romaneo_summary_line()
            romaneo = summary_line.romaneo_id
            species = summary_line.species_id
            troop_number = romaneo.troop_number
            kg_qty = int(summary_line.weight)
            head_qty = summary_line.heads+1
            category_code = self.config.get_category_code(species)
            billing_type = romaneo.billing_type
            liquidation_code = self.config.get_liquidation_type_code(billing_type)
            tax = line.invoice_line_tax_id
            voucher_type = invoice._get_wslsp_voucher_type()
            beed_code = 1

            vals = { #One or more repetitons
                #'cuitCliente' : partner.vat, #Optional
                'codCategoria' : category_code,
                'tipoLiquidacion' : liquidation_code,
                'cantidad' : int(line.quantity),
                'precioUnitario' : line.price_unit,
                # 'tipoIVANulo' : '', #'NA', #Opcional
                'raza' : {
                    'codRaza' : beed_code, #species.afip_code.code,
                },
                'nroTropa' : troop_number, #Optional
                #'codCorte' : '1', #Optional
                'cantidadKgVivo' : kg_qty, #Optional
                #'precioRecupero' : line.price_unit, #Optional
                }

            if int(beed_code) in (21, 99):
                vals['raza'].update({'detalle' : species.name})

            if tax:
                if int(voucher_type) != 189: #No se informa si la denominacion es C
                    vals['alicuotaIVA'] = float("{0:.2f}".format(tax.amount * 100))

            #Informamos la cantidad de cabezas si el tipo de liquidacion es por cabeza
            if int(liquidation_code) != 1:
                vals['cantidadCabezas'] = int(head_qty)

            #TODO: no esta desarrollado
            #Si es liquidacion de compra
            if int(voucher_type) in (183,185):
                #One or more repetitions
                vals['liquidacionCompraAsociada'] = [{
                    'tipoComprobante' : False,
                    'puntoVenta' : False,
                    'nroComprobante' : False,
                    'nroItem' : False,
                    'cantidadAsociada' : False,
                }]

            item_lst.append(vals)
        return item_lst

    def _get_expenses(self):
        expense_lst = []
        invoice = self.data.invoice
        purchase_data = invoice.purchase_data_id
        for expenses_line in purchase_data.expenses_lines:
            vals = {
                'codGasto' : expenses_line.expense_type_id.code,
                #'descripcion' : None, #Optional
                #'baseImponible' : None, #Optional
                #'alicuota' : None, #Optional
                #'importe' : None, #Optional
                #'alicuotaIVA' : expenses_line.expense_type_id.tax.amount * 100.0, #Optional
                #'tipoIVANulo' : 'NG', #Optional
                }
            if expenses_line.expense_type_id.code == "99":
                vals['descripcion'] = "TODO" #TODO
            if expenses_line.amount_type == "percentage":
                vals['alicuota'] = expenses_line.expense_amount_percentage
                vals['baseImponible'] = purchase.untaxed_total
            else:
                #TODO MUST BE 10.5 OR 21
                vals['importe'] = expenses_line.expense_amount_bill
            expense_lst.append(vals)
        return {'gasto' :  expense_lst}

    def _get_tribute(self):
        tribute_lst = []
        invoice = self.data.invoice
        # for tribute in tributes:
        #     vals = { #Zero or more repetitions
        #         'codTributo' : None,
        #         'descripcion' : None, #Optional
        #         'baseImponible' : None, #Optional
        #         'alicuota' : None, #Optional
        #         'importe' : None, #Optional
        #     }
        # tribute_lst.append({'tribute' : vals})
        return tribute_lst

    def _get_guide(self):
        guide = {
            'nroGuia' : '1'
        }
        return guide

    def _get_dte(self):
        dte = {
            'nroDTE' : '012682055-0',
            'nroRenspa' : '20.002.0.00116/D0', #Opcional
        }
        return {'dte' : [dte]}

    def parse_invoice_response(self, response):
        comp = {}

        #Si tenemos errores lo guardamos
        errors = self._check_error(response, False)
        if errors:
            err_vals = {'errors' : errors}
            self.last_request['parse_result'] = err_vals
            raise except_orm(_("WSLSP Invoice Error"),
                    _("Error when validating the invoice. Please, see it and send the invoice again!"))

        header = response.cabecera
        setting = response.emisor
        liquidation = response.datosLiquidacion
        total = response.resumenTotales
        comp = {
            'CAE' : header.cae,
            'CAE_due_date' : header.fechaVencimientoCae,
            'AFIPProcess' : header.fechaProcesoAFIP,
            'voucher_type' : setting.tipoComprobante,
            'voucher_number' : setting.nroComprobante,
            'pos_ar' : setting.puntoVenta,
            'date_invoice': liquidation.fechaComprobante,
            'amount_total' : total.importeTotalNeto,
            'pdf' : response.pdf,
        }

        #Guardamos los datos de la liquidación para usarlo en los logs
        self.last_request['parse_result'] = comp

        #Armamos los valores para escribir en la factura
        internal_number = '%04d-%08d' % (comp['pos_ar'], comp['voucher_number'])
        invoice_vals = {
            'cae' : comp['CAE'],
            'cae_due_date' : comp['CAE_due_date'],
            'internal_number' :  internal_number,
            'date_invoice' : comp['date_invoice'],
            'pdf' : comp['pdf'],
        }
        return invoice_vals

    def log_request(self, environment):
        env = environment
        if not hasattr(self, 'last_request'):
            return False

        wsfe_req_obj = env['wsfe.request']
        voucher_type_obj = env['wslsp.voucher_type.codes']
        res = self.last_request['parse_result']

        #No hay rechazos ni aprobaciones, solo hay errores.
        #Completamos con los datos que enviamos de la factura
        invoice = self.data.invoice
        voucher_type_code = invoice._get_wslsp_voucher_type()
        voucher_type = voucher_type_obj.search([('code', '=', voucher_type_code)])
        voucher_type_name = voucher_type.name
        pos = invoice._get_pos()

        errs = res.get('errors', False)
        result = 'A'
        if errs:
            result = 'R'

        detail_vals ={
            'name': invoice.id,
            'voucher_number': res.get('voucher_number'),
            'voucher_date': invoice.date_invoice,
            'amount_total': res.get('amount_total'),
            'cae': res.get('CAE'),
            'cae_duedate': res.get('CAE_due_date'),
            'result' : result,
        }

        request_vals = {
            'voucher_type': voucher_type_name,
            'nregs': 1,
            'pos_ar': '%04d' % pos,
            'date_request': time.strftime('%Y-%m-%d %H:%M:%S'),
            'result' : result,
            # 'reprocess': False,
            'errors': errs,
            'detail_ids': [(0,0, detail_vals)],
        }

        request = wsfe_req_obj.create(request_vals)
        return request
