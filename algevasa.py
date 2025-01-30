#This file is part asterisk module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
# https://help.yeastar.com/en/p-series-cloud-edition/index.html
import requests
import urllib.parse
from lxml import etree

from trytond.config import config

URL = config.get('algevasa', 'url')


def _process_response(response):
    root = etree.fromstring(response.content)
    namespaces = {
        "soap": "http://www.w3.org/2003/05/soap-envelope",
        "ws": "http://webservice.algevasa.com/",
    }

    wsagv_result = root.xpath("//ws:WSAGVResult", namespaces=namespaces)[0].text
    wsagv_root = etree.fromstring(wsagv_result)
    inner_ns = {"env": "http://schemas.xmlsoap.org/soap/envelope/"}

    answer = wsagv_root.xpath("//env:respuesta", namespaces=inner_ns)[0].text
    message = wsagv_root.xpath("//env:Mensaje", namespaces=inner_ns)[0].text

    return {
        'answer': answer,
        'message': message,
        'text': response.text,
        }


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

    result = {
        'code': response.status_code,
    }
    result.update(_process_response(response))
    return result
