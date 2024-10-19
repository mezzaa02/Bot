import requests
import os
import re

# Obtener el directorio actual donde se encuentra el script
current_directory = os.path.dirname(os.path.abspath(__file__))

def authenticate_wuzapi(token):
    url = f"http://localhost:8080/login/?token={token}"
    response = requests.get(url)
    if response.status_code == 200:
        print("Autenticación exitosa.")
        return True
    else:
        print(f"Error de autenticación {response.status_code}: {response.text}")
        return False

def send_message_wuzapi(phone_number, message, token):
    url = "http://localhost:8080/chat/send/text"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "token": token
    }
    payload = {
        "Phone": phone_number,
        "Body": message
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Mensaje enviado correctamente a: {phone_number}")
            return True
        else:
            print(f"Error {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        return False

def process_numbers(input_file, output_file, token):
    # Ruta completa del archivo de entrada y salida
    input_path = os.path.join(current_directory, input_file)
    output_path = os.path.join(current_directory, output_file)

    # Verificar si el archivo de entrada existe
    if not os.path.exists(input_path):
        print(f'Error: No se encontró el archivo de entrada "{input_path}".')
        return

    # Leer los números desde el archivo de entrada
    with open(input_path, 'r', encoding='utf-8') as f:
        phone_numbers = f.readlines()
    
    print(f"Números leídos desde el archivo: {phone_numbers}")

    # Limpiar los números y extraer solo el número después del prefijo '+51' con exactamente 9 dígitos
    phone_numbers = [re.sub(r'@.*', '', number.strip()) for number in phone_numbers]
    phone_numbers = [number[2:] if number.startswith('51') and len(number[2:]) == 9 else None for number in phone_numbers]
    phone_numbers = [number for number in phone_numbers if number is not None]
    phone_numbers = list(set(phone_numbers))
    
    print(f"Números después de limpieza y filtrado: {phone_numbers}")

    # Leer los números ya procesados para evitar enviar el mensaje dos veces
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            sent_numbers = set(f.read().splitlines())
    else:
        sent_numbers = set()

    print(f"Números ya procesados (enviado.txt): {sent_numbers}")

    # Enviar mensajes a los números que no han sido procesados y actualizar la lista de enviados
    messages = [
        "Buenas 🤗✨\n\n🌟📦Podemos *continuar con su pedido* 🤩",
        "70 soles le podemos dejar por unidad",
        "60 si lleva 2"
    ]
    with open(output_path, 'a', encoding='utf-8') as f:
        for number in phone_numbers:
            full_number = f"+51{number}"
            if full_number not in sent_numbers:
                for message in messages:
                    print(f"Intentando enviar mensaje a: {full_number} -> {message}")
                    success = send_message_wuzapi(full_number, message, token)
                    if not success:
                        print(f"Error al enviar mensaje a: {full_number}")
                        break
                else:
                    # Solo se agrega a enviados si todos los mensajes se envían correctamente
                    f.write(full_number + "\n")
                    print(f"Mensajes enviados a: {full_number}")

# Configuración de archivo de entrada y salida
token = "jhon"  # Reemplaza con tu token de Wuzapi
input_file = 'sent_numbers.txt'  # Archivo de texto con los números (uno por línea)
output_file = 'enviado.txt'  # Archivo de texto con los números a los que ya se les envió el mensaje

# Ejecutar autenticación y procesamiento
if authenticate_wuzapi(token):
    process_numbers(input_file, output_file, token)
