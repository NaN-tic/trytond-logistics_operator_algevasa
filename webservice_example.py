import requests
import json
import base64

URL = 'http://localhost:8507/'
DBNAME = 'openetics_241016'
USERNAME = 'algevasa'
PASSWORD = 'Mastercow00'
CREDENTIALS = (USERNAME, PASSWORD)

def call(data):
    headers = {
        'Content-type': 'application/json',
        'Authorization': 'Basic ' + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode(),
        }
    # TODO catch errors
    return requests.post('%s%s/' % (URL, DBNAME), data=json.dumps(data), headers=headers)

data = {'method': 'model.res.user.get_preferences', 'params': [True, {}]}
result = call(data)
context = json.loads(result.text)

xml_file = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><WSAGVResponse xmlns="http://webservice.algevasa.com/"><WSAGVResult>&lt;Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/"&gt;&lt;Body&gt;&lt;respuesta&gt;FALSE&lt;/respuesta&gt;&lt;Mensaje&gt;Pedido con artículo incorrecto 2330\r\n\r\n Pedido 091863&lt;/Mensaje&gt;&lt;/Body&gt;&lt;/Envelope&gt;</WSAGVResult></WSAGVResponse></soap:Body></soap:Envelope>"""
data = {'method': 'model.stock.shipment.out.algevasa_response', 'params': [xml_file, context] }
result = call(data)
print(result.status_code)
print(result.text)
