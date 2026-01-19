"""
Preset Manager - Quản lý custom presets
"""

import tkinter as tk
from tkinter import ttk, messagebox

from config import COLORS, FONTS


class PresetManager:
    """Class quản lý custom filter presets"""
    
    @staticmethod
    def save_preset_dialog(root, custom_params, custom_presets, save_callback):
        """Dialog để lưu preset"""
        dialog = tk.Toplevel(root)
        dialog.title("Lưu Custom Preset")
        dialog.geometry("350x150")
        dialog.configure(bg=COLORS['white'])
        dialog.transient(root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (150 // 2)
        dialog.geometry(f"350x150+{x}+{y}")
        
        tk.Label(
            dialog,
            text="Nhập tên cho preset:",
            font=FONTS['normal'],
            bg=COLORS['white']
        ).pack(pady=(20, 10))
        
        name_entry = tk.Entry(dialog, font=FONTS['normal'], width=30)
        name_entry.pack(pady=(0, 20))
        name_entry.focus()
        
        def save_preset():
            preset_name = name_entry.get().strip()
            if not preset_name:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên preset!")
                return
            
            # Lưu preset
            custom_presets[preset_name] = {
                k: v.get() for k, v in custom_params.items()
            }
            
            # Lưu vào file
            save_callback()
            
            messagebox.showinfo("Thành công", f"Đã lưu preset '{preset_name}'!")
            dialog.destroy()
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg=COLORS['white'])
        btn_frame.pack()
        
        tk.Button(
            btn_frame,
            text="💾 Lưu",
            font=FONTS['normal'],
            bg=COLORS['primary'],
            fg=COLORS['white'],
            padx=20,
            pady=8,
            cursor="hand2",
            bd=0,
            command=save_preset
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="✖ Hủy",
            font=FONTS['normal'],
            bg=COLORS['text_light'],
            fg=COLORS['white'],
            padx=20,
            pady=8,
            cursor="hand2",
            bd=0,
            command=dialog.destroy
        ).pack(side="left", padx=5)
        
        # Bind Enter
        name_entry.bind('<Return>', lambda e: save_preset())
    
    @staticmethod
    def manage_presets_dialog(root, custom_presets, custom_params, value_labels, save_callback, update_preview_callback):
        """Dialog quản lý presets"""
        if not custom_presets:
            messagebox.showinfo("Thông báo", "Chưa có preset nào được lưu!")
            return
        
        dialog = tk.Toplevel(root)
        dialog.title("Quản lý Custom Presets")
        dialog.geometry("400x350")
        dialog.configure(bg=COLORS['white'])
        dialog.transient(root)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f"400x350+{x}+{y}")
        
        tk.Label(
            dialog,
            text="💾 Custom Presets của bạn",
            font=FONTS['heading'],
            bg=COLORS['white'],
            fg=COLORS['primary']
        ).pack(pady=(15, 10))
        
        # Listbox
        list_frame = tk.Frame(dialog, bg=COLORS['white'])
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        preset_listbox = tk.Listbox(
            list_frame,
            font=FONTS['normal'],
            yscrollcommand=scrollbar.set,
            bg=COLORS['background'],
            selectbackground=COLORS['primary'],
            selectforeground=COLORS['white']
        )
        preset_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=preset_listbox.yview)
        
        # Load presets
        for name in custom_presets.keys():
            preset_listbox.insert("end", name)
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg=COLORS['white'])
        btn_frame.pack(pady=(0, 15))
        
        def load_selected():
            selection = preset_listbox.curselection()
            if not selection:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn preset!")
                return
            
            preset_name = preset_listbox.get(selection[0])
            preset_data = custom_presets[preset_name]
            
            # Load vào UI
            for param_name, value in preset_data.items():
                custom_params[param_name].set(value)
                value_labels[param_name].config(text=f"{value:.2f}")
            
            update_preview_callback()
            messagebox.showinfo("Thành công", f"Đã load preset '{preset_name}'!")
            dialog.destroy()
        
        def delete_selected():
            selection = preset_listbox.curselection()
            if not selection:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn preset!")
                return
            
            preset_name = preset_listbox.get(selection[0])
            
            if messagebox.askyesno("Xác nhận", f"Xóa preset '{preset_name}'?"):
                del custom_presets[preset_name]
                save_callback()
                preset_listbox.delete(selection[0])
                messagebox.showinfo("Thành công", "Đã xóa preset!")
        
        tk.Button(
            btn_frame,
            text="📂 Load Preset",
            font=FONTS['normal'],
            bg=COLORS['primary'],
            fg=COLORS['white'],
            padx=15,
            pady=8,
            cursor="hand2",
            bd=0,
            command=load_selected
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="🗑 Xóa Preset",
            font=FONTS['normal'],
            bg=COLORS['danger'],
            fg=COLORS['white'],
            padx=15,
            pady=8,
            cursor="hand2",
            bd=0,
            command=delete_selected
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="✖ Đóng",
            font=FONTS['normal'],
            bg=COLORS['text_light'],
            fg=COLORS['white'],
            padx=15,
            pady=8,
            cursor="hand2",
            bd=0,
            command=dialog.destroy
        ).pack(side="left", padx=5)