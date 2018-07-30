# -*- coding: utf-8 -*-
##############################################################################

#   Copyright (c) 2017 Rafaela Alimentos (Eynes - Ingenieria del software)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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


DATE_FORMAT = '%Y-%m-%d'

class WSLSP(WebService):

    def __init__(self, conf, url, **kwargs):
        WebService.__init__(self, url, **kwargs)
        self.config = conf

    ###############################################################################
    # AFIP Data Validation Methods According to:
    # https://www.afip.gob.ar/ws/WSLSP/manual_wslsp_1.2.pdf
    INTEGER = ['codOperacion', 'codCaracter','nroComprobante',
           'tipoComprobante','puntoVenta']

    DATES = ['fechaInicioActividades', 'fechaComprobante',
            'fechaOperacion', 'fechaRecepcion', 'fechaFaena']

    @wsapi.check(INTEGER)
    def _check_emitter_required_fields(value, sequence=1):
        if not isinstance(value, int):
            return False
        return True

    @wsapi.check(DATES)
    def _check_date(value, sequence=2):
        datetime.strptime(value, DATE_FORMAT)
        return True


    ###############################################################################

    #--------------------authentication-----------------------#
    def prepare_auth(self, conf):
        token, sign = self.config.wsaa_ticket_id.get_token_sign()
        auth = {
            'token': token,
            'sign': sign,
            'cuit': conf.cuit
        }
        self.login('auth', auth)
        return True

    #-------------------End-Authentication-------------------#



    #------------------------Queries-------------------------#
    def wslsp_query(self,qry_data, operation):
        __import__('ipdb').set_trace()
        self.prepare_auth()
        self.add(qry_data, no_check='all')
        response = self.request(operation)
        return response

    def _check_error(self, response, raise_exception=True):
        msg = ''
        if 'errors' in response:
            error = response['error'].msg
            err_code = str(response['error'].code)
            msg = 'Codigo/s Error: %s[%s]' % (error, err_code)

            if msg != '' and raise_exception:
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
        # conf = invoice.get_wslsp_config()
        #Guardamos la configuracion y la factura
        #self.data.sent_invoice = invoice
        #self.data.invoice_conf = conf

        invoice_data = self.parse_invoice(invoice)

        #Enviamos la liquidación
        response = self.wslsp_query(invoice_data, 'generarLiquidacion')

        #Esta mal generada?
        # errors = self._check_invoice_error(response)
        # if errors:
        #     raise except_orm(errors)

        invoice_vals = self.parse_invoice_response(response)
        return invoice_vals

    def parse_invoice(self, invoice):
        voucher_type = invoice._get_wslsp_voucher_type()
        pos = invoice._get_pos()

        operation_code = self._get_operation_code(invoice)
        emitter_data = self._get_emitter_data(invoice)
        receiver_data = self._get_receiver_data(invoice)
        liquidation_data = self._get_liquidation_data(invoice)
        items_data = self._get_items_to_liquidation(invoice)
        expense_data = self._get_expenses(invoice)
        tribute_data = self._get_tribute(invoice)
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
        if expense_data:
            data['GenerarLiquidacionReq']['solicitud'].update(expense_data)
        if tribute_data:
            data['GenerarLiquidacionReq']['solicitud'].update(tribute_data)
        return data

    def _get_operation_code(self, invoice):
        purchase_data = invoice._check_ranch_purchase()
        billing_type = purchase_data.billing_type
        operation_code = self.config.get_operation_code(billing_type)
        return operation_code

    def _get_emitter_data(self, invoice):
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
            'codCaracter' : '4', #TODO
            'fechaInicioActividades' : date,
            'iibb' : iibb, #Opcional
            'nroRUCA' : '1011', #Opcional #VER EL CODIGO VERDADERO
            #'nroRenspa' : '22.123.1.12345/A4', #Opcional
            #'cuitAutorizado' : '30678155469', #Opcional
        }

        return vals

    # def _has_all_attrs(self, suds_obj, *args, **kwargs):
    #     if 'itemDetalleLiquidacion' in suds_obj.solicitud:
    #         for detail in suds_obj.solicitud.itemDetalleLiquidacion:
    #             del(detail.tipoIVANulo)
    # return

    def _get_receiver_data(self, invoice):
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

    def _get_liquidation_data(self, invoice):
        invoice_date = invoice.date_invoice
        invoice_line = invoice.invoice_line[0]
        purchase_data = invoice._check_ranch_purchase()
        billing_type = purchase_data.billing_type
        motive_code = self.config.get_motive_code(billing_type)

        vals = {
            'fechaComprobante' : '2018-07-26',#invoice_date,
            'fechaOperacion' : '2018-07-23', #Compra
            #'lugarRealizacion' : False,#Opcional
            'codMotivo' : motive_code,
            'fechaRecepcion' : '2018-07-24', #Opcional
            'fechaFaena' :'2018-07-25', #Opcional
            #'frigorifico' : { #Opcional
            #    'cuit' : '30678155469',
            #    'nroPlanta' : '1',
            #},
        }
        return vals

    def _get_items_to_liquidation(self, invoice):
        invoice_lines = invoice.invoice_line
        item_lst = []
        for line in invoice_lines:
            partner = line.invoice_id.company_id.partner_id
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
            beed_code = 1

            vals = { #One or more repetitons
                #'cuitCliente' : partner.vat, #Optional
                'codCategoria' : category_code,
                'tipoLiquidacion' : liquidation_code,
                'cantidad' : int(line.quantity),
                'precioUnitario' : line.price_unit,
                #'tipoIVANulo' : 'NG', #'NA', #Opcional
                'alicuotaIVA' : 21.0, #21.0,#tax.amount * 100, #Opcional #No se informa si la denominacion es C
                'cantidadCabezas' : int(head_qty), #Opcional
                'raza' : {
                    'codRaza' : beed_code, #species.afip_code.code,
                    #'detalle' : species.name, #SOLO COMPLETAR SI ES 21 O 99
                },
                'nroTropa' : '1',#troop_number, #Optional
                #'codCorte' : '1', #Optional
                'cantidadKgVivo' : kg_qty, #Optional
                #'precioRecupero' : line.price_unit, #Optional
                # 'liquidacionCompraAsociada' : [{ #Zero or more repetitons
                #     'tipoComprobante' : False,
                #     'puntoVenta' : None,
                #     'nroComprobante' : None,
                #     'nroItem' : None,
                #     'cantidadAsociada' : None,
                #     }]
                }

            if int(beed_code) in (21, 99):
                vals['raza'].update({'detalle' : species.name})

            item_lst.append(vals)
        return item_lst

    def _get_expenses(self, invoice):
        expense_lst = []
        purchase_data = invoice.purchase_data_id
        for expense_line in purchase_data.expenses_lines:
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
            expense_lst.append({'gasto' : vals})
        return expense_lst

    def _get_tribute(self, invoice):
        tribute_lst = []
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

    def _check_invoice_error(self, response):
        errors = []
        #Error de campos incorrectos?
        if 'errores' in response:
            for e in response.errores.error:
                desc = e.descripcion.encode('latin1')
                e_msg = _("Error [%s] \n Description: %s \n\n") %(e.codigo, desc)
                errors.append(e_msg)
        return errors

    def parse_invoice_response(self, response):
        comp = {}

        #Si tenemos errores lo guardamos
        errors = self._check_invoice_error(response)
        if errors:
            comp.update(errors)

        if 'cabecera' in response:
            header = response.cabecera
            header_vals = {
                'CAE' : header.cae,
                'CAE_due_date' : header.fechaVencimientoCae,
                'AFIPProcess' : header.fechaProcesoAFIP,
            }
            comp.update(header_vals)

        if 'emisor' in response:
            setting = response.emisor
            setting_vals = {
                'voucher_type' : setting.tipoComprobante,
                'voucher_number' : setting.nroComprobante,
                'pos_ar' : setting.puntoVenta,
            }
            comp.update(setting_vals)

        if 'datosLiquidacion' in response:
            liquidation = response.datosLiquidacion
            liquidation_vals = {
                'date_invoice': liquidation.fechaComprobante,
            }
            comp.update(liquidation_vals)

        if 'resumenTotales' in response:
            total = response.resumenTotales
            total_vals = {
                'amount_total' : total.importeTotalNeto
            }
            comp.update(total_vals)


        if 'pdf' in response:
            pdf_vals = {
                'pdf' : response.pdf,
            }
            comp.update(pdf_vals)

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
        __import__('ipdb').set_trace()
        if not hasattr(self, 'last_request'):
            return False

        wsfe_req_obj = env['wsfe.request']
        voucher_type_obj = env['wslsp.voucher_type.codes']
        res = self.last_request['parse_result']
        voucher_type_code = res['voucher_type']

        voucher_type = voucher_type_obj.search([('code', '=', voucher_type_code)])
        voucher_type_name = voucher_type.name

        req_details = []
        pos = res['pos_ar']

        errs = ''.join(res.get('errors',[]))
        result = 'A'
        if errs:
            result = 'R'

        detail_vals ={
            #'name': invoice_id,
            'voucher_number': res['voucher_number'],
            'voucher_date': res['date_invoice'],
            'amount_total': res['amount_total'],
            'cae': res['CAE'],
            'cae_duedate': res['CAE_due_date'],
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
