import time, signal, os, dotenv
from bambu_connect import BambuClient, PrinterStatus

# get connection details from env (hostname, access code, serial)
dotenv.load_dotenv()
HOSTNAME = os.environ.get("BAMBU_HOSTNAME")
ACCESS_CODE = os.environ.get("BAMBU_ACCESS_CODE")
SERIAL = os.environ.get("BAMBU_SERIAL")
bambu = BambuClient(HOSTNAME, ACCESS_CODE, SERIAL)

# formatted print of status updates
def callback(s: PrinterStatus):
    print(f"--- msg {s.sequence_id} ---")
    print(f"Nozzle Temperature:  {s.nozzle_temper:5.1f} / {s.nozzle_target_temper:5.1f} °C")
    print(f"Hotbed Temperature:  {s.bed_temper:5.1f} / {s.bed_target_temper:5.1f} °C")
    print(f"Fans:   nozzle:{s.heatbreak_fan_speed}, cooling:{s.cooling_fan_speed}") # s.big_fan1_speed, s.big_fan2_speed
    print()
    print(f"Progress: {s.gcode_state} ({s.print_type}) {s.mc_percent}%, {s.mc_remaining_time} minutes remaining")
    print(f"GCODE:  {s.gcode_file}{ f' ({s.subtask_name})' if s.gcode_file != f'{s.subtask_name}.gcode.3mf' else ''}, line {s.mc_print_line_number}")
    print(f"Layer:  {s.layer_num} / {s.total_layer_num}")
    print()
    print(f"WiFi:", s.wifi_signal)
    print(f"Lights:", s.lights_report[0].node, s.lights_report[0].mode)
    print()

# dump full info once on connection
def onconnect():
    time.sleep(1)
    bambu.dump_info()

# start watching mqtt messages
bambu.start_watch_client(callback, onconnect)

# suspend main thread and wait for cancellation
try: signal.pause()
except KeyboardInterrupt: pass
bambu.stop_watch_client()
