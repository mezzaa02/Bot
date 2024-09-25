import json
import base64
import requests
from flask import Flask, request, jsonify
import os
import threading
from threading import Lock

app = Flask(__name__)

# Ruta base para los archivos
BASE_PATH = "./"

# Archivos que contienen los números que ya han recibido los mensajes
sent_numbers_file = os.path.join(BASE_PATH, "sent_numbers.txt")
precio_file = os.path.join(BASE_PATH, "precio.txt")  # Cambiado de tienda.txt a precio.txt

# Bloqueos para acceso a archivos
sent_numbers_lock = Lock()
precio_file_lock = Lock()  # Cambiado de tienda_file_lock a precio_file_lock

# Nombres de los archivos PDF
pdf_names = ["RELOJES de Caballero.pdf", "CARTERAS de Dama.pdf", "RELOJES de Dama.pdf", "MORRALES de Dama.pdf", "MORRALES de Caballero.pdf"]
pdf_files = [os.path.join(BASE_PATH, pdf) for pdf in pdf_names]

# Mensajes de bienvenida
welcome_messages = [
    "👋💚 *Buenas* 🤗",
    "Somos empresa 💼 *RUC: 20610868577* Registrada desde *1993* 🥳⭐⭐⭐⭐⭐",
    "✅🩷🩵 Precios *POR DOCENA*\n(si lleva 12 productos *en TOTAL* ) 🛒✨\n▫️⌚Relojes: *50 soles*\n▫️👜Carteras: *50 soles*\n▫️💼Morrales: *50 soles*\n▫️ Billeteras: *20 soles*\n▫️👛Monederos: *15 soles*\n▫️👝Chequeras: *30 soles*\n▫️Correas: *30 soles*"
]

# Nombres de los archivos de video
video_files = [
    os.path.join(BASE_PATH, "video2.mp4"),
    os.path.join(BASE_PATH, "video3.mp4"),
    os.path.join(BASE_PATH, "video4.mp4"),
    os.path.join(BASE_PATH, "video5.mp4")
]

# Texto para el primer video
first_video_message = """🥳Replica *A1 Rolex* ✨😍
⌚Por *DOCENA* relojes *50 soles*
💚 *CUALQUIER MODELO mismos precios* 🛍️"""

# Wuzapi API endpoint y token
wuzapi_url_text = "http://localhost:8080/chat/send/text"
wuzapi_url_document = "http://localhost:8080/chat/send/document"
wuzapi_url_video = "http://localhost:8080/chat/send/video"
wuzapi_token = "jhon"

# Diccionarios para manejar las sesiones y bloqueos por usuario
active_sessions = {}
session_locks = {}

def encode_file_to_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def has_received_catalog(phone_number):
    if not os.path.exists(sent_numbers_file):
        return False
    with sent_numbers_lock:
        with open(sent_numbers_file, 'r') as file:
            return phone_number in file.read()

def mark_as_sent(phone_number):
    with sent_numbers_lock:
        with open(sent_numbers_file, 'a') as file:
            file.write(phone_number + '\n')

def has_received_precio(phone_number):
    if not os.path.exists(precio_file):
        return False
    with precio_file_lock:
        with open(precio_file, 'r') as file:
            return phone_number in file.read()

def mark_as_precio_sent(phone_number):
    with precio_file_lock:
        with open(precio_file, 'a') as file:
            file.write(phone_number + '\n')

def send_message(phone_number, message_text):
    """Función para enviar un mensaje de texto."""
    print(f"Enviando mensaje: {message_text} a {phone_number}")
    
    payload = {
        "Phone": phone_number,
        "Body": message_text
    }

    response = requests.post(wuzapi_url_text, json=payload, headers={"token": wuzapi_token})
    print(f"Respuesta de Wuzapi: {response.json()}")

def send_pdf(phone_number, pdf_filename, pdf_name):
    """Función para enviar un PDF."""
    print(f"Enviando PDF {pdf_name} a {phone_number}")
    
    encoded_pdf = encode_file_to_base64(pdf_filename)
    
    payload = {
        "Phone": phone_number,
        "Document": f"data:application/octet-stream;base64,{encoded_pdf}",
        "FileName": pdf_name
    }

    response = requests.post(wuzapi_url_document, json=payload, headers={"token": wuzapi_token})
    print(f"Respuesta de Wuzapi: {response.json()}")

def send_video(phone_number, video_filename):
    """Función para enviar un video sin texto."""
    if not os.path.exists(video_filename):
        print(f"Error: {video_filename} no existe.")
        return
    
    print(f"Enviando video {video_filename} a {phone_number}")
    
    encoded_video = encode_file_to_base64(video_filename)
    
    payload = {
        "Phone": phone_number,
        "Video": f"data:video/mp4;base64,{encoded_video}",
        "FileName": os.path.basename(video_filename)
    }

    response = requests.post(wuzapi_url_video, json=payload, headers={"token": wuzapi_token})
    print(f"Respuesta de Wuzapi: {response.json()}")

@app.route('/webhook', methods=['POST'])
def webhook():
    # Obtener los datos entrantes
    if request.content_type == 'application/json':
        data = request.get_json()
    elif request.content_type == 'application/x-www-form-urlencoded':
        data = request.form.to_dict()
        if 'jsonData' in data:
            data['jsonData'] = json.loads(data['jsonData'])
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415

    print(f"Datos recibidos: {data}")  # Para depuración

    try:
        sender_full = data['jsonData']['event']['Info']['Sender']
        sender = sender_full.split('@')[0]  # Extraer solo el número de teléfono
    except KeyError:
        return jsonify({"error": "Bad Request: No sender found"}), 400

    # Obtener el texto del mensaje si está disponible
    message_text = ''
    try:
        message_text = data['jsonData']['event']['Message']['conversation']
    except KeyError:
        pass  # El mensaje puede no contener 'conversation' en algunos casos

    # Procesar el texto del mensaje para verificar palabras clave
    keywords = ["docena","docena","cuanto","costo", "unidad","unidades", "precios", "precios"]
    message_lower = message_text.lower()

    # Asegurar que solo un hilo procese la interacción de un cliente
    if sender not in session_locks:
        session_locks[sender] = Lock()

    with session_locks[sender]:
        if not has_received_catalog(sender):
            # Es la primera vez que nos contacta, enviar mensajes de bienvenida
            if sender not in active_sessions:
                active_sessions[sender] = True
                threading.Thread(target=send_welcome_pdfs_videos_to_client, args=(sender,)).start()
        else:
            # Ya ha recibido los mensajes de bienvenida
            if any(keyword in message_lower for keyword in keywords):
                # El mensaje contiene una de las palabras clave
                if not has_received_precio(sender):
                    threading.Thread(target=send_precio_message, args=(sender,)).start()

    return jsonify({"status": "success"}), 200

def send_precio_message(sender):
    # Enviar los dos mensajes solicitados
    messages = [
        "⌚Por DOCENA relojes 50 soles",
        "¿Cuántas unidades desea llevar? 🙌☺️"
    ]
    for message in messages:
        send_message(sender, message)
    mark_as_precio_sent(sender)
    # Limpiar la sesión y el bloqueo
    session_locks.pop(sender, None)

def send_welcome_pdfs_videos_to_client(sender):
    """Envía los mensajes de bienvenida, PDFs y videos al cliente."""
    # Enviar mensajes de bienvenida
    for message in welcome_messages:
        send_message(sender, message)
    
    # Enviar PDFs
    for pdf_filename, pdf_name in zip(pdf_files, pdf_names):
        send_pdf(sender, pdf_filename, pdf_name)

    # Enviar el mensaje para el primer video antes de enviar el video
    send_message(sender, first_video_message)
    
    # Enviar videos
    for video in video_files:
        send_video(sender, video)

    mark_as_sent(sender)
    active_sessions.pop(sender, None)
    session_locks.pop(sender, None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=True)
