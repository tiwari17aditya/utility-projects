import tkinter as tk
import json
import os

class NativeDashboard:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_file = os.path.join(self.script_dir, "screentime_data.json")
        self.data = self.load_data()
        
        self.root = tk.Tk()
        self.root.title("Interactive Screen Time Stats")
        self.root.geometry("650x550")
        self.root.configure(bg="#2c3e50")
        self.root.eval('tk::PlaceWindow . center')
        
        tk.Label(self.root, text="📊 7-Day Screen Time Trends", font=("Helvetica", 18, "bold"), fg="#f1c40f", bg="#2c3e50").pack(pady=(20, 10))
        
        self.info_label = tk.Label(self.root, text="Hover over a bar to see details", font=("Helvetica", 14), fg="#ecf0f1", bg="#2c3e50")
        self.info_label.pack(pady=(0, 10))
        
        self.draw_chart()
        
        tk.Button(self.root, text="Close Dashboard", command=self.root.destroy, bg="#e74c3c", fg="white", font=("Helvetica", 12, "bold"), relief="flat", cursor="hand2", padx=20, pady=5).pack(pady=20)
        
        self.root.mainloop()

    def load_data(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return {}
        return {}

    def draw_chart(self):
        c_width = 550
        c_height = 300
        canvas = tk.Canvas(self.root, width=c_width, height=c_height, bg="#34495e", highlightthickness=0)
        canvas.pack()

        if not self.data:
            canvas.create_text(c_width/2, c_height/2, text="No data available yet.", fill="#ecf0f1", font=("Helvetica", 14))
            return

        sorted_dates = sorted(self.data.keys())[-7:]
        max_mins = max([self.data[d] for d in sorted_dates]) if self.data else 1
        
        if max_mins < 60:
            max_mins = 60 

        bar_width = 50
        spacing = (c_width - (len(sorted_dates) * bar_width)) / (len(sorted_dates) + 1)

        self.bars_info = {}
        for i, date_str in enumerate(sorted_dates):
            mins = self.data[date_str]
            hours, m = divmod(mins, 60)
            
            x0 = spacing + i * (bar_width + spacing)
            y0 = c_height - 30
            x1 = x0 + bar_width
            y1 = y0 - ((mins / max_mins) * (c_height - 60))
            
            bar_id = canvas.create_rectangle(x0, y0, x1, y1, fill="#3498db", outline="", tags="bar")
            
            display_date = date_str[-5:]
            canvas.create_text(x0 + (bar_width/2), y0 + 15, text=display_date, fill="#ecf0f1", font=("Helvetica", 10))
            
            self.bars_info[bar_id] = f"{date_str}: {hours}h {m}m ({mins} total mins)"
            
        canvas.tag_bind("bar", "<Enter>", lambda e, c=canvas: self.on_hover(e, c))
        canvas.tag_bind("bar", "<Leave>", lambda e, c=canvas: self.on_leave(e, c))

    def on_hover(self, event, canvas):
        item = canvas.find_withtag("current")[0]
        canvas.itemconfig(item, fill="#5dade2")
        self.info_label.config(text=self.bars_info[item], fg="#f1c40f")

    def on_leave(self, event, canvas):
        item = canvas.find_withtag("current")[0]
        canvas.itemconfig(item, fill="#3498db")
        self.info_label.config(text="Hover over a bar to see details", fg="#ecf0f1")

if __name__ == "__main__":
    NativeDashboard()
