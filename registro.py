from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
import re
from gevent.pywsgi import WSGIServer

app = Flask(__name__)

# Configura la conexión a MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client['dbPagos']  # Reemplaza 'tu_base_de_datos' con el nombre de tu base de datos
collection = db['Pagos']  # Reemplaza 'tus_datos' con el nombre de tu colección

# Ruta para almacenar datos
@app.route('/guardar_datos', methods=['POST'])
def guardar_datos():
    data = request.json

    # Asegúrate de que los campos necesarios estén presentes en la solicitud
    required_fields = ['Referencia','Fecha', 'Detalle']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Campos requeridos incompletos'}), 400

    # Inserta los datos en la base de datos
    result = collection.insert_one(data)

    # Retorna la ID del documento recién insertado
    return jsonify({'message': 'Datos almacenados con éxito', 'id': str(result.inserted_id)}), 201

# Ruta para buscar por Referencia
@app.route('/buscar_por_referencia', methods=['POST'])
def buscar_por_referencia():
    data = request.json
    referencia = data.get('Referencia')
    print(referencia)
    if not referencia:
        return jsonify({'error': 'Se requiere el parámetro "referencia"'}), 400

    # Realiza la búsqueda en la base de datos por el campo "Referencia"
    result = list(collection.find({'Referencia': referencia}))
    print(result)
    # Convierte los ObjectId a cadenas antes de serializar a JSON
    for item in result:
        item['_id'] = str(item['_id'])

    return jsonify({'resultados': result})

def extract_numeric_value(monto_with_symbol):
    match = re.search(r'\d+(\.\d+)?', monto_with_symbol)
    return float(match.group()) if match else 0.0
# Ruta para listar registros por rango de fechas y calcular la sumatoria del campo Monto
@app.route('/listar_por_fechas', methods=['GET'])
def listar_por_fechas():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')

    if not fecha_inicio or not fecha_fin:
        return jsonify({'error': 'Se requieren los parámetros "fecha_inicio" y "fecha_fin"'}), 400

    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')

    # Realiza la búsqueda en la base de datos por el rango de fechas
    result = list(collection.find({'Fecha': {'$gte': fecha_inicio, '$lte': fecha_fin}}))

    # Calcula la sumatoria del campo Monto
    #total_monto = sum(item['Monto'] for item in result)
    total_monto = sum(extract_numeric_value(item.get('Detalle', {}).get('Monto', '')) for item in result)
    total_comision = 0
    numpagos = 0
    # Convierte los ObjectId a cadenas antes de serializar a JSON
    for item in result:
        item['_id'] = str(item['_id'])
        detalle = item.get('Detalle')
        if detalle.get('TransID'):
            total_comision += 10
        else:
            total_comision +=15
    
    numpagos = len(result)
    

    
    return jsonify({'resultados': result, 'monto': total_monto,'comision':total_comision, 'pagos': numpagos})

if __name__ == '__main__':
   http_server = WSGIServer(("0.0.0.0",8080), app)
   http_server.serve_forever()
