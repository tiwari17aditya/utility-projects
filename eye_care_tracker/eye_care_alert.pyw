import tkinter as tk
import time
import os
import json
import ctypes
from datetime import date

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("dwTime", ctypes.c_uint)]

class EyeCareAlert:
    def __init__(self):
        self.alert_interval_mins = 40 
        self.idle_threshold_seconds = 300 
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_file = os.path.join(script_dir, "screentime_data.json")

    def get_idle_seconds(self):
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0

    def load_data(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_data(self, data):
        with open(self.log_file, "w") as file:
            json.dump(data, file, indent=2)

    def add_one_minute(self):
        today = str(date.today())
        data = self.load_data()
        if today not in data:
            data[today] = 0
        data[today] += 1
        self.save_data(data)
        return data[today]

    def show_alert(self, total_minutes_today):
        hours, mins = divmod(total_minutes_today, 60)
        root = tk.Tk()
        root.title("Eye Care Alert")
        root.geometry("450x250")
        root.configure(bg="#2c3e50")
        root.eval('tk::PlaceWindow . center')
        root.attributes('-topmost', True)
        root.overrideredirect(True) 
        
        title_msg = "👀 Time for a Break! 👀"
        body_msg = (
            "Look at something 20 feet away for 20 seconds.\n\n"
            f"Total Active Screen Time Today:\n{hours} hours and {mins} minutes"
        )
        
        tk.Label(root, text=title_msg, font=("Helvetica", 18, "bold"), fg="#f1c40f", bg="#2c3e50").pack(pady=(30, 10))
        tk.Label(root, text=body_msg, font=("Helvetica", 14), fg="#ecf0f1", bg="#2c3e50", justify="center").pack(expand=True)
        tk.Button(root, text="I have rested my eyes", command=root.destroy, bg="#e74c3c", fg="white", font=("Helvetica", 12, "bold"), relief="flat", cursor="hand2", padx=20, pady=5).pack(pady=(0, 30))
        
        root.mainloop()

    def run(self):
        while True:
            time.sleep(60)
            if self.get_idle_seconds() < self.idle_threshold_seconds:
                total_today = self.add_one_minute()
                if total_today > 0 and total_today % self.alert_interval_mins == 0:
                    self.show_alert(total_today)

if __name__ == "__main__":
    app = EyeCareAlert()
    app.run()
