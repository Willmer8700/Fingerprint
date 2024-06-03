import mysql.connector
import serial
import time
from pyfirmata import Arduino, util

# Configuración de la base de datos
config_db = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'fingerprint-db',
}

mydb = mysql.connector.connect(**config_db)
mycursor = mydb.cursor()

def abrir_puerta(board, servo_pin, buzzer_pin, lock_pin):
    lock_pin.write(1)  # Abre la cerradura
    servo_pin.write(90)  # Abre la puerta
    buzzer_pin.write(1)  # Enciende el buzzer
    time.sleep(0.5)  # Tiempo para mantener el buzzer encendido
    buzzer_pin.write(0)  # Apaga el buzzer
    print("Puerta abierta")

def cerrar_puerta(board, servo_pin, buzzer_pin, lock_pin):
    servo_pin.write(170)  # Cierra la puerta
    lock_pin.write(0)  # Cierra la cerradura
    buzzer_pin.write(1)  # Enciende el buzzer
    time.sleep(0.5)  # Tiempo para mantener el buzzer encendido
    buzzer_pin.write(0)  # Apaga el buzzer
    print("Puerta cerrada")

def setup_fingerprint_sensor(port):
    uart = serial.Serial(port, baudrate=57600, timeout=1)
    return uart

def get_fingerprint(uart):
    print("Esperando por una huella...")
    # Envía comandos al sensor de huellas
    uart.write(b'get_image\n')
    response = uart.readline().strip()
    if response != b'OK':
        return False
    
    uart.write(b'image_2_tz 1\n')
    response = uart.readline().strip()
    if response != b'OK':
        return False
    
    uart.write(b'finger_fast_search\n')
    response = uart.readline().strip()
    if response != b'OK':
        return False
    
    fingerprint_id = int(uart.readline().strip())
    confidence = int(uart.readline().strip())
    return (fingerprint_id, confidence)

def main():
    # Conectar al Arduino
    print("Conectando al Arduino en COM11...")
    try:
        board = Arduino('COM11')
        it = util.Iterator(board)
        it.start()
    except Exception as e:
        print(f"Error al conectar con Arduino: {e}")
        return

    # Inicializar los pines del hardware
    try:
        servo_pin = board.get_pin('d:9:s')  # Pin 9 como servo
        buzzer_pin = board.get_pin('d:7:o')  # Pin 7 como salida para el buzzer
        lock_pin = board.get_pin('d:5:o')  # Pin 5 como salida para la cerradura
    except Exception as e:
        print(f"Error al inicializar los pines: {e}")
        return

    # Esperar para asegurar que la conexión esté establecida
    time.sleep(2)
    print("Conexión establecida con Arduino")

    try:
        # Configurar el sensor de huellas dactilares
        uart = setup_fingerprint_sensor('COM5')  # Ajusta el puerto serial según tu configuración
        uart.flushInput()  # Limpiar el búfer de entrada
        
        while True:
            fingerprint_data = get_fingerprint(uart)
            if fingerprint_data:
                fingerprint_id, confidence = fingerprint_data
                print(f"Huella detectada. ID: {fingerprint_id}, Confianza: {confidence}")
                
                # Insertar datos en MySQL
                sql = "INSERT INTO fingerprints (fingerprint_id, confidence) VALUES (%s, %s)"
                val = (fingerprint_id, confidence)
                mycursor.execute(sql, val)
                mydb.commit()
                print(f"Dato insertado: fingerprint_id={fingerprint_id}, confidence={confidence}")
                
                # Lógica de control de la puerta
                if 1 <= fingerprint_id <= 10:  # ID válidos
                    abrir_puerta(board, servo_pin, buzzer_pin, lock_pin)
                    time.sleep(5)  # Mantener la puerta abierta por 5 segundos
                    cerrar_puerta(board, servo_pin, buzzer_pin, lock_pin)
                else:
                    print("Huella no autorizada")
            else:
                print("No se pudo leer la huella")

    except Exception as e:
        print(f"Error durante la operación: {e}")
    finally:
        board.exit()
        mydb.close()
        print("Programa terminado.")

if __name__ == "__main__":
    main()
