import mysql.connector
import serial
import time
from pyfirmata import Arduino, util
from adafruit_fingerprint import Adafruit_Fingerprint

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
    uart = serial.Serial(port = "COM11", baudrate=57600, timeout=1)
    finger = Adafruit_Fingerprint(uart)
    return finger

def get_fingerprint(finger):
    print("Esperando por una huella...")
    while finger.get_image() != finger.OK:
        pass
    print("Imagen de huella capturada")
    
    if finger.image_2_tz(1) != finger.OK:
        return False
    
    if finger.finger_fast_search() != finger.OK:
        return False
    
    return True

def main():
    # Conectar al Arduino
    print("Conectando al Arduino en COM11...")
    board = Arduino('COM11')
    it = util.Iterator(board)
    it.start()

    # Inicializar los pines del hardware
    servo_pin = board.get_pin('d:9:s')  # Pin 9 como servo
    buzzer_pin = board.get_pin('d:7:o')  # Pin 7 como salida para el buzzer
    lock_pin = board.get_pin('d:5:o')  # Pin 5 como salida para la cerradura

    # Esperar para asegurar que la conexión esté establecida
    time.sleep(2)

    try:
        # Configurar el sensor de huellas dactilares
        finger = setup_fingerprint_sensor('COM11')

        while True:
            if get_fingerprint(finger):
                fingerprint_id = finger.finger_id
                confidence = finger.confidence
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

    except KeyboardInterrupt:
        # Cerrar conexiones cuando se presiona Ctrl+C
        board.exit()
        mydb.close()
        print("Programa terminado.")
    except Exception as e:
        print(f"Error: {e}")
        board.exit()
        mydb.close()

if __name__ == "__main__":
    main()
