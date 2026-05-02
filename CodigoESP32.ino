const int ldrPin = 34; // Pin ADC del ESP32
const float VCC = 3.3;
const int ADC_RES = 4095; // Resolución de 12 bits

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  
  // Inicializamos la semilla para el ruido aleatorio
  randomSeed(analogRead(0));
}

void loop() {
  // 1. Adquisición y escalamiento (Actividad 2)
  int adcVal = analogRead(ldrPin);
  float voltageOriginal = (adcVal * VCC) / ADC_RES;

  // 2. Incorporar ruido simulado mediante código (Actividad 2)
  // Generamos un ruido aleatorio entre -0.3V y +0.3V
  float ruido = ((float)random(-300, 300) / 1000.0);
  float voltageConRuido = voltageOriginal + ruido;

  // Limitamos para que el voltaje ruidoso no sea negativo por error
  if (voltageConRuido < 0.0) {
    voltageConRuido = 0.0;
  }

  // 3. Enviar datos al entorno de análisis separados por coma
  Serial.print(voltageOriginal);
  Serial.print(",");
  Serial.println(voltageConRuido);

  // Tiempo de muestreo Ts = 100ms
  delay(100); 
}