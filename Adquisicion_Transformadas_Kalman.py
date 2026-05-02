import serial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

# --- CONFIGURACIÓN ---
puerto = 'COM7'  # Cambia a '/dev/ttyUSB0' si vuelves a Linux
baudrate = 115200
Ts = 0.1  # 100ms
N = 200

s_valores = [0.5 + 1j, 2 + 0j] 
z_valores = [1.0 * np.exp(1j * np.pi/4), 1.4 + 0j]

# --- VECTORES DE DATOS ---
t = np.arange(N) * Ts
n_muestras = np.arange(N)
datos_original = np.zeros(N)
datos_ruido = np.zeros(N)
datos_kalman = np.zeros(N)
Vs_t = np.zeros((len(s_valores), N)) 
Vz_t = np.zeros((len(z_valores), N))

# --- PARÁMETROS KALMAN ---
R = 0.5
Q = 0.1
P = 1.0
x_estimado = 0.0
k = 0  # Contador global

# --- CONEXIÓN SERIAL ---
try:
    # Usamos un timeout bajo para no congelar la animación si el ESP32 se retrasa
    s_serial = serial.Serial(puerto, baudrate, timeout=0.2)
    s_serial.setDTR(False)
    s_serial.setRTS(False)
    time.sleep(2)
    s_serial.reset_input_buffer()
except serial.SerialException as e:
    print(f"Error serial: {e}")
    exit()

# --- CONFIGURACIÓN DE GRÁFICAS (Se hace solo UNA vez) ---
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
fig.tight_layout(pad=4.0)

# Inicializamos las líneas vacías
line_orig, = ax1.plot([], [], 'g--', alpha=0.6, label='Original Limpia')
line_ruido, = ax1.plot([], [], 'r', alpha=0.5, label='Con Ruido')
line_kalman, = ax1.plot([], [], 'b', linewidth=2, label='Estimada (Kalman)')
ax1.set_ylim([0, 4.0])
ax1.set_xlim([0, N * Ts])
ax1.set_title("Dominio del Tiempo: Adquisición y Filtrado")
ax1.set_ylabel("Voltaje (V)")
ax1.grid(True)
ax1.legend(loc='upper right')

lines_laplace = []
for s_val in s_valores:
    l, = ax2.plot([], [], label=f"s = {s_val}")
    lines_laplace.append(l)
ax2.set_xlim([0, N * Ts])
ax2.set_ylim([0, 5]) # Límite inicial, se autoescalará
ax2.set_title("Frecuencia Continua (Magnitud Laplace)")
ax2.grid(True)
ax2.legend(loc='upper right')

lines_z = []
for z_val in z_valores:
    l, = ax3.plot([], [], label=f"z = {np.round(z_val, 2)}")
    lines_z.append(l)
ax3.set_xlim([0, N * Ts])
ax3.set_ylim([0, 5]) # Límite inicial, se autoescalará
ax3.set_title("Frecuencia Discreta (Magnitud Transformada Z)")
ax3.set_xlabel("Tiempo (s)")
ax3.grid(True)
ax3.legend(loc='upper right')

# --- FUNCIÓN DE ACTUALIZACIÓN EN TIEMPO REAL ---
def update(frame):
    global k, P, x_estimado
    
    if k >= N:
        return line_orig, line_ruido, line_kalman, *lines_laplace, *lines_z
        
    linea = s_serial.readline().decode('utf-8').strip()
    if not linea:
        return line_orig, line_ruido, line_kalman, *lines_laplace, *lines_z
        
    try:
        v_orig, v_ruido = map(float, linea.split(','))
    except ValueError:
        return line_orig, line_ruido, line_kalman, *lines_laplace, *lines_z

    # Puedes comentar esta línea si no quieres que la terminal se llene de texto
    print(f"Procesando muestra {k}: Original={v_orig}V, Ruido={v_ruido}V")

    datos_original[k] = v_orig
    datos_ruido[k] = v_ruido

    # --- Filtro Kalman ---
    dP = Q - (P**2 / R)
    P = max(P + dP, 0)
    K = P / R
    x_estimado = x_estimado + K * (v_ruido - x_estimado)
    datos_kalman[k] = x_estimado

    # --- Laplace ---
    for i, s_val in enumerate(s_valores):
        y_laplace = datos_ruido[:k+1] * np.exp(-s_val * t[:k+1])
        # FIX NUMPY 2.0: Cambiamos trapz por trapezoid
        Vs_t[i, k] = np.abs(np.trapezoid(y_laplace, dx=Ts))
        
    # --- Transformada Z ---
    for i, z_val in enumerate(z_valores):
        z_inv_n = np.power(z_val, -n_muestras[:k+1])
        y_z = datos_ruido[:k+1] * z_inv_n
        Vz_t[i, k] = np.abs(np.sum(y_z))

    # --- Actualizar datos visuales ---
    line_orig.set_data(t[:k+1], datos_original[:k+1])
    line_ruido.set_data(t[:k+1], datos_ruido[:k+1])
    line_kalman.set_data(t[:k+1], datos_kalman[:k+1])

    for i, l in enumerate(lines_laplace):
        l.set_data(t[:k+1], Vs_t[i, :k+1])
    ax2.relim()
    ax2.autoscale_view(scalex=False, scaley=True)

    for i, l in enumerate(lines_z):
        l.set_data(t[:k+1], Vz_t[i, :k+1])
    ax3.relim()
    ax3.autoscale_view(scalex=False, scaley=True)

    k += 1
    return line_orig, line_ruido, line_kalman, *lines_laplace, *lines_z

# Iniciar la animación
print("Iniciando adquisición de datos...")
ani = animation.FuncAnimation(fig, update, interval=10, blit=False, cache_frame_data=False)

plt.show()

# Cierre seguro del puerto al cerrar la ventana
s_serial.close()
print("Ejecución finalizada.")