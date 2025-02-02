#This file is part asterisk module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
# https://help.yeastar.com/en/p-series-cloud-edition/index.html
import requests
import urllib.parse
from lxml import etree
import html

from trytond.config import config

URL = config.get('algevasa', 'url')

def xml_to_dict(element):
    """Convert an XML element to dictionary without namespaces."""
    result = {}

    for child in element:
        # Delete namespace from tag
        tag = etree.QName(child).localname
        child_dict = (xml_to_dict(child)
            if len(child) > 0 else (child.text or ""))

        # If key exist convert to a list
        if tag in result:
            if isinstance(result[tag], list):
                result[tag].append(child_dict)
            else:
                result[tag] = [result[tag], child_dict]
        else:
            result[tag] = child_dict

    return result


def parse_xml(xml_data):
    """From an XML, detect if a SOAP and convert to dict."""
    # If necessary convert from string to bytes
    if isinstance(xml_data, str):
        xml_data = xml_data.encode("utf-8")

    root = etree.fromstring(xml_data)

    # Define the possible namespaces obtained in the response from SOAP.
    namespaces = {
        'soap': "http://www.w3.org/2003/05/soap-envelope",
        'ns': "http://webservice.algevasa.com/"
    }

    # If is a SOAP message, get the WSAGVResult
    wsagv_result = root.find('.//ns:WSAGVResult', namespaces)
    if wsagv_result is not None:
        # As the WSAGVResult value is an HTML escape, need to unscape.
        extracted_xml = html.unescape(wsagv_result.text)
        root = etree.fromstring(extracted_xml)

    return xml_to_dict(root)


def _requests(type_, data=None, headers=None, verify=True):
    if not URL:
        return None

    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        }

    encoded_data = urllib.parse.quote(data)
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
    <soap12:Body>
        <WSAGV xmlns="http://webservice.algevasa.com/">
        <_xmldata>{encoded_data}</_xmldata>
        </WSAGV>
    </soap12:Body>
    </soap12:Envelope>
    """

    headers["Content-Length"] = str(len(soap_body))

    if type_ == 'POST':
        response = requests.post(URL, data=soap_body, headers=headers,
            verify=verify)
    else:
        return {
            'code': 400,
            }

    res = parse_xml(response.content)
    result = {
        'code': response.status_code,
        'text': response.text,
        'answer': res.get('Body', {}).get(
            'respuesta', 'FALSE'),
        'message': res.get('Body', {}).get('Mensaje', ''),
    }
    return result
