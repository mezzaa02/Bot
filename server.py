import json
import base64
import requests
from flask import Flask, request, jsonify
import os
import threading
from threading import Lock

app = Flask(__name__)

# Ruta al archivo de seguimiento de números
sent_numbers_file = 'sent_numbers.txt'

# Nombres de los archivos PDF
pdf_files = [
    "CARTERAS_Dama.pdf",
    "RELOJES_CABALLERO.pdf",
    "MORRALES_Caballero.pdf",
    "MORRALES_Dama.pdf",
    "RELOJES_Dama.pdf"
]

# Mensajes de bienvenida
welcome_messages = [
    "👋💚 *Buenas* 🤗",
    "Somos empresa 💼 RUC: *20610868577* Registrada desde *1993* 🥳⭐⭐⭐⭐⭐",
    "✅🩷🩵 Precios *POR DOCENA*\n(si lleva 12 productos *en TOTAL* ) 🛒✨\n▫️⌚Relojes: *50 soles*\n▫️👜Carteras: *50 soles*\n▫️💼Morrales: *50 soles*\n▫️ Billeteras: *20 soles*\n▫️👛Monederos: *15 soles*\n▫️👝Chequeras: *30 soles*\n▫️Correas: *30 soles*"
]

# Wuzapi API endpoint y token
wuzapi_url_text = "http://localhost:8080/chat/send/text"
wuzapi_url_document = "http://localhost:8080/chat/send/document"
wuzapi_token = "jhon"

# Diccionario para manejar las sesiones y su respectivo bloqueo
active_sessions = {}
session_locks = {}

def encode_file_to_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def has_received_catalog(phone_number):
    if not os.path.exists(sent_numbers_file):
        return False
    with open(sent_numbers_file, 'r') as file:
        return phone_number in file.read()

def mark_as_sent(phone_number):
    with open(sent_numbers_file, 'a') as file:
        file.write(phone_number + '\n')

def send_message(phone_number, message_text):
    """Función para enviar un mensaje de texto."""
    print(f"Sending message: {message_text} to {phone_number}")
    
    payload = {
        "Phone": phone_number,
        "Body": message_text
    }

    response = requests.post(wuzapi_url_text, json=payload, headers={"token": wuzapi_token})
    print(f"Response from Wuzapi: {response.json()}")

def send_pdf(phone_number, pdf_filename):
    """Función para enviar un PDF."""
    print(f"Sending PDF {pdf_filename} to {phone_number}")
    
    encoded_pdf = encode_file_to_base64(pdf_filename)
    
    payload = {
        "Phone": phone_number,
        "Document": f"data:application/octet-stream;base64,{encoded_pdf}",
        "FileName": pdf_filename
    }

    response = requests.post(wuzapi_url_document, json=payload, headers={"token": wuzapi_token})
    print(f"Response from Wuzapi: {response.json()}")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.content_type == 'application/json':
        data = request.get_json()
    elif request.content_type == 'application/x-www-form-urlencoded':
        data = request.form.to_dict()
        if 'jsonData' in data:
            data['jsonData'] = json.loads(data['jsonData'])
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415

    try:
        sender = data['jsonData']['event']['Info']['Sender']
    except KeyError:
        return jsonify({"error": "Bad Request: No sender found"}), 400

    # Asegurarse de que solo un hilo procese la primera interacción de un cliente
    if sender not in session_locks:
        session_locks[sender] = Lock()

    with session_locks[sender]:  # Bloquear la sesión para este cliente específico
        if sender not in active_sessions:
            active_sessions[sender] = True  # Marcar la sesión como activa
            if not has_received_catalog(sender):
                # Utilizar threading para evitar bloquear el webhook
                threading.Thread(target=send_welcome_and_pdfs_to_client, args=(sender,)).start()

    return jsonify({"status": "success"}), 200

def send_welcome_and_pdfs_to_client(sender):
    """Envía los mensajes de bienvenida y PDFs al cliente."""
    # Enviar mensajes de bienvenida
    for message in welcome_messages:
        send_message(sender, message)
    
    # Enviar PDFs
    for pdf in pdf_files:
        send_pdf(sender, pdf)

    mark_as_sent(sender)
    active_sessions.pop(sender, None)  # Eliminar la sesión después de enviar los PDFs
    session_locks.pop(sender, None)  # Eliminar el bloqueo de sesión después de completar el envío

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7774, debug=True)
