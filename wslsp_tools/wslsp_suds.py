from suds.client import Client
from wsaa_suds import WSAA
from wsfe_suds import WSFEv1
from datetime import datetime
import urllib2

import logging

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


class Error:

    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

    def __str__(self):
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

    def consultarUltimoNroComprobantePorPtoVta(self, puntoVenta = 1, tipoComprobante = 1):

        # Llamamos a la funcion
        arg = self.client.factory.create('ns0:ConsultarUltNroComprobantePorPtoVtaSolicitud')
        #TODO THROW ERROR
        arg.puntoVenta = puntoVenta if 1 <= puntoVenta <= 99999 else 1
        arg.tipoComprobante = tipoComprobante if 1 <= tipoComprobante <= 999 else 1
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

    def consultarLiquidacionPorNroComprobante(self, puntoVenta = 1, tipoComprobante = 1, nroComprobante = 1):

        # Llamamos a la funcion
        arg = self.client.factory.create('ns0:ConsultarLiquidacionPorNroComprobanteSolicitud')
        #TODO THROW ERROR
        arg.puntoVenta = puntoVenta if 1 <= puntoVenta <= 99999 else 1
        arg.tipoComprobante = tipoComprobante if 1 <= tipoComprobante <= 999 else 1
        arg.nroComprobante = nroComprobante if 1 <= nroComprobante <= 99999999 else 1
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

    def generarAjuste (self, tipoAjuste = 'C', fechaComprobante = '2018-03-26'):
        
        # Llamamos a la funcion
        arg = self.client.factory.create('ns0:GenerarAjusteSolicitud')
        #TODO WIP generar ajuste
        arg.tipoAjuste = 'C' if tipoAjuste == 'C' else 'D'
        arg.fechaComprobante = fechaComprobante
        arg.tipoComprobante = tipoComprobante if 1 <= tipoComprobante <= 999 else 1
        arg.nroComprobante = nroComprobante if 1 <= nroComprobante <= 99999999 else 1
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
        # generarLiquidacion(Auth auth, GenerarLiquidacionSolicitud solicitud, )

    def fe_CAE_solicitar(self, pto_vta, cbte_tipo, detalles):

        argcaereq = self.client.factory.create('ns0:FECAERequest')
        # print argcaereq

        # FECAECabRequest
        argcaereq.FeCabReq.CantReg = len(detalles)
        argcaereq.FeCabReq.PtoVta = pto_vta
        argcaereq.FeCabReq.CbteTipo = cbte_tipo

        for detalle in detalles:
            arrayIva = []
            arrayTributos = []

            argdetreq = self.client.factory.create('ns0:FECAEDetRequest')

            for k, v in detalle.iteritems():
                if isinstance(v, list):
                    if k == 'Iva':
                        for iva in v:
                            argiva = self.client.factory.create('ns0:AlicIva')
                            for k, v in iva.iteritems():
                                if k in argiva:
                                    argiva[k] = v
                                else:
                                    argiva[k] = None

                            arrayIva.append(argiva)
                            continue
                    elif k == 'Tributos':
                        for trib in v:
                            argtrib = self.client.factory.create('ns0:Tributo')
                            for k, v in trib.iteritems():
                                if k in argtrib:
                                    argtrib[k] = v
                                else:
                                    argtrib[k] = None

                            arrayTributos.append(argtrib)
                            continue
                else:
                    if k in argdetreq:
                        argdetreq[k] = v
                    # else:
                        #argdetreq[k] = None

            if len(arrayIva):
                argdetreq.Iva.AlicIva.append(arrayIva)
            if len(arrayTributos):
                argdetreq.Tributos.Tributo.append(arrayTributos)
            argcaereq.FeDetReq.FECAEDetRequest.append(argdetreq)

        result = self.client.service.FECAESolicitar(self.argauth, argcaereq)

        errores = []
        comprobantes = []

        if 'Errors' in result:
            for e in result.Errors.Err:
                error = '%s (Err. %s)' % (e.Msg, e.Code)
                errores.append(error)

        for det_response in result.FeDetResp.FECAEDetResponse:
            observaciones = []
            comp = {}

            if 'Observaciones' in det_response:
                for o in det_response.Observaciones.Obs:
                    observacion = '%s (Err. %s)' % (o.Msg, o.Code)
                    observaciones.append(observacion)

            comp['Concepto'] = det_response.Concepto
            comp['DocTipo'] = det_response.DocTipo
            comp['DocNro'] = det_response.DocNro
            comp['CbteDesde'] = det_response.CbteDesde
            comp['CbteHasta'] = det_response.CbteHasta
            comp['CbteFch'] = det_response.CbteFch
            comp['Resultado'] = det_response.Resultado
            comp['CAE'] = det_response.CAE
            comp['CAEFchVto'] = det_response.CAEFchVto
            comp['Observaciones'] = observaciones
            comprobantes.append(comp)

        res = {'Comprobantes': comprobantes, 'Errores': errores, 'PtoVta': pto_vta, 'Resultado': result.FeCabResp.Resultado, 'Reproceso': result.FeCabResp.Reproceso}
        return res

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
    

    if args.mode == 'A':

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
        ipdb.set_trace()
        print 'generarAjuste ' + str(len(wslsp.generarAjuste()))
        

#    wsaa = WSAA()
#    wsfe = WSFE(wsaa, CUIT)
#    wsfe.print_services()
#    #wsfe.fe_recupera_last_CMP_request(1, 1)
#    #wsfe.fe_ult_nro_request()
#    #wsfe.fe_dummy()
#    wsfe.fe_aut_request([])
# #    #wsfe.fe_recuperar_qty()
#             FECAEAConsultar(FEAuthRequest Auth, xs:int Periodo, xs:short Orden, )
#             FECAEARegInformativo(FEAuthRequest Auth, FECAEARequest FeCAEARegInfReq, )
#             FECAEASinMovimientoConsultar(FEAuthRequest Auth, xs:string CAEA, xs:int PtoVta, )
#             FECAEASinMovimientoInformar(FEAuthRequest Auth, xs:int PtoVta, xs:string CAEA, )
#             FECAEASolicitar(FEAuthRequest Auth, xs:int Periodo, xs:short Orden, )
#             FECAESolicitar(FEAuthRequest Auth, FECAERequest FeCAEReq, )
#             FECompConsultar(FEAuthRequest Auth, FECompConsultaReq FeCompConsReq, )
#             FECompTotXRequest(FEAuthRequest Auth, )
#             FECompUltimoAutorizado(FEAuthRequest Auth, xs:int PtoVta, xs:int CbteTipo, )
#             FEDummy()
#             FEParamGetCotizacion(FEAuthRequest Auth, xs:string MonId, )
#             FEParamGetPtosVenta(FEAuthRequest Auth, )
#             FEParamGetTiposCbte(FEAuthRequest Auth, )
#             FEParamGetTiposConcepto(FEAuthRequest Auth, )
#             FEParamGetTiposDoc(FEAuthRequest Auth, )
#             FEParamGetTiposIva(FEAuthRequest Auth, )
#             FEParamGetTiposMonedas(FEAuthRequest Auth, )
#             FEParamGetTiposOpcional(FEAuthRequest Auth, )
#             FEParamGetTiposPaises(FEAuthRequest Auth, )
#             FEParamGetTiposTributos(FEAuthRequest Auth, )
