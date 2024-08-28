from flask import Flask, request, jsonify
import requests
import os

app = Flask(_name_)

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
    with open(sent_numbers_file, 'r') as file:
        return phone_number in file.read()

def mark_as_sent(phone_number):
    with open(sent_numbers_file, 'a') as file:
        file.write(phone_number + '\n')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    sender = data['sender']

    if not has_received_catalog(sender):
        for pdf in pdf_files:
            send_pdf(sender, pdf)
        mark_as_sent(sender)
    
    return jsonify({"status": "success"}), 200

def send_pdf(phone_number, pdf_filename):
    with open(pdf_filename, 'rb') as pdf_file:
        files = {'document': pdf_file}
        payload = {'token': wuzapi_token, 'to': phone_number}
        response = requests.post(wuzapi_url, files=files, data=payload)
        print(response.json())

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=8765)