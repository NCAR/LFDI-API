from flask import Flask, render_template, jsonify, request
import Hardware_API.LFDI_API as LFDI
import Hardware_API.Spectrograph as Spectrograph
from DataCollection.LFDI_Experiment import Total_Data_Collection
import threading
import base64
import io
from PIL import Image
import os

app = Flask(__name__)

# Global variables for hardware connections
spectrometer = None
lfdi = None
experiment_thread = None
current_experiment_running = False

def init_hardware():
    global spectrometer, lfdi
    try:
        spectrometer = Spectrograph.Spectrometer()
        spectrometer.camera.auto_exposure = False
    except Exception as e:
        print(f"Could not connect to Spectrometer Camera: {e}")
        return False

    try:
        lfdi = LFDI.LFDI_TCB("COM3", 9600)
        lfdi.set_controller_kd(controller_number=1, kd=1)
        lfdi.set_controller_ki(controller_number=1, ki=0)
        lfdi.set_controller_kp(controller_number=1, kp=1)
    except Exception as e:
        print(f"Could not connect to LFDI_TCB On Com3: {e}")
        return False
    
    return True

def run_experiment(channel, temp_start, temp_end, temp_step, voltage_start, 
                  voltage_end, voltage_step, tolerance):
    global current_experiment_running
    current_experiment_running = True
    
    folder = f"Experiment_Output_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(folder, exist_ok=True)
    
    try:
        Total_Data_Collection(
            spectrometer=spectrometer,
            LFDI_TCB=lfdi,
            start_temp=float(temp_start),
            end_temp=float(temp_end),
            step_temp=float(temp_step),
            tolerance=float(tolerance),
            start_voltage=float(voltage_start),
            end_voltage=float(voltage_end),
            step_voltage=float(voltage_step),
            folder=folder
        )
    finally:
        current_experiment_running = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_experiment', methods=['POST'])
def start_experiment():
    global experiment_thread
    
    if current_experiment_running:
        return jsonify({'status': 'error', 'message': 'Experiment already running'})
    
    data = request.json
    experiment_thread = threading.Thread(
        target=run_experiment,
        kwargs={
            'channel': data['channel'],
            'temp_start': data['tempStart'],
            'temp_end': data['tempEnd'],
            'temp_step': data['tempStep'],
            'voltage_start': data['voltageStart'],
            'voltage_end': data['voltageEnd'],
            'voltage_step': data['voltageStep'],
            'tolerance': data['tolerance']
        }
    )
    experiment_thread.start()
    return jsonify({'status': 'success'})

@app.route('/stop_experiment', methods=['POST'])
def stop_experiment():
    global current_experiment_running
    current_experiment_running = False
    return jsonify({'status': 'success'})

@app.route('/get_status')
def get_status():
    if not lfdi or not spectrometer:
        return jsonify({
            'status': 'error',
            'message': 'Hardware not connected'
        })
    
    # Get current temperature and other relevant data
    current_temp = lfdi.Controllers[0].average
    current_voltage = lfdi.Compensators[2].voltage
    
    return jsonify({
        'status': 'running' if current_experiment_running else 'idle',
        'temperature': current_temp,
        'voltage': current_voltage
    })

@app.route('/get_spectrometer_image')
def get_spectrometer_image():
    if not spectrometer:
        return jsonify({'status': 'error', 'message': 'Spectrometer not connected'})
    
    # Capture current image and convert to base64
    spectrometer.single_output(show=False)
    img_path = spectrometer.current_graph
    
    with open(img_path, 'rb') as img_file:
        img_data = base64.b64encode(img_file.read()).decode('utf-8')
    
    return jsonify({'status': 'success', 'image': img_data})

if __name__ == '__main__':
    if init_hardware():
        app.run(debug=True)
    else:
        print("Failed to initialize hardware. Please check connections.")
