#!/usr/bin/env python
import argparse
import socket
import ssl
import struct
from BeautifulSoup import BeautifulStoneSoup
from xml import contact as contact_xml, sidn


class EPP:

    def __init__(self, **kwargs):
        self.config = kwargs
        self.connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(2)
        self.socket.connect((self.config['host'], self.config['port']))
        self.ssl = ssl.wrap_socket(self.socket)
        self.format_32 = self.format_32()
        self.login()

    def __del__(self):
        self.logout()
        self.socket.close()

    # http://www.bortzmeyer.org/4934.html
    def format_32(self):
        # Get the size of C integers. We need 32 bits unsigned.
        format_32 = ">I"
        if struct.calcsize(format_32) < 4:
            format_32 = ">L"              
            if struct.calcsize(format_32) != 4:
                raise Exception("Cannot find a 32 bits integer")
        elif struct.calcsize(format_32) > 4:
            format_32 = ">H"                
            if struct.calcsize(format_32) != 4:
                raise Exception("Cannot find a 32 bits integer")
        else:
            pass
        return format_32

    def int_from_net(self, data):
        return struct.unpack(self.format_32, data)[0]

    def int_to_net(self, value):
        return struct.pack(self.format_32, value)

    def cmd(self, xml, silent=True):
        self.write(xml)
        #soup = BeautifulStoneSoup(self.read())
        xml = self.read()
        soup = BeautifulStoneSoup(xml)
        response = soup.find('response')
        result = soup.find('result')
        try:
            code = int(result.get('code'))
        except AttributeError:
            print "\nERROR: Could not get result code, exiting."
            print xml
            exit(1)
        if not silent:
            print("- [%d] %s" % (code, result.msg.text))
        if code == 2308:
            print("Something wrong!")
            return False
        if code == 2502:
            print("Limit exceeded.")
            return False
        return response

    def read(self):
        length = self.ssl.read(4)
        if length:
            i = self.int_from_net(length)-4
            print "Length: %d" % i
            return self.ssl.read(i)

    def write(self, xml):
        epp_as_string = xml #ElementTree.tostring(xml, encoding="UTF-8")
        # +4 for the length field itself (section 4 mandates that)
        # +2 for the CRLF at the end
        length = self.int_to_net(len(epp_as_string) + 4 + 2)
        self.ssl.send(length)
        return self.ssl.send(epp_as_string + "\r\n")

    def login(self):
        """ Read greeting """
        greeting = self.read()
        soup = BeautifulStoneSoup(greeting)
        svid = soup.find('svid')
        version = soup.find('version')
        print("Connected to %s (v%s)\n" % (svid.text, version.text))

        """ Login """
        xml = sidn.login % self.config
        if not self.cmd(xml, silent=True):
            exit(1)

    def logout(self):
        xml = sidn.logout
        print xml
        return self.cmd(xml, silent=False)

    def poll(self):
        xml = sidn.poll
        return self.cmd(xml)


class EPPObject:
    def __init__(self, epp):
        self.epp = epp

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            pass


class Domain(EPPObject):
    def __init__(self, epp, domain):
        self.domain = domain
        self.epp = epp
        self.roid = ""
        self.status = ""
        #self.registrant = Contact()
        #self.admin = Contact()
        #self.tech = Contact()
        #self.ns = Nameserver(epp)

    def available(self):
        xml = sidn.available % self.domain
        res = self.epp.cmd(xml)
        if not res:
            # exception would be more fitting
            return False
        return res.resdata.find('domain:name').get('avail') == 'true'

    def create(self, contacts, ns):
        xml = sidn.create % dict({
            'domain': self.domain,
            'ns': ns[0],
            'registrant': contacts['registrant'],
            'admin': contacts['admin'],
            'tech': contacts['tech'],
        })
        res = self.epp.cmd(xml)

    def delete(self, undo=False):
        if undo:
            xml = sidn.canceldelete % self.domain
        else:
            xml = sidn.delete % self.domain
        return self.epp.cmd(xml)

    def info(self):
        xml = sidn.info % self.domain
        res = self.epp.cmd(xml).resdata
        self.roid = res.find('domain:roid').text
        self.status = res.find('domain:status').get('s')
        self.registrant = Contact(self.epp, res.find('domain:registrant').text)
        self.admin = Contact(self.epp, res.find('domain:contact', type='admin').text)
        self.tech = Contact(self.epp, res.find('domain:contact', type='tech').text)
        return self

    def token(self):
        xml = sidn.info % self.domain
        res = self.epp.cmd(xml)
        return res.resdata.find('domain:pw')

    def transfer(self, token):
        xml = sidn.transfer % dict({
            'domain': self.domain,
            'token': token,
        })
        return self.epp.cmd(xml)

class Nameserver(EPPObject):
    def __init__(self, epp, nameserver=False):
        self.nameserver = nameserver
        self.epp = epp

    def __unicode__(self):
        return self.nameserver

    def get_ip(self):
        xml = sidn.nameserver % self.nameserver
        res = self.epp.cmd(xml)
        return res.resdata.find('host:addr').text


class Contact(EPPObject):
    def __init__(self, epp, handle=False, **kwargs):
        self.epp = epp
        self.handle = handle
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __unicode__(self):
        return "[%(handle)s] %(name)s, %(street)s, %(pc)s %(city)s (%(cc)s)" % self

    def available(self):
        xml = contact_xml.available % self.handle
        res = self.epp.cmd(xml, silent=True)
        return res.resdata.find('contact:id').get('avail') == 'true'

    def info(self):
        xml = contact_xml.info % self.handle
        res = self.epp.cmd(xml).resdata
        self.roid = res.find('contact:roid').text
        self.status = res.find('contact:status').get('s')
        self.name = res.find('contact:name').text
        self.street = res.find('contact:street').text
        self.city = res.find('contact:city').text
        self.pc = res.find('contact:pc').text
        self.cc = res.find('contact:cc').text
        self.voice = res.find('contact:voice').text
        self.email = res.find('contact:email').text
        return self

    def update(self):
        xml = contact_xml.update % self
        return self.epp.cmd(xml)
