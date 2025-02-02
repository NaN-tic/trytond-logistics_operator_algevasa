import requests
import json
import base64

URL = 'http://localhost:8507/'
DBNAME = '<DB_NAME>'
USERNAME = '<USER>'
PASSWORD = '<PASSWORD>'
COMPANY_ID = 3

def login(data):
    headers = {'Content-type': 'application/json'}
    return requests.post('%s%s/' % (URL, DBNAME), data=json.dumps(data), headers=headers)

def call(data):
    headers = {
        'Content-type': 'application/json',
        'Authorization': 'Basic ' + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode(),
        }
    return requests.post('%s%s/' % (URL, DBNAME), data=json.dumps(data), headers=headers)

# Hacemos login, para obtener el usaurio y la sesión
data = {'method':'common.db.login', 'params': [USERNAME, {'password': PASSWORD}]}
result = login(data)

# Definimos la compañía al usuario
data = {'method': 'model.res.user.set_preferences', 'params': [{'company': COMPANY_ID,}, {}]}
result = call(data)

# Obtenemos el context que necesitamos para el resto de llamadas
data = {'method': 'model.res.user.get_preferences', 'params': [True, {}]}
response = call(data)
if response.status_code == 200:
    context = json.loads(response.text)

    xml_file = """<BODY>
    <OPERACION>ALBARANVENTA</OPERACION>
    <CLAVE>3X546AC3X69F8B3X8B6A43X1B69B3X1B80B</CLAVE>
    <PROPIETARIO>OPENET</PROPIETARIO>
    <IDPED></IDPED>
    <NUMDOC>093924</NUMDOC>
    <NUMALB>A34561</NUMALB>
    <FECDOC>30/01/2025</FECDOC>
    <TEXTOBS>aaaaaa</TEXTOBS>
    <ITEMS>
        <ITEM>
        <LINORI></LINORI>
        <LINDOC></LINDOC>
        <CODART>0020</CODART>
        <NUMLOT></NUMLOT>
        <CADUCIDAD></CADUCIDAD>
        <CANTIDAD_PED>100</CANTIDAD_PED>
        <CANTIDAD_SER>100</CANTIDAD_SER>
        <NBULTOS></NBULTOS>
        <NPALETS></NPALETS>
        <TEXTOBS></TEXTOBS>
        </ITEM>
        <ITEM>
        <LINORI></LINORI>
        <LINDOC></LINDOC>
        <CODART>0848C</CODART>
        <NUMLOT></NUMLOT>
        <CADUCIDAD></CADUCIDAD>
        <CANTIDAD_PED>1000</CANTIDAD_PED>
        <CANTIDAD_SER>900</CANTIDAD_SER>
        <NBULTOS></NBULTOS>
        <NPALETS></NPALETS>
        <TEXTOBS></TEXTOBS>
        </ITEM>
    </ITEMS>
    </BODY>"""

    # Para escribir en un registro existente (El '1' es el ID del registro)
    data = {'method': 'model.stock.shipment.out.algevasa_response', 'params': [{'data': xml_file}, context]}
    result = call(data)
