import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
import threading
import time
import psutil
from collections import defaultdict
import win32gui
import win32process

class TesseractApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tesseract")
        self.root.geometry("1000x700")
        self.root.configure(bg='#e6f2f1')  # Earth-themed background
        self.root.resizable(True, True)
        
        self.data_file = "tesseract_data.json"
        self.app_usage = defaultdict(int)
        self.daily_usage = defaultdict(int)
        self.session_start = datetime.now()
        self.current_app = ""
        self.last_check = datetime.now()
        
        self.break_interval = 60
        self.break_reminder_active = False
        self.break_thread = None
        
        self.app_limits = {}
        self.is_tracking = True
        self.tracking_thread = None
        
        self.setup_styles()
        self.load_data()
        self.create_widgets()
        self.start_tracking()
        self.update_display()

    def setup_styles(self):
        # Earth-themed colors
        self.colors = {
            'bg': '#e6f2f1',            
            'surface': '#d1e8e2',       
            'primary': '#4a9c8c',       
            'accent': '#6cc5a1',        
            'text_primary': '#1b3b36',  
            'text_secondary': '#3b5e56',
            'success': '#27ae60',       
            'warning': '#f1c40f',       
            'danger': '#e74c3c'         
        }

        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Title.TLabel', 
                       foreground=self.colors['text_primary'],
                       background=self.colors['bg'],
                       font=('Segoe UI', 28, 'bold'))

        style.configure('Subtitle.TLabel',
                       foreground=self.colors['text_secondary'], 
                       background=self.colors['bg'],
                       font=('Segoe UI', 12))

        style.configure('Card.TFrame',
                       background=self.colors['surface'],
                       relief='flat',
                       borderwidth=1)

        style.configure('CardTitle.TLabel',
                       foreground=self.colors['text_primary'],
                       background=self.colors['surface'],
                       font=('Segoe UI', 14, 'bold'))

        style.configure('BigNumber.TLabel',
                       foreground=self.colors['accent'],
                       background=self.colors['surface'],
                       font=('Segoe UI', 36, 'bold'))

        style.configure('Custom.TNotebook',
                       background=self.colors['bg'],
                       borderwidth=0)

        style.configure('Custom.TNotebook.Tab',
                       background=self.colors['surface'],
                       foreground=self.colors['text_secondary'],
                       padding=[20, 10],
                       font=('Segoe UI', 11))

        style.map('Custom.TNotebook.Tab',
                  background=[('selected', self.colors['primary'])],
                  foreground=[('selected', self.colors['text_primary'])])

        style.configure('TProgressbar', 
                        troughcolor=self.colors['surface'], 
                        background=self.colors['primary'], 
                        thickness=20)

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.app_usage = defaultdict(int, data.get('app_usage', {}))
                    self.daily_usage = defaultdict(int, data.get('daily_usage', {}))
                    self.app_limits = data.get('app_limits', {})
                    self.break_interval = data.get('break_interval', 60)
        except:
            pass

    def save_data(self):
        try:
            data = {
                'app_usage': dict(self.app_usage),
                'daily_usage': dict(self.daily_usage),
                'app_limits': self.app_limits,
                'break_interval': self.break_interval,
                'last_saved': datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def get_active_window(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                return process.name()
        except:
            return "Unknown"
        return "Unknown"

    def track_usage(self):
        while self.is_tracking:
            try:
                current_app = self.get_active_window()
                current_time = datetime.now()
                time_diff = (current_time - self.last_check).total_seconds()
                if current_app and time_diff < 5:
                    self.app_usage[current_app] += time_diff
                    today = current_time.strftime("%Y-%m-%d")
                    self.daily_usage[today] += time_diff
                    self.check_app_limits(current_app)
                self.current_app = current_app
                self.last_check = current_time
                if int(time_diff) % 30 == 0:
                    self.save_data()
            except:
                pass
            time.sleep(1)

    def check_app_limits(self, app_name):
        if app_name in self.app_limits:
            usage_minutes = self.app_usage[app_name] / 60
            limit_minutes = self.app_limits[app_name]
            if usage_minutes > limit_minutes and usage_minutes % 5 < 0.1:
                self.show_limit_warning(app_name, limit_minutes)

    def show_limit_warning(self, app_name, limit):
        messagebox.showwarning(
            "Time's Up! ⏰",
            f"You've been using {app_name} for over {limit} minutes today.\nMaybe time for a break? 🌿"
        )

    def start_tracking(self):
        if not self.tracking_thread or not self.tracking_thread.is_alive():
            self.tracking_thread = threading.Thread(target=self.track_usage, daemon=True)
            self.tracking_thread.start()

    def format_time(self, seconds):
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m"
        else:
            hours = int(seconds/3600)
            minutes = int((seconds % 3600)/60)
            return f"{hours}h {minutes}m"

    def get_total_screen_time_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self.daily_usage.get(today, 0)

    def create_widgets(self):
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        header_frame = tk.Frame(main_container, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 30))
        title_label = ttk.Label(header_frame, text="Tesseract", style='Title.TLabel')
        title_label.pack()
        subtitle = ttk.Label(header_frame, text="Your Digital Wellness Dashboard", style='Subtitle.TLabel')
        subtitle.pack(pady=(5, 0))
        self.notebook = ttk.Notebook(main_container, style='Custom.TNotebook')
        self.notebook.pack(fill='both', expand=True)
        self.create_dashboard_tab()
        self.create_limits_tab()
        self.create_settings_tab()

    # --- Card Helper ---
    def create_card_frame(self, parent, title):
        card = tk.Frame(parent, bg=self.colors['surface'], relief='solid', bd=1)
        card.pack(fill='both', expand=True, padx=10, pady=10)
        title_frame = tk.Frame(card, bg=self.colors['surface'])
        title_frame.pack(fill='x', padx=20, pady=(20, 10))
        title_label = tk.Label(title_frame, text=title, 
                              bg=self.colors['surface'], 
                              fg=self.colors['text_primary'],
                              font=('Segoe UI', 14, 'bold'))
        title_label.pack(anchor='w')
        content_frame = tk.Frame(card, bg=self.colors['surface'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        return content_frame

    # --- Dashboard Tab ---
    def create_dashboard_tab(self):
        dashboard_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(dashboard_frame, text="  Dashboard  ")
        top_row = tk.Frame(dashboard_frame, bg=self.colors['bg'])
        top_row.pack(fill='x', pady=10)
        left_col = tk.Frame(top_row, bg=self.colors['bg'])
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 5))
        right_col = tk.Frame(top_row, bg=self.colors['bg'])
        right_col.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Today's Screen Time
        screen_time_card = self.create_card_frame(left_col, "Today's Screen Time")
        self.total_time_label = tk.Label(screen_time_card, text="0h 0m",
                                        bg=self.colors['surface'],
                                        fg=self.colors['accent'],
                                        font=('Segoe UI', 42, 'bold'))
        self.total_time_label.pack(pady=30)
        self.time_progress = ttk.Progressbar(screen_time_card, length=300, mode='determinate')
        self.time_progress.pack(pady=(0, 20))

        # Current App
        current_card = self.create_card_frame(right_col, "Right Now")
        self.current_app_label = tk.Label(current_card, text="Starting up...",
                                         bg=self.colors['surface'],
                                         fg=self.colors['text_secondary'],
                                         font=('Segoe UI', 16),
                                         wraplength=250)
        self.current_app_label.pack(pady=40)

        # Most Used Apps
        apps_card = self.create_card_frame(dashboard_frame, "Most Used Apps Today")
        self.app_listbox = tk.Listbox(apps_card,
                                     bg=self.colors['surface'],
                                     fg=self.colors['text_primary'],
                                     selectbackground=self.colors['accent'],
                                     font=('Segoe UI', 11),
                                     bd=0,
                                     highlightthickness=0,
                                     activestyle='none')
        self.app_listbox.pack(fill='both', expand=True)

    # --- Limits Tab ---
    def create_limits_tab(self):
        limits_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(limits_frame, text="  App Limits  ")
        add_card = self.create_card_frame(limits_frame, "Set New Limit")
        input_frame = tk.Frame(add_card, bg=self.colors['surface'])
        input_frame.pack(fill='x', pady=20)

        tk.Label(input_frame, text="App Name:", 
                bg=self.colors['surface'], 
                fg=self.colors['text_primary'],
                font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        self.app_name_entry = tk.Entry(input_frame,
                                      bg=self.colors['primary'],
                                      fg=self.colors['text_primary'],
                                      font=('Segoe UI', 11),
                                      bd=0,
                                      insertbackground=self.colors['text_primary'])
        self.app_name_entry.pack(fill='x', ipady=8, pady=(0, 15))

        tk.Label(input_frame, text="Time Limit (minutes):", 
                bg=self.colors['surface'], 
                fg=self.colors['text_primary'],
                font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        self.time_limit_entry = tk.Entry(input_frame,
                                        bg=self.colors['primary'],
                                        fg=self.colors['text_primary'],
                                        font=('Segoe UI', 11),
                                        bd=0,
                                        insertbackground=self.colors['text_primary'])
        self.time_limit_entry.pack(fill='x', ipady=8, pady=(0, 15))

        set_btn = tk.Button(input_frame, text="Set Limit",
                           bg=self.colors['accent'],
                           fg=self.colors['text_primary'],
                           font=('Segoe UI', 11, 'bold'),
                           bd=0,
                           pady=10,
                           cursor='hand2',
                           command=self.set_app_limit)
        set_btn.pack(fill='x')

        current_card = self.create_card_frame(limits_frame, "Current Limits")
        self.limits_listbox = tk.Listbox(current_card,
                                        bg=self.colors['surface'],
                                        fg=self.colors['text_primary'],
                                        selectbackground=self.colors['accent'],
                                        font=('Segoe UI', 11),
                                        bd=0,
                                        highlightthickness=0,
                                        activestyle='none')
        self.limits_listbox.pack(fill='both', expand=True, pady=(0, 10))

        remove_btn = tk.Button(current_card, text="Remove Selected",
                              bg=self.colors['danger'],
                              fg=self.colors['text_primary'],
                              font=('Segoe UI', 10),
                              bd=0,
                              pady=8,
                              cursor='hand2',
                              command=self.remove_app_limit)
        remove_btn.pack(fill='x')

    # --- Settings Tab ---
    def create_settings_tab(self):
        settings_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(settings_frame, text="  Settings  ")
        break_card = self.create_card_frame(settings_frame, "Break Reminders")
        tk.Label(break_card, text="Reminder Interval (minutes):",
                bg=self.colors['surface'],
                fg=self.colors['text_primary'],
                font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))

        self.break_interval_var = tk.StringVar(value=str(self.break_interval))
        interval_entry = tk.Entry(break_card,
                                 textvariable=self.break_interval_var,
                                 bg=self.colors['primary'],
                                 fg=self.colors['text_primary'],
                                 font=('Segoe UI', 11),
                                 bd=0,
                                 insertbackground=self.colors['text_primary'])
        interval_entry.pack(fill='x', ipady=8, pady=(0, 15))

        self.break_button = tk.Button(break_card, text="Start Reminders",
                                     bg=self.colors['success'],
                                     fg=self.colors['text_primary'],
                                     font=('Segoe UI', 11, 'bold'),
                                     bd=0,
                                     pady=10,
                                     cursor='hand2',
                                     command=self.toggle_break_reminders)
        self.break_button.pack(fill='x', pady=(0, 10))

        data_card = self.create_card_frame(settings_frame, "Data Management")
        export_btn = tk.Button(data_card, text="Export Data",
                              bg=self.colors['primary'],
                              fg=self.colors['text_primary'],
                              font=('Segoe UI', 10),
                              bd=0,
                              pady=8,
                              cursor='hand2',
                              command=self.export_data)
        export_btn.pack(fill='x', pady=5)

        clear_btn = tk.Button(data_card, text="Clear All Data",
                             bg=self.colors['danger'],
                             fg=self.colors['text_primary'],
                             font=('Segoe UI', 10),
                             bd=0,
                             pady=8,
                             cursor='hand2',
                             command=self.clear_data)
        clear_btn.pack(fill='x', pady=5)

    # --- App Limit Functions ---
    def set_app_limit(self):
        app_name = self.app_name_entry.get().strip()
        time_limit = self.time_limit_entry.get().strip()
        if not app_name or not time_limit:
            messagebox.showerror("Oops!", "Please fill in both fields")
            return
        try:
            limit_minutes = int(time_limit)
            if limit_minutes <= 0:
                raise ValueError("Must be positive")
            self.app_limits[app_name] = limit_minutes
            self.save_data()
            messagebox.showinfo("Done!", f"Set {limit_minutes} minute limit for {app_name}")
            self.app_name_entry.delete(0, tk.END)
            self.time_limit_entry.delete(0, tk.END)
            self.update_limits_display()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number")

    def remove_app_limit(self):
        selection = self.limits_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an app to remove")
            return
        selected_text = self.limits_listbox.get(selection[0])
        app_name = selected_text.split(' - ')[0]
        if app_name in self.app_limits:
            del self.app_limits[app_name]
            self.save_data()
            self.update_limits_display()
            messagebox.showinfo("Removed", f"Removed limit for {app_name}")

    # --- Break Reminders ---
    def toggle_break_reminders(self):
        if not self.break_reminder_active:
            try:
                self.break_interval = int(self.break_interval_var.get())
                if self.break_interval <= 0:
                    raise ValueError("Must be positive")
                self.break_reminder_active = True
                self.break_button.config(text="Stop Reminders", bg=self.colors['warning'])
                self.start_break_reminders()
                messagebox.showinfo("Started!", f"Break reminders every {self.break_interval} minutes")
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number")
        else:
            self.break_reminder_active = False
            self.break_button.config(text="Start Reminders", bg=self.colors['success'])
            messagebox.showinfo("Stopped", "Break reminders disabled")

    def start_break_reminders(self):
        def reminder_loop():
            while self.break_reminder_active:
                time.sleep(self.break_interval * 60)
                if self.break_reminder_active:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Break Time! 🌿", 
                        f"You've been focused for {self.break_interval} minutes.\nTime to stretch and rest your eyes!"
                    ))
        self.break_thread = threading.Thread(target=reminder_loop, daemon=True)
        self.break_thread.start()

    # --- Data Management ---
    def export_data(self):
        try:
            data = {
                'app_usage': dict(self.app_usage),
                'daily_usage': dict(self.daily_usage),
                'app_limits': self.app_limits,
                'break_interval': self.break_interval
            }
            export_file = f"tesseract_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Export Successful", f"Data exported to {export_file}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Couldn't export data:\n{e}")

    def clear_data(self):
        if messagebox.askyesno("Are you sure?", "This will delete all your tracking data. This can't be undone!"):
            self.app_usage.clear()
            self.daily_usage.clear()
            self.app_limits.clear()
            self.save_data()
            messagebox.showinfo("Cleared", "All data has been cleared")
            self.update_display()

    # --- Display Updates ---
    def update_display(self):
        try:
            total_seconds = self.get_total_screen_time_today()
            self.total_time_label.config(text=self.format_time(total_seconds))
            progress_value = min((total_seconds / (8 * 3600)) * 100, 100)
            self.time_progress['value'] = progress_value
            if self.current_app and self.current_app != "Unknown":
                display_name = self.current_app.replace('.exe', '').title()
                self.current_app_label.config(text=f"Using {display_name}")
            else:
                self.current_app_label.config(text="Not tracking")
            self.app_listbox.delete(0, tk.END)
            sorted_apps = sorted(self.app_usage.items(), key=lambda x: x[1], reverse=True)
            for i, (app, seconds) in enumerate(sorted_apps[:8]):
                display_name = app.replace('.exe', '').title()
                time_str = self.format_time(seconds)
                self.app_listbox.insert(tk.END, f"{display_name} - {time_str}")
                if seconds > 3600:
                    self.app_listbox.itemconfig(i, bg=self.colors['warning'])
                elif seconds > 1800:
                    self.app_listbox.itemconfig(i, bg=self.colors['primary'])
            self.update_limits_display()
        except:
            pass
        self.root.after(1000, self.update_display)

    def update_limits_display(self):
        try:
            self.limits_listbox.delete(0, tk.END)
            for app, limit in self.app_limits.items():
                used_seconds = self.app_usage.get(app, 0)
                used_minutes = int(used_seconds / 60)
                status = "✅" if used_minutes <= limit else "⚠️"
                display_name = app.replace('.exe', '').title()
                self.limits_listbox.insert(tk.END, f"{display_name} - {limit}m limit ({used_minutes}m used) {status}")
        except:
            pass

    def on_closing(self):
        self.is_tracking = False
        self.break_reminder_active = False
        self.save_data()
        self.root.destroy()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    try:
        import psutil
        import win32gui
        import win32process
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("\nInstall with: pip install psutil pywin32")
        exit(1)
    
    app = TesseractApp()
    app.run()
