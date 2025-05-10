import pyautogui
import time
import threading
import pickle
import os
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard
from datetime import datetime

DEFAULT_CONFIG = {
    'golden_toggle_key': 'f8',
    'golden_check_interval_sec': 0,
    'golden_check_interval_ms': 500,
    'golden_confidence': 0.80,
    'golden_image_path': 'golden_cookie.png',
    'golden_cookies_clicked_total': 0,
    
    'big_toggle_key': 'f9',
    'big_check_interval_sec': 0,
    'big_check_interval_ms': 0,
    'big_confidence': 0.80,
    'big_image_path': 'big_cookie.png',
    'big_cookies_clicked_total': 0
}
CONFIG_FILE = 'cccc-data.pkl'

class CookieClickerBot:
    def __init__(self):
        self.golden_running = False
        self.big_running = False
        self.stop_event = threading.Event()
        
        self.golden_cookies_clicked_session = 0
        self.golden_cookies_clicked_total = 0
        self.big_cookies_clicked_session = 0
        self.big_cookies_clicked_total = 0
        
        self.config = self.load_config()
        self.golden_cookies_clicked_total = self.config['golden_cookies_clicked_total']
        self.big_cookies_clicked_total = self.config['big_cookies_clicked_total']
        
        self.golden_status_label = None
        self.big_status_label = None
        self.golden_toggle_button = None
        self.big_toggle_button = None
        self.golden_session_counter_label = None
        self.golden_total_counter_label = None
        self.big_session_counter_label = None
        self.big_total_counter_label = None
        
        self.golden_watcher_thread = None
        self.big_clicker_thread = None
        self.keyboard_listener = None
        
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'rb') as f:
                    loaded_config = pickle.load(f)
                    
                config = DEFAULT_CONFIG.copy() # set defaults in case of missing keys
                for key, value in loaded_config.items():
                    if key in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()
    
    def save_config(self, show_confirmation=True):
        try:
            self.config['golden_cookies_clicked_total'] = self.golden_cookies_clicked_total
            self.config['big_cookies_clicked_total'] = self.big_cookies_clicked_total
            
            with open(CONFIG_FILE, 'wb') as f:
                pickle.dump(self.config, f)
                
            if show_confirmation:
                messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!")
            return True
        except Exception as e:
            if show_confirmation:
                messagebox.showerror("Save Error", f"Could not save settings: {e}")
            print(f"Error saving config: {e}")
            return False
    
    def toggle_golden_bot(self):
        self.golden_running = not self.golden_running
        self.update_status_display()
        status = "ON" if self.golden_running else "OFF"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Golden Cookie detection toggled {status}")
    
    def toggle_big_bot(self):
        self.big_running = not self.big_running
        self.update_status_display()
        status = "ON" if self.big_running else "OFF"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Big Cookie clicking toggled {status}")
    
    def update_status_display(self):
        if self.golden_status_label:
            status_text = "ON" if self.golden_running else "OFF"
            status_color = "#4CAF50" if self.golden_running else "#F44336"  # Green or Red
            self.golden_status_label.config(text=status_text, foreground=status_color)
            
        if self.big_status_label:
            status_text = "ON" if self.big_running else "OFF"
            status_color = "#4CAF50" if self.big_running else "#F44336"  # Green or Red
            self.big_status_label.config(text=status_text, foreground=status_color)
            
        if self.golden_toggle_button:
            button_text = "Turn OFF" if self.golden_running else "Turn ON"
            self.golden_toggle_button.config(text=button_text)
            
        if self.big_toggle_button:
            button_text = "Turn OFF" if self.big_running else "Turn ON"
            self.big_toggle_button.config(text=button_text)
    
    def format_count_display(self, count):
        if count < 1000:  # exact for <1k
            return str(count)
        
        if count < 100000:  # Thousands (k) w/ dp
            return f"{count / 1000:.1f}k".replace('.0k', 'k')
        
        if count < 1000000:  # Thousands (k) no dp
            return f"{count / 1000:.0f}k"
        
        if count < 100000000:  # Millions (m) w/ dp
            return f"{count / 1000000:.1f}m".replace('.0m', 'm')
            
        if count < 1000000000:  # Millions (m) no dp
            return f"{count / 1000000:.0f}m"
            
        if count < 100000000000:  # Billions (b) w/ dp
            return f"{count / 1000000000:.1f}b".replace('.0b', 'b')
            
        if count < 1000000000000:  # Billions (b) no dp
            return f"{count / 1000000000:.0f}b"
            
        if count < 100000000000000:  # Trillions (t) w/ dp
            return f"{count / 1000000000000:.1f}t".replace('.0t', 't')
            
        if count < 1000000000000000:  # Trillions (t) no dp
            return f"{count / 1000000000000:.0f}t"
        
        # e notation
        magnitude = 0
        temp_count = count
        while temp_count >= 10:
            magnitude += 1
            temp_count /= 10
            
        return f"{temp_count:.1f}e{magnitude}".replace('.0e', 'e')

    def update_counter_display(self):
        if self.golden_session_counter_label and self.golden_total_counter_label:
            session_text = self.format_count_display(self.golden_cookies_clicked_session)
            total_text = self.format_count_display(self.golden_cookies_clicked_total)
            
            self.golden_session_counter_label.config(text=session_text)
            self.golden_total_counter_label.config(text=total_text)
            
        if self.big_session_counter_label and self.big_total_counter_label:
            session_text = self.format_count_display(self.big_cookies_clicked_session)
            total_text = self.format_count_display(self.big_cookies_clicked_total)
            
            self.big_session_counter_label.config(text=session_text)
            self.big_total_counter_label.config(text=total_text)
    
    def on_key_press(self, key):
        try:
            if hasattr(key, 'name'):
                golden_toggle_key = self.config['golden_toggle_key'].lower()
                if key.name.lower() == golden_toggle_key.lower():
                    self.toggle_golden_bot()
                
                big_toggle_key = self.config['big_toggle_key'].lower()
                if key.name.lower() == big_toggle_key.lower():
                    self.toggle_big_bot()
        except AttributeError:
            pass
    
    def golden_cookie_watcher(self):
        while not self.stop_event.is_set():
            if self.golden_running:
                try:
                    location = pyautogui.locateCenterOnScreen(self.config['golden_image_path'], confidence=self.config['golden_confidence'])
                    
                    if location:
                        self.golden_cookies_clicked_session += 1
                        self.golden_cookies_clicked_total += 1
                        self.update_counter_display()
                        
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Found golden cookie at {location} (Session: {self.golden_cookies_clicked_session}, Total: {self.golden_cookies_clicked_total})")
                        
                        big_cookie_was_running = self.big_running # store big cookie clicker status
                        
                        original_pos = pyautogui.position()
                        pyautogui.click(location)
                        pyautogui.moveTo(original_pos)
                        
                        if big_cookie_was_running != self.big_running: # restore big cookie state
                            print(f"[{timestamp}] Restoring big cookie clicker state to {big_cookie_was_running}")
                            self.big_running = big_cookie_was_running
                            self.update_status_display()
                        
                        self.save_config(show_confirmation=False)
                        
                except Exception as e:
                    print(f"Golden cookie error: {e}")
            
            total_interval = self.config['golden_check_interval_sec'] + (self.config['golden_check_interval_ms'] / 1000)
            time.sleep(max(0.1, total_interval))
    
    def big_cookie_clicker(self):
        big_cookie_position = None
        click_threads = []
        should_click = False
        click_count_lock = threading.Lock()
        start_time = 0  # To track when clicking started
        
        # Create worker threads for clicking
        def click_worker(worker_id):
            local_count = 0
            while not self.stop_event.is_set() and self.big_running and should_click:
                try:
                    pyautogui.click()
                    local_count += 1
                    
                    if local_count >= 125:
                        with click_count_lock:
                            self.big_cookies_clicked_session += local_count
                            self.big_cookies_clicked_total += local_count
                        
                        local_count = 0
                        
                        # limit ui updates
                        if time.time() * 10 % 2 < 0.1:  # ~5% chance to update UI
                            self.update_counter_display()
                        
                except Exception:
                    pass
        
        click_thread_count = 100 if self.config['big_check_interval_sec'] == 0 and self.config['big_check_interval_ms'] == 0 else 1
        
        while not self.stop_event.is_set():
            if self.big_running:
                try:
                    
                    if big_cookie_position is None:
                        location = pyautogui.locateCenterOnScreen(self.config['big_image_path'], confidence=self.config['big_confidence'])
                        
                        if location:
                            big_cookie_position = location
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"[{timestamp}] Big cookie found at {big_cookie_position}")

                            pyautogui.moveTo(big_cookie_position)
                            print(f"[{timestamp}] Mouse positioned for continuous clicking")
                            
                            start_time = time.time()
                            print(f"[{timestamp}] Starting {click_thread_count} click thread(s)")
                    
                    if big_cookie_position:
                        current_position = pyautogui.position()
                        
                        position_difference = (
                            abs(current_position.x - big_cookie_position[0]),
                            abs(current_position.y - big_cookie_position[1])
                        )
                        
                        # stop clicking if mouse moved significantly
                        if (time.time() - start_time > 0.5 and
                            (position_difference[0] > 10 or position_difference[1] > 10)):
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"[{timestamp}] Mouse moved by user, stopping big cookie clicker")
                            self.toggle_big_bot()
                            continue
                        
                        # start threads if not already
                        if not click_threads:
                            should_click = True
                            for i in range(click_thread_count):
                                thread = threading.Thread(target=click_worker, args=(i,))
                                thread.daemon = True
                                thread.start()
                                click_threads.append(thread)
                        
                        # Periodically save counters
                        if (self.big_cookies_clicked_session // 500) > ((self.big_cookies_clicked_session - 10) // 500):
                            self.save_config(show_confirmation=False)
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"[{timestamp}] Big cookie clicks: Session: {self.big_cookies_clicked_session}, Total: {self.big_cookies_clicked_total}")
                                
                except Exception as e:
                    print(f"Big cookie error: {e}")
            else:
                # if not clicking stop all threads
                if click_threads:
                    with click_count_lock:
                        should_click = False
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] Stopping click threads")
                        click_threads = []
                        self.update_counter_display()
                
                # reset position to force rescan on next start
                big_cookie_position = None
                start_time = 0
            
            time.sleep(0.05)
    
    def start_bot_threads(self):
        if (self.golden_watcher_thread and self.golden_watcher_thread.is_alive()) or \
           (self.big_clicker_thread and self.big_clicker_thread.is_alive()):
            self.stop_event.set()
            if self.golden_watcher_thread:
                self.golden_watcher_thread.join(timeout=1)
            if self.big_clicker_thread:
                self.big_clicker_thread.join(timeout=1)
            self.stop_event.clear()
        
        self.golden_watcher_thread = threading.Thread(target=self.golden_cookie_watcher)
        self.golden_watcher_thread.daemon = True
        self.golden_watcher_thread.start()
        
        self.big_clicker_thread = threading.Thread(target=self.big_cookie_clicker)
        self.big_clicker_thread.daemon = True
        self.big_clicker_thread.start()
        
        # Start keyboard listener if needed
        if not self.keyboard_listener or not self.keyboard_listener.is_alive():
            self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
            self.keyboard_listener.start()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Press {self.config['golden_toggle_key'].upper()} to toggle Golden Cookie detection ON/OFF.")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Press {self.config['big_toggle_key'].upper()} to toggle Big Cookie clicking ON/OFF.")
    
    def reset_session_counter(self, cookie_type):
        if cookie_type == 'golden':
            self.golden_cookies_clicked_session = 0
        else:  # big
            self.big_cookies_clicked_session = 0
        self.update_counter_display()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {cookie_type.capitalize()} cookie session counter reset to 0")
    
    def reset_total_counter(self, cookie_type):
        if cookie_type == 'golden':
            self.golden_cookies_clicked_total = 0
        else:  # big
            self.big_cookies_clicked_total = 0
        self.update_counter_display()
        self.save_config(show_confirmation=False)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {cookie_type.capitalize()} cookie total counter reset to 0")
    
    def save_settings_from_gui(self, vars_dict, cookie_type):
        try:
            f_key_number = int(vars_dict[f'{cookie_type}_f_key_number'].get())
            if 1 <= f_key_number <= 24:
                self.config[f'{cookie_type}_toggle_key'] = f'f{f_key_number}'
                
            self.config[f'{cookie_type}_check_interval_sec'] = int(vars_dict[f'{cookie_type}_interval_sec'].get())
            self.config[f'{cookie_type}_check_interval_ms'] = int(vars_dict[f'{cookie_type}_interval_ms'].get())
            self.config[f'{cookie_type}_confidence'] = float(vars_dict[f'{cookie_type}_confidence'].get())
            
            self.save_config()
            
            # Restart the bot threads with new settings
            self.start_bot_threads()
        except ValueError as e:
            messagebox.showerror("Invalid Value", f"Please check your input values: {e}")
    
    def create_gui(self):
        root = tk.Tk()
        root.title("Cookie Clicker Cookie Clicker")
        root.geometry("500x620") # still too small on windows vm
        root.resizable(True, True)
        
        current_golden_f_num = self._extract_f_num(self.config['golden_toggle_key'], 8)
        current_big_f_num = self._extract_f_num(self.config['big_toggle_key'], 9)
        
        vars_dict = {
            'golden_confidence': tk.StringVar(value=f"{self.config['golden_confidence']:.2f}"),
            'golden_interval_sec': tk.StringVar(value=str(self.config['golden_check_interval_sec'])),
            'golden_interval_ms': tk.StringVar(value=str(self.config['golden_check_interval_ms'])),
            'golden_f_key_number': tk.StringVar(value=str(current_golden_f_num)),
            
            'big_confidence': tk.StringVar(value=f"{self.config['big_confidence']:.2f}"),
            'big_interval_sec': tk.StringVar(value=str(self.config['big_check_interval_sec'])),
            'big_interval_ms': tk.StringVar(value=str(self.config['big_check_interval_ms'])),
            'big_f_key_number': tk.StringVar(value=str(current_big_f_num)),
        }
        
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # head
        ttk.Label(main_frame, text="Cookie Clicker Cookie Clicker", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 15))
        
        # sub
        ttk.Label(main_frame, text="Turn off Fancy Graphics in the game's settings for\nGolden Cookie detection to function properly.", 
                font=("Arial", 10)).grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
        # tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        golden_tab = ttk.Frame(notebook, padding=5)
        big_tab = ttk.Frame(notebook, padding=5)
        
        notebook.add(golden_tab, text="Golden Cookie")
        notebook.add(big_tab, text="Big Cookie")
        
        self._create_settings_widgets(golden_tab, 'golden', vars_dict)
        self._create_settings_widgets(big_tab, 'big', vars_dict)
        
        # Status and toggle buttons for both (always visible)
        status_frame = ttk.LabelFrame(main_frame, text="Cookie Detection Status")
        status_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky="ew")
        
        # Golden cookie status
        golden_status_frame = ttk.Frame(status_frame)
        golden_status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(golden_status_frame, text="Golden Cookie detection: ").pack(side=tk.LEFT)
        self.golden_status_label = ttk.Label(golden_status_frame, text="OFF", foreground="#F44336", font=("Arial", 10, "bold"))
        self.golden_status_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Golden cookie toggle button
        self.golden_toggle_button = ttk.Button(golden_status_frame, text="Turn ON", command=self.toggle_golden_bot, width=10)
        self.golden_toggle_button.pack(side=tk.LEFT)
        
        # Big cookie status
        big_status_frame = ttk.Frame(status_frame)
        big_status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(big_status_frame, text="Big Cookie clicking: ").pack(side=tk.LEFT, padx=(0, 28))  # Added extra padding for alignment
        self.big_status_label = ttk.Label(big_status_frame, text="OFF", foreground="#F44336", font=("Arial", 10, "bold"))
        self.big_status_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Big cookie toggle button
        self.big_toggle_button = ttk.Button(big_status_frame, text="Turn ON", command=self.toggle_big_bot, width=10)
        self.big_toggle_button.pack(side=tk.LEFT)
        
        # Cookie counters section
        counter_frame = ttk.LabelFrame(main_frame, text="Cookie Counters")
        counter_frame.grid(row=4, column=0, columnspan=3, pady=10, sticky="ew")
        
        # Golden cookie counters
        golden_counter_frame = ttk.Frame(counter_frame)
        golden_counter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(golden_counter_frame, text="Golden Cookies:").pack(side=tk.LEFT)
        
        # Session counter
        ttk.Label(golden_counter_frame, text="Session:").pack(side=tk.LEFT, padx=(10, 0))
        self.golden_session_counter_label = ttk.Label(golden_counter_frame, 
                                                text=self.format_count_display(self.golden_cookies_clicked_session),  # Use formatted display
                                                font=("Arial", 9, "bold"))
        self.golden_session_counter_label.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(golden_counter_frame, text="Reset", command=lambda: self.reset_session_counter('golden'), 
                width=5).pack(side=tk.LEFT, padx=(5, 15))
        
        # Total counter
        ttk.Label(golden_counter_frame, text="Total:").pack(side=tk.LEFT)
        self.golden_total_counter_label = ttk.Label(golden_counter_frame, 
                                                text=self.format_count_display(self.golden_cookies_clicked_total),  # Use formatted display
                                                font=("Arial", 9, "bold"))
        self.golden_total_counter_label.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(golden_counter_frame, text="Reset", command=lambda: self.reset_total_counter('golden'), 
                width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # Big cookie counters
        big_counter_frame = ttk.Frame(counter_frame)
        big_counter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(big_counter_frame, text="Big Cookies (inaccurate):").pack(side=tk.LEFT, padx=(0, 14))  # Added padding for alignment
        
        # Session counter
        ttk.Label(big_counter_frame, text="Session:").pack(side=tk.LEFT, padx=(10, 0))
        self.big_session_counter_label = ttk.Label(big_counter_frame, 
                                                text=self.format_count_display(self.big_cookies_clicked_session),  # Use formatted display
                                                font=("Arial", 9, "bold"))
        self.big_session_counter_label.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(big_counter_frame, text="Reset", command=lambda: self.reset_session_counter('big'), 
                width=5).pack(side=tk.LEFT, padx=(5, 15))
        
        # Total counter
        ttk.Label(big_counter_frame, text="Total:").pack(side=tk.LEFT)
        self.big_total_counter_label = ttk.Label(big_counter_frame, 
                                            text=self.format_count_display(self.big_cookies_clicked_total),  # Use formatted display
                                            font=("Arial", 9, "bold"))
        self.big_total_counter_label.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(big_counter_frame, text="Reset", command=lambda: self.reset_total_counter('big'), 
                width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # Start the bot threads
        self.start_bot_threads()
        
        # When window closes
        def on_closing():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Saving settings and shutting down...")
            self.save_config(show_confirmation=False)
            self.stop_event.set()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        return root
    
    def _extract_f_num(self, key_str, default):
        key_str = key_str.lower()
        if key_str.startswith('f') and len(key_str) > 1:
            try:
                num_part = key_str[1:]
                if num_part.isdigit():
                    f_num = int(num_part)
                    if 1 <= f_num <= 24:
                        return f_num
            except:
                pass
        return default
    
    def _create_settings_widgets(self, parent, cookie_type, vars_dict):
        # Settings grid
        ttk.Label(parent, text="Confidence Threshold:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(parent, textvariable=vars_dict[f'{cookie_type}_confidence'], width=10).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        if cookie_type == "golden":
            ttk.Label(parent, text="Check Interval:").grid(row=1, column=0, sticky=tk.W, pady=5)
        else:
            ttk.Label(parent, text="Click Interval:").grid(row=1, column=0, sticky=tk.W, pady=5)
        interval_frame = ttk.Frame(parent)
        interval_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Seconds spinbox (0-1800)
        seconds_spinbox = ttk.Spinbox(
            interval_frame,
            from_=0,
            to=1800,
            width=4,
            textvariable=vars_dict[f'{cookie_type}_interval_sec'],
            wrap=True,
            validate="all",
            validatecommand=(parent.register(lambda P: (P.isdigit() or P == "") and (int(P) <= 1800 if P.isdigit() else True)), '%P')
        )
        seconds_spinbox.pack(side=tk.LEFT)
        ttk.Label(interval_frame, text="s").pack(side=tk.LEFT)
        
        # Milliseconds spinbox (0-999)
        ms_spinbox = ttk.Spinbox(
            interval_frame,
            from_=0,
            to=999,
            width=4,
            textvariable=vars_dict[f'{cookie_type}_interval_ms'],
            wrap=True,
            validate="all",
            validatecommand=(parent.register(lambda P: (P.isdigit() or P == "") and (int(P) <= 999 if P.isdigit() else True)), '%P')
        )
        ms_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(interval_frame, text="ms").pack(side=tk.LEFT)
        
        ttk.Label(parent, text="Toggle Key:").grid(row=2, column=0, sticky=tk.W, pady=5)
        key_frame = ttk.Frame(parent)
        key_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # F-key spinner with F prefix
        ttk.Label(key_frame, text="F").pack(side=tk.LEFT)
        f_key_spinner = ttk.Spinbox(
            key_frame, 
            from_=1, 
            to=24, 
            width=2, 
            textvariable=vars_dict[f'{cookie_type}_f_key_number'],
            wrap=True,
            validate="all",
            validatecommand=(parent.register(lambda P: (P.isdigit() or P == "") and (1 <= int(P) <= 24 if P.isdigit() and P != "" else True)), '%P')
        )
        f_key_spinner.pack(side=tk.LEFT)
        
        # Save button
        ttk.Button(parent, text="Save Settings", 
                command=lambda: self.save_settings_from_gui(vars_dict, cookie_type)).grid(
                    row=3, column=0, columnspan=2, pady=15)
    
    def run(self):
        root = self.create_gui()
        root.mainloop()

if __name__ == "__main__":
    bot = CookieClickerBot()
    bot.run()