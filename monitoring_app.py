import tkinter as tk
from tkinter import ttk
from gui_utils import update_labels
import os
import subprocess
import signal
import wmi
from dotenv import load_dotenv


# Initialize WMI client
w = wmi.WMI(namespace="root\OpenHardwareMonitor")

load_dotenv()  # This will load the key-value pairs from .env into environment variables

# Start OpenHardwareMonitor in silent mode
def start_ohm():
    path_to_ohm = os.getenv("OHM_PATH")  # Get the path from environment variables
    if not path_to_ohm:
        raise ValueError("OHM_PATH not found in .env file")
    
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.Popen([path_to_ohm], startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

# Stop OpenHardwareMonitor
def stop_ohm(process):
    os.kill(process.pid, signal.SIGTERM)

def on_closing():
    stop_ohm(ohm_process)
    root.destroy()

def fetch_system_details():
    # Fetching data using WMI and OpenHardwareMonitor
    sensors = w.Sensor()

    cpu_load_data = [sensor for sensor in sensors if sensor.Name == 'CPU Total' and sensor.SensorType == "Load"]

    # Filter out the CPU temperature sensor
    cpu_temp_data = [sensor for sensor in sensors if sensor.Name == 'CPU Package' and sensor.SensorType == "Temperature"]

    # If the sensor is found, return the value, otherwise return "N/A"

    if cpu_load_data:
        cpu_load = cpu_load_data[0].Value
    else:
        cpu_load = "N/A"

    if cpu_temp_data:
        cpu_temp = cpu_temp_data[0].Value
    else:
        cpu_temp = "N/A"  # Or any default value in case the sensor isn't found

    gpu_temp, gpu_load, vram_used, vram_total = fetch_gpu_details_from_ohm()

    return cpu_load, cpu_temp, gpu_load, gpu_temp, vram_used, vram_total

def fetch_gpu_details_from_ohm():
    sensors = w.Sensor()

    # Filter for the metrics we're interested in
    gpu_temp_data = next((sensor for sensor in sensors if sensor.Name == 'GPU Core' and sensor.SensorType == "Temperature"), None)
    gpu_load_data = next((sensor for sensor in sensors if sensor.Name == 'GPU Core' and sensor.SensorType == "Load"), None)
    gpu_memory_used_data = next((sensor for sensor in sensors if sensor.Name == 'GPU Memory Used' and sensor.SensorType == "SmallData"), None)
    gpu_memory_total_data = next((sensor for sensor in sensors if sensor.Name == 'GPU Memory Total' and sensor.SensorType == "SmallData"), None)

    gpu_temp = gpu_temp_data.Value if gpu_temp_data else "N/A"
    gpu_load = gpu_load_data.Value if gpu_load_data else "N/A"
    gpu_memory_used = gpu_memory_used_data.Value if gpu_memory_used_data else "N/A"
    gpu_memory_total = gpu_memory_total_data.Value if gpu_memory_total_data else "N/A"

    return gpu_temp, gpu_load, gpu_memory_used, gpu_memory_total


def update_gui():
    cpu_load, cpu_temp, gpu_load, gpu_temp, vram_used, vram_total = fetch_system_details()

    # CPU Load
    if isinstance(cpu_load, (float, int)):
        update_labels(cpu_load_label, f"Load: {cpu_load:.1f}%")
    else:
        update_labels(cpu_load_label, f"Load: {cpu_load}")

    # CPU Temperature
    if isinstance(cpu_temp, (float, int)):
        update_labels(cpu_temp_label, f"Temp: {cpu_temp:.1f}°C")
    else:
        update_labels(cpu_temp_label, f"Temp: {cpu_temp}")

    # GPU Load
    try:
        gpu_load = float(gpu_load)
        update_labels(gpu_load_label, f"Load: {gpu_load:.1f}%")
    except ValueError:
        update_labels(gpu_load_label, f"Load: {gpu_load}")

    # GPU Temperature
    if isinstance(gpu_temp, (float, int)):
        update_labels(gpu_temp_label, f"Temp: {gpu_temp:.1f}°C")
    else:
        update_labels(gpu_temp_label, f"Temp: {gpu_temp}")

    # VRAM Used
    if isinstance(vram_used, (float, int)):
        update_labels(vram_label, f"VRAM: {vram_used:,.1f}/{vram_total:,.1f} MB")
    else:
        update_labels(vram_label, f"VRAM: {vram_used}/{vram_total}")

    root.after(500, update_gui)



# Start OpenHardwareMonitor
ohm_process = start_ohm()

root = tk.Tk()
root.title("Monitoring App")
root.configure(bg="#2C2F33")  # Setting a dark background

frame = tk.Frame(root, bg="#2C2F33", padx=10, pady=10)
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Setting up CPU labels
tk.Label(frame, text="CPU", font=("Arial", 14), fg="white", bg="#2C2F33").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
cpu_load_label = tk.Label(frame, font=("Arial", 12), fg="cyan", bg="#2C2F33")
cpu_load_label.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
cpu_temp_label = tk.Label(frame, font=("Arial", 12), fg="red", bg="#2C2F33")
cpu_temp_label.grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)

# Setting up GPU labels
tk.Label(frame, text="GPU", font=("Arial", 14), fg="white", bg="#2C2F33").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
gpu_load_label = tk.Label(frame, font=("Arial", 12), fg="cyan", bg="#2C2F33")
gpu_load_label.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
gpu_temp_label = tk.Label(frame, font=("Arial", 12), fg="red", bg="#2C2F33")
gpu_temp_label.grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)
vram_label = tk.Label(frame, font=("Arial", 12), fg="yellow", bg="#2C2F33")
vram_label.grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)

root.protocol("WM_DELETE_WINDOW", on_closing)

update_gui()
root.mainloop()