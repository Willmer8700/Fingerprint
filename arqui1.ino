#include <Adafruit_Fingerprint.h>
#include <Servo.h>

SoftwareSerial mySerial(2, 3); // Crear Serial para Sensor Rx, TX del Arduino
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial); // Crea el objeto Finger comunicación pin 2, 3
int analogo5 = 0; // Variable de lectura del Analógico 5 para sensor de obstáculos
Servo servoPT; // Asocia la librería servo a servoPT

void setup() {
    pinMode(7, OUTPUT);
    pinMode(5, OUTPUT);
    pinMode(3, OUTPUT);
    Serial.begin(9600);
    servoPT.attach(9); // Servo asociado al pin 9 y lleva a 170 grados
    servoPT.write(170);
    while (!Serial); // Yun/Leo/Micro/Zero/...
    delay(100);
    Serial.println("Sistema de apertura con huella dactilar");
    finger.begin(57600); // inicializa comunicación con sensor a 57600 Baudios
    delay(5);
    if (finger.verifyPassword()) {
        Serial.println("Detectado un sensor de huella!");
    } else {
        Serial.println("No hay comunicación con el sensor de huella");
        Serial.println("Revise las conexiones");
        while (1) {
            delay(1);
        }
    }
    finger.getTemplateCount();
    Serial.print("El sensor contiene ");
    Serial.print(finger.templateCount);
    Serial.println(" plantillas");
    Serial.println("Esperando por una huella válida...");
}

void loop() {
    analogo5 = analogRead(A5);
    if (analogo5 <= 600) { // Si el sensor de obstáculos fue obstruido, abre la puerta
        Serial.print("Salida Interna *** ");
        abrirPuerta();
    }
    int fingerprint_id = getFingerprintIDez();
    if (fingerprint_id >= 0) {
        Serial.print(fingerprint_id);
        Serial.print(",");
        Serial.println(finger.confidence);
        
        abrirPuerta();
    }
    delay(50);
}

void abrirPuerta() {
    Serial.println(" AUTORIZADA ***");
    digitalWrite(5, HIGH); // Abrir la cerradura
    delay(1000);
    servoPT.write(90); // Abrir la puerta
    delay(3000); // Tiempo de la puerta abierta
    digitalWrite(7, HIGH); // Suena el buzzer para indicar que se va a cerrar la puerta
    delay(500);
    servoPT.write(170); // Cierra puerta
    delay(500);
    digitalWrite(7, LOW); // apaga el buzzer
    digitalWrite(5, LOW); // cierra la cerradura
}

void Mal_Registro() {
    digitalWrite(7, HIGH);
    delay(200);
    digitalWrite(7, LOW);
    delay(100);
    digitalWrite(7, HIGH);
    delay(200);
    digitalWrite(7, LOW);
}

int getFingerprintIDez() {
    uint8_t p = finger.getImage();
    if (p != FINGERPRINT_OK) return -1;
    p = finger.image2Tz();
    if (p != FINGERPRINT_OK) return -1;
    p = finger.fingerFastSearch();
    if (p != FINGERPRINT_OK) {
        Mal_Registro();
        return -1;
    }
    return finger.fingerID;
}