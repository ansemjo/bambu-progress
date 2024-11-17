import os, subprocess, dotenv, time
import urllib.request as request
from bambu_connect import BambuClient, PrinterStatus
from dateutil.relativedelta import relativedelta as delta
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Header, Label, ProgressBar


# get connection details from env (hostname, access code, serial)
dotenv.load_dotenv()
HOSTNAME = os.environ.get("BAMBU_HOSTNAME")
ACCESS_CODE = os.environ.get("BAMBU_ACCESS_CODE")
SERIAL = os.environ.get("BAMBU_SERIAL")
NTFY_TOPIC = os.environ.get("BAMBU_NTFY_TOPIC")
bambu = BambuClient(HOSTNAME, ACCESS_CODE, SERIAL)

# textual application window
class BambuProgress(App):

    TITLE = f"Bambu Progress ({HOSTNAME}) "

    CSS = """
    Container { margin-left: 2; margin-top: 1; }
    .thin { height: auto; }
    #gauges { width: 70; }
    #printstatus { height: 3; }
    .nozzle .bar--bar, .nozzle .bar--complete { color: red; }
    .hotbed .bar--bar, .hotbed .bar--complete { color: orange; }
    .fan .bar--bar, .fan .bar--complete { color: lightblue; }
    #progress .bar--bar { color: green; }
    #layers .bar--bar { color: darkgreen; }
    #sequence { color: gray; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon="☰")
        with VerticalScroll(classes="thin"):

            with Container(id="printstatus"):
                with Horizontal():
                    yield Label("Status  ")
                    # s.gcode_state (s.print_type) s.subtask_name
                    yield Label("", id="status")
                    yield Label("waiting", id="sequence")
                with Horizontal():
                    # s.mc_percent (s.mc_remaining_time)
                    yield Label("Total   ")
                    yield ProgressBar(id="progress", total=100, show_eta=False, show_percentage=True)
                    yield Label(" ")
                    yield Label("", id="remaining") # s.mc_remaining_time minutes
                with Horizontal():
                    # s.(total_)layer_num, line s.mc_print_line_number
                    yield Label("Layer   ")
                    yield ProgressBar(id="layers", total=1, show_eta=False, show_percentage=False)
                    yield Label(" ")
                    yield Label("", id="layertext")

            with Horizontal(id="gauges"):
                with Container(id="temperatures"):
                    yield ProgressBar(classes="nozzle", total=300, show_eta=False, show_percentage=False)
                    yield Label("Nozzle", classes="nozzle")
                    yield ProgressBar(classes="hotbed", total=300, show_eta=False, show_percentage=False)
                    yield Label("Hotbed", classes="hotbed")
                with Container(): # fans
                    yield ProgressBar(classes="heatbreak fan", total=15, show_eta=False, show_percentage=False)
                    yield Label("Nozzle Fan", classes="heatbreak")
                    yield ProgressBar(classes="cooling fan", total=15, show_eta=False, show_percentage=False)
                    yield Label("Cooling Fan", classes="cooling")

    def update_progress(self, s: PrinterStatus):
        # status text, task name and line number
        status = f"{s.gcode_state} ({s.print_type})  {s.subtask_name}"
        self.query_one("#status").update(status)
        # progress bar in total percent
        self.query_one("#progress").update(progress=s.mc_percent)
        # remaining time calculated from minutes
        dt = delta(minutes=int(s.mc_remaining_time))
        if dt.hours > 0: hm = f"{dt.hours}:{dt.minutes:02d}h"
        elif dt.minutes > 0: hm = f"{dt.minutes:02d} min"
        else: hm = None
        self.query_one("#remaining").update(f"({hm} remaining)" if hm else "")
        # layer progress bar and gcode line
        self.query_one("#layers").update(progress=s.layer_num, total=s.total_layer_num)
        self.query_one("#layertext").update(f"{s.layer_num} / {s.total_layer_num}, line {s.mc_print_line_number}")

    def update_temperatures(self, s: PrinterStatus):
        nz, nzt, hb, hbt = s.nozzle_temper, s.nozzle_target_temper, s.bed_temper, s.bed_target_temper
        # nozzle temperature
        self.query_one("ProgressBar.nozzle").update(progress=nz)
        self.query_one("Label.nozzle").update(f"Nozzle     {nz:5.1f} / {nzt:5.1f} °C")
        # hotbed temperature
        self.query_one("ProgressBar.hotbed").update(progress=hb)
        self.query_one("Label.hotbed").update(f"Hotbed     {hb:5.1f} / {hbt:5.1f} °C")

    def update_fans(self, s: PrinterStatus):
        heatbreak, cooling = int(s.heatbreak_fan_speed), int(s.cooling_fan_speed)
        # nozzle fan speed
        self.query_one("ProgressBar.heatbreak").update(progress=heatbreak)
        self.query_one("Label.heatbreak").update(f"Nozzle Fan   {heatbreak:2d}")
        # cooling fan speed
        self.query_one("ProgressBar.cooling").update(progress=cooling)
        self.query_one("Label.cooling").update(f"Cooling Fan  {cooling:2d}")

    # send a notification when the print is done
    laststate = None
    def notify_done(self, s: PrinterStatus):
        old, new = self.laststate, s.gcode_state
        if old != None and old != new and new == "FINISH":
            message = f"Your print {s.subtask_name!r} is done."
            # desktop notification
            subprocess.Popen(["notify-send", "--app-name=bambu-progress", "Finished printing", message])
            if NTFY_TOPIC:
                # optional ntfy.sh message
                request.urlopen(request.Request(f"https://ntfy.sh/{NTFY_TOPIC}", message.encode("utf-8"), headers={ "content-type": "text/plain" }))
        self.laststate = new

    def update_all(self, s: PrinterStatus):
        self.query_one("#sequence").update(f"  {s.sequence_id}")
        # ignore updates before dump_info returned once
        if s.gcode_state is None: return
        self.update_progress(s)
        self.update_temperatures(s)
        self.update_fans(s)
        self.notify_done(s)


app = BambuProgress()

# dump full info once on connection
def onconnect():
    bambu.dump_info()
    time.sleep(1)
    bambu.dump_info()

bambu.start_watch_client(app.update_all, onconnect)
try: app.run()
finally: bambu.stop_watch_client()
