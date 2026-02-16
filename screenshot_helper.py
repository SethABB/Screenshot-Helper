import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
from pathlib import Path
from PIL import Image
import threading
from pynput import keyboard
from datetime import datetime
import mss


class ScreenshotHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot Helper")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        self.config_file = Path(__file__).parent / "config.json"
        self.config = self.load_config()
        
        self.hotkey_listener = None
        self.listening = False
        self.selecting_area = False
        self.rect = None
        self.start_x = 0
        self.start_y = 0
        self.selection_window = None
        self.selection_windows = []
        self.canvases = []
        self.rects = []
        
        self.setup_ui()
        self.setup_hotkey_listener()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_config(self):
        """Load configuration from JSON file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            "save_location": "",
            "hotkey": {"key": "F12", "ctrl": False, "shift": False, "alt": False},
            "screen_areas": []
        }
    
    def save_config(self):
        """Save configuration to JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def setup_ui(self):
        """Setup the GUI components"""
        # Title
        title_label = ttk.Label(self.root, text="Screenshot Helper", 
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Save Location Frame
        save_frame = ttk.LabelFrame(self.root, text="Save Location", padding=10)
        save_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_location_label = ttk.Label(save_frame, text=self.config["save_location"] or "No location selected")
        self.save_location_label.pack(fill="x", side="left", expand=True)
        
        browse_button = ttk.Button(save_frame, text="Browse", command=self.browse_folder)
        browse_button.pack(side="left", padx=5)
        
        # Hotkey Frame
        hotkey_frame = ttk.LabelFrame(self.root, text="Hotkey Configuration", padding=10)
        hotkey_frame.pack(fill="x", padx=10, pady=5)
        
        self.hotkey_label = ttk.Label(hotkey_frame, text=self.format_hotkey())
        self.hotkey_label.pack(fill="x", side="left", expand=True)
        
        hotkey_button = ttk.Button(hotkey_frame, text="Set Hotkey", command=self.set_hotkey)
        hotkey_button.pack(side="left", padx=5)
        
        # Screen Areas Frame
        areas_frame = ttk.LabelFrame(self.root, text="Screen Areas", padding=10)
        areas_frame.pack(fill="both", padx=10, pady=5, expand=True)
        
        # Buttons for area management (above listbox, right-justified)
        button_frame = ttk.Frame(areas_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        add_button = ttk.Button(button_frame, text="Add Area", command=self.add_area)
        add_button.pack(side="right", padx=5)
        
        delete_button = ttk.Button(button_frame, text="Delete Selected", command=self.delete_area)
        delete_button.pack(side="right", padx=5)
        
        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(areas_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.areas_listbox = tk.Listbox(areas_frame, yscrollcommand=scrollbar.set, height=12)
        self.areas_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.areas_listbox.yview)
        
        self.refresh_areas_list()
        
        # Status label
        self.status_label = ttk.Label(self.root, text="Ready", foreground="green")
        self.status_label.pack(pady=5)
    
    def format_hotkey(self):
        """Format hotkey for display"""
        hotkey = self.config["hotkey"]
        parts = []
        if hotkey["ctrl"]:
            parts.append("Ctrl")
        if hotkey["shift"]:
            parts.append("Shift")
        if hotkey["alt"]:
            parts.append("Alt")
        parts.append(hotkey["key"])
        return " + ".join(parts)
    
    def browse_folder(self):
        """Browse for save location"""
        folder = filedialog.askdirectory(title="Select Save Location")
        if folder:
            self.config["save_location"] = folder
            self.save_config()
            self.save_location_label.config(text=folder)
            self.update_status("Save location updated", "green")
    
    def set_hotkey(self):
        """Set the hotkey by listening to user input"""
        messagebox.showinfo("Set Hotkey", 
                           "Press any key on your keyboard to set the hotkey.")
        
        captured_key = None
        listener = None
        
        def on_press(key):
            nonlocal captured_key, listener
            if captured_key is None:
                try:
                    key_name = key.char.upper() if hasattr(key, 'char') and key.char else key.name.upper()
                except:
                    key_name = key.name.upper()
                
                captured_key = {
                    "key": key_name,
                    "ctrl": False,
                    "shift": False,
                    "alt": False
                }
                if listener:
                    listener.stop()
            return False
        
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        listener.join()
        
        if captured_key:
            self.config["hotkey"] = captured_key
            self.save_config()
            self.hotkey_label.config(text=self.format_hotkey())
            self.update_status("Hotkey updated to: " + self.format_hotkey(), "green")
        else:
            messagebox.showwarning("Hotkey", "No key detected. Please try again.")
    
    def add_area(self):
        """Start the area selection process"""
        if not self.config["save_location"]:
            messagebox.showwarning("Save Location", "Please set a save location first!")
            return
        
        self.update_status("Drag to select area... (Esc to cancel)", "blue")
        self.selecting_area = True
        self.create_selection_window()
    
    def create_selection_window(self):
        """Create overlay windows for area selection on all monitors"""
        import mss
        
        # Get all monitor information
        with mss.mss() as sct:
            monitors = sct.monitors[1:]  # Skip the first element which is a combined view
        
        self.selection_windows = []
        self.rects = []
        self.canvases = []
        
        self.rect = None
        self.start_x = 0
        self.start_y = 0
        
        def on_mouse_down(event, canvas_idx=0):
            self.start_x = event.x_root
            self.start_y = event.y_root
            for idx, canvas in enumerate(self.canvases):
                if self.rects[idx]:
                    canvas.delete(self.rects[idx])
                self.rects[idx] = None
        
        def on_mouse_drag(event, canvas_idx=0):
            for idx, (canvas, window) in enumerate(zip(self.canvases, self.selection_windows)):
                monitor = monitors[idx]
                # Check if cursor is over this monitor
                if (monitor['left'] <= event.x_root < monitor['left'] + monitor['width'] and
                    monitor['top'] <= event.y_root < monitor['top'] + monitor['height']):
                    # Calculate position relative to the window
                    rel_x = event.x_root - monitor['left']
                    rel_y = event.y_root - monitor['top']
                    if self.rects[idx]:
                        canvas.delete(self.rects[idx])
                    self.rects[idx] = canvas.create_rectangle(
                        self.start_x - monitor['left'], self.start_y - monitor['top'],
                        rel_x, rel_y,
                        outline='red', width=2
                    )
        
        def on_mouse_up(event):
            if self.selecting_area:
                x1 = min(self.start_x, event.x_root)
                y1 = min(self.start_y, event.y_root)
                x2 = max(self.start_x, event.x_root)
                y2 = max(self.start_y, event.y_root)
                
                if x2 - x1 > 5 and y2 - y1 > 5:  # Minimum size check
                    self.config["screen_areas"].append({
                        "x1": x1, "y1": y1, "x2": x2, "y2": y2
                    })
                    self.save_config()
                    self.refresh_areas_list()
                    self.update_status("Area added successfully", "green")
                
                self.cleanup_selection_windows()
        
        def on_key_press(event):
            if event.keysym == 'Escape':
                self.cleanup_selection_windows()
                self.update_status("Area selection cancelled", "orange")
        
        # Create a window for each monitor
        for monitor in monitors:
            window = tk.Toplevel(self.root)
            window.wm_overrideredirect(True)
            window.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}")
            window.attributes('-topmost', True)
            window.attributes('-alpha', 0.3)
            window.configure(bg='black')
            
            canvas = tk.Canvas(window, cursor="crosshair", bg='black', highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_drag)
            canvas.bind("<ButtonRelease-1>", on_mouse_up)
            window.bind("<Escape>", on_key_press)
            
            self.selection_windows.append(window)
            self.canvases.append(canvas)
            self.rects.append(None)
        
        # Focus the first window
        if self.selection_windows:
            self.selection_windows[0].focus_set()
    
    def cleanup_selection_windows(self):
        """Clean up all selection windows"""
        self.selecting_area = False
        for window in self.selection_windows:
            try:
                window.destroy()
            except:
                pass
        self.selection_windows = []
        self.canvases = []
        self.rects = []
    
    def delete_area(self):
        """Delete the selected area"""
        selection = self.areas_listbox.curselection()
        if selection:
            index = selection[0]
            self.config["screen_areas"].pop(index)
            self.save_config()
            self.refresh_areas_list()
            self.update_status("Area deleted", "green")
        else:
            messagebox.showwarning("Delete Area", "Please select an area to delete!")
    
    def refresh_areas_list(self):
        """Refresh the areas listbox"""
        self.areas_listbox.delete(0, tk.END)
        for i, area in enumerate(self.config["screen_areas"], 1):
            area_text = f"Area {i}: ({area['x1']}, {area['y1']}) to ({area['x2']}, {area['y2']})"
            self.areas_listbox.insert(tk.END, area_text)
    
    def setup_hotkey_listener(self):
        """Setup the global hotkey listener"""
        def on_key_press(key):
            try:
                # Get the key name
                key_name = key.char.upper() if hasattr(key, 'char') and key.char else key.name.upper()
                
                # Check if it matches the configured hotkey
                if key_name == self.config["hotkey"]["key"]:
                    self.take_screenshots()
            except:
                pass
        
        def on_key_release(key):
            pass
        
        self.hotkey_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
        self.hotkey_listener.start()
        self.listening = True
    
    def take_screenshots(self):
        """Take screenshots of all defined areas"""
        if not self.config["screen_areas"]:
            self.update_status("No areas defined!", "red")
            return
        
        if not self.config["save_location"]:
            self.update_status("No save location set!", "red")
            return
        
        save_location = Path(self.config["save_location"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            with mss.mss() as sct:
                for i, area in enumerate(self.config["screen_areas"], 1):
                    # Use mss for proper multi-monitor support
                    monitor = {
                        'left': area["x1"],
                        'top': area["y1"],
                        'width': area["x2"] - area["x1"],
                        'height': area["y2"] - area["y1"]
                    }
                    screenshot = sct.grab(monitor)
                    # Convert mss image to PIL Image
                    img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                    
                    filename = save_location / f"screenshot_{timestamp}_area{i}.png"
                    img.save(filename)
            
            self.update_status(f"Screenshots saved to {save_location}", "green")
        except Exception as e:
            self.update_status(f"Error taking screenshot: {str(e)}", "red")
            messagebox.showerror("Screenshot Error", f"Failed to take screenshot:\n{str(e)}")
    
    def update_status(self, message, color="green"):
        """Update the status label"""
        self.status_label.config(text=message, foreground=color)
    
    def on_closing(self):
        """Handle window closing"""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ScreenshotHelper(root)
    root.mainloop()


if __name__ == "__main__":
    main()
