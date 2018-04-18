from suds.client import Client
from wsaa_suds import WSAA
from wsfe_suds import WSFEv1
from datetime import datetime
import urllib2

import logging
import re

# Direcciones de los servicios web
WSLSP_URL_HOMO = "https://fwshomo.afip.gov.ar/wslsp/LspService?wsdl"
WSLSP_URL_PROD = "https://serviciosjava.afip.gob.ar/wslsp/LspService?wsdl"

# TODO: Este seteo nunca se hace por como se importa este archivo
# Por otro lao habria que setear el loglevel desde el config
# del OpenERP
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.INFO)
logging.getLogger('suds.transport').setLevel(logging.INFO)
logging.getLogger('suds.xsd.schema').setLevel(logging.INFO)
logging.getLogger('suds.wsdl').setLevel(logging.INFO)


#TODO REVISE CHECKS    

def _no_check(value):
    return True

def _check_short(value):
    return -32768 <= value <= 32767

def _check_int(llen = 0):
    
    if llen > 0:
        def f(value):
            return 0 < value < 10**llen
    else:
        def f(value):
            return -2147483648 <= value <= 2147483647

    return f

def _check_long(llen = 0):
    
    if llen > 0:
        def f(value):
            return 0 < value < 10**llen
    else:
        def f(value):
            return -9223372036854775808 <= value <= 9223372036854775807

    return f

def _check_cuit():
    return _check_long(11)

def _check_string(llen = 0):
    
    if llen > 0:
        def f(value):
            return len(value) <= llen
    else:
        def f(value):
            #?
            return -2147483648 <= value <= 2147483647

    return f

def _check_regex(regex):
    def f(value):
        return re.match(regex,value)
    return f

def _check_date():
    return _check_regex("([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))")

def _check_decimal(intt,comma,signed=False):
    def f(value):
        try:
            decimal_str = "{0:f}".format(value)
            if signed:
                return _check_regex("-?([1-9]\d{1,%d}|0).\d{%d}0{%d}" % (intt-1,comma,6-comma))(decimal_str)
            else:
                return _check_regex("([1-9]\d{1,%d}|0).\d{%d}0{%d}" % (intt-1,comma,6-comma))(decimal_str)
        except ValueError as e:
            return False
    return f

def _check_amount():
    return _check_decimal(13,3)

def _check_quantity():
    return _check_int(5)

def _check_alicuotaIVA(value):
    return str(value) == "10.5" or str(value) == "21"


class Error:

    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

    def __str__(self):
        return '%s (Err. %s)' % (self.msg, self.code)

    def __repr__(self):
        return '%s (Err. %s)' % (self.msg, self.code)


class Event:

    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

    def __str__(self):
        return '%s (Evento %s)' % (self.msg, self.code)

# Initial implementation v 1.4.1
class WSLSP:

    def __init__(self, cuit, token, sign, wslsp=WSLSP_URL_HOMO):
        self.wslsp_url = wslsp
        self.connected = True
        self.cuit = cuit
        self.token = token
        self.sign = sign
        self.client = None

        # Creamos el cliente
        self._create_client(token, sign)

        #TODO move
        self._resetItemsDetalleLiquidacion()
        self._resetGuias()
        self._resetDTE()
        self._resetGastos()
        self._resetTributos()

    def _create_client(self, token, sign):
        try:
            self.client = Client(self.wslsp_url)
            self.client.set_options(location=self.wslsp_url.replace('?wsdl', ''))
        except urllib2.URLError:
            #logger.warning("WSFE: No hay conexion disponible")
            self.connected = False
            raise Exception('No se puede conectar al servicio WSLSP')

        # Creamos el argauth
        if self.connected:
            self.argauth = self.client.factory.create('ns0:Auth')
            self.argauth.cuit = self.cuit
            self.argauth.token = token
            self.argauth.sign = sign

        return True

    def _get_errors(self, result):
        errors = []
        if 'errores' in result:
            for error in result.errores.error:
                error = Error(error.codigo, error.descripcion)
                errors.append(error)
        return errors

    def _get_events(self, result):
        events = []
        if 'Events' in result:
            for event in result.Events.Evt:
                event = Event(event.codigo, event.descripcion)
                events.append(event)
        return events

    def print_services(self):
        if self.connected:
            print self.client
        return

    def dummy(self):
        result = self.client.service.dummy()
        res = {}
        res['response'] = {
                'appserver': result.appserver,
                'dbserver': result.dbserver,
                'authserver': result.authserver}
        return res

    def consultarCaracteresParticipante(self):

        # Llamamos a la funcion
        result = self.client.service.consultarCaracteresParticipante(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'caracter' in result:
            res['response'] = result.caracter

        return res

    def consultarCategorias(self):

        # Llamamos a la funcion
        result = self.client.service.consultarCategorias(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'categoria' in result:
            res['response'] = result.categoria

        return res

    def consultarCortes(self):

        # Llamamos a la funcion
        result = self.client.service.consultarCortes(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'corte' in result:
            res['response'] = result.corte

        return res

    def consultarGastos(self):

        # Llamamos a la funcion
        result = self.client.service.consultarGastos(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'gasto' in result:
            res['response'] = result.gasto

        return res

    def consultarMotivos(self):

        # Llamamos a la funcion
        result = self.client.service.consultarMotivos(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'motivo' in result:
            res['response'] = result.motivo

        return res

    def consultarOperaciones(self):

        # Llamamos a la funcion
        result = self.client.service.consultarOperaciones(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'operacion' in result:
            res['response'] = result.operacion

        return res

    def consultarProvincias(self):

        # Llamamos a la funcion
        result = self.client.service.consultarProvincias(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'provincia' in result:
            res['response'] = result.provincia

        return res

    def consultarPuntosVenta(self):

        # Llamamos a la funcion
        result = self.client.service.consultarPuntosVenta(self.argauth,1)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'puntoVenta' in result:
            res['response'] = result.puntoVenta

        return res

    def consultarRazas(self):

        # Llamamos a la funcion
        result = self.client.service.consultarRazas(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'raza' in result:
            res['response'] = result.raza

        return res

    def consultarTiposComprobante(self):

        # Llamamos a la funcion
        result = self.client.service.consultarTiposComprobante(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'tipoComprobante' in result:
            res['response'] = result.tipoComprobante

        return res

    def consultarTiposLiquidacion(self):

        # Llamamos a la funcion
        result = self.client.service.consultarTiposLiquidacion(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'tipoLiquidacion' in result:
            res['response'] = result.tipoLiquidacion

        return res

    def consultarTributos(self):

        # Llamamos a la funcion
        result = self.client.service.consultarTributos(self.argauth)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'tributo' in result:
            res['response'] = result.tributo

        return res

    def consultarLocalidadesPorProvincia(self, codProvincia = 1):

        # Llamamos a la funcion
        arg = self.client.factory.create('ns0:ConsultarLocalidadesPorProvinciaSolicitud')
        arg.codProvincia = codProvincia
        result = self.client.service.consultarLocalidadesPorProvincia(self.argauth, arg)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'localidad' in result:
            res['response'] = result.localidad

        return res

    def consultarUltimoNroComprobantePorPtoVta(self, puntoVenta = None, tipoComprobante = None):

        # Llamamos a la funcion
        arg = self.client.factory.create('ns0:ConsultarUltNroComprobantePorPtoVtaSolicitud')
        #TODO THROW ERROR
        arg.puntoVenta = self._get_puntoVenta() or puntoVenta
        arg.tipoComprobante = self._get_tipoComprobante() or tipoComprobante
        result = self.client.service.consultarUltimoNroComprobantePorPtoVta(self.argauth, arg)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        if 'nroComprobante' in result:
            res['response'] = result.nroComprobante

        return res

    def consultarLiquidacionPorNroComprobante(self):

        # Llamamos a la funcion
        arg = self.client.factory.create('ns0:ConsultarLiquidacionPorNroComprobanteSolicitud')
        #TODO THROW ERROR
        arg.puntoVenta = self._get_puntoVenta()
        arg.tipoComprobante = self._get_tipoComprobante()
        arg.nroComprobante = self._get_nroComprobante()
        result = self.client.service.consultarLiquidacionPorNroComprobante(self.argauth, arg)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        #ONLY ERROR GOTTEN
        if 'nroComprobante' in result:
            res['response'] = result.nroComprobante

        return res

    def generarAjuste (self, tipoAjuste = "C", fechaComprobante = '2018-03-26'):
        
        # Llamamos a la funcion
        arg = self.client.factory.create('ns0:GenerarAjusteSolicitud')
        #TODO WIP generar ajuste

        #tipoAjuste = self.client.factory.create('ns0:TipoAjuste')
        #tipoAjuste.value = "C" if tipoAjuste == "C" else "D" 
        arg.tipoAjuste = tipoAjuste
        #arg.tipoAjuste = "C" if tipoAjuste == "C" else "D"
        arg.fechaComprobante = fechaComprobante
        emisor = self.client.factory.create('ns0:EmisorAjusteSolicitud')
        emisor.puntoVenta = self._get_puntoVenta()
        emisor.nroComprobante = self._get_nroComprobante()
        comprobanteAAjustar = self.client.factory.create('ns0:ComprobanteAAjustar')
        comprobanteAAjustar.puntoVenta = self._get_puntoVenta() #TODO diff emisor, comprobante
        comprobanteAAjustar.tipoComprobante = self._get_tipoComprobante()
        comprobanteAAjustar.nroComprobante = _get_nroComprobante()
        emisor.comprobanteAAjustar = comprobanteAAjustar
        arg.emisor = emisor
        #ajusteFinanciero = self.client.factory.create('ns0:AjusteFinancieroSolicitud')
        #gasto = self.client.factory.create('ns0:GastoSolicitud')
        #tributo = self.client.factory.create('ns0:TributoSolicitud')

        # <xsd:complexType name="AjusteFinancieroSolicitud">
        # <xsd:sequence>
        # <xsd:element name="gasto" type="tns:GastoSolicitud" maxOccurs="unbounded" minOccurs="0"></xsd:element>
        # <xsd:element name="tributo" type="tns:TributoSolicitud" maxOccurs="unbounded" minOccurs="0"></xsd:element>
        # </xsd:sequence>
        result = self.client.service.generarAjuste(self.argauth, arg)

        # <xsd:element name="itemDetalleAjusteLiquidacion" type="tns:ItemDetalleAjusteSolicitud" maxOccurs="unbounded" minOccurs="0"></xsd:element>
        # <xsd:element name="ajusteFinanciero" type="tns:AjusteFinancieroSolicitud" maxOccurs="1" minOccurs="0"></xsd:element>
        # <xsd:element name="datosAdicionales" type="tns:Texto1000" maxOccurs="1" minOccurs="0"></xsd:element>

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        events = self._get_events(result)
        if len(events):
            res['events'] = events

        #ONLY ERROR GOTTEN
        if 'nroComprobante' in result:
            res['response'] = result.nroComprobante

        return res
    
    def generarLiquidacion(self):

        # Llamamos a la funcion
        arg = self.client.factory.create('ns0:GenerarLiquidacionSolicitud')

#         <xsd:sequence>
# <xsd:element name="datosAdicionales" type="tns:Texto1000" maxOccurs="1" minOccurs="0"></xsd:element>
#         </xsd:sequence>

        arg.codOperacion = self._get_codOperacion()
        arg.emisor = self._get_emisorSolicitud()
        arg.receptor = self._get_receptorSolicitud() 
        arg.datosLiquidacion = self._get_datosLiquidacionSolicitud()
        arg.itemDetalleLiquidacion = self._get_itemsDetalleLiquidacion()
        arg.guia = self._get_guia()
        arg.dte = self._get_dte()
        arg.gasto = self._get_gasto()
        arg.tributo = self._get_tributo()
        arg.datosAdicionales = self._get_datosAdicionales()
        #import ipdb;ipdb.set_trace()

        result = self.client.service.generarLiquidacion(self.argauth, arg)

        res = {}
        # Obtenemos Errores y Eventos
        errors = self._get_errors(result)
        if len(errors):
            res['errors'] = errors

        if 'errors' not in result:
            res['response'] = result
        # TODO Check if 500 (pdf)

        return {
            'cae' : result.cabecera['cae'],
            'cae_due_date' : result.cabecera['fechaVencimientoCae'],
            'nroComprobante' : result.emisor['nroComprobante'],
            'pdf' : result.pdf,
            'summary' : result.resumenTotales,
        }


        # OK consultarCaracteresParticipante(Auth auth, )
        # OK consultarCategorias(Auth auth, )
        # OK consultarCortes(Auth auth, )
        # OK consultarGastos(Auth auth, )
        # ?  consultarLiquidacionPorNroComprobante(Auth auth, ConsultarLiquidacionPorNroComprobanteSolicitud solicitud, )
        # OK consultarLocalidadesPorProvincia(Auth auth, ConsultarLocalidadesPorProvinciaSolicitud solicitud, )
        # OK consultarMotivos(Auth auth, )
        # OK consultarOperaciones(Auth auth, )
        # OK consultarProvincias(Auth auth, )
        # OK consultarPuntosVenta(Auth auth, )
        # OK consultarRazas(Auth auth, )
        # OK consultarTiposComprobante(Auth auth, )
        # OK consultarTiposLiquidacion(Auth auth, )
        # OK consultarTributos(Auth auth, )
        # OK consultarUltimoNroComprobantePorPtoVta(Auth auth, ConsultarUltNroComprobantePorPtoVtaSolicitud solicitud, )
        # OK dummy()
        # generarAjuste(Auth auth, GenerarAjusteSolicitud solicitud, )
        # OK generarLiquidacion(Auth auth, GenerarLiquidacionSolicitud solicitud, )

    def set_puntoVenta(self, pos):
        self.puntoVenta = puntoVenta

    def set_tipoComprobante(self, tipoComprobante):
        self.tipoComprobante = tipoComprobante

    def set_nroComprobante(self, nroComprobante):
        self.nroComprobante = nroComprobante

    def set_codOperacion(self, codOperacion):
        self.codOperacion = codOperacion

    def set_datosAdicionales(self, datosAdicionales):
        self.datosAdicionales = datosAdicionales

    def set_emisorSolicitud(self, dictt):

        emisor = self.client.factory.create('ns0:EmisorSolicitud')
        #TODO consultarUltim... can have no 'response'
        dictt['nroComprobante'] = self.consultarUltimoNroComprobantePorPtoVta(puntoVenta = dictt['puntoVenta'], tipoComprobante = dictt['tipoComprobante'])['response'] + 1 
        keys = ['puntoVenta','tipoComprobante','nroComprobante','codCaracter','fechaInicioActividades','iibb','nroRUCA','nroRenspa','cuitAutorizado']
        
        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(emisor,name,value)
                else:
                    #TODO ERROR
                    pass

        self.emisorSolicitud = emisor

    def set_receptorSolicitud(self, dictt):
        receptor = self.client.factory.create('ns0:ReceptorSolicitud')
        
        keys = ['codCaracter','operador',]
        if 'operador' in dictt:
            dictt['operador'] = self.new_receptorOperadorSolicitud(dictt['operador'])
        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(receptor,name,value)
                else:
                    #TODO ERROR
                    pass

        if 'operador' not in dictt:
            datosLiquidacion.operador = None

        self.receptorSolicitud = receptor

    def new_receptorOperadorSolicitud(self, dictt):
        
        operador = self.client.factory.create('ns0:ReceptorOperadorSolicitud')
        
        keys = ['cuit','iibb','nroRenspa','nroRUCA','cuitAutorizado']

        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(operador,name,value)
                else:
                    #TODO ERROR
                    pass

        return operador

    def set_datosLiquidacionSolicitud(self, dictt):
        datosLiquidacion = self.client.factory.create('ns0:DatosLiquidacionSolicitud')
        
        keys = ['fechaComprobante','fechaOperacion','lugarRealizacion','codMotivo','fechaRecepcion','fechaFaena','cuit','nroPlanta','frigorifico']
        
        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(datosLiquidacion,name,value)
                else:
                    #TODO ERROR
                    pass

        #TODO frigorifico
        if 'frigorifico' not in dictt:
            datosLiquidacion.frigorifico = None

        self.datosLiquidacionSolicitud = datosLiquidacion

    def add_itemDetalleLiquidacion(self, dictt):
        itemDetalleLiquidacion = self.client.factory.create('ns0:ItemDetalleLiquidacionSolicitud')

        if 'raza' in dictt:
            dictt['raza'] = self.new_raza(dictt['raza'])

        keys = ['cuitCliente', 'codCategoria', 'tipoLiquidacion', 'cantidad', 'precioUnitario', 'alicuotaIVA', 'cantidadCabezas', 'nroTropa', 'codCorte', 'cantidadKilovivo', 'precioRecupero', 'raza','tipoIVANulo'] 
        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(itemDetalleLiquidacion,name,value)
                else:
                    #TODO ERROR
                    pass

        #TODO tipoIVANulo
        if 'tipoIVANulo' not in dictt:
            itemDetalleLiquidacion.tipoIVANulo = None

        self.itemsDetalleLiquidacion.append(itemDetalleLiquidacion)

    def new_raza(self, dictt):
        raza = self.client.factory.create('ns0:Raza')

        keys = ['codRaza', 'detalle'] 
        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(raza,name,value)
                else:
                    #TODO ERROR
                    pass

        return raza

    def add_Gasto(self, dictt):
        gasto = self.client.factory.create('ns0:GastoSolicitud')

        keys = ['codGasto', 'descripcion', 'baseImponible', 'importe', 'alicuotaIVA', 'alicuota', 'tipoIVANulo'] 
        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(gasto,name,value)
                else:
                    #TODO ERROR
                    pass

        if 'tipoIVANulo' not in dictt:
            gasto.tipoIVANulo = None

        self.gastos.append(gasto)

    def add_DTE(self, dictt):
        dte = self.client.factory.create('ns0:DTESolicitud')

        keys = ['nroDTE', 'nroRenspa'] 
        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(dte,name,value)
                else:
                    #TODO ERROR
                    pass

        self.DTE.append(dte)

    def add_Guia(self, dictt):
        guia = self.client.factory.create('ns0:GuiaSolicitud')

        keys = ['nroGuia']
        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(guia,name,value)
                else:
                    #TODO ERROR
                    pass

        self.guias.append(guia)

    def add_Tributo(self, dictt):
        tributo = self.client.factory.create('ns0:TributoSolicitud')

        keys = ['codTributo', 'descripcion', 'baseImponible','alicuota','importe'] 
        
        for name,value in dictt.items():
            if name in keys:
                if self._check(name,value):
                    setattr(tributo,name,value)
                else:
                    #TODO ERROR
                    pass

        self.tributos.append(tributo)

    def _resetItemsDetalleLiquidacion(self):
        self.itemsDetalleLiquidacion = []

    def _resetDTE(self):
        self.DTE = []
    
    def _resetGastos(self):
        self.gastos = []
    
    def _resetGuias(self):
        self.guias = []

    def _resetTributos(self):
        self.tributos = []

    CHECK_FUNC_DICT = {
        'codCaracter': _check_short,
        'codCategoria': _check_short, 
        'codCorte': _check_short, 
        'codGasto': _check_short, 
        'codOperacion': _check_short,
        'codMotivo': _check_short,
        'codRaza': _check_short, 
        'codTributo': _check_short,
        'tipoComprobante': _check_short,
        'tipoLiquidacion': _check_short, 
        'nroComprobante': _check_int(8),
        'nroPlanta': _check_int(7),
        'puntoVenta': _check_int(5),
        'nroRUCA': _check_long(10),
        'nroTropa': _check_long(10), 
        'descripcion': _check_string(80), 
        'detalle': _check_string(90),
        'iibb': _check_string(15),
        'lugarRealizacion': _check_string(50),
        'nroGuia': _check_string(50),
        'precioRecupero': _check_decimal(13,3), 
        'cuit': _check_cuit(),
        'cuitAutorizado': _check_cuit(),
        'cuitCliente': _check_cuit(), 
        'fechaComprobante': _check_date(),
        'fechaFaena': _check_date(),
        'fechaInicioActividades': _check_date(),
        'fechaOperacion': _check_date(),
        'fechaRecepcion': _check_date(),
        'cantidad': _check_quantity(), 
        'cantidadCabezas': _check_quantity(), 
        'cantidadKilovivo': _check_quantity(), 
        'baseImponible': _check_amount(), 
        'importe': _check_amount(), 
        'precioUnitario': _check_amount(), 
        'alicuota': _check_decimal(intt = 2, comma = 3, signed = True), 
        'nroDTE': _check_regex("\d{1,9}[-]\d{1}"),
        'nroRenspa': _check_regex("(0[0-9]|1[0-9]|2[0-3])[.]\d{3}[.]\d{1}.\d{5}[/]\w{2}"),
        'alicuotaIVA': _check_alicuotaIVA, 
        'frigorifico': _no_check,
        'operador': _no_check,
        'tipoIVANulo': _no_check,
        'raza': _no_check,
    }

    def _check(self,name,value):
        if name in self.CHECK_FUNC_DICT:
            return self.CHECK_FUNC_DICT[name](value)
        else:
            return False

    def _get_puntoVenta(self):
        if hasattr(self,'puntoVenta'):
            return self.puntoVenta
        return None

    def _get_tipoComprobante(self):
        if hasattr(self,'tipoComprobante'):
            return self.tipoComprobante
        return None

    def _get_nroComprobante(self):
        if hasattr(self,'nroComprobante'):
            return self.nroComprobante
        return None

    def _get_codOperacion(self):
        if hasattr(self,'codOperacion'):
            return self.codOperacion
        return None

    def _get_emisorSolicitud(self):
        if hasattr(self,'emisorSolicitud'):
            return self.emisorSolicitud
        return None

    def _get_receptorSolicitud(self):
        if hasattr(self,'receptorSolicitud'):
            return self.receptorSolicitud
        return None

    def _get_datosLiquidacionSolicitud(self):
        if hasattr(self,'datosLiquidacionSolicitud'):
            return self.datosLiquidacionSolicitud
        return None

    def _get_datosAdicionales(self):
        if hasattr(self,'datosAdicionales'):
            return self.datosAdicionales
        return None

    def _get_itemsDetalleLiquidacion(self):
        if hasattr(self,'itemsDetalleLiquidacion'):
            return self.itemsDetalleLiquidacion
        return []

    def _get_dte(self):
        if hasattr(self,'DTE'):
            return self.DTE
        return []

    def _get_guia(self):
        if hasattr(self,'guias'):
            return self.guias
        return []

    def _get_gasto(self):
        if hasattr(self,'gastos'):
            return self.gastos
        return []

    def _get_tributo(self):
        if hasattr(self,'tributos'):
            return self.tributos
        return []


CERT = "/home/work/raf/app/rafaela_addons/l10n_ar_wslsp/a.crt"        # El certificado X.509 obtenido de Seg. Inf.
PRIVATEKEY = "/home/work/raf/app/rafaela_addons/l10n_ar_wslsp/a.key"  # La clave privada del certificado CERT
WSAAURL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl" # homologacion (pruebas)

PRIVATEKEY_C = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAz1tZBDpvrok4m5Dnfql3ItZRWbK93ilQNdXsX2SgQ7aDDIws
lb4oauOhrDld0fbTSDWWN/q4SkvBWNbcvFqGQuY2LdjklAiZhk/7FJwfXs++lTaM
94fz6dFDYsFQyYqShexeI1zE8Y6uKLgZiOqq4s74e3IuqxQqr16xUk0vsBvTKRFO
G4LyQGqnMRQ9/wGpUIwUndTTmEuGOFFJnZb5OX38g1egXMhJD+Ur+qVdKfhHERWV
NfgzQIcZLx6vDLVIV3fCb+4qGoPHNEdRxHfBxZmyUstAmEmH3mSwR+Oi0P/z3PSO
UnNFwQfdKMfYC7YFfF7RjHk632LsG0lBRo/kPwIDAQABAoIBABzOA7+inoEQbtyt
dHsT74jXXNWpDtcdxha0cPGPePPvFqVXk5n5oIO4u2zBS1cvgoo1Z3i/S3qGq4U7
084WhTAl6sDTsG0gBLOzyJ1EUtdI5KC1wz9fk3KXr1S4phBZP6F7BFjFOlaUC318
lY9/id2YAsyjP/hkBMn3zYoxTr6X3tWE3GNmAVJArhEqxg5Rkc4Ux0VvIqr9riSP
GcPDgurj6vRWpZPzVzE1bK1xS/y23IFRyW+BE4ssJuD0xdKIIceUDh2VrwbiNS59
lr3QTXnHYvj/JydGaqRx+MpZyg9C/5URoKy3ZPWkllmh6PxZtvcv1E8vrTyeG4wS
dpG4VgECgYEA8lcnlpy8vIe2PcDZQpU19WOdQI4ez07LfN1eEM3F1oxKCox01NIK
QQfsDpP+dIYUiKm95XHGkvTNxJSzjJYz4574cu1rCdn2OMYWfBntwjyjjU22oyfV
YSrQ0/DC1w8NxwN7j1DFLzG5Oi8tQQ4V4V81SnkjgIxdpi4tZy8V7lECgYEA2wtl
1sG+bbpytzikgiGYaMzN1ZLnuqqr3wAlNZT0fZqQdnTQ+Dw08duG5YgAoEKg5cQS
jC/gjmeghxMeAlBSCAwEUxAgsMU+CFZEe9AiM3D6vC32d3dFTnAvm6gKLSJPVuoV
2pw5EFgmQdgT/hHLsHYNwn3aGkKBOCSBAgQpNY8CgYBDb6dPjQwkNmurIYgTtCvQ
vkibFzFRpO6RL5SmfmxoOJ+98bntIwnBcO/qWpp7WHhMU1fJinCkokTESFDydTW5
SJqAeLrJggK3Z8AIBrsXywIEJzUEj+gb4us7nwrJB6Jg2AJBLkvAx0hw/YHNUZsb
HQBaWf1cHzNMNBtkVED5EQKBgDeb9yjEWxIEaac2TB11ZfoFNKRp/UaYmbWtlcS6
oi9ZFB/enEbJEi/sqZyQIIiPIcXzNzo71WiRymFAazfvKEQ+uMJVr9bw3ETFkfFU
77nbjuxDRvUhZIj7VjrQOHUo5reMCixLyPjrSBsjPkAcSHfuIKQlyz8rbx7PtajL
YaLlAoGAPNOwZRsekbJGWSqKKukynGsVfYB4QlH7fPORc1vZEQZkejLplWrwXEg6
zvf5o8MDyochI5ABHWJEOdObsWGzob4U6dL8A7CvDl02J8Fy2MgHE/ZgcfZrObUS
iIIiQd8sF+O+VKq8PYvysiEp3Ky8l4tVMK+4wy5IHr9UsjmD0ds=
-----END RSA PRIVATE KEY-----"""
CERT_C = """-----BEGIN CERTIFICATE-----
MIIDSTCCAjGgAwIBAgIIV03yVsvVZdUwDQYJKoZIhvcNAQENBQAwODEaMBgGA1UEAwwRQ29tcHV0
YWRvcmVzIFRlc3QxDTALBgNVBAoMBEFGSVAxCzAJBgNVBAYTAkFSMB4XDTE3MDkxNDEzMzYyNloX
DTE5MDkxNDEzMzYyNlowLzESMBAGA1UEAwwJZW1pcHN0ZXN0MRkwFwYDVQQFExBDVUlUIDIwMjky
NjUyNzEzMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAz1tZBDpvrok4m5Dnfql3ItZR
WbK93ilQNdXsX2SgQ7aDDIwslb4oauOhrDld0fbTSDWWN/q4SkvBWNbcvFqGQuY2LdjklAiZhk/7
FJwfXs++lTaM94fz6dFDYsFQyYqShexeI1zE8Y6uKLgZiOqq4s74e3IuqxQqr16xUk0vsBvTKRFO
G4LyQGqnMRQ9/wGpUIwUndTTmEuGOFFJnZb5OX38g1egXMhJD+Ur+qVdKfhHERWVNfgzQIcZLx6v
DLVIV3fCb+4qGoPHNEdRxHfBxZmyUstAmEmH3mSwR+Oi0P/z3PSOUnNFwQfdKMfYC7YFfF7RjHk6
32LsG0lBRo/kPwIDAQABo2AwXjAMBgNVHRMBAf8EAjAAMB8GA1UdIwQYMBaAFLOy0//96bre3o2v
ESGc1iB98k9vMB0GA1UdDgQWBBT04s6q7sB1R1SAQS01NwOgP2ePvzAOBgNVHQ8BAf8EBAMCBeAw
DQYJKoZIhvcNAQENBQADggEBAJwRR+AGB5CcOMA8q3iZw6y4N2JfisXRXhqUK+a26tPjLjWQdUZI
GF/bVm15vxnhT9+rIo3uLdLJdpti6fC0ilG9tFEGxjV+nA2cJqPFdTD0CYlZup/r111uzXD7GVZV
D41g7DakKX1DzCpc7R25X+7/kTBUUn2mVny5M3CPradCj/ulx9e622ZjKZhqzbVFNHew/fE2Z/rA
ouUh0cHuKb9WTYJPIZyrGMy6a53YhXue/14nXj1gn9zVPXEHkiR7eyTFju7XJbOxrkW7L6agiXgH
WYzDQm80GMxev/p8MBAhWmTJLNSTQQ4HTqQVogiUzE/04bDqWeBUucoWkvQbSe4=
-----END CERTIFICATE-----"""
CUIT = 20292652713

if __name__ == "__main__":

    import argparse
    import ipdb
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--mode')
    args = arg_parser.parse_args()

    #WSAA part

    if args.mode == 'A':
        service = "wsfe"
    else:
        service = "wslsp" 

    wsaa = WSAA(CERT, PRIVATEKEY, WSAAURL, service)
    token = None
    sign = None
    expiration_time = None
    try:
        # Se puede llamar a get_token_and_sign o pasarle un TA
        # anterior a wsaa.parse_ta
        wsaa.get_token_and_sign(CERT_C, PRIVATEKEY_C)
        token = wsaa.token
        expiration_time = wsaa.expiration_time
        sign = wsaa.sign
    except Exception, e:
        print e
    
    # Vemos si ya expiro
    if datetime.now() > expiration_time:
        print "Certificado expirado"
    #print 'Token: ', token
    #print 'Sign: ', sign
    #print 'Expiration Time: ', expiration_time.strftime("%d/%m/%Y %H:%M:%S")
    

    if args.mode == 'T':
        wslsp = WSLSP(cuit = CUIT, token = wsaa.token, sign = wsaa.sign)
        #wslsp.print_services()
        wslsp.dummy()
        ipdb.set_trace()
    if args.mode == 'TL':
        wslsp = WSLSP(cuit = CUIT, token = wsaa.token, sign = wsaa.sign)
        #wslsp.print_services()
        wslsp.dummy()
        ipdb.set_trace()

        wslsp.set_codOperacion(4)
        wslsp.set_emisorSolicitud({"puntoVenta" : 3000, "tipoComprobante" : 183, "codCaracter" : 1, "fechaInicioActividades":"2018-03-20","nroRenspa":"21.123.4.56789/A4"})
        wslsp.set_receptorSolicitud({"codCaracter":1, "operador":{"cuit":30160000011,"nroRenspa":"21.123.4.56789/A4"}})
        #TODO cod motivo checks
        wslsp.set_datosLiquidacionSolicitud({"fechaComprobante":"2018-04-06", "fechaOperacion" : "2018-04-06", "codMotivo":2})
        wslsp.add_itemDetalleLiquidacion({"cuitCliente" : 20160000199, "codCategoria" : 1202, "tipoLiquidacion" : 2, "cantidad" : 15, "cantidadCabezas" : 15, "precioUnitario" : 50.200, "alicuotaIVA":10.5, "raza" : {"codRaza" : 22}})
        wslsp.add_Gasto({"codGasto" : 4, "importe" : 415.15, "alicuotaIVA":10.5})
        wslsp.add_DTE({"nroDTE" : "123456789-2"})
        wslsp.add_Guia({"nroGuia" : "125354"})
        wslsp.add_Tributo({"codTributo" : 1, "importe" : 12.53})

        print 'generarLiquidacion ' + str(len(wslsp.generarLiquidacion()))
    elif args.mode == 'A':

        wsfe = WSFEv1(cuit = CUIT, token = wsaa.token, sign = wsaa.sign)
        #wsfe.print_services()
        ipdb.set_trace()
        wsfe.fe_param_get_tipos_cbte()
        
    else:

        #WSLSP part

        wslsp = WSLSP(cuit = CUIT, token = wsaa.token, sign = wsaa.sign)
        #wslsp.print_services()
        wslsp.dummy()
        print 'dummy'
        print 'consultarCaracteresParticipante ' + str(len(wslsp.consultarCaracteresParticipante()))
        print 'consultarCategorias ' + str(len(wslsp.consultarCategorias()))
        print 'consultarCortes ' + str(len(wslsp.consultarCortes()))
        print 'consultarGastos ' + str(len(wslsp.consultarGastos()))
        print 'consultarMotivos ' + str(len(wslsp.consultarMotivos()))
        print 'consultarOperaciones ' + str(len(wslsp.consultarOperaciones()))
        print 'consultarProvincias ' + str(len(wslsp.consultarProvincias()))
        print 'consultarPuntosVenta ' + str(len(wslsp.consultarPuntosVenta()))
        print 'consultarRazas ' + str(len(wslsp.consultarRazas()))
        print 'consultarTiposComprobante ' + str(len(wslsp.consultarTiposComprobante()))
        print 'consultarTiposLiquidacion ' + str(len(wslsp.consultarTiposLiquidacion()))
        print 'consultarTributos ' + str(len(wslsp.consultarTributos()))
        print 'consultarLocalidadesPorProvincia() ' + str(len(wslsp.consultarLocalidadesPorProvincia()))
        print 'consultarLocalidadesPorProvincia(2) ' + str(len(wslsp.consultarLocalidadesPorProvincia(2)))
        print 'consultarUltimoNroComprobantePorPtoVta ' + str(len(wslsp.consultarUltimoNroComprobantePorPtoVta()))
        print 'consultarLiquidacionPorNroComprobante ' + str(len(wslsp.consultarLiquidacionPorNroComprobante()))
        #THIS
        wslsp.set_codOperacion(4)
        wslsp.set_emisorSolicitud({"puntoVenta" : 3000, "tipoComprobante" : 183, "codCaracter" : 1, "fechaInicioActividades":"2018-03-20","nroRenspa":"21.123.4.56789/A4"})
        wslsp.set_receptorSolicitud({"codCaracter":1, "operador":{"cuit":30160000011,"nroRenspa":"21.123.4.56789/A4"}})
        #TODO cod motivo checks
        wslsp.set_datosLiquidacionSolicitud({"fechaComprobante":"2018-04-06", "fechaOperacion" : "2018-04-06", "codMotivo":2})
        wslsp.add_itemDetalleLiquidacion({"cuitCliente" : 20160000199, "codCategoria" : 1202, "tipoLiquidacion" : 2, "cantidad" : 15, "cantidadCabezas" : 15, "precioUnitario" : 50.200, "alicuotaIVA":10.5, "raza" : {"codRaza" : 22}})
        wslsp.add_Gasto({"codGasto" : 4, "importe" : 415.15, "alicuotaIVA":10.5})
        wslsp.add_Gasto({"codGasto" : 4, "baseImponible" : 415.15, "alicuota" : 20.15, "alicuotaIVA":10.5})
        wslsp.add_DTE({"nroDTE" : "123456789-2"})
        wslsp.add_Guia({"nroGuia" : "125354"})
        wslsp.add_Tributo({"codTributo" : 1, "importe" : 12.53})

        print 'generarLiquidacion ' + str(len(wslsp.generarLiquidacion()))

        #print 'generarAjuste ' + str(len(wslsp.generarAjuste()))