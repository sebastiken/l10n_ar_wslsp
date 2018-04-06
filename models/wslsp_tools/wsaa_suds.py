from lxml import etree
from datetime import datetime
import time
import sys
import email
import urllib2
from M2Crypto import BIO, SMIME
from suds.client import Client
from xml.sax import SAXParseException
import logging
import pytz
from tzlocal import get_localzone

## Configuracion del logger
logger = logging.getLogger('afipws')
logger.setLevel(logging.DEBUG)
#streamH = logging.StreamHandler(sys.stdout)
#streamH.setLevel(logging.DEBUG)
#streamH.setFormatter(formatter)
#logger.addHandler(streamH)


class WSAA:
    def __init__(self, cert, private_key, wsaaurl, service, tz = False):
        """Init."""
        self.token = None
        self.sign = None
        self.wsaaurl = wsaaurl
        self.service = service
        self.expiration_time = None
        self.ta = None
        self.connected = True
        self.timezone = tz if tz else get_localzone() 

        try:
            self._create_client()
        except urllib2.URLError, e:
            logger.error("No hay conexion disponible")
            self.connected = False
            raise Exception, 'No se puede conectar con AFIP: %s' % str(e)
        except SAXParseException, e:
            raise Exception, 'WSAA URL malformada: %s' % e.getMessage()
        except Exception, e:
            raise Exception, 'Unknown Error: %s' % e

    def _create_client(self):
        # Creamos el cliente contra la URL
        self.client = Client(self.wsaaurl)

    def _create_tra(self):
        """Funcion para crear el TRA."""
        # Creamos el root
        logger.debug("Creando TRA")
        root = etree.Element('loginTicketRequest')
        doc = etree.ElementTree(root)
        root.set('version', '1.0')

        # Creamos los childs de loginTicketRequest
        header = etree.SubElement(root, 'header')

        # UniqueId
        uniqueid = etree.SubElement(header, 'uniqueId')
        timestamp = int(time.mktime(datetime.now().timetuple()))
        uniqueid.text = str(timestamp)

        # generationTime
        tsgen = datetime.fromtimestamp(timestamp-2400)
        tsgen = pytz.utc.localize(tsgen).astimezone(self.timezone)
        gentime = etree.SubElement(header, 'generationTime')
        gentime.text = tsgen.isoformat()

        # expirationTime
        tsexp = datetime.fromtimestamp(timestamp+14400)
        tsexp = pytz.utc.localize(tsexp).astimezone(self.timezone)
        exptime = etree.SubElement(header, 'expirationTime')
        exptime.text = tsexp.isoformat()

        # service
        serv = etree.SubElement(root, 'service')
        serv.text = self.service

#        try:
#            f = open('tra.xml', 'w')
#            doc.write(f, xml_declaration=True, encoding='UTF-8', pretty_print=True)
#        except Exception, e:
#            print 'No se puede grabar el archivo: %s' % e
#            return None

        logger.debug("TRA Creado")
        return etree.tostring(doc)


    def _sign_tra(self, tra, cert, key):
        """Funcion que firma el tra."""

        # Creamos un buffer a partir del TRA
        buf = BIO.MemoryBuffer(tra)
        key_bio = BIO.MemoryBuffer(key.encode('ascii'))
        cert_bio = BIO.MemoryBuffer(cert.encode('ascii'))

        # Firmamos el TRA
        s = SMIME.SMIME()
        s.load_key_bio(key_bio, cert_bio)
        p7 = s.sign(buf, 0)
        out = BIO.MemoryBuffer()
        s.write(out, p7)

        # Extraemos la parte que nos interesa
        msg = email.message_from_string(out.read())
        for part in msg.walk():
            filename = part.get_filename()
            if filename == "smime.p7m":
                logger.debug("TRA Firmado")
                return part.get_payload(decode=False)


    def _call_wsaa(self, cms):
        """ Funcion para llamar al WSAA y loguearse """

        # Si no esta conectado, probamos conectar nuevamente
        if not self.connected:
            try:
                self._create_client()
            except urllib2.URLError, e:
                logger.warning("No hay conexion disponible")
                self.connected = False
                raise Exception, 'No hay conexion: %s' % e

        # Llamamos a loginCms y obtenemos el resultado
        logger.debug("Llamando a loginCms:\n%s", cms)
        try:
            result = self.client.service.loginCms(cms)
        except Exception, e:
            logger.exception("Excepcion al llamar a loginCms")
            raise Exception, 'Exception al autenticar: %s' % e

        self.ta = result
        return result

    def parse_ta(self, ta=None):
        if not ta:
            ta = self.ta
            if not ta:
                return

        # Quitamos la declaracion de XML
        tas = ta.split('\n')
        if tas[0].find("?xml"):
            ta = '\n'.join(tas[1:])

        # Parseamos el resultado
        root = etree.XML(ta)

        # Buscamos el expirationTime
        header = root.find('header')
        exptime = header.find('expirationTime')
        exptime_iso = exptime.text[0:exptime.text.rfind('-')]
        self.expiration_time = datetime.strptime(exptime_iso, '%Y-%m-%dT%H:%M:%S.%f')

         # Si no expiro, obtenemos el token y el sign
        cred = root.find('credentials')
        self.token =  cred.find('token').text
        self.sign =  cred.find('sign').text

        return True

    # TODO: Agregar una flag de force para tomarlo igual
    # TODO: Hacer chequeo de errores
    def get_token_and_sign(self, cert, key, force=True):
        # Primero chequeamos si ya tenemos un token
        if not force:
            if self.ta and self.expiration_time and self.token and self.sign:
                # Si todavia no expiro el que tenemos, lo retornamos
                if datetime.now() < self.expiration_time:
                    return self.token, self.sign

        tra = self._create_tra()
        cms = self._sign_tra(tra, cert, key)
        try:
            self._call_wsaa(cms)
        except Exception, e:
            raise e

        self.parse_ta(self.ta)
        return True

CERT = "/home/skennedy/proyectos/afipws/certs2012/eynes/cert_eynes.crt"        # El certificado X.509 obtenido de Seg. Inf.
PRIVATEKEY = "/home/skennedy/proyectos/afipws/certs2012/eynes/privada_eynes.key"  # La clave privada del certificado CERT
WSAAURL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl" # homologacion (pruebas)
#WSAAURL="https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl"

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
if __name__ == '__main__':
    wsaa = WSAA(CERT, PRIVATEKEY, WSAAURL, "wsfe")
    token = None
    sign = None
    expiration_time = None
    try:
        # Se puede llamar a get_token_and_sign o pasarle un TA
        # anterior a wsaa.parse_ta
        wsaa.get_token_and_sign(CERT_C,PRIVATEKEY_C)
        token = wsaa.token
        expiration_time = wsaa.expiration_time
        sign = wsaa.sign
    except Exception, e:
        print e

    # Vemos si ya expiro
    if datetime.now() > expiration_time:
        print "Certificado expirado"

    print 'Token: ', token
    print 'Sign: ', sign
    print 'Expiration Time: ', expiration_time.strftime("%d/%m/%Y %H:%M:%S")
