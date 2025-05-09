import pyautogui
import time
import threading
import pickle
import os
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard
from datetime import datetime

# Constants and defaults
DEFAULT_CONFIG = {
    'toggle_key': 'f8',
    'check_interval_sec': 0,
    'check_interval_ms': 500,
    'confidence': 0.90,
    'image_path': 'golden_cookie.png',
    'cookies_clicked_total': 0
}
CONFIG_FILE = 'options.pkl'

class CookieClickerBot:
    def __init__(self):
        # State variables
        self.running = False
        self.stop_event = threading.Event()
        self.cookies_clicked_session = 0
        self.cookies_clicked_total = 0
        self.config = self.load_config()
        self.cookies_clicked_total = self.config['cookies_clicked_total']
        
        # UI elements (initialized in create_gui)
        self.status_label = None
        self.toggle_button = None
        self.session_counter_label = None
        self.total_counter_label = None
        
        # Initialize thread and listener
        self.watcher_thread = None
        self.keyboard_listener = None
        
    def load_config(self):
        """Load configuration from file or use defaults"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()
    
    def save_config(self, show_confirmation=True):
        """Save current configuration to file"""
        try:
            # Update total cookies in config
            self.config['cookies_clicked_total'] = self.cookies_clicked_total
            
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
    
    def toggle_bot(self):
        """Toggle the bot state between running and stopped"""
        self.running = not self.running
        self.update_status_display()
        status = "ON" if self.running else "OFF"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Golden Cookie detection toggled {status}")
    
    def update_status_display(self):
        """Update UI elements to reflect current bot state"""
        if self.status_label:
            status_text = "ON" if self.running else "OFF"
            status_color = "#4CAF50" if self.running else "#F44336"  # Green or Red
            self.status_label.config(text=status_text, foreground=status_color)
            
        if self.toggle_button:
            button_text = "Turn OFF" if self.running else "Turn ON"
            self.toggle_button.config(text=button_text)
    
    def update_counter_display(self):
        """Update cookie counter displays"""
        if self.session_counter_label and self.total_counter_label:
            self.session_counter_label.config(text=str(self.cookies_clicked_session))
            self.total_counter_label.config(text=str(self.cookies_clicked_total))
    
    def on_key_press(self, key):
        """Handle key press events"""
        try:
            current_toggle_key = self.config['toggle_key'].lower()
            if hasattr(key, 'name') and key.name.lower() == current_toggle_key.lower():
                self.toggle_bot()
        except AttributeError:
            pass
    
    def golden_cookie_watcher(self):
        """Thread function to watch for and click golden cookies"""
        while not self.stop_event.is_set():
            if self.running:
                try:
                    # Look for golden cookie
                    location = pyautogui.locateCenterOnScreen(
                        self.config['image_path'], 
                        confidence=self.config['confidence']
                    )
                    
                    if location:
                        # Increment cookie counters
                        self.cookies_clicked_session += 1
                        self.cookies_clicked_total += 1
                        self.update_counter_display()
                        
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Found golden cookie at {location} (Session: {self.cookies_clicked_session}, Total: {self.cookies_clicked_total})")
                        
                        # Click the cookie and return to original position
                        original_pos = pyautogui.position()
                        pyautogui.click(location)
                        pyautogui.moveTo(original_pos)
                        
                        # Auto-save the updated total count
                        self.save_config(show_confirmation=False)
                        
                except Exception as e:
                    print(f"ERROR: {e}")
            
            # Calculate sleep interval in seconds            
            total_interval = self.config['check_interval_sec'] + (self.config['check_interval_ms'] / 1000)
            time.sleep(max(0.1, total_interval))  # Minimum 0.1s to avoid CPU hogging
    
    def start_bot_thread(self):
        """Start or restart the bot thread and keyboard listener"""
        # Stop any existing thread
        if self.watcher_thread and self.watcher_thread.is_alive():
            self.stop_event.set()
            self.watcher_thread.join(timeout=1)
            self.stop_event.clear()
        
        # Start new thread
        self.watcher_thread = threading.Thread(target=self.golden_cookie_watcher)
        self.watcher_thread.daemon = True
        self.watcher_thread.start()
        
        # Start keyboard listener if needed
        if not self.keyboard_listener or not self.keyboard_listener.is_alive():
            self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
            self.keyboard_listener.start()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Press {self.config['toggle_key'].upper()} to toggle Golden Cookie detection ON/OFF.")
    
    def reset_session_counter(self):
        """Reset the session counter to zero"""
        self.cookies_clicked_session = 0
        self.update_counter_display()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Session counter reset to 0")
    
    def reset_total_counter(self):
        """Reset the total counter to zero"""
        self.cookies_clicked_total = 0
        self.update_counter_display()
        self.save_config(show_confirmation=False)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Total cookies counter reset to 0")
    
    def save_settings_from_gui(self, vars_dict):
        """Save settings from GUI inputs"""
        try:
            # Update config from GUI variables
            f_key_number = int(vars_dict['f_key_number'].get())
            if 1 <= f_key_number <= 24:
                self.config['toggle_key'] = f'f{f_key_number}'
                
            self.config['check_interval_sec'] = int(vars_dict['interval_sec'].get())
            self.config['check_interval_ms'] = int(vars_dict['interval_ms'].get())
            self.config['confidence'] = float(vars_dict['confidence'].get())
            
            # Save to file
            self.save_config()
            
            # Restart the bot thread with new settings
            self.start_bot_thread()
        except ValueError as e:
            messagebox.showerror("Invalid Value", f"Please check your input values: {e}")
    
    def create_gui(self):
        """Create the main GUI window"""
        # Create root window
        root = tk.Tk()
        root.title("Cookie Clicker Cookie Clicker")
        root.geometry("500x340")  # Further reduced height after removing hint label
        root.resizable(True, True)
        
        # Extract F-key number from current toggle key
        current_key = self.config['toggle_key'].lower()
        current_f_num = 8  # Default to F8
        if current_key.startswith('f') and len(current_key) > 1:
            try:
                num_part = current_key[1:]
                if num_part.isdigit():
                    current_f_num = int(num_part)
                    if not (1 <= current_f_num <= 24):
                        current_f_num = 8
            except:
                current_f_num = 8
        
        # Variables for GUI
        vars_dict = {
            'confidence': tk.StringVar(value=f"{self.config['confidence']:.2f}"),
            'interval_sec': tk.StringVar(value=str(self.config['check_interval_sec'])),
            'interval_ms': tk.StringVar(value=str(self.config['check_interval_ms'])),
            'f_key_number': tk.StringVar(value=str(current_f_num))
        }
        
        # Main frame - reduce vertical padding since we removed a row
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Cookie Clicker Cookie Clicker", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 15))
        
        # Instructions
        ttk.Label(main_frame, text="Turn off Fancy Graphics and Numbers in settings.\nAlso disable Particles if autoclicking the big cookie is slow.", 
                 font=("Arial", 12)).grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
        # Settings grid
        ttk.Label(main_frame, text="Confidence Threshold:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=vars_dict['confidence'], width=10).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Check Interval:").grid(row=3, column=0, sticky=tk.W, pady=5)
        interval_frame = ttk.Frame(main_frame)
        interval_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Entry(interval_frame, textvariable=vars_dict['interval_sec'], width=3).pack(side=tk.LEFT)
        ttk.Label(interval_frame, text="s").pack(side=tk.LEFT)
        ttk.Entry(interval_frame, textvariable=vars_dict['interval_ms'], width=3).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(interval_frame, text="ms").pack(side=tk.LEFT)
        
        ttk.Label(main_frame, text="Toggle Key:").grid(row=4, column=0, sticky=tk.W, pady=5)
        key_frame = ttk.Frame(main_frame)
        key_frame.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # F-key spinner with F prefix
        ttk.Label(key_frame, text="F").pack(side=tk.LEFT)
        f_key_spinner = ttk.Spinbox(
            key_frame, 
            from_=1, 
            to=24, 
            width=2, 
            textvariable=vars_dict['f_key_number'],
            wrap=True,
            validate="all",
            validatecommand=(root.register(lambda P: P.isdigit() and 1 <= int(P) <= 24 if P else True), '%P')
        )
        f_key_spinner.pack(side=tk.LEFT)
        
        # Bot status and toggle button in same row
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        ttk.Label(status_frame, text="Golden Cookie detection: ").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="OFF", foreground="#F44336", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Toggle button in the same row
        self.toggle_button = ttk.Button(status_frame, text="Turn ON", command=self.toggle_bot, width=10)
        self.toggle_button.pack(side=tk.LEFT)
        
        # Cookie counter section
        counter_frame = ttk.Frame(main_frame)
        counter_frame.grid(row=7, column=0, columnspan=3, pady=5)
        
        # Session counter
        session_counter_container = ttk.Frame(counter_frame)
        session_counter_container.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(session_counter_container, text="Session Cookies:", font=("Arial", 9)).pack(side=tk.LEFT)
        self.session_counter_label = ttk.Label(session_counter_container, 
                                            text=str(self.cookies_clicked_session), 
                                            font=("Arial", 9, "bold"))
        self.session_counter_label.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(session_counter_container, text="Reset", command=self.reset_session_counter, 
                  width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # Total counter
        total_counter_container = ttk.Frame(counter_frame)
        total_counter_container.pack(side=tk.LEFT)
        
        ttk.Label(total_counter_container, text="Total Cookies:", font=("Arial", 9)).pack(side=tk.LEFT)
        self.total_counter_label = ttk.Label(total_counter_container, 
                                          text=str(self.cookies_clicked_total), 
                                          font=("Arial", 9, "bold"))
        self.total_counter_label.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(total_counter_container, text="Reset", command=self.reset_total_counter, 
                  width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # Save button
        ttk.Button(main_frame, text="Save Settings", 
                  command=lambda: self.save_settings_from_gui(vars_dict)).grid(
                      row=8, column=0, columnspan=3, pady=5)
        
        # No need to update hint label since it's removed
        
        # Start the bot thread
        self.start_bot_thread()
        
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
    
    def run(self):
        """Start the application"""
        root = self.create_gui()
        root.mainloop()

if __name__ == "__main__":
    bot = CookieClickerBot()
    bot.run()