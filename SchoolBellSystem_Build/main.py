import psutil
import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
import ctypes
import os
import json
from datetime import datetime, timedelta
import threading
import time
import sys
import pygame
import subprocess
import re
import shutil
import pystray

os.environ['PYTHONPATH'] = ''

try:
    p = psutil.Process(os.getpid())
    p.nice(psutil.HIGH_PRIORITY_CLASS)
except Exception as e:
    print(f"Could not set priority: {e}")


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class TimePickerPopup(tk.Toplevel):
    """
    A pop-up window for selecting time using user-friendly comboboxes.
    """

    def __init__(self, parent, initial_time, callback, theme):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        self.theme = theme
        self.transient(parent)
        self.grab_set()

        try:
            icon_path = resource_path("app_icon.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass

        self.initial_time_parts = self.parse_time(initial_time)
        self.hours = [f"{h:02d}" for h in range(1, 13)]
        self.minutes = [f"{m:02d}" for m in range(0, 60)]
        self.seconds = [f"{s:02d}" for s in range(0, 60)]
        self.am_pm = ["AM", "PM"]

        self.hour_var = tk.StringVar(self, self.initial_time_parts['hour'])
        self.minute_var = tk.StringVar(self, self.initial_time_parts['minute'])
        self.second_var = tk.StringVar(self, self.initial_time_parts['second'])
        self.ampm_var = tk.StringVar(self, self.initial_time_parts['ampm'])

        self.title("Set Time")
        self.configure(bg=self.theme["colors"]["accent_bg"], highlightbackground=self.theme["colors"]["primary"],
                       highlightthickness=1.5, relief="solid")
        self.geometry("320x150")
        self.resizable(False, False)

        time_selection_frame = tk.Frame(self, bg=self.theme["colors"]["accent_bg"])
        time_selection_frame.pack(pady=20, padx=10)

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TimePicker.TCombobox",
                        fieldbackground=self.theme["colors"]["primary"],
                        background=self.theme["colors"]["primary"],
                        foreground=self.theme["colors"]["text_light"],
                        arrowcolor=self.theme["colors"]["text_light"],
                        font=("Poppins", 18))
        style.map('TimePicker.TCombobox', fieldbackground=[('readonly', self.theme["colors"]["primary"])])
        style.map('TimePicker.TCombobox', selectbackground=[('readonly', self.theme["colors"]["primary"])])
        style.map('TimePicker.TCombobox', selectforeground=[('readonly', self.theme["colors"]["text_light"])])

        hour_combo = ttk.Combobox(time_selection_frame, textvariable=self.hour_var, values=self.hours,
                                  width=4, state='readonly', style="TimePicker.TCombobox", justify='center')
        hour_combo.pack(side="left", padx=5)

        tk.Label(time_selection_frame, text=":", bg=self.theme["colors"]["accent_bg"],
                 fg=self.theme["colors"]["primary"], font=("Poppins", 16, "bold")).pack(side="left")

        minute_combo = ttk.Combobox(time_selection_frame, textvariable=self.minute_var, values=self.minutes,
                                    width=4, state='readonly', style="TimePicker.TCombobox", justify='center')
        minute_combo.pack(side="left", padx=5)

        tk.Label(time_selection_frame, text=":", bg=self.theme["colors"]["accent_bg"],
                 fg=self.theme["colors"]["primary"], font=("Poppins", 16, "bold")).pack(side="left")

        second_combo = ttk.Combobox(time_selection_frame, textvariable=self.second_var, values=self.seconds,
                                    width=4, state='readonly', style="TimePicker.TCombobox", justify='center')
        second_combo.pack(side="left", padx=5)

        ampm_combo = ttk.Combobox(time_selection_frame, textvariable=self.ampm_var, values=self.am_pm,
                                  width=4, state='readonly', style="TimePicker.TCombobox", justify='center')
        ampm_combo.pack(side="left", padx=5)

        ok_button = tk.Button(self, text="OK", command=self.on_ok,
                              bg=self.theme["colors"]["primary"], fg=self.theme["colors"]["text_light"],
                              font=("Poppins", 14), relief="flat", padx=20)
        ok_button.pack(pady=(0, 15))
        self.center_window()

    def parse_time(self, time_string):
        """Parses a time string into a dictionary of its parts."""
        parts = time_string.replace(':', ' ').split()
        return {
            'hour': parts[0],
            'minute': parts[1],
            'second': parts[2],
            'ampm': parts[3]
        }

    def on_ok(self):
        """Callback for the OK button, returns the selected time."""
        selected_time = f"{self.hour_var.get()}:{self.minute_var.get()}:{self.second_var.get()} {self.ampm_var.get()}"
        self.callback(selected_time)
        self.destroy()

    def center_window(self):
        """Centers the pop-up window on the screen."""
        self.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        popup_width = self.winfo_width()
        popup_height = self.winfo_height()

        x = parent_x + (parent_width // 2) - (popup_width // 2)
        y = parent_y + (parent_height // 2) - (popup_height // 2)

        self.geometry(f'+{x}+{y}')


class SplashScreen(tk.Toplevel):
    """
    A splash screen window that displays an image for a set duration.
    """

    def __init__(self, parent, splash_image_path):
        super().__init__(parent)
        self.parent = parent
        self.splash_image_path = splash_image_path
        self.overrideredirect(True)
        self.attributes("-transparent", "white")

        try:
            image_path = resource_path(self.splash_image_path)
            original_image = Image.open(image_path).convert("RGBA")
            self.splash_photo = ImageTk.PhotoImage(original_image)

            self.canvas = tk.Canvas(self, width=original_image.width, height=original_image.height,
                                    highlightthickness=0, bg="white")
            self.canvas.pack()
            self.canvas.create_image(0, 0, anchor="nw", image=self.splash_photo)

            self.update_idletasks()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width // 2) - (self.winfo_width() // 2)
            y = (screen_height // 2) - (self.winfo_height() // 2)
            self.geometry(f'+{x}+{y}')

        except FileNotFoundError:
            print(f"Error: Splash screen image file not found at {resource_path(self.splash_image_path)}")
            self.splash_photo = None
            self.destroy()

    def show_main_window(self):
        """
        Destroys the splash screen and shows the main application window.
        """
        self.destroy()
        self.parent.deiconify()


class BellSystemApp(tk.Frame):
    """
    Main application class for the School Bell System.
    This class encapsulates the entire application, managing frames, widgets and logic.
    """

    class CustomToggle(tk.Canvas):
        """A modern, canvas-based toggle switch."""

        def __init__(self, parent, variable, command=None, **kwargs):
            super().__init__(parent, width=50, height=28, bd=0, highlightthickness=0, **kwargs)
            self.variable = variable
            self.command = command
            self.configure(bg=parent.cget("bg"))

            self.bind("<Button-1>", self.toggle)
            self.draw()

        def draw(self):
            self.delete("all")
            bg_color = "#FF8787" if self.variable.get() else "#A0AEC0"
            circle_color = "#FF6B6B" if self.variable.get() else "#E2E8F0"

            self.create_oval(2, 2, 26, 26, fill=bg_color, outline=bg_color)
            self.create_oval(24, 2, 48, 26, fill=bg_color, outline=bg_color)
            self.create_rectangle(14, 2, 36, 26, fill=bg_color, outline=bg_color)

            if self.variable.get():
                self.create_oval(25, 3, 47, 25, fill=circle_color, outline=circle_color)
            else:
                self.create_oval(3, 3, 25, 25, fill=circle_color, outline=circle_color)

        def toggle(self, event=None):
            if self.cget('state') == 'disabled':
                return
            self.variable.set(not self.variable.get())
            self.draw()
            if self.command:
                self.command()

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"Could not initialize pygame mixer: {e}")
            messagebox.showwarning("Audio Error", "Could not initialize audio system. Bell sounds will not play.")

        self.light_theme = {
            "primary": "#FF6B6B", "secondary": "#FFFFFF", "accent_bg": "#FEE5E5",
            "text_light": "#FFFFFF", "text_dark": "#4A5568"
        }
        self.dark_theme = {
            "primary": "#FF6B6B", "secondary": "#2D3748", "accent_bg": "#4A5568",
            "text_light": "#F7FAFC", "text_dark": "#E2E8F0"
        }

        # CHANGED: Added '_v2' to the folder name to isolate data from version 1
        app_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'SchoolBellSystem_v2')
        os.makedirs(app_data_dir, exist_ok=True)

        self.settings_file = os.path.join(app_data_dir, "settings.json")
        self.load_settings()

        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        scale_factor = 0.85
        min_width = 1000
        min_height = 700

        self.app_width = max(min_width, int(screen_width * scale_factor))
        self.app_height = max(min_height, int(screen_height * scale_factor))
        self.base_font_scale = min(max(self.app_width / 1200, 0.85), 1.25)

        self.rebuild_theme()

        self.master.config(bg=self.theme['colors']['primary'])
        self.pack(fill="both", expand=True)

        self.master.title("School Bell System")

        self.master.geometry(f"{self.app_width}x{self.app_height}")
        self.master.minsize(min_width, min_height)
        self.master.resizable(True, True)

        try:
            icon_path = resource_path("app_icon.ico")
            self.master.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error setting window icon: {e}")
            messagebox.showwarning("Icon Error", "Could not load application icon 'app_icon.ico'.")

        self.timetables_dir = os.path.join(app_data_dir, "timetables")
        os.makedirs(self.timetables_dir, exist_ok=True)

        self.add_icon_original_light = self.load_icon("assets/Icons/add_icon (white mode).png")
        self.open_icon_original_light = self.load_icon("assets/Icons/open_icon (white mode).png")
        self.cross_icon_original = self.load_icon("assets/Icons/Cross_icon.png", size=(20, 20))
        self.delete_icon_original = self.load_icon("assets/Icons/delete_icon.png", size=(30, 30))
        self.create_another_icon_original = self.load_icon("assets/Icons/add_icon (white mode).png", size=(40, 40))

        self.cross_icon_photo = ImageTk.PhotoImage(self.cross_icon_original) if self.cross_icon_original else None
        self.delete_icon_photo = ImageTk.PhotoImage(self.delete_icon_original) if self.delete_icon_original else None
        self.create_another_icon_photo = ImageTk.PhotoImage(
            self.create_another_icon_original) if self.create_another_icon_original else None
        self.add_icon_photo = None
        self.open_icon_photo = None

        self.line_image_photo = self.load_line_image("assets/Line.png", width=190)

        self.home_button = None
        self.about_button = None
        self.settings_button = None
        self.timetables_list_frame = None

        self.font_family_name = "Poppins"
        self.setup_fonts()

        self.configure(bg=self.theme["colors"]["primary"])

        self.current_frame_name = "home"
        self.current_timetable_data = None
        self.bell_timer_thread = None
        self.is_timer_running = False
        self.next_bell_info = None
        self.current_sound = None
        self.tray_icon = None
        self.timer_stop_event = threading.Event()

        self.home_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.settings_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.about_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.create_timetable_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.saved_timetables_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.view_timetable_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])

        self.period_rows = []
        self.view_period_rows = []

        self.init_enhanced_settings_vars()

        self.setup_styles()
        self.vcmd = self.register(self.validate_time_input)
        self.create_widgets()
        self._update_button_icons()
        self.setup_window_close_handler()
        self.run_auto_backup()

    def center_main_window(self):
        self.master.update_idletasks()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.master.geometry(f'+{x}+{y}')

    def load_settings(self):
        defaults = {
            "run_on_startup": False, "minimize_to_tray": False, "theme": "light",
            "font_size": "Medium", "start_minimized": False, "last_active_timetable": "",
            "bell_volume": "75%", "bell_fade": True, "bell_duration": "10",
            "auto_stop_bells": False, "show_notifications": True, "warning_time": "5",
            "sound_notifications": True, "auto_backup": True, "backup_location": "",
            "backup_frequency": "Weekly",
            "last_backup_timestamp": 0
        }
        try:
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)
            for key, value in defaults.items():
                self.settings.setdefault(key, value)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = defaults
            self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
        print("Settings saved.")

    def rebuild_theme(self):
        font_size_setting = self.settings.get("font_size", "Medium")

        user_font_scale = {"Small": 0.9, "Medium": 1.0, "Large": 1.1}.get(font_size_setting, 1.0)
        base_scale = getattr(self, 'base_font_scale', 1.0)
        final_font_scale = base_scale * user_font_scale

        def scale_font(font_tuple):
            family, size = font_tuple[0], font_tuple[1]
            style = font_tuple[2] if len(font_tuple) > 2 else "normal"
            new_size = int(size * final_font_scale)
            return (family, new_size, style) if style != "normal" else (family, new_size)

        self.theme = {
            "colors": self.dark_theme if self.settings.get("theme") == "dark" else self.light_theme,
            "fonts": {
                "title_large": scale_font(("Poppins", 65)), "title": scale_font(("Poppins", 40)),
                "header": scale_font(("Poppins", 35)), "subheader": scale_font(("Poppins", 24)),
                "body_large": scale_font(("Poppins", 20)), "body": scale_font(("Poppins", 16)),
                "body_bold": scale_font(("Poppins", 16, "bold")), "button": scale_font(("Poppins", 16)),
                "button_bold": scale_font(("Poppins", 16, "bold")), "small": scale_font(("Poppins", 12)),
                "small_bold": scale_font(("Poppins", 12, "bold"))
            },
            "padding": {"large": 40, "medium": 20, "small": 10}
        }

    def apply_button_style(self, button, style_type="primary"):
        if style_type == "primary":
            button.config(bg=self.theme['colors']['primary'], fg=self.theme['colors']['text_light'],
                          font=self.theme['fonts']['button_bold'], relief="flat", borderwidth=0, padx=50, pady=5)
        elif style_type == "secondary":
            button.config(bg=self.theme['colors']['secondary'], fg=self.theme['colors']['text_dark'],
                          font=self.theme['fonts']['button'], relief="solid", bd=0,
                          highlightbackground=self.theme['colors']['primary'], highlightthickness=2, padx=30, pady=4)

    def setup_fonts(self):
        self.loaded_font_path = None  # Initialize
        try:
            font_path = resource_path(os.path.join("assets", "Fonts", "Tektur-Regular.ttf"))
            if os.path.exists(font_path):
                if os.name == 'nt':
                    if ctypes.windll.gdi32.AddFontResourceW(font_path) != 0:
                        self.loaded_font_path = font_path
                        self.font_family_name = "Tektur"
                    else:
                        print("Failed to add font resource.")
                else:
                    self.font_family_name = "Tektur"
            else:
                print(f"Font file not found at: {font_path}")
        except Exception as e:
            print(f"Error loading font: {e}")

    def load_icon(self, file_path, size=(50, 50)):
        try:
            full_path = resource_path(file_path)
            original_image = Image.open(full_path).convert("RGBA")
            return original_image.resize(size, Image.LANCZOS)
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")
            return None

    def load_line_image(self, file_path, width=210, height=2):
        try:
            full_path = resource_path(file_path)
            original_image = Image.open(full_path)
            resized_image = original_image.resize((width, 1), Image.LANCZOS)
            return ImageTk.PhotoImage(resized_image)
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")
            return None

    def _update_button_icons(self):
        if self.add_icon_original_light:
            self.add_icon_photo = ImageTk.PhotoImage(self.add_icon_original_light)
            if hasattr(self, 'create_button'): self.create_button.config(image=self.add_icon_photo)
        if self.open_icon_original_light:
            self.open_icon_photo = ImageTk.PhotoImage(self.open_icon_original_light)
            if hasattr(self, 'open_button'): self.open_button.config(image=self.open_icon_photo)

    def show_frame(self, frame_name):
        self.current_frame_name = frame_name
        highlight_bg = self.theme["colors"]["primary"]
        default_bg = self.theme["colors"]["primary"]

        buttons = {"home": self.home_button, "about": self.about_button, "settings": self.settings_button}
        for name, button in buttons.items():
            if button:
                button.config(bg=default_bg, activebackground=default_bg, font=self.theme["fonts"]["body"])

        if frame_name in buttons and buttons[frame_name]:
            buttons[frame_name].config(bg=highlight_bg, activebackground=highlight_bg,
                                       font=self.theme["fonts"]["body_bold"])
        elif frame_name in ["create_timetable", "saved_timetables", "view_timetable"] and self.home_button:
            self.home_button.config(bg=highlight_bg, activebackground=highlight_bg,
                                    font=self.theme["fonts"]["body_bold"])

        for frame in [self.home_frame, self.settings_frame, self.about_frame,
                      self.create_timetable_frame, self.saved_timetables_frame, self.view_timetable_frame]:
            if frame:
                frame.pack_forget()

        if hasattr(self, 'next_bell_time_label') and self.is_timer_running:
            self.update_all_countdown_displays(self.get_remaining_time() if self.next_bell_info else None)

        if frame_name == "home":
            if hasattr(self, 'update_home_page_status'):
                self.update_home_page_status()
            if hasattr(self, 'update_last_active_display'):
                self.update_last_active_display()

        if self.is_timer_running and self.current_timetable_data:
            self.master.title("School Bell System - Running")
        else:
            self.master.title("School Bell System")

        frame_map = {
            "home": self.home_frame, "about": self.about_frame, "settings": self.settings_frame,
            "create_timetable": self.create_timetable_frame, "saved_timetables": self.saved_timetables_frame,
            "view_timetable": self.view_timetable_frame
        }
        if frame_name in frame_map and frame_map[frame_name]:
            frame_map[frame_name].pack(side="right", fill="both", expand=True)

    def on_add_button_click(self):
        for row in self.period_rows:
            row["frame"].destroy()
        self.period_rows.clear()
        if hasattr(self, 'timetable_name_entry'):
            self.timetable_name_entry.delete(0, tk.END)
        self.show_frame("create_timetable")
        self.add_period_row()

    def on_open_button_click(self):
        self.load_saved_timetables()
        self.show_frame("saved_timetables")

    def on_timetable_click(self, timetable_name):
        if self.is_timer_running:
            if not messagebox.askyesno("Confirm Switch",
                                       "A timetable is currently active. Do you want to stop it and open a new one?"):
                return
            self.stop_bell_system()

        file_path = os.path.join(self.timetables_dir, f"{timetable_name}.json")
        try:
            with open(file_path, 'r') as f:
                self.current_timetable_data = json.load(f)
            self.load_timetable_view()
            self.show_frame("view_timetable")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load timetable: {e}")

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        try:
            style.element_create("Custom.Vertical.Scrollbar.thumb", "from", "default")
        except tk.TclError:
            pass
        style.layout('Custom.Vertical.TScrollbar',
                     [('Vertical.Scrollbar.trough', {
                         'children': [('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})],
                         'sticky': 'ns'
                     })])
        style.configure('Custom.Vertical.TScrollbar',
                        troughcolor=self.theme['colors']['secondary'],
                        background=self.theme['colors']['primary'],
                        borderwidth=1, relief='flat', width=12)
        style.map('Custom.Vertical.TScrollbar',
                  background=[('active', '#FF8787'), ('!active', self.theme['colors']['primary'])],
                  relief=[('pressed', 'sunken'), ('!pressed', 'flat')])

        self.master.option_add("*TCombobox*Listbox.background", self.theme['colors']['accent_bg'])
        self.master.option_add("*TCombobox*Listbox.foreground", self.theme['colors']['text_dark'])
        self.master.option_add("*TCombobox*Listbox.selectBackground", self.theme['colors']['primary'])
        self.master.option_add("*TCombobox*Listbox.selectForeground", self.theme['colors']['text_light'])
        self.master.option_add("*TCombobox*Listbox.font", self.theme['fonts']['small'])

        style.configure("Settings.TCombobox",
                        fieldbackground=self.theme['colors']['accent_bg'],
                        background=self.theme['colors']['primary'],
                        foreground=self.theme['colors']['text_dark'],
                        arrowcolor=self.theme['colors']['text_dark'],
                        font=self.theme['fonts']['body'], padding=8,
                        relief='flat', borderwidth=0)
        style.map("Settings.TCombobox", fieldbackground=[('readonly', self.theme['colors']['accent_bg'])])

    def init_enhanced_settings_vars(self):
        self.dark_mode_var = tk.BooleanVar(value=(self.settings.get("theme") == "dark"))
        self.run_on_startup_var = tk.BooleanVar(value=self.settings.get("run_on_startup", False))
        self.minimize_to_tray_var = tk.BooleanVar(value=self.settings.get("minimize_to_tray", False))
        self.bell_fade_var = tk.BooleanVar(value=self.settings.get("bell_fade", True))
        self.font_size_var = tk.StringVar(value=self.settings["font_size"])
        self.bell_volume_var = tk.StringVar(value=self.settings["bell_volume"])
        self.backup_location_var = tk.StringVar(value=self.settings["backup_location"])

    def create_widgets(self):
        self.sidebar_frame = tk.Frame(self, width=210, bg=self.theme["colors"]["primary"])
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        self.title_label = tk.Label(self.sidebar_frame, text="School Bell\nSystem",
                                    bg=self.theme["colors"]["primary"], fg=self.theme["colors"]["text_light"],
                                    font=(self.font_family_name, 30))
        self.title_label.pack(pady=(40, 0))

        self.line_label_top = tk.Label(self.sidebar_frame, image=self.line_image_photo,
                                       bg=self.theme["colors"]["primary"])
        self.line_label_top.image = self.line_image_photo
        self.line_label_top.pack(pady=(40, 20), padx=10)

        self.home_button = tk.Button(self.sidebar_frame, text="Home",
                                     bg=self.theme["colors"]["primary"], fg=self.theme["colors"]["text_light"],
                                     font=self.theme["fonts"]["body"], borderwidth=0, highlightthickness=0,
                                     activebackground=self.theme["colors"]["primary"],
                                     activeforeground=self.theme["colors"]["text_light"],
                                     command=lambda: self.show_frame("home"))
        self.home_button.pack(fill="x", ipady=2, padx=30, pady=10)
        self.about_button = tk.Button(self.sidebar_frame, text="About",
                                      bg=self.theme["colors"]["primary"], fg=self.theme["colors"]["text_light"],
                                      font=self.theme["fonts"]["body"], borderwidth=0, highlightthickness=0,
                                      activebackground=self.theme["colors"]["primary"],
                                      activeforeground=self.theme["colors"]["text_light"],
                                      command=lambda: self.show_frame("about"))
        self.about_button.pack(fill="x", ipady=2, padx=30, pady=10)
        self.settings_container_frame = tk.Frame(self.sidebar_frame, bg=self.theme["colors"]["primary"])
        self.settings_container_frame.pack(fill="x", side="bottom", anchor="s")

        self.line_label_bottom = tk.Label(self.settings_container_frame, image=self.line_image_photo,
                                          bg=self.theme["colors"]["primary"])
        self.line_label_bottom.image = self.line_image_photo
        self.line_label_bottom.pack(pady=(5, 5), padx=10)

        self.settings_button = tk.Button(self.settings_container_frame, text="Settings",
                                         bg=self.theme["colors"]["primary"], fg=self.theme["colors"]["text_light"],
                                         font=self.theme["fonts"]["body"], borderwidth=0, highlightthickness=0,
                                         activebackground=self.theme["colors"]["primary"],
                                         activeforeground=self.theme["colors"]["text_light"],
                                         command=lambda: self.show_frame("settings"))
        self.settings_button.pack(fill="x", ipady=4, padx=30, pady=5, anchor="s")

        self.create_home_page()
        self.create_settings_page()
        self.create_about_page()
        self.create_timetable_page()
        self.create_saved_timetables_page()
        self.create_view_timetable_page()

        self.show_frame("home")

    def add_hover_effect(self, button):
        button.bind("<Enter>", lambda e: button.config(fg=self.theme["colors"]["primary"]))
        button.bind("<Leave>", lambda e: button.config(fg=self.theme["colors"]["text_dark"]))

    def create_home_page(self):
        home_container = tk.Frame(self.home_frame, bg=self.theme["colors"]["secondary"])
        home_container.pack(fill="both", expand=True, padx=40, pady=40)
        center_frame = tk.Frame(home_container, bg=self.theme["colors"]["secondary"])
        center_frame.place(relx=0.5, rely=0.4, anchor="center")
        self.welcome_label = tk.Label(center_frame, text="Hi there,",
                                      bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                                      font=self.theme["fonts"]["title_large"])
        self.welcome_label.pack(pady=(0, 20))
        self.home_bell_status_button = tk.Button(
            center_frame, text="🔕 Bell system inactive", bg=self.theme["colors"]["secondary"],
            fg=self.theme["colors"]["primary"], font=self.theme["fonts"]["body_bold"], relief="solid", bd=0, padx=20,
            pady=10, cursor="hand2", command=self.on_bell_status_click)
        self.home_bell_status_button.pack(pady=(0, 40))
        self.home_bell_status_button.config(
            highlightbackground=self.theme["colors"]["primary"], highlightthickness=2,
            highlightcolor=self.theme["colors"]["primary"], activebackground=self.theme["colors"]["secondary"],
            activeforeground=self.theme["colors"]["primary"])
        self.action_button_frame = tk.Frame(center_frame, bg=self.theme["colors"]["secondary"])
        self.action_button_frame.pack(anchor="center")
        self.create_button = tk.Button(
            self.action_button_frame, compound="left", text=" Create new timetable",
            font=self.theme["fonts"]["body_large"], bg=self.theme["colors"]["secondary"],
            fg=self.theme["colors"]["text_dark"], command=self.on_add_button_click, borderwidth=0,
            highlightthickness=0, activebackground=self.theme["colors"]["secondary"],
            activeforeground=self.theme["colors"]["text_dark"])
        self.create_button.pack(pady=15, anchor="w")
        self.open_button = tk.Button(
            self.action_button_frame, compound="left", text=" Open saved timetables",
            font=self.theme["fonts"]["body_large"], bg=self.theme["colors"]["secondary"],
            fg=self.theme["colors"]["text_dark"], command=self.on_open_button_click, borderwidth=0,
            highlightthickness=0, activebackground=self.theme["colors"]["secondary"],
            activeforeground=self.theme["colors"]["text_dark"])
        self.open_button.pack(pady=15, anchor="w")

        self.add_hover_effect(self.create_button)
        self.add_hover_effect(self.open_button)

        last_active_frame = tk.Frame(home_container, bg=self.theme["colors"]["accent_bg"],
                                     highlightbackground=self.theme["colors"]["primary"], highlightthickness=1)
        last_active_frame.pack(side="bottom", fill="x", pady=(20, 0))

        self.last_active_label = tk.Label(last_active_frame, text="Last Active:",
                                          bg=self.theme["colors"]["accent_bg"],
                                          fg=self.theme["colors"]["text_dark"],
                                          font=self.theme["fonts"]["small"])
        self.last_active_label.pack(side="left", padx=(15, 5), pady=10)

        self.last_active_name_label = tk.Label(last_active_frame, text="None",
                                               bg=self.theme["colors"]["accent_bg"],
                                               fg=self.theme["colors"]["primary"],
                                               font=self.theme["fonts"]["small_bold"])
        self.last_active_name_label.pack(side="left", padx=(0, 15), pady=10)

        self.load_last_active_button = tk.Button(last_active_frame, text="Load",
                                                 command=self.load_last_active, state="disabled")
        self.apply_button_style(self.load_last_active_button, "secondary")
        self.load_last_active_button.config(padx=15, pady=0, font=self.theme["fonts"]["small_bold"])
        self.load_last_active_button.pack(side="right", padx=15, pady=5)

        self.update_last_active_display()
        self._update_button_icons()

    def update_last_active_display(self):
        last_active = self.settings.get("last_active_timetable", "")
        if last_active and os.path.exists(os.path.join(self.timetables_dir, f"{last_active}.json")):
            self.last_active_name_label.config(text=last_active)
            self.load_last_active_button.config(state="normal")
        else:
            self.last_active_name_label.config(text="None")
            self.load_last_active_button.config(state="disabled")

    def load_last_active(self):
        last_active = self.settings.get("last_active_timetable", "")
        if last_active:
            self.on_timetable_click(last_active)

    def update_home_page_status(self):
        """Updates the home page status based on the current timer state."""
        if self.is_timer_running:
            remaining = self.get_remaining_time()
            self.update_all_countdown_displays(remaining)
        else:
            self.update_all_countdown_displays(None, finished=True)

    def on_bell_status_click(self):
        if self.is_timer_running and self.current_timetable_data:
            self.show_frame("view_timetable")
        else:
            messagebox.showinfo("No Active Timetable",
                                "No timetable is currently active. Please select a timetable to start the bell system.")
            self.load_saved_timetables()
            self.show_frame("saved_timetables")

    def _configure_scroll_region(self, canvas):
        """Helper to configure scroll region and prevent content centering."""
        bbox = canvas.bbox("all")
        if bbox:
            canvas_height = canvas.winfo_height()
            scroll_height = max(bbox[3], canvas_height)
            canvas.configure(scrollregion=(bbox[0], bbox[1], bbox[2], scroll_height))

    def create_settings_page(self):
        self.settings_content_area = tk.Frame(self.settings_frame, bg=self.theme["colors"]["secondary"])
        self.settings_content_area.pack(fill="both", expand=True)
        header_frame = tk.Frame(self.settings_content_area, bg=self.theme["colors"]["secondary"])
        header_frame.pack(fill="x", padx=40, pady=(20, 0))
        self.settings_title = tk.Label(header_frame, text="Settings",
                                       bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                                       font=self.theme["fonts"]["title"])
        self.settings_title.pack(side="left", anchor="nw")
        tk.Frame(self.settings_content_area, bg=self.theme["colors"]["primary"], height=2).pack(fill="x", padx=40,
                                                                                                pady=(10, 20))
        canvas_frame = tk.Frame(self.settings_content_area, bg=self.theme["colors"]["secondary"])
        canvas_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        settings_canvas = tk.Canvas(canvas_frame, bg=self.theme["colors"]["secondary"], highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=settings_canvas.yview,
                                           style="Custom.Vertical.TScrollbar")
        settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        settings_scrollbar.pack(side="right", fill="y")
        settings_canvas.pack(side="left", fill="both", expand=True)
        options_container = tk.Frame(settings_canvas, bg=self.theme["colors"]["secondary"], padx=10)
        canvas_window = settings_canvas.create_window((0, 0), window=options_container, anchor="nw")

        options_container.bind("<Configure>", lambda e, c=settings_canvas: self._configure_scroll_region(c))

        settings_canvas.bind("<Configure>", lambda e: settings_canvas.itemconfig(canvas_window, width=e.width))

        def create_section_header(parent, title):
            tk.Label(parent, text=title, font=self.theme["fonts"]["subheader"],
                     bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"]
                     ).pack(anchor="w", pady=(25, 5))
            tk.Frame(parent, bg=self.theme["colors"]["primary"], height=1).pack(fill="x", pady=(0, 10))

        def create_setting_row(parent, text, description, widget_type, **kwargs):
            row_frame = tk.Frame(parent, bg=self.theme["colors"]["secondary"])
            row_frame.pack(fill="x", pady=8)
            text_frame = tk.Frame(row_frame, bg=self.theme["colors"]["secondary"])
            text_frame.pack(side="left", fill="x", expand=True, padx=(0, 20))
            tk.Label(text_frame, text=text, font=self.theme["fonts"]["body"],
                     bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"]
                     ).pack(anchor="w")
            tk.Label(text_frame, text=description, font=self.theme["fonts"]["small"],
                     bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                     wraplength=500, justify="left").pack(anchor="w", pady=(2, 0))
            widget_frame = tk.Frame(row_frame, bg=self.theme["colors"]["secondary"])
            widget_frame.pack(side="right")
            widget = None
            if widget_type == "toggle":
                widget = BellSystemApp.CustomToggle(widget_frame, variable=kwargs['variable'],
                                                    command=kwargs['command'])
            elif widget_type == "dropdown":
                widget = ttk.Combobox(widget_frame, textvariable=kwargs['variable'], values=kwargs['values'],
                                      width=15, state='readonly', style="Settings.TCombobox")
                widget.bind('<<ComboboxSelected>>', kwargs['command'])
            elif widget_type == "file":
                file_frame = tk.Frame(widget_frame, bg=self.theme["colors"]["secondary"])
                entry = tk.Entry(file_frame, textvariable=kwargs['variable'], font=self.theme["fonts"]["small"],
                                 bg=self.theme['colors']['accent_bg'], fg=self.theme['colors']['text_dark'],
                                 width=25, relief='flat', state="readonly")
                entry.pack(side="left")
                browse_btn = tk.Button(file_frame, text="Browse", font=self.theme["fonts"]["small_bold"],
                                       bg=self.theme['colors']['primary'], fg=self.theme['colors']['text_light'],
                                       relief="flat", padx=10, command=lambda: self.browse_file(kwargs['variable']))
                browse_btn.pack(side="left", padx=(5, 0))
                widget = file_frame
            if widget: widget.pack()

        create_section_header(options_container, "Appearance")
        create_setting_row(options_container, "Dark Mode", "Switch between light and dark themes.",
                           "toggle", variable=self.dark_mode_var, command=self.toggle_dark_mode)
        create_setting_row(options_container, "Font Size", "Adjust the overall font size.",
                           "dropdown", variable=self.font_size_var, values=["Small", "Medium", "Large"],
                           command=lambda e: self.update_setting("font_size", self.font_size_var.get()))
        create_section_header(options_container, "System Integration")
        create_setting_row(options_container, "Run on Windows Startup", "Automatically start when Windows boots",
                           "toggle", variable=self.run_on_startup_var,
                           command=lambda: self.update_setting("run_on_startup", self.run_on_startup_var.get()))
        create_setting_row(options_container, "Minimize to System Tray",
                           "On close, minimize to tray instead of showing exit dialog", "toggle",
                           variable=self.minimize_to_tray_var,
                           command=lambda: self.update_setting("minimize_to_tray", self.minimize_to_tray_var.get()))
        create_section_header(options_container, "Bell System Behavior")
        create_setting_row(options_container, "Default Bell Volume", "Set the default volume for bell sounds",
                           "dropdown", variable=self.bell_volume_var, values=["10%", "25%", "50%", "75%", "100%"],
                           command=lambda e: self.update_setting("bell_volume", self.bell_volume_var.get()))
        create_setting_row(options_container, "Fade In/Out Bell Sounds", "Gradually fade bell sounds in and out",
                           "toggle", variable=self.bell_fade_var,
                           command=lambda: self.update_setting("bell_fade", self.bell_fade_var.get()))
        create_section_header(options_container, "Backup & Recovery")
        create_setting_row(options_container, "Backup Location", "Choose where to store timetable backups", "file",
                           variable=self.backup_location_var)
        button_frame = tk.Frame(self.settings_content_area, bg=self.theme["colors"]["secondary"])
        button_frame.pack(fill="x", padx=40, pady=20)
        reset_btn = tk.Button(button_frame, text="Reset to Defaults", command=self.reset_settings_to_defaults)
        self.apply_button_style(reset_btn, "secondary")
        reset_btn.pack(side="left")
        export_btn = tk.Button(button_frame, text="Export Settings", command=self.export_settings)
        self.apply_button_style(export_btn, "secondary")
        export_btn.pack(side="left", padx=(10, 0))
        import_btn = tk.Button(button_frame, text="Import Settings", command=self.import_settings)
        self.apply_button_style(import_btn, "secondary")
        import_btn.pack(side="left", padx=(10, 0))

        self.bind_mousewheel(settings_canvas, options_container)

    def toggle_dark_mode(self):
        self.update_setting("theme", "dark" if self.dark_mode_var.get() else "light")

    def update_setting(self, key, value):
        """Updates a setting, saves it, and applies it in real-time."""
        old_value = self.settings.get(key)
        self.settings[key] = value
        self.save_settings()

        if key in ["theme", "font_size"]:
            state = self._save_ui_state()
            self.rebuild_ui()
            self._restore_ui_state(state)
            self.show_frame(state.get('current_frame', 'home'))
        elif key == "run_on_startup":
            if old_value != value:
                self.set_startup()
                if value:
                    current_status = self.check_startup_status()
                    if not current_status:
                        messagebox.showwarning("Startup Setting",
                                               "The startup setting may not have been applied successfully. "
                                               "Try running the application as Administrator.")

    def browse_file(self, var):
        folder = filedialog.askdirectory(title="Select Backup Location")
        if folder:
            var.set(folder)
            self.update_setting("backup_location", folder)

    def reset_settings_to_defaults(self):
        if messagebox.askyesno("Reset Settings",
                               "Are you sure you want to reset all settings to defaults? This cannot be undone."):
            defaults = {
                "run_on_startup": False, "minimize_to_tray": False, "theme": "light",
                "font_size": "Medium", "bell_volume": "75%", "last_active_timetable": "",
                "bell_fade": True, "backup_location": ""
            }
            state = self._save_ui_state()

            for key, value in defaults.items():
                self.settings[key] = value

            self.dark_mode_var.set(defaults["theme"] == "dark")
            self.run_on_startup_var.set(defaults["run_on_startup"])
            self.minimize_to_tray_var.set(defaults["minimize_to_tray"])
            self.bell_fade_var.set(defaults["bell_fade"])
            self.font_size_var.set(defaults["font_size"])
            self.bell_volume_var.set(defaults["bell_volume"])
            self.backup_location_var.set(defaults["backup_location"])

            self.save_settings()
            self.set_startup()
            self.rebuild_ui()
            self._restore_ui_state(state)
            self.show_frame(state.get('current_frame', 'home'))

            messagebox.showinfo("Settings Reset", "All settings have been reset to their default values.")

    def export_settings(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")],
                                                 title="Export Settings")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.settings, f, indent=4)
                messagebox.showinfo("Export Successful", f"Settings exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export settings: {e}")

    def import_settings(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], title="Import Settings")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported_settings = json.load(f)
                if messagebox.askyesno("Import Settings", "This will overwrite your current settings. Continue?"):
                    state = self._save_ui_state()
                    self.settings.update(imported_settings)

                    self.dark_mode_var.set(self.settings.get("theme") == "dark")
                    self.run_on_startup_var.set(self.settings.get("run_on_startup", False))
                    self.minimize_to_tray_var.set(self.settings.get("minimize_to_tray", False))
                    self.bell_fade_var.set(self.settings.get("bell_fade", True))
                    self.font_size_var.set(self.settings.get("font_size", "Medium"))
                    self.bell_volume_var.set(self.settings.get("bell_volume", "75%"))
                    self.backup_location_var.set(self.settings.get("backup_location", ""))

                    self.save_settings()
                    self.set_startup()
                    self.rebuild_ui()
                    self._restore_ui_state(state)
                    self.show_frame(state.get('current_frame', 'home'))

            except Exception as e:
                messagebox.showerror("Import Failed", f"Failed to import settings: {e}")

    def set_startup(self):
        if os.name != 'nt':
            return

        import winreg
        # CHANGED: Added '_v2' to the app name for startup registry to avoid conflict with v1
        app_name = "SchoolBellSystem_v2"
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)

            if self.settings.get("run_on_startup", False):
                if getattr(sys, 'frozen', False):
                    executable_path = f'"{sys.executable}"'
                else:
                    python_executable = sys.executable.replace('python.exe', 'pythonw.exe')
                    script_path = os.path.abspath(sys.argv[0])
                    executable_path = f'"{python_executable}" "{script_path}"'

                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, executable_path)
                print(f"Startup enabled: {executable_path}")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    print("Startup disabled")
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)

        except PermissionError:
            messagebox.showerror("Permission Error",
                                 "Could not modify startup settings due to insufficient permissions.\n\n"
                                 "Try running the application as Administrator once to set this option.")
        except Exception as e:
            messagebox.showerror("Startup Error",
                                 f"Could not modify startup settings: {e}")

    def check_startup_status(self):
        if os.name != 'nt':
            return False

        import winreg
        # CHANGED: Added '_v2' here as well
        app_name = "SchoolBellSystem_v2"
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, app_name)
                winreg.CloseKey(key)
                print(f"Startup entry found: {value}")
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                print("No startup entry found")
                return False
        except Exception as e:
            print(f"Error checking startup status: {e}")
            return False

    def bind_mousewheel(self, canvas, widget):
        """Binds mousewheel events to a widget and its children to scroll the canvas."""

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        widget.bind('<MouseWheel>', _on_mousewheel, add="+")
        widget.bind('<Button-4>', _on_mousewheel_linux, add="+")
        widget.bind('<Button-5>', _on_mousewheel_linux, add="+")

        for child in widget.winfo_children():
            self.bind_mousewheel(canvas, child)

    def create_about_page(self):
        self.about_content_area = tk.Frame(self.about_frame, bg=self.theme["colors"]["secondary"])
        self.about_content_area.pack(fill="both", expand=True)
        header_frame = tk.Frame(self.about_content_area, bg=self.theme["colors"]["secondary"])
        header_frame.pack(fill="x", pady=(30, 20), padx=40)
        self.about_title = tk.Label(header_frame, text="About School Bell System",
                                    bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                                    font=self.theme["fonts"]["header"], anchor="w", justify="left")
        self.about_title.pack(fill="x")
        version_label = tk.Label(header_frame, text="Version 1.0", bg=self.theme["colors"]["secondary"],
                                 fg=self.theme["colors"]["text_dark"], font=self.theme["fonts"]["small"], anchor="w",
                                 justify="left")
        version_label.pack(fill="x")
        self.about_line_separator = tk.Frame(self.about_content_area, bg=self.theme["colors"]["primary"], height=2)
        self.about_line_separator.pack(fill="x", padx=40, pady=(0, 30))
        canvas_frame = tk.Frame(self.about_content_area, bg=self.theme["colors"]["secondary"])
        canvas_frame.pack(fill="both", expand=True, padx=40, pady=(0, 30))
        about_canvas = tk.Canvas(canvas_frame, bg=self.theme["colors"]["secondary"], highlightthickness=0)
        about_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=about_canvas.yview,
                                        style="Custom.Vertical.TScrollbar")
        about_canvas.configure(yscrollcommand=about_scrollbar.set)

        def on_configure(event=None):
            bbox = about_canvas.bbox("all")
            if bbox:
                canvas_height = about_canvas.winfo_height()
                scroll_height = max(bbox[3], canvas_height)
                about_canvas.configure(scrollregion=(bbox[0], bbox[1], bbox[2], scroll_height))
            if bbox and about_canvas.winfo_height() < bbox[3]:
                about_scrollbar.pack(side="right", fill="y")
            else:
                about_scrollbar.pack_forget()

        about_scrollbar.pack(side="right", fill="y")
        about_canvas.pack(side="left", fill="both", expand=True)
        scrollable_content = tk.Frame(about_canvas, bg=self.theme["colors"]["secondary"])
        canvas_window = about_canvas.create_window((0, 0), window=scrollable_content, anchor="nw")
        scrollable_content.bind("<Configure>", on_configure)
        about_canvas.bind("<Configure>", lambda e: about_canvas.itemconfig(canvas_window, width=e.width))

        columns_container = tk.Frame(scrollable_content, bg=self.theme["colors"]["secondary"])
        columns_container.pack(fill="both", expand=True, pady=(0, 20))
        left_frame = tk.Frame(columns_container, bg=self.theme["colors"]["secondary"])
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right_frame = tk.Frame(columns_container, bg=self.theme["colors"]["secondary"])
        right_frame.pack(side="right", fill="both", expand=True, padx=(20, 0))
        desc_title = tk.Label(left_frame, text="Our Mission", bg=self.theme["colors"]["secondary"],
                              fg=self.theme["colors"]["primary"], font=self.theme["fonts"]["subheader"])
        desc_title.pack(anchor="w", pady=(0, 15))
        desc_text = """School Bell System is designed to provide educational institutions with a reliable, easy-to-use bell scheduling solution. 

    I created this application to ensure punctual and organized school operations.

    This application represents my first software project, born from a genuine need to solve a practical problem in educational environments."""

        desc_label = tk.Label(left_frame, text=desc_text, bg=self.theme["colors"]["secondary"],
                              fg=self.theme["colors"]["text_dark"], font=self.theme["fonts"]["body"], justify="left")
        desc_label.pack(anchor="w", fill="both")

        def on_about_resize(event):
            desc_label.config(wraplength=event.width - 10)

        left_frame.bind("<Configure>", on_about_resize)
        features_title = tk.Label(right_frame, text="Key Features", bg=self.theme["colors"]["secondary"],
                                  fg=self.theme["colors"]["primary"], font=self.theme["fonts"]["subheader"])
        features_title.pack(anchor="w", pady=(0, 15))
        features = ["• Custom timetable creation", "• Precise bell scheduling", "• Multiple sound options",
                    "• Intuitive visual dashboard", "• Easy integration with existing schedules",
                    "• Modern, user-friendly interface"]
        for feature in features:
            feat_label = tk.Label(right_frame, text=feature, bg=self.theme["colors"]["secondary"],
                                  fg=self.theme["colors"]["text_dark"], font=self.theme["fonts"]["body"],
                                  justify="left", anchor="w")
            feat_label.pack(anchor="w", pady=(0, 8))
        bottom_frame = tk.Frame(scrollable_content, bg=self.theme["colors"]["secondary"])
        bottom_frame.pack(side="bottom", fill="x", pady=(50, 30))
        self.thank_you_label = tk.Label(bottom_frame, text="Thank you for choosing School Bell System",
                                        bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["primary"],
                                        font=self.theme["fonts"]["body_bold"])
        self.thank_you_label.pack(pady=(0, 10))
        credit_label = tk.Label(bottom_frame, text="Created by Malinda Lakshan",
                                bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                                font=self.theme["fonts"]["small"])
        credit_label.pack()

        self.bind_mousewheel(about_canvas, scrollable_content)

    def create_timetable_page(self):
        content_frame = tk.Frame(self.create_timetable_frame, bg=self.theme["colors"]["secondary"])
        content_frame.pack(fill="both", expand=True, padx=50, pady=30)

        header_bar_frame = tk.Frame(content_frame, bg=self.theme["colors"]["secondary"])
        header_bar_frame.pack(fill="x", pady=(5, 5))

        title_label = tk.Label(header_bar_frame, text="Let's create a new Timetable",
                               bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                               font=self.theme["fonts"]["header"])
        title_label.pack(side="left", anchor="nw")

        bell_icon_label = tk.Label(header_bar_frame, text="🔔",
                                   bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                                   font=self.theme["fonts"]["header"])
        bell_icon_label.pack(side="right", anchor="ne", padx=10)

        tk.Frame(content_frame, bg=self.theme['colors']['primary'], height=2).pack(fill="x", pady=(5, 25))
        name_frame = tk.Frame(content_frame, bg=self.theme["colors"]["secondary"])
        name_frame.pack(fill="x", pady=(0, 20))
        tk.Label(name_frame, text="Timetable name:", bg=self.theme["colors"]["secondary"],
                 fg=self.theme["colors"]["text_dark"], font=self.theme["fonts"]["body_large"]).pack(side="left",
                                                                                                    padx=(0, 20))
        self.timetable_name_entry = tk.Entry(name_frame, font=self.theme["fonts"]["body"],
                                             bg=self.theme['colors']['accent_bg'],
                                             fg=self.theme['colors']['text_dark'], highlightthickness=2,
                                             relief="solid", bd=0,
                                             highlightbackground=self.theme['colors']['primary'])
        self.timetable_name_entry.pack(side="left", fill="x", expand=True, ipady=5)

        tk.Frame(content_frame, bg=self.theme['colors']['primary'], height=2).pack(fill="x", pady=(10, 10))

        main_content_frame = tk.Frame(content_frame, bg=self.theme['colors']['accent_bg'], relief="solid", bd=0,
                                      highlightthickness=1.5,
                                      highlightbackground=self.theme['colors']['primary'])
        main_content_frame.pack(fill="both", expand=True)

        setup_title_label = tk.Label(main_content_frame, text="Setup Your Schedules Here",
                                     bg=self.theme['colors']['accent_bg'],
                                     fg=self.theme['colors']['primary'],
                                     font=self.theme["fonts"]["body_bold"])
        setup_title_label.grid(row=0, column=0, pady=(10, 10))

        main_content_frame.grid_rowconfigure(1, weight=1)
        main_content_frame.grid_columnconfigure(0, weight=1)

        canvas_frame = tk.Frame(main_content_frame, bg=self.theme['colors']['accent_bg'])
        canvas_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 10), padx=10)
        self.canvas = tk.Canvas(canvas_frame, bg=self.theme['colors']['accent_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview,
                                  style="Custom.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.periods_container = tk.Frame(self.canvas, bg=self.theme['colors']['accent_bg'])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.periods_container, anchor="nw")

        self.periods_container.bind("<Configure>",
                                    lambda e, c=self.canvas: self._configure_scroll_region(c))

        self.bind_mousewheel(self.canvas, self.periods_container)

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        add_period_button = tk.Button(main_content_frame, text="Add period +", command=self.add_period_row,
                                      font=self.theme['fonts']['button_bold'], bg=self.theme['colors']['primary'],
                                      fg=self.theme['colors']['text_light'], relief="flat", borderwidth=0, padx=20,
                                      pady=5)
        add_period_button.grid(row=2, column=0, pady=(5, 15))
        button_frame = tk.Frame(content_frame, bg=self.theme["colors"]["secondary"])
        button_frame.pack(fill="x", pady=(20, 0))
        save_button = tk.Button(button_frame, text="Save", command=self.save_timetable)
        self.apply_button_style(save_button, "primary")
        save_button.pack(side="right", padx=(10, 0))
        cancel_button = tk.Button(button_frame, text="Cancel", command=lambda: self.show_frame("home"))
        self.apply_button_style(cancel_button, "secondary")
        cancel_button.pack(side="right")

    def create_saved_timetables_page(self):
        content_frame = tk.Frame(self.saved_timetables_frame, bg=self.theme["colors"]["secondary"])
        content_frame.pack(fill="both", expand=True, padx=50, pady=30)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)
        title_label = tk.Label(content_frame, text="Saved Timetables", bg=self.theme["colors"]["secondary"],
                               fg=self.theme["colors"]["text_dark"], font=self.theme["fonts"]["header"])
        title_label.grid(row=0, column=0, sticky="nw", pady=(5, 5))
        tk.Frame(content_frame, bg=self.theme['colors']['primary'], height=2).grid(row=0, column=0, sticky="ew",
                                                                                   pady=(75, 25), padx=6)
        scrollable_outer_frame = tk.Frame(content_frame, bg=self.theme["colors"]["secondary"])
        scrollable_outer_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        scrollable_outer_frame.columnconfigure(0, weight=1)
        scrollable_outer_frame.rowconfigure(0, weight=1)
        self.saved_canvas = tk.Canvas(scrollable_outer_frame, bg=self.theme["colors"]["secondary"],
                                      highlightthickness=0)
        saved_scrollbar = ttk.Scrollbar(scrollable_outer_frame, orient="vertical", command=self.saved_canvas.yview,
                                        style="Custom.Vertical.TScrollbar")
        self.saved_canvas.configure(yscrollcommand=saved_scrollbar.set)
        saved_scrollbar.grid(row=0, column=1, sticky="ns")
        self.saved_canvas.grid(row=0, column=0, sticky="nsew")
        self.timetables_list_frame = tk.Frame(self.saved_canvas, bg=self.theme["colors"]["secondary"])
        canvas_window_id = self.saved_canvas.create_window((0, 0), window=self.timetables_list_frame, anchor="nw")

        self.timetables_list_frame.bind("<Configure>",
                                        lambda e, c=self.saved_canvas: self._configure_scroll_region(c))

        self.bind_mousewheel(self.saved_canvas, self.timetables_list_frame)
        self.bind_mousewheel(self.saved_canvas, self.saved_canvas)  # Binds the empty background too

        self.saved_canvas.bind("<Configure>",
                               lambda e: self.saved_canvas.itemconfig(canvas_window_id, width=e.width))

        create_another_frame = tk.Frame(content_frame, bg=self.theme["colors"]["secondary"])
        create_another_frame.grid(row=2, column=0, pady=(20, 0))
        create_another_button = tk.Button(create_another_frame, image=self.create_another_icon_photo,
                                          text=" Create another timetable", compound="left", font=("Poppins", 18),
                                          bg=self.theme["colors"]["secondary"],
                                          fg=self.theme["colors"]["text_dark"], command=self.on_add_button_click,
                                          borderwidth=0, highlightthickness=0,
                                          activebackground=self.theme["colors"]["secondary"],
                                          activeforeground=self.theme["colors"]["text_dark"])
        create_another_button.pack(pady=10)

    def create_view_timetable_page(self):
        content_frame = tk.Frame(self.view_timetable_frame, bg=self.theme["colors"]["secondary"])
        content_frame.pack(fill="both", expand=True, padx=50, pady=30)

        # 1. Header Section (Title + Bell)
        header_frame = tk.Frame(content_frame, bg=self.theme["colors"]["secondary"])
        header_frame.pack(fill="x", pady=(0, 5))

        self.view_timetable_name_label = tk.Label(header_frame, text="Timetable Name Here",
                                                  bg=self.theme["colors"]["secondary"],
                                                  fg=self.theme["colors"]["text_dark"],
                                                  font=self.theme["fonts"]["header"])
        self.view_timetable_name_label.pack(side="left", anchor="nw")

        bell_label = tk.Label(header_frame, text="🔔", bg=self.theme["colors"]["secondary"],
                              fg=self.theme["colors"]["text_dark"], font=("Arial", 24))
        bell_label.pack(side="right", anchor="ne")

        tk.Frame(content_frame, bg=self.theme['colors']['primary'], height=2).pack(fill="x", pady=(5, 10))

        # 2. Main Content Box
        main_box_frame = tk.Frame(content_frame, bg=self.theme['colors']['accent_bg'], relief="solid", bd=0,
                                  highlightthickness=1.5, highlightbackground=self.theme['colors']['primary'])
        main_box_frame.pack(fill="both", expand=True)

        # Setup grid for main box frame
        main_box_frame.grid_rowconfigure(1, weight=1)  # Content row
        main_box_frame.grid_columnconfigure(0, weight=1)

        # 3. Sub-Header Text (Inside the box)
        sub_header_label = tk.Label(main_box_frame, text="This is the place where your schedules\nare running.",
                                    bg=self.theme['colors']['accent_bg'],
                                    fg=self.theme["colors"]["primary"],
                                    font=self.theme["fonts"]["subheader"], justify="center")
        sub_header_label.grid(row=0, column=0, pady=(10, 10))

        # Canvas frame
        canvas_frame = tk.Frame(main_box_frame, bg=self.theme['colors']['accent_bg'])
        canvas_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20), padx=10)

        self.view_canvas = tk.Canvas(canvas_frame, bg=self.theme['colors']['accent_bg'], highlightthickness=0)
        view_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.view_canvas.yview,
                                       style="Custom.Vertical.TScrollbar")
        self.view_canvas.configure(yscrollcommand=view_scrollbar.set)

        view_scrollbar.pack(side="right", fill="y")
        self.view_canvas.pack(side="left", fill="both", expand=True)

        self.periods_list_frame = tk.Frame(self.view_canvas, bg=self.theme['colors']['accent_bg'])
        self.view_canvas_window = self.view_canvas.create_window((0, 0), window=self.periods_list_frame, anchor="nw")

        self.periods_list_frame.bind("<Configure>",
                                     lambda e, c=self.view_canvas: self._configure_scroll_region(c))

        self.bind_mousewheel(self.view_canvas, self.periods_list_frame)

        self.view_canvas.bind("<Configure>",
                              lambda e: self.view_canvas.itemconfig(self.view_canvas_window, width=e.width))

        # 4. Footer Section
        bottom_frame = tk.Frame(content_frame, bg=self.theme["colors"]["secondary"])
        bottom_frame.pack(fill="x", pady=(20, 0))

        # "The next bell is in" + Timer
        timer_frame = tk.Frame(bottom_frame, bg=self.theme["colors"]["secondary"])
        timer_frame.pack(anchor="w", pady=(0, 10))

        tk.Label(timer_frame, text="The next bell is in", bg=self.theme["colors"]["secondary"],
                 fg=self.theme["colors"]["text_dark"], font=("Poppins", 16)).pack(side="left")

        self.next_bell_time_label = tk.Label(timer_frame, text="00:00:00",
                                             bg=self.theme['colors']['secondary'],
                                             fg=self.theme['colors']['text_dark'],
                                             font=("Poppins", 16),
                                             relief="solid", bd=1, padx=15, pady=5)
        self.next_bell_time_label.pack(side="left", padx=(15, 0))

        # ---------------------------------------------------------------------
        # LOCATE THIS SECTION IN: create_view_timetable_page
        # REPLACE THE PREVIOUS "Back and Start Buttons" CODE WITH THIS:
        # ---------------------------------------------------------------------

        # Back, Start, and Edit Buttons container
        action_buttons_frame = tk.Frame(bottom_frame, bg=self.theme["colors"]["secondary"])
        action_buttons_frame.pack(fill="x")

        # Back Button (Stays on the left)
        back_button = tk.Button(action_buttons_frame, text="← Back",
                                command=lambda: self.show_frame("saved_timetables"),
                                bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                                font=self.theme["fonts"]["body"], borderwidth=0,
                                activebackground=self.theme["colors"]["secondary"])
        back_button.pack(side="left", anchor="sw")

        # --- NEW: Right side container to stack Start and Edit buttons vertically ---
        right_buttons_frame = tk.Frame(action_buttons_frame, bg=self.theme["colors"]["secondary"])
        right_buttons_frame.pack(side="right", anchor="se")

        # Start Button (Top)
        self.start_stop_button = tk.Button(right_buttons_frame, text="Start", command=self.toggle_bell_system)
        self.start_stop_button.config(bg=self.theme['colors']['primary'], fg=self.theme['colors']['text_light'],
                                      font=self.theme['fonts']['button'], relief="flat", borderwidth=0, padx=40, pady=8)
        self.start_stop_button.pack(fill="x", pady=(0, 10))  # Added padding to separate from Edit button

        # Edit Button (Bottom)
        self.edit_button = tk.Button(right_buttons_frame, text="Edit", command=self.edit_timetable)
        self.apply_button_style(self.edit_button, "secondary")  # Applies the outline style
        self.edit_button.pack(fill="x")

    def load_timetable_view(self):
        if not self.current_timetable_data: return
        self.view_timetable_name_label.config(text=self.current_timetable_data["timetable_name"])
        for widget in self.periods_list_frame.winfo_children(): widget.destroy()
        self.view_period_rows.clear()

        for i, period in enumerate(self.current_timetable_data["periods"]):
            # Use grid for alignment matching Create Timetable
            row_frame = tk.Frame(self.periods_list_frame, bg=self.theme['colors']['accent_bg'])
            row_frame.pack(fill="x", expand=True, pady=5, padx=10)

            # Column configuration matching Create Timetable
            col_configs = {
                0: {'minsize': 40},  # Number
                1: {'weight': 3, 'minsize': 100},  # Period Box
                2: {'minsize': 175},  # Time Box
                3: {'weight': 2, 'minsize': 100},  # Sound Box
                4: {'minsize': 50}  # Status Circle
            }
            for col, config in col_configs.items():
                if 'weight' in config:
                    row_frame.columnconfigure(col, weight=config['weight'], minsize=config.get('minsize', 0))
                if 'minsize' in config and 'weight' not in config:
                    row_frame.columnconfigure(col, minsize=config['minsize'])

            # 1. Number (Red Text)
            no_label = tk.Label(row_frame, text=f"{i + 1:02d}.",
                                bg=self.theme['colors']['accent_bg'],
                                fg=self.theme['colors']['primary'],
                                font=self.theme["fonts"]["body_bold"])
            no_label.grid(row=0, column=0, sticky="w")

            # 2. Name Box - Styled to look EXACTLY like Entry (White BG, Red Border)
            # Using a Frame wrapper to simulate border thickness
            name_wrapper = tk.Frame(row_frame, bg=self.theme['colors']['primary'], padx=2, pady=2)
            name_wrapper.grid(row=0, column=1, sticky="ew", padx=(0, 10))

            # --- FIX: Added width=1 to lock resizing logic (it stretches due to weight) ---
            name_label = tk.Label(name_wrapper, text=period["period"],
                                  bg=self.theme['colors']['secondary'],
                                  fg=self.theme['colors']['primary'],
                                  font=("Poppins", 14),
                                  anchor="w", padx=5, width=1)
            name_label.pack(fill="both", expand=True)

            # 3. Time Box (Red BG, White Text) - Styled like Create Time Button
            # --- FIX: Added width=18 to lock size ---
            time_label = tk.Label(row_frame, text=period["time"],
                                  bg=self.theme['colors']['primary'],
                                  fg=self.theme['colors']['text_light'],
                                  font=self.theme['fonts']['small'],
                                  pady=5, width=18)
            time_label.grid(row=0, column=2, sticky="ew")

            # 4. Sound Box (White BG, Red Border) - Styled like Create Sound Button
            file_name = os.path.basename(period["sound_file"])
            # Truncate display name if too long to fit cleanly
            display_name = (file_name[:8] + "..." + file_name[-8:]) if len(file_name) > 20 else file_name

            # Wrapper for border
            sound_wrapper = tk.Frame(row_frame, bg=self.theme['colors']['primary'], padx=2, pady=2)
            sound_wrapper.grid(row=0, column=3, sticky="ewns", padx=10)

            # --- FIX: Added width=1 to lock resizing logic ---
            sound_label = tk.Label(sound_wrapper, text=display_name,
                                   bg=self.theme['colors']['secondary'],
                                   fg=self.theme['colors']['primary'],
                                   font=self.theme['fonts']['small'], width=1)
            sound_label.pack(fill="both", expand=True)

            # 5. Status Circle
            status_canvas = tk.Canvas(row_frame, width=30, height=30, bg=self.theme['colors']['accent_bg'],
                                      highlightthickness=0)
            status_canvas.grid(row=0, column=4, sticky="e")
            status_circle = status_canvas.create_oval(2, 2, 28, 28, outline=self.theme['colors']['primary'], width=2)

            self.view_period_rows.append({
                "period": period,
                "status_canvas": status_canvas,
                "status_circle": status_circle,
                "index": i
            })

            # Bind mousewheel to the new row
            self.bind_mousewheel(self.view_canvas, row_frame)
            self.bind_mousewheel(self.view_canvas, name_wrapper)
            self.bind_mousewheel(self.view_canvas, name_label)
            self.bind_mousewheel(self.view_canvas, time_label)
            self.bind_mousewheel(self.view_canvas, sound_wrapper)
            self.bind_mousewheel(self.view_canvas, sound_label)
            self.bind_mousewheel(self.view_canvas, status_canvas)

        self.periods_list_frame.update_idletasks()
        self.update_all_countdown_displays(None)

    def toggle_bell_system(self):
        if not self.is_timer_running:
            self.start_bell_system()
        else:
            self.stop_bell_system()

    def start_bell_system(self):
        if self.current_timetable_data:
            self.update_setting("last_active_timetable", self.current_timetable_data.get("timetable_name", ""))
        self.is_timer_running = True
        if hasattr(self, 'start_stop_button'): self.start_stop_button.config(text="Stop")

        for row in self.view_period_rows:
            row["status_canvas"].itemconfig(row["status_circle"], fill="")

        self.timer_stop_event.clear()
        self.bell_timer_thread = threading.Thread(target=self.bell_timer_loop, daemon=True)
        self.bell_timer_thread.start()
        self.update_home_page_status()

    def stop_bell_system(self):
        self.is_timer_running = False
        self.timer_stop_event.set()
        if hasattr(self, 'start_stop_button'): self.start_stop_button.config(text="Start")
        self.update_all_countdown_displays(None, finished=True)

    def update_all_countdown_displays(self, remaining_delta, finished=False):
        """A single function to update all countdown-related UI elements."""
        text = "00:00:00"
        if not self.is_timer_running and not finished:
            text = "00:00:00"
        elif finished:
            text = "Finished"
        elif remaining_delta:
            total_seconds = int(remaining_delta.total_seconds())
            h, rem = divmod(total_seconds, 3600)
            m, s = divmod(rem, 60)
            text = f"{h:02d}:{m:02d}:{s:02d}"

        if hasattr(self, 'next_bell_time_label') and self.next_bell_time_label.winfo_exists():
            self.next_bell_time_label.config(text=text)

        if hasattr(self, 'home_bell_status_button') and self.home_bell_status_button.winfo_exists():
            if self.is_timer_running and self.current_timetable_data and not finished:
                status_text = f"🔔 {self.current_timetable_data['timetable_name']} - Next: {text}"
                self.home_bell_status_button.config(text=status_text,
                                                    bg=self.theme["colors"]["accent_bg"],
                                                    fg=self.theme["colors"]["primary"],
                                                    activebackground=self.theme["colors"]["accent_bg"],
                                                    activeforeground=self.theme["colors"]["primary"])
            else:
                self.home_bell_status_button.config(text="🔕 Bell system inactive",
                                                    bg=self.theme["colors"]["secondary"],
                                                    fg=self.theme["colors"]["primary"],
                                                    activebackground=self.theme["colors"]["secondary"],
                                                    activeforeground=self.theme["colors"]["primary"])

        if self.is_timer_running and self.current_timetable_data:
            if not finished:
                self.master.title(f"School Bell System - Next bell in {text}")
            else:
                self.master.title("School Bell System - Running (Finished)")
        else:
            self.master.title("School Bell System")

    def bell_timer_loop(self):
        """
        CRITICAL FIX: Call ring_bell() DIRECTLY instead of scheduling it.
        The diagnostic proved that .after() has 553ms average delay on this system.
        """
        while self.is_timer_running and not self.timer_stop_event.is_set():
            self.find_next_bell()
            if self.next_bell_info:
                bell_time = self.next_bell_info["datetime"]

                # Wait loop until the specific bell time
                while self.is_timer_running and datetime.now() < bell_time:
                    now = datetime.now()
                    remaining = bell_time - now

                    # Update the countdown UI (schedule this, it's not critical)
                    self.master.after(0, self.update_all_countdown_displays, remaining)

                    total_seconds = remaining.total_seconds()

                    # DYNAMIC SLEEP STRATEGY:
                    if total_seconds > 1:
                        wait_time = 0.5
                    elif total_seconds > 0.1:
                        wait_time = 0.1
                    else:
                        wait_time = 0.01

                    if self.timer_stop_event.wait(wait_time):
                        break

                if not self.is_timer_running or self.timer_stop_event.is_set():
                    break

                # CRITICAL FIX: Call ring_bell() DIRECTLY (not scheduled)
                # This executes immediately instead of waiting 553ms for GUI thread
                if self.is_timer_running:
                    self.ring_bell()  # Direct call - no more .after()!

                    # Wait to ensure we're past the bell second
                    time.sleep(1.0)
            else:
                # No more bells today or tomorrow?
                self.master.after(0, self.update_all_countdown_displays, None, finished=True)
                self.is_timer_running = False
                self.master.after(0, self.stop_bell_system)
                break

            # Small yield to prevent CPU hogging in tight loops
            if self.timer_stop_event.wait(0.1):
                break

        print("Bell timer loop exiting.")

    def ring_bell(self):
        """
        CRITICAL FIX: Play audio directly from background thread.
        Only schedule UI updates on the GUI thread.

        The diagnostic showed 553ms average delay when scheduling on GUI thread.
        This was causing bells to be missed.
        """
        if not self.next_bell_info:
            return

        info = self.next_bell_info
        row_data = self.view_period_rows[info["index"]]
        sound_file = info["period"]["sound_file"]

        # Schedule only the UI countdown update (non-critical)
        self.master.after(0, self.update_all_countdown_displays, None)

        try:
            # CRITICAL: Play audio DIRECTLY from this thread (no scheduling)
            # Pygame audio calls are thread-safe
            pygame.mixer.stop()  # Stop any currently playing sound
            time.sleep(0.05)  # Brief pause

            sound = pygame.mixer.Sound(sound_file)
            volume_str = self.settings.get("bell_volume", "75%").replace('%', '')
            sound.set_volume(float(volume_str) / 100.0)

            print(f"🔔 Ringing bell at {datetime.now().strftime('%I:%M:%S %p')}: {info['period'].get('name', 'Bell')}")

            if self.settings.get("bell_fade", True):
                channel = sound.play(fade_ms=1000)
            else:
                channel = sound.play()

            # Verify it's actually playing
            if channel and channel.get_busy():
                # Schedule UI update (can be delayed, not critical)
                self.master.after(0, lambda: row_data["status_canvas"].itemconfig(
                    row_data["status_circle"], fill=self.theme['colors']['primary']))
                print(f"✅ Bell playing successfully")
            else:
                print(f"⚠️ Bell scheduled but channel not busy")
                self.master.after(0, lambda: row_data["status_canvas"].itemconfig(
                    row_data["status_circle"], fill="orange"))

        except Exception as e:
            print(f"❌ Error playing sound {sound_file}: {e}")
            import traceback
            traceback.print_exc()
            # Schedule UI error indicator
            self.master.after(0, lambda: row_data["status_canvas"].itemconfig(
                row_data["status_circle"], fill="red"))

    def find_next_bell(self):
        if not self.current_timetable_data:
            self.next_bell_info = None
            return

        all_periods = self.current_timetable_data.get("periods", [])
        if not all_periods:
            self.next_bell_info = None
            return

        parsed_periods = []
        for i, period in enumerate(all_periods):
            try:
                bell_time_obj = datetime.strptime(period["time"], "%I:%M:%S %p").time()
                parsed_periods.append({"period": period, "index": i, "time_obj": bell_time_obj})
            except Exception as e:
                print(f"Error parsing time {period['time']}: {e}")

        if not parsed_periods:
            self.next_bell_info = None
            return

        now = datetime.now()

        # FIX: Add 2-second buffer to prevent re-detecting just-rung bells
        # Since we sleep for 1.0s after ringing, this ensures we never find the same bell twice
        now_with_buffer = now + timedelta(seconds=2)
        now_time_buffered = now_with_buffer.time()

        # FIX: Use strict > comparison (not >=) with buffered time
        today_bells = [p for p in parsed_periods if p["time_obj"] > now_time_buffered]

        if today_bells:
            next_bell_data = min(today_bells, key=lambda p: p["time_obj"])
            bell_time_obj = next_bell_data["time_obj"]
            today_bell_dt = now.replace(hour=bell_time_obj.hour, minute=bell_time_obj.minute,
                                        second=bell_time_obj.second, microsecond=0)
            self.next_bell_info = {"period": next_bell_data["period"],
                                   "index": next_bell_data["index"],
                                   "datetime": today_bell_dt}
        else:
            first_bell_data = min(parsed_periods, key=lambda p: p["time_obj"])
            bell_time_obj = first_bell_data["time_obj"]
            tomorrow_bell_dt = (now + timedelta(days=1)).replace(hour=bell_time_obj.hour,
                                                                 minute=bell_time_obj.minute,
                                                                 second=bell_time_obj.second, microsecond=0)
            self.next_bell_info = {"period": first_bell_data["period"],
                                   "index": first_bell_data["index"],
                                   "datetime": tomorrow_bell_dt}

    def get_remaining_time(self):
        if self.next_bell_info and self.is_timer_running:
            now = datetime.now()
            bell_time = self.next_bell_info["datetime"]
            if bell_time > now:
                return bell_time - now
        return None

    def validate_time_input(self, P, limit):
        return (P.isdigit() and len(P) <= int(limit)) or P == ""

    def on_entry_focus_in(self, event, placeholder):
        """Handles focus-in event for placeholder entries."""
        widget = event.widget
        if widget.get() == placeholder:
            widget.delete(0, tk.END)
            widget.config(fg=self.theme['colors']['text_dark'])

    def on_entry_focus_out(self, event, placeholder):
        """Handles focus-out event for placeholder entries."""
        widget = event.widget
        if not widget.get():
            widget.insert(0, placeholder)
            widget.config(fg='grey')

    def add_period_row(self, add_placeholder=True):
        row_frame = tk.Frame(self.periods_container, bg=self.theme['colors']['accent_bg'])
        row_frame.pack(fill="x", expand=True, pady=5, padx=10)

        col_configs = {
            0: {'minsize': 40},  # Cross button
            1: {'minsize': 40},  # Number
            2: {'weight': 3, 'minsize': 100},  # Period Entry
            3: {'minsize': 175},  # Time Button
            4: {'weight': 2, 'minsize': 100},  # Sound Button
            5: {'minsize': 10}  # Padding
        }
        for col, config in col_configs.items():
            if 'weight' in config:
                row_frame.columnconfigure(col, weight=config['weight'], minsize=config.get('minsize', 0))
            if 'minsize' in config and 'weight' not in config:
                row_frame.columnconfigure(col, minsize=config['minsize'])

        tk.Button(row_frame, image=self.cross_icon_photo, borderwidth=0, highlightthickness=0, relief="flat",
                  bg=self.theme['colors']['accent_bg'], activebackground=self.theme['colors']['accent_bg'],
                  command=lambda: self.remove_period(row_frame)).grid(row=0, column=0, sticky="w")

        number_label = tk.Label(row_frame, text=f"{len(self.period_rows) + 1:02d}.",
                                bg=self.theme['colors']['accent_bg'], fg=self.theme['colors']['primary'],
                                font=self.theme["fonts"]["body_bold"])
        number_label.grid(row=0, column=1, sticky="w")

        period_widget = tk.Entry(row_frame, font=("Poppins", 14), bg=self.theme['colors']['secondary'],
                                 fg=self.theme['colors']['text_dark'], highlightthickness=2, bd=0, relief="solid",
                                 highlightbackground=self.theme['colors']['primary'])
        period_widget.grid(row=0, column=2, sticky="ew", ipady=5, padx=(0, 10))

        if add_placeholder:
            placeholder = "Period Name"
            period_widget.insert(0, placeholder)
            period_widget.config(fg='grey')
            period_widget.bind("<FocusIn>", lambda e, p=placeholder: self.on_entry_focus_in(e, p))
            period_widget.bind("<FocusOut>", lambda e, p=placeholder: self.on_entry_focus_out(e, p))

        time_display_var = tk.StringVar(self, "12:00:00 AM")
        tk.Button(row_frame, textvariable=time_display_var, bg=self.theme['colors']['primary'],
                  fg=self.theme['colors']['text_light'], font=self.theme['fonts']['small'], borderwidth=0,
                  relief="flat", command=lambda var=time_display_var: self.open_time_picker(var)).grid(row=0,
                                                                                                       column=3,
                                                                                                       sticky="ew",
                                                                                                       ipady=5)

        sound_path_var, sound_display_var = tk.StringVar(self), tk.StringVar(self, "Browse a sound")
        sound_button_frame = tk.Frame(row_frame, highlightbackground=self.theme['colors']['primary'],
                                      highlightthickness=2, bd=0)
        sound_button_frame.grid(row=0, column=4, sticky="ewns", padx=10)
        sound_button_frame.pack_propagate(False)

        tk.Button(sound_button_frame, textvariable=sound_display_var, bg=self.theme['colors']['secondary'],
                  fg=self.theme['colors']['text_dark'], font=self.theme['fonts']['small'], relief="flat", bd=0,
                  highlightthickness=0,
                  command=lambda p=sound_path_var, d=sound_display_var: self.choose_sound_file(p, d)).pack(
            fill="both", expand=True)

        self.period_rows.append({"frame": row_frame, "number_label": number_label, "period_widget": period_widget,
                                 "time_display_var": time_display_var, "sound_path_var": sound_path_var,
                                 "sound_display_var": sound_display_var})

        self.bind_mousewheel(self.canvas, row_frame)

        self.periods_container.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def open_time_picker(self, time_var):
        TimePickerPopup(self.master, time_var.get(), lambda time: time_var.set(time), self.theme)

    def choose_sound_file(self, sound_path_var, sound_display_var):
        file_path = filedialog.askopenfilename(title="Select a Bell Sound File",
                                               filetypes=(("Audio files", "*.mp3 *.wav"), ("All files", "*.*")))
        if file_path:
            sound_path_var.set(file_path)
            file_name, _ = os.path.splitext(os.path.basename(file_path))
            truncated_name = (file_name[:8] + "..." + file_name[-8:]) if len(file_name) > 20 else file_name
            sound_display_var.set(truncated_name)

    def remove_period(self, frame_to_remove):
        row_to_remove = next((row for row in self.period_rows if row["frame"] == frame_to_remove), None)
        if row_to_remove:
            self.period_rows.remove(row_to_remove)
            frame_to_remove.destroy()
            for i, row in enumerate(self.period_rows):
                row["number_label"].config(text=f"{i + 1:02d}.")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def load_saved_timetables(self):
        for widget in self.timetables_list_frame.winfo_children(): widget.destroy()
        try:
            timetable_files = [f for f in os.listdir(self.timetables_dir) if f.endswith(".json")]
            if not timetable_files:
                tk.Label(self.timetables_list_frame, text="No saved timetables found.",
                         bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                         font=("Poppins", 18)).pack(pady=20)
                return
            for file_name in sorted(timetable_files):
                name = os.path.splitext(file_name)[0]
                item_frame = tk.Frame(self.timetables_list_frame, bg=self.theme["colors"]["secondary"])
                item_frame.pack(fill="x", expand=True, pady=10, padx=20)
                item_frame.grid_columnconfigure(0, weight=1)
                name_label = tk.Label(item_frame, text=name, bg=self.theme["colors"]["secondary"],
                                      fg=self.theme["colors"]["text_dark"], font=self.theme["fonts"]["subheader"],
                                      cursor="hand2")
                name_label.grid(row=0, column=0, sticky="w")
                name_label.bind("<Button-1>", lambda e, n=name: self.on_timetable_click(n))
                delete_button = tk.Button(item_frame, image=self.delete_icon_photo,
                                          bg=self.theme["colors"]["secondary"],
                                          activebackground=self.theme["colors"]["secondary"], borderwidth=0,
                                          relief="flat", command=lambda n=name: self.delete_timetable(n))
                delete_button.grid(row=0, column=1, sticky="e", padx=(10, 0))
                tk.Frame(item_frame, bg=self.theme['colors']['primary'], height=1).grid(row=1, column=0,
                                                                                        columnspan=2, sticky="ew",
                                                                                        pady=(5, 0))

                self.bind_mousewheel(self.saved_canvas, item_frame)
        except FileNotFoundError:
            print(f"Error: Timetables directory not found at {self.timetables_dir}")

    def sanitize_filename(self, filename):
        return re.sub(r'[\\/*?:"<>|]', "", filename)

    def save_timetable(self):
        timetable_name = self.timetable_name_entry.get().strip()
        if not timetable_name:
            messagebox.showerror("Error", "Timetable name cannot be empty.")
            return
        sanitized_name = self.sanitize_filename(timetable_name)
        if timetable_name != sanitized_name:
            messagebox.showwarning("Name Sanitized",
                                   f"The timetable name contained invalid characters and was saved as:\n'{sanitized_name}'")
            self.timetable_name_entry.delete(0, tk.END)
            self.timetable_name_entry.insert(0, sanitized_name)

        for i, row in enumerate(self.period_rows):
            period_widget = row["period_widget"]
            period_name = period_widget.get().strip()
            is_placeholder = (period_widget.cget('fg') == 'grey')

            if not period_name or is_placeholder:
                messagebox.showerror("Error", f"Period name in row {i + 1} cannot be empty.")
                return

            sound_path = row["sound_path_var"].get()
            if not sound_path:
                messagebox.showerror("Error", f"Please select an audio file for period in row {i + 1}.")
                return
            if not os.path.exists(sound_path):
                messagebox.showerror("File Not Found",
                                     f"Audio file for row {i + 1} does not exist:\n{sound_path}")
                return

        data = {"timetable_name": sanitized_name, "periods": []}
        for r in self.period_rows:
            period_widget = r["period_widget"]
            period_name = period_widget.get()

            if period_widget.cget('fg') == 'grey':
                period_name = ""

            data["periods"].append({
                "period": period_name,
                "time": r["time_display_var"].get(),
                "sound_file": r["sound_path_var"].get()
            })

        save_path = os.path.join(self.timetables_dir, f"{sanitized_name}.json")
        if os.path.exists(save_path) and not messagebox.askyesno("Confirm Save",
                                                                 f"'{sanitized_name}' already exists. Overwrite?"):
            return
        try:
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Success", f"Timetable '{sanitized_name}' saved successfully!")
            self.on_open_button_click()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save timetable: {e}")

    def edit_timetable(self):
        if not self.current_timetable_data: return
        for row in self.period_rows: row["frame"].destroy()
        self.period_rows.clear()
        self.timetable_name_entry.delete(0, tk.END)
        self.timetable_name_entry.insert(0, self.current_timetable_data["timetable_name"])
        for period_data in self.current_timetable_data["periods"]:
            self.add_period_row(add_placeholder=False)
            new_row = self.period_rows[-1]
            new_row["period_widget"].insert(0, period_data["period"])
            new_row["time_display_var"].set(period_data["time"])
            new_row["sound_path_var"].set(period_data["sound_file"])
            file_path = period_data["sound_file"]
            if file_path:
                file_name, _ = os.path.splitext(os.path.basename(file_path))
                truncated_name = (file_name[:8] + "..." + file_name[-8:]) if len(file_name) > 20 else file_name
                new_row["sound_display_var"].set(truncated_name)
        self.show_frame("create_timetable")

    def delete_timetable(self, timetable_name):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{timetable_name}'?"):
            try:
                os.remove(os.path.join(self.timetables_dir, f"{timetable_name}.json"))
                messagebox.showinfo("Success", f"Timetable '{timetable_name}' has been deleted.")
                self.load_saved_timetables()
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

    def _save_ui_state(self):
        """Saves transient UI state before widgets are destroyed."""
        state = {'current_frame': self.current_frame_name}
        if self.current_frame_name == 'create_timetable' and hasattr(self,
                                                                     'timetable_name_entry') and self.timetable_name_entry.winfo_exists():
            state['timetable_name'] = self.timetable_name_entry.get()
            state['periods'] = []
            for row in self.period_rows:
                period_widget = row['period_widget']
                period_name = period_widget.get()
                if period_widget.cget('fg') == 'grey':
                    period_name = ""

                period_data = {
                    'period': period_name,
                    'time': row['time_display_var'].get(),
                    'sound_path': row['sound_path_var'].get(),
                    'sound_display': row['sound_display_var'].get()
                }
                state['periods'].append(period_data)
        return state

    def _restore_ui_state(self, state):
        """Restores transient UI state after widgets are recreated."""
        if state.get('current_frame') == 'create_timetable' and state.get('periods') is not None:
            self.timetable_name_entry.insert(0, state.get('timetable_name', ''))
            for period_data in state['periods']:
                has_text = bool(period_data['period'])
                self.add_period_row(add_placeholder=not has_text)

                new_row = self.period_rows[-1]

                if has_text:
                    new_row['period_widget'].insert(0, period_data['period'])

                new_row['time_display_var'].set(period_data['time'])
                new_row['sound_path_var'].set(period_data['sound_path'])
                new_row['sound_display_var'].set(period_data['sound_display'])

    def rebuild_ui(self):
        """Destroys and recreates the entire UI to apply theme/font changes."""
        for widget in self.winfo_children():
            widget.destroy()

        self.rebuild_theme()

        self.home_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.settings_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.about_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.create_timetable_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.saved_timetables_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])
        self.view_timetable_frame = tk.Frame(self, bg=self.theme["colors"]["secondary"])

        self.period_rows = []
        self.view_period_rows = []

        self.setup_styles()
        self.create_widgets()
        self._update_button_icons()

    def setup_tray_icon(self):
        """Creates and runs the system tray icon using 'app_icon.ico'."""
        try:
            icon_path = resource_path("app_icon.ico")
            image = Image.open(icon_path)

            menu = (pystray.MenuItem('Show', self.show_window_from_tray, default=True),
                    pystray.MenuItem('Quit', self.quit_from_tray))

            # CHANGED: Added '_v2' to the tray icon ID
            self.tray_icon = pystray.Icon("SchoolBellSystem_v2", image, "School Bell System", menu)
            self.tray_icon.run()

        except FileNotFoundError:
            messagebox.showerror(
                "Application Error",
                "Could not find 'app_icon.ico'. The application cannot minimize to the tray.\n\nPlease ensure the icon file is correctly bundled with the executable."
            )
            self.show_window_from_tray()
        except Exception as e:
            messagebox.showerror("Tray Icon Error", f"An unexpected error occurred: {e}")
            self.show_window_from_tray()

    def show_window_from_tray(self):
        """Shows the main window when called from the tray icon menu."""
        if self.tray_icon and self.tray_icon.visible:
            self.tray_icon.stop()
        self.master.after(0, self.master.deiconify)

    def quit_from_tray(self):
        """Stops the tray icon and posts a quit message to the main thread."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.master.after(0, self.quit_app)

    def minimize_to_tray(self):
        """Hides the main window and starts the tray icon in a separate thread."""
        self.master.withdraw()
        threading.Thread(target=self.setup_tray_icon, daemon=True).start()

    def quit_app(self):
        """Safely quits the application by cleaning up all resources."""
        print("Shutting down...")

        self.is_timer_running = False
        self.timer_stop_event.set()

        if self.tray_icon and self.tray_icon.visible:
            print("Stopping tray icon...")
            self.tray_icon.stop()

        if os.name == 'nt' and hasattr(self, 'loaded_font_path') and self.loaded_font_path:
            try:
                ctypes.windll.gdi32.RemoveFontResourceW(self.loaded_font_path)
                print(f"Unloaded font: {self.loaded_font_path}")
            except Exception as e:
                print(f"Error unloading font: {e}")

        try:
            pygame.mixer.quit()
            print("Pygame mixer quit.")
        except Exception as e:
            print(f"Error quitting pygame mixer: {e}")

        print("Destroying main window...")
        self.master.destroy()
        print("Application quit.")

    def create_close_confirmation_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Exit Application")
        dialog.resizable(False, False)
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.configure(bg=self.theme["colors"]["secondary"])

        try:
            icon_path = resource_path("app_icon.ico")
            dialog.iconbitmap(icon_path)
        except Exception:
            pass

        dialog.protocol("WM_DELETE_WINDOW", lambda: self.handle_close_option(dialog, "cancel"))
        dialog.bind('<Escape>', lambda e: self.handle_close_option(dialog, "cancel"))

        main_frame = tk.Frame(dialog, bg=self.theme["colors"]["secondary"], padx=30, pady=25)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        header_frame = tk.Frame(main_frame, bg=self.theme["colors"]["secondary"])
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        icon_label = tk.Label(header_frame, text="❓", bg=self.theme["colors"]["secondary"],
                              fg=self.theme["colors"]["primary"], font=(self.font_family_name, 48))
        icon_label.pack(side="left", padx=(0, 20), anchor='n')

        text_frame = tk.Frame(header_frame, bg=self.theme["colors"]["secondary"])
        text_frame.pack(side="left", fill="x", expand=True)

        title_label = tk.Label(text_frame, text="Exit Application?", bg=self.theme["colors"]["secondary"],
                               fg=self.theme["colors"]["text_dark"], font=self.theme["fonts"]["subheader"], anchor="w",
                               justify="left")
        title_label.pack(fill="x")

        message_text = "Closing will stop the bell system from running.\nYou can also minimize to the system tray to keep it active."

        message_label = tk.Label(text_frame, text=message_text,
                                 bg=self.theme["colors"]["secondary"], fg=self.theme["colors"]["text_dark"],
                                 font=self.theme["fonts"]["small"], wraplength=320, justify="left", anchor="w")
        message_label.pack(fill="x", pady=(5, 0))

        button_frame = tk.Frame(main_frame, bg=self.theme["colors"]["secondary"])
        button_frame.grid(row=2, column=0, sticky="sew", pady=(20, 0))
        button_frame.grid_columnconfigure(0, weight=1)

        cancel_btn = tk.Button(button_frame, text="Cancel", command=lambda: self.handle_close_option(dialog, "cancel"))
        self.apply_button_style(cancel_btn, "secondary")
        cancel_btn.config(padx=20, pady=7)
        cancel_btn.grid(row=0, column=1, padx=(0, 10))

        minimize_btn = tk.Button(button_frame, text="Minimize to Tray",
                                 command=lambda: self.handle_close_option(dialog, "minimize"))
        self.apply_button_style(minimize_btn, "secondary")
        minimize_btn.config(padx=20, pady=7)
        minimize_btn.grid(row=0, column=2, padx=(0, 10))

        close_btn = tk.Button(button_frame, text="Close Application",
                              command=lambda: self.handle_close_option(dialog, "close"))
        self.apply_button_style(close_btn, "primary")
        close_btn.config(padx=20, pady=8)
        close_btn.grid(row=0, column=3)

        dialog.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - dialog.winfo_width()) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.focus_set()

    def handle_close_option(self, dialog, option):
        dialog.destroy()
        if option == "close":
            self.quit_app()
        elif option == "minimize":
            self.minimize_to_tray()

    def on_window_close(self):
        if self.settings.get("minimize_to_tray", False):
            self.minimize_to_tray()
        else:
            self.create_close_confirmation_dialog()

    def setup_window_close_handler(self):
        self.master.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def run_auto_backup(self):
        if not self.settings.get("auto_backup", True): return
        backup_loc = self.settings.get("backup_location", "")
        if not os.path.isdir(backup_loc): return
        last_backup = self.settings.get("last_backup_timestamp", 0)
        now = time.time()
        if now - last_backup > 7 * 24 * 60 * 60:
            try:
                backup_subdir = os.path.join(backup_loc, f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
                os.makedirs(backup_subdir, exist_ok=True)
                for filename in os.listdir(self.timetables_dir):
                    if filename.endswith(".json"):
                        shutil.copy2(os.path.join(self.timetables_dir, filename), backup_subdir)
                self.settings["last_backup_timestamp"] = now
                self.save_settings()
                print(f"Automatic backup completed to {backup_subdir}")
            except Exception as e:
                print(f"Auto backup failed: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    splash = SplashScreen(root, "assets/Splash_screen.png")


    def on_splash_done():
        app = BellSystemApp(root)
        app.center_main_window()


    root.after(3000, lambda: [splash.show_main_window(), on_splash_done()])
    root.mainloop()