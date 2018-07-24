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

import logging

_logger = logging.getLogger(__name__)

class WSLSP(WebService):

    #--------------------authentication-----------------------#
    def prepare_auth(self, conf):
        token, sign = conf.wsaa_ticket_id.get_token_sign()
        auth = {
            'token': token,
            'sign': sign,
            'cuit': conf.cuit
        }
        self.login('auth', auth)
        return True

    #-------------------End-Authentication-------------------#



    #------------------------Queries-------------------------#
    def wslsp_query(self, conf, qry_data, operation):
        self.prepare_auth(conf)
        self.add(qry_data)
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

    def get_states(self, conf):
        qry_data = {'ConsultarProvinciasReq' : {}}
        operation = 'consultarProvincias'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'provincia')
        states_lst = self._parse_code_name(data_objects)
        return states_lst

    def get_location_for_states(self, conf, state_code):
        data = {'solicitud' : state_code}
        qry_data = {'ConsultarLocalidadesPorProvinciaReq' : data}
        operation = 'consultarLocalidadesPorProvincia'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'localidad')
        location_lst = self._parse_code_name(data_objects)
        return location_lst

    def get_point_of_sale(self, conf):
        point_of_sale_lst = []
        qry_data = {'ConsultarPuntosVentaReq' : {}}
        operation = 'consultarPuntosVenta'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'puntoVenta')
        if data_objects:
            point_of_sale_lst = self._parse_code_name(data_objects)
        return point_of_sale_lst

    def get_last_voucher_number(self, conf, point_of_sale, voucher_type):
        data = {'solicitud' : {
                    'puntoVenta' : point_of_sale,
                    'tipoComprobante' : voucher_type,
                    }
                }
        qry_data = {'ConsultarUltimoNroComprobantePorPtoVtaReq' : data}
        operation = 'consultarUltimoNroComprobantePorPtoVta'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        voucher_number = getattr(response, 'nroComprobante')
        return voucher_number

    def get_operations(self, conf):
        qry_data = {'ConsultarOperacionesReq' : {}}
        operation = 'consultarOperaciones'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'operacion')
        operation_lst = self._parse_code_name(data_objects)
        return operation_lst

    def get_voucher_type(self, conf):
        qry_data = {'ConsultarTiposComprobanteReq' : {}}
        operation = 'consultarTiposComprobante'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'tipoComprobante')
        voucher_type_lst = self._parse_code_name(data_objects)
        return voucher_type_lst

    def get_liquidation_type(self, conf):
        qry_data = {'ConsultarTiposLiquidacionReq' : {}}
        operation = 'consultarTiposLiquidacion'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'tipoLiquidacion')
        liquidation_type_lst = self._parse_code_name(data_objects)
        return liquidation_type_lst

    def get_participant_characters(self, conf):
        qry_data = {'ConsultarCaracteresParticipanteReq' : {}}
        operation = 'consultarCaracteresParticipante'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'caracter')
        participant_lst = self._parse_code_name(data_objects)
        return participant_lst

    def get_categories(self, conf):
        qry_data = {'ConsultarCategoriasReq' : {}}
        operation = 'consultarCategorias'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'categoria')
        category_lst = self._parse_code_name(data_objects)
        return category_lst

    def get_motives(self, conf):
        qry_data = {'ConsultarMotivosReq' : {}}
        operation = 'consultarMotivos'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'motivo')
        motive_lst = self._parse_code_name(data_objects)
        return motive_lst

    def get_breeds(self, conf):
        qry_data = {'ConsultarRazasReq' : {}}
        operation = 'consultarRazas'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'raza')
        breed_lst = self._parse_code_name(data_objects)
        return breed_lst

    def get_cuts(self, conf):
        qry_data = {'ConsultarCortesReq' : {}}
        operation = 'consultarCortes'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'corte')
        cut_lst = self._parse_code_name(data_objects)
        return cut_lst

    def get_expenses(self, conf):
        qry_data = {'ConsultarGastosReq' : {}}
        operation = 'consultarGastos'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'gasto')
        expense_lst = self._parse_code_name(data_objects)
        return expense_lst

    def get_tributes(self, conf):
        qry_data = {'ConsultarTributosReq' : {}}
        operation = 'consultarTributos'
        response = self.wslsp_query(conf, qry_data, operation)
        self._check_error(response)
        data_objects = getattr(response, 'tributo')
        tribute_lst = self._parse_code_name(data_objects)
        return tribute_lst

    # def get_liquidation_for_voucher(self, conf, point_of_sale, voucher_type, number):
    #     qry_data = {'ConsultarLiquidacionPorNroComprobanteReq' : {}}
    #     operation = 'consultarLiquidacionPorNroComprobante'
    #     response = self.wslsp_query(conf, qry_data, operation)
    #     self._check_error(response)
    #     data_objects = getattr(response, 'provincia')
    #     states_lst = self._parse_code_name(data_objects)
    #     return states_lst
    #----------------------End-Queries-----------------------#
    def parse_invoices(self, invoices, first_number=False):
        reg_qty = len(invoices)
        voucher_type = invoices[0]._get_voucher_type()
        pos = invoices[0]._get_pos()
        data = {
            'GenerarLiquidacionReq': {
                'solicitud': {
                    'codOperacion' : None,
                    'emisor' : {
                        'puntoVenta' : None,
                        'tipoComprobante' : None,
                        'nroComprobante' : None,
                        'codCaracter' : None,
                        'fechaInicioActividades' : None,
                        'iibb' : None, #Opcional
                        'nroRUCA' : None, #Opcional
                        'nroRenspa' : None, #Opcional
                        'cuitAutorizado' : None, #Opcional
                    },
                    'receptor' : {
                        'codCaracter' : None,
                        'operador' :{
                            'cuit' : None,
                            'iibb' : None,#Opcional
                            'nroRUCA' : None, #Opcional
                            'nroRenspa' : None, #Opcional
                            'cuitAutorizado' : None, #Opcional
                            },
                    },
                    'datosLiquidacion' : {
                        'fechaComprobante' : None,
                        'fechaOperacion' : None,
                        'lugarRealizacion' : None, #Opcional
                        'codMotivo' : None,
                        'fechaRecepcion' : None, #Opcional
                        'fechaFaena' : None, #Opcional
                        'frigorifico' : { #Opcional
                            'cuit' : None,
                            'nroPlanta' : None,
                        },
                    },
                    'guia' : [{ #Zero or more repetitons
                        'nroGuia' : None,
                    }],
                    'dte' : [{ #Zero or more repetitons
                        'nroDTE' : None,
                        'nroRenspa' : None,
                    }],
                    'itemDetalleLiquidacion' : [{ #One or more repetitons
                        'cuitCliente' : None, #Optional
                        'codCategoria' : None,
                        'tipoLiquidacion' : None,
                        'cantidad' : None,
                        'precioUnitario' : None,
                        'alicuotaIVA' : None,
                        'cantidadCabezas' : None,
                        'raza' : {
                            'codRaza' : None,
                            'detalle' : None,
                        },
                        'nroTropa' : None, #Optional
                        'codCorte' : None, #Optional
                        'cantidadKgVivo' : None, #Optional
                        'precioRecupero' : None, #Optional
                        'liquidacionCompraAsociada' : [{ #Zero or more repetitons
                            'tipoComprobante' : None,
                            'puntoVenta' : None,
                            'nroComprobante' : None,
                            'nroItem' : None,
                            'cantidadAsociada' : None,
                        }],
                    }],
                    'gasto' : [{#Zero or more repetions
                        'codGasto' : None,
                        'descripcion' : None, #Optional
                        'baseImponible' : None, #Optional
                        'alicuota' : None, #Optional
                        'importe' : None, #Optional
                        'alicuotaIVA' : None, #Optional
                        'tipoIVANulo' : None, #Optional
                    }],
                    'tributo' : [{ #Zero or more repetitions
                        'codTributo' : None,
                        'descripcion' : None, #Optional
                        'baseImponible' : None, #Optional
                        'alicuota' : None, #Optional
                        'importe' : None, #Optional
                    }],
                    'datosAdicionales' : None, #Optional
                },
            },
        }
        details_array = data['FECAESolicitar']['FeCAEReq'][
            'FeDetReq']['FECAEDetRequest']
        nn = False
        for inv_index, inv in enumerate(invoices):
            if first_number:
                nn = first_number + inv_index
            inv_data = self.parse_invoice(inv, number=nn)
            inv_data['first_of_lot'] = False
            if (first_number and nn == first_number) or len(invoices) == 1:
                inv_data['first_of_lot'] = True
            details_array.append(inv_data)
        return data

    def _get_emitter_data(self, invoice, number=False):
        #pos_ar = invoice.pos_ar_id.name
        pos_ar = invoice._get_pos()
        voucher_type = invoice._get_voucher_type() #TODO
        date = invoice.company_id.date
        if not number:
            number = invoice.split_number()[1]

        vals = {
            'puntoVenta' : pos_ar,
            'tipoComprobante' : voucher_type,
            'nroComprobante' : number,
            'codCaracter' : None,
            'fechaInicioActividades' : date,
            #'iibb' : None, #Opcional
            #'nroRUCA' : None, #Opcional
            #'nroRenspa' : None, #Opcional
            #'cuitAutorizado' : None, #Opcional
        }
        return vals

    def _get_recever_data(self, invoice):
        partner_cuit = invoice.partner_id.vat
        vals = {
            'codCaracter' : None,
            'operador' : {
                'cuit' : partner_cuit,
                #'iibb' : None,#Opcional
                #'nroRUCA' : None, #Opcional
                #'nroRenspa' : None, #Opcional
                #'cuitAutorizado' : None, #Opcional
            }
        }
        return vals

    def _get_liquidation_data(self, invoice, config):
        invoice_date = invoice.date_invoice
        invoice_line = invoice.invoice_line[0]
        purchase_data = invoice.get_ranch_purchase_data()
        billing_type = purchase_data.billing_type
        motive_code = config.get_motive_code(billing_type)

        vals = {
            'fechaComprobante' : invoice_date,
            'fechaOperacion' : invoice_date,
            #'lugarRealizacion' : None, #Opcional
            'codMotivo' : motive_code,
            #'fechaRecepcion' : None, #Opcional
            #'fechaFaena' : None, #Opcional
            #'frigorifico' : { #Opcional
                #'cuit' : None,
                #'nroPlanta' : None,
            #},
        }
        return vals

    def _get_items_to_liquidation(self, invoice, config):
        invoice_lines = invoice.invoice_line
        item_lst = []
        for line in invoice_lines:
            summary_line = line.get_romaneo_summary_line()
            romaneo = summary_id.romaneo_id
            species = summary_line.species_id
            troop_number = romaneo.troop_number
            kg_qty = int(summary_line.weight)
            head_qty = summary_line.heads+1
            category_code = config.get_category_code(species)
            liquidation_code = config.get_liquidation_type_code(billing_type)
            vals = { #One or more repetitons
                #'cuitCliente' : None, #Optional
                'codCategoria' : category_code,
                'tipoLiquidacion' : liquidation_code,
                'cantidad' : line.quantity,
                'precioUnitario' : line.price_unit,
                'alicuotaIVA' : invoice_line_tax_id.amount * 100,
                'cantidadCabezas' : head_qty,
                'raza' : {
                    'codRaza' : species.afip_code,
                    'detalle' : species.name,
                },
                'nroTropa' : troop_number, #Optional
                'codCorte' : None, #Optional
                'cantidadKgVivo' : kg_qty, #Optional
                'precioRecupero' : line.price_unit, #Optional
                'liquidacionCompraAsociada' : [{ #Zero or more repetitons
                    'tipoComprobante' : None,
                    'puntoVenta' : None,
                    'nroComprobante' : None,
                    'nroItem' : None,
                    'cantidadAsociada' : None,
                    }]
                }
        return item_lst

    def _get_expenses(self, invoice):
        expense_lst = []
        purchase_data = invoice.get_ranch_purchase_data()
        for expense_line in purchase_data.expenses_lines:
            vals = {
                'codGasto' : expenses_line.expense_type_id.code,
                #'descripcion' : None, #Optional
                #'baseImponible' : None, #Optional
                #'alicuota' : None, #Optional
                #'importe' : None, #Optional
                'alicuotaIVA' : expenses_line.expense_type_id.tax.amount * 100.0, #Optional
                'tipoIVANulo' : None, #Optional
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
        return {'gasto' : expense_lst}

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
        # tribute_lst.append(vals)
        return {'tribute' : tribute_lst}
