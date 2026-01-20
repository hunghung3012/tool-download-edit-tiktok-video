"""
Settings Manager - Quản lý các cài đặt xử lý video
"""

import tkinter as tk
from tkinter import ttk

from config import COLORS, FONTS, DEFAULT_SETTINGS, FILTERS, CUSTOM_PARAMS
from gui.preset_manager import PresetManager


class SettingsManager:
    """Class quản lý settings (speed, zoom, filter, custom params)"""
    
    def __init__(self, parent, user_settings, custom_params, custom_presets, 
                 filter_change_callback, save_presets_callback, preview_callback):
        self.parent = parent
        self.user_settings = user_settings
        self.custom_params = custom_params
        self.custom_presets = custom_presets
        self.filter_change_callback = filter_change_callback
        self.save_presets_callback = save_presets_callback
        self.preview_callback = preview_callback
        
        # Variables
        self.speed_var = tk.DoubleVar(value=user_settings.get('speed', DEFAULT_SETTINGS['speed']))
        self.zoom_var = tk.DoubleVar(value=user_settings.get('zoom', DEFAULT_SETTINGS['zoom']))
        self.filter_var = tk.StringVar(value=user_settings.get('filter', DEFAULT_SETTINGS['filter']))
        
        # Create UI
        self.create_settings_section()
        self.create_custom_section()
    
    def create_settings_section(self):
        """Tạo phần cài đặt"""
        settings_frame = tk.LabelFrame(
            self.parent,
            text="⚙ Cài đặt xử lý",
            font=FONTS['heading'],
            bg=COLORS['white'],
            fg=COLORS['primary'],
            padx=20,
            pady=15,
            relief="solid",
            bd=1
        )
        settings_frame.pack(fill="x", pady=(0, 15))
        
        # Speed
        speed_frame = tk.Frame(settings_frame, bg=COLORS['white'])
        speed_frame.pack(fill="x", pady=8)
        
        tk.Label(
            speed_frame,
            text="Tốc độ:",
            font=FONTS['normal'],
            bg=COLORS['white'],
            width=10,
            anchor="w"
        ).pack(side="left")
        
        speed_scale = ttk.Scale(
            speed_frame,
            from_=0.5,
            to=5.0,
            variable=self.speed_var,
            orient="horizontal"
        )
        speed_scale.pack(side="left", fill="x", expand=True, padx=10)
        
        self.speed_label = tk.Label(
            speed_frame,
            text=f"{self.speed_var.get():.1f}x",
            font=FONTS['normal'],
            bg=COLORS['white'],
            width=6,
            fg=COLORS['primary']
        )
        self.speed_label.pack(side="right")
        
        speed_scale.configure(command=self.update_speed_label)
        
        # Zoom
        zoom_frame = tk.Frame(settings_frame, bg=COLORS['white'])
        zoom_frame.pack(fill="x", pady=8)
        
        tk.Label(
            zoom_frame,
            text="Zoom:",
            font=FONTS['normal'],
            bg=COLORS['white'],
            width=10,
            anchor="w"
        ).pack(side="left")
        
        zoom_scale = ttk.Scale(
            zoom_frame,
            from_=0.5,
            to=3.0,
            variable=self.zoom_var,
            orient="horizontal"
        )
        zoom_scale.pack(side="left", fill="x", expand=True, padx=10)
        
        self.zoom_label = tk.Label(
            zoom_frame,
            text=f"{self.zoom_var.get():.1f}x",
            font=FONTS['normal'],
            bg=COLORS['white'],
            width=6,
            fg=COLORS['primary']
        )
        self.zoom_label.pack(side="right")
        
        zoom_scale.configure(command=self.update_zoom_label)
        
        # Filter
        filter_frame = tk.Frame(settings_frame, bg=COLORS['white'])
        filter_frame.pack(fill="x", pady=8)
        
        tk.Label(
            filter_frame,
            text="Filter:",
            font=FONTS['normal'],
            bg=COLORS['white'],
            width=10,
            anchor="w"
        ).pack(side="left")
        
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=list(FILTERS.keys()),
            state="readonly",
            font=FONTS['small']
        )
        filter_combo.pack(side="left", fill="x", expand=True, padx=10)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_change_callback())
        
        preset_btn = tk.Button(
            settings_frame,
            text="💾 Quản lý Presets",
            font=FONTS['small'],
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            padx=15,
            pady=5,
            cursor="hand2",
            bd=0,
            command=self.manage_presets
        )
        preset_btn.pack(pady=(8, 0))
    
    def create_custom_section(self):
        """Tạo section cho custom filter"""
        self.custom_frame = tk.LabelFrame(
            self.parent,
            text="🎨 Custom Filter Settings",
            font=FONTS['heading'],
            bg=COLORS['white'],
            fg=COLORS['primary'],
            padx=15,
            pady=10,
            relief="solid",
            bd=1
        )
        
        self.create_custom_controls()
    
    def create_custom_controls(self):
        """Tạo các control cho custom filter"""
        param_labels = {
            'brightness': 'Brightness',
            'contrast': 'Contrast',
            'saturation': 'Saturation',
            'gamma': 'Gamma',
            'hue': 'Hue',
            'vibrance': 'Vibrance',
            'red': 'Red Channel',
            'green': 'Green Channel',
            'blue': 'Blue Channel',
        }
        
        self.custom_value_labels = {}
        
        for param_name, (min_val, max_val, default_val) in CUSTOM_PARAMS.items():
            frame = tk.Frame(self.custom_frame, bg=COLORS['white'])
            frame.pack(fill="x", pady=3)
            
            label_text = param_labels[param_name] + ":"
            label_fg = COLORS['text_dark']
            
            # Đổi màu label cho RGB
            if param_name == 'red':
                label_fg = '#FF0000'
            elif param_name == 'green':
                label_fg = '#00AA00'
            elif param_name == 'blue':
                label_fg = '#0000FF'
            
            tk.Label(
                frame,
                text=label_text,
                font=FONTS['small'],
                bg=COLORS['white'],
                fg=label_fg,
                width=15,
                anchor="w"
            ).pack(side="left")
            
            scale = ttk.Scale(
                frame,
                from_=min_val,
                to=max_val,
                variable=self.custom_params[param_name],
                orient="horizontal"
            )
            scale.pack(side="left", fill="x", expand=True, padx=5)
            
            # Lấy giá trị hiện tại từ custom_params
            current_val = self.custom_params[param_name].get()
            
            value_label = tk.Label(
                frame,
                text=f"{current_val:.2f}",
                font=FONTS['small'],
                bg=COLORS['white'],
                width=6,
                fg=COLORS['primary']
            )
            value_label.pack(side="right")
            
            self.custom_value_labels[param_name] = value_label
            
            scale.configure(command=lambda v, p=param_name: self.update_custom_param(p, v))
        
        # Buttons
        btn_frame = tk.Frame(self.custom_frame, bg=COLORS['white'])
        btn_frame.pack(fill="x", pady=(10, 0))
        
        reset_btn = tk.Button(
            btn_frame,
            text="🔄 Reset",
            font=FONTS['small'],
            bg=COLORS['warning'],
            fg=COLORS['white'],
            padx=12,
            pady=5,
            cursor="hand2",
            bd=0,
            command=self.reset_custom_params
        )
        reset_btn.pack(side="left", padx=(0, 5))
        
        save_btn = tk.Button(
            btn_frame,
            text="💾 Lưu Preset",
            font=FONTS['small'],
            bg=COLORS['success'],
            fg=COLORS['white'],
            padx=12,
            pady=5,
            cursor="hand2",
            bd=0,
            command=self.save_custom_preset
        )
        save_btn.pack(side="left")
    
    def update_speed_label(self, value):
        """Cập nhật label tốc độ"""
        speed = float(value)
        self.speed_label.config(text=f"{speed:.1f}x")
    
    def update_zoom_label(self, value):
        """Cập nhật label zoom"""
        zoom = float(value)
        self.zoom_label.config(text=f"{zoom:.1f}x")
    
    def update_custom_param(self, param_name, value):
        """Cập nhật giá trị custom parameter"""
        val = float(value)
        self.custom_value_labels[param_name].config(text=f"{val:.2f}")
    
    def reset_custom_params(self):
        """Reset custom parameters về default"""
        for param_name, (min_val, max_val, default_val) in CUSTOM_PARAMS.items():
            self.custom_params[param_name].set(default_val)
            self.custom_value_labels[param_name].config(text=f"{default_val:.2f}")
    
    def save_custom_preset(self):
        """Lưu custom preset"""
        PresetManager.save_preset_dialog(
            self.parent,
            self.custom_params,
            self.custom_presets,
            self.save_presets_callback
        )
    
    def manage_presets(self):
        """Quản lý custom presets"""
        PresetManager.manage_presets_dialog(
            self.parent,
            self.custom_presets,
            self.custom_params,
            self.custom_value_labels,
            self.save_presets_callback,
            lambda: None  # No preview update needed
        )