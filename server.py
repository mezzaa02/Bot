from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Ruta al archivo de seguimiento de números (en la misma carpeta)
sent_numbers_file = 'sent_numbers.txt'

# Nombres de los archivos PDF (en la misma carpeta que el script)
pdf_files = [
    "CARTERAS_Dama.pdf",
    "RELOJES_CABALLERO.pdf",
    "MORRALES_Caballero.pdf",
    "MORRALES_Dama.pdf",
    "RELOJES_Dama.pdf"
]

# Wuzapi API endpoint y token
wuzapi_url = "http://localhost:8080/chat/send/document"
wuzapi_token = "jhon"  # Reemplaza con tu token real

def has_received_catalog(phone_number):
    if not os.path.exists(sent_numbers_file):
        return False
    with open(sent_numbers_file, 'r') as file:
        return phone_number in file.read()

def mark_as_sent(phone_number):
    with open(sent_numbers_file, 'a') as file:
        file.write(phone_number + '\n')

@app.route('/webhook', methods=['POST'])
def webhook():
    # Mostrar los headers y el contenido de la solicitud para depuración
    print(f"Headers: {request.headers}")
    print(f"Request data: {request.data}")

    # Asegurarse de que la solicitud sea JSON
    if not request.is_json:
        print("Unsupported Media Type: Expected application/json")
        return jsonify({"error": "Unsupported Media Type"}), 415

    data = request.get_json()  # Se usa get_json() para parsear la solicitud JSON
    print(f"Parsed JSON data: {data}")
    
    sender = data.get('sender')
    print(f"Sender: {sender}")

    if not sender:
        print("No sender found in request data")
        return jsonify({"error": "Bad Request: No sender found"}), 400

    if not has_received_catalog(sender):
        for pdf in pdf_files:
            send_pdf(sender, pdf)
        mark_as_sent(sender)
    
    return jsonify({"status": "success"}), 200

def send_pdf(phone_number, pdf_filename):
    print(f"Sending PDF {pdf_filename} to {phone_number}")
    with open(pdf_filename, 'rb') as pdf_file:
        files = {'document': pdf_file}
        payload = {'token': wuzapi_token, 'to': phone_number}
        response = requests.post(wuzapi_url, files=files, data=payload)
        print(f"Response from Wuzapi: {response.json()}")

if __name__ == '__main__':
    # Habilitar el modo de depuración
    app.run(host='0.0.0.0', port=8765, debug=True)
