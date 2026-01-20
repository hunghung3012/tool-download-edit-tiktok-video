import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import queue
import shutil
from pathlib import Path
import json

from video_processor import VideoProcessor
from config import COLORS, FONTS, DEFAULT_SETTINGS, FILTERS, CUSTOM_PARAMS
from gui.preview_panel import PreviewPanel
from gui.video_manager import VideoManager
from gui.settings_manager import SettingsManager


class FFmpegVideoProcessor:
    """Class chính cho giao diện ứng dụng"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Bibi- Edit Video với FFmpeg")
        self.root.geometry("1100x780")  # Giảm từ 870 xuống 780
        self.root.configure(bg=COLORS['background'])
        
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # Biến lưu trữ
        self.video_files = []
        self.processing = False
        self.current_file_index = 0
        
        # Settings file
        self.settings_file = "user_settings.json"
        
        # Load settings từ file
        self.load_user_settings()
        
        # Custom filter parameters
        self.custom_params = {
            'brightness': tk.DoubleVar(value=self.user_settings.get('brightness', CUSTOM_PARAMS['brightness'][2])),
            'contrast': tk.DoubleVar(value=self.user_settings.get('contrast', CUSTOM_PARAMS['contrast'][2])),
            'saturation': tk.DoubleVar(value=self.user_settings.get('saturation', CUSTOM_PARAMS['saturation'][2])),
            'gamma': tk.DoubleVar(value=self.user_settings.get('gamma', CUSTOM_PARAMS['gamma'][2])),
            'hue': tk.DoubleVar(value=self.user_settings.get('hue', CUSTOM_PARAMS['hue'][2])),
            'vibrance': tk.DoubleVar(value=self.user_settings.get('vibrance', CUSTOM_PARAMS['vibrance'][2])),
            'red': tk.DoubleVar(value=self.user_settings.get('red', CUSTOM_PARAMS['red'][2])),
            'green': tk.DoubleVar(value=self.user_settings.get('green', CUSTOM_PARAMS['green'][2])),
            'blue': tk.DoubleVar(value=self.user_settings.get('blue', CUSTOM_PARAMS['blue'][2])),
        }
        
        # Lưu trữ custom presets
        self.custom_presets = {}
        self.load_custom_presets()
        
        # Event khi đóng ứng dụng
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Tạo giao diện
        self.create_widgets()
        
        # Kiểm tra FFmpeg
        self.check_ffmpeg()
        
        # Bind event để lưu settings khi thay đổi
        self.bind_settings_changes()
    
    def load_user_settings(self):
        """Load settings từ file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.user_settings = json.load(f)
                print(f"✅ Đã load settings: {self.user_settings}")
            else:
                self.user_settings = {
                    'speed': DEFAULT_SETTINGS['speed'],
                    'zoom': DEFAULT_SETTINGS['zoom'],
                    'filter': DEFAULT_SETTINGS['filter'],
                    'brightness': CUSTOM_PARAMS['brightness'][2],
                    'contrast': CUSTOM_PARAMS['contrast'][2],
                    'saturation': CUSTOM_PARAMS['saturation'][2],
                    'gamma': CUSTOM_PARAMS['gamma'][2],
                    'hue': CUSTOM_PARAMS['hue'][2],
                    'vibrance': CUSTOM_PARAMS['vibrance'][2],
                    'red': CUSTOM_PARAMS['red'][2],
                    'green': CUSTOM_PARAMS['green'][2],
                    'blue': CUSTOM_PARAMS['blue'][2],
                }
        except Exception as e:
            print(f"⚠️ Lỗi load settings: {e}")
            self.user_settings = {}
    
    def save_user_settings(self):
        """Lưu settings vào file"""
        try:
            settings = {
                'speed': self.speed_var.get(),
                'zoom': self.zoom_var.get(),
                'filter': self.filter_var.get(),
                'brightness': self.custom_params['brightness'].get(),
                'contrast': self.custom_params['contrast'].get(),
                'saturation': self.custom_params['saturation'].get(),
                'gamma': self.custom_params['gamma'].get(),
                'hue': self.custom_params['hue'].get(),
                'vibrance': self.custom_params['vibrance'].get(),
                'red': self.custom_params['red'].get(),
                'green': self.custom_params['green'].get(),
                'blue': self.custom_params['blue'].get(),
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Đã lưu settings")
        except Exception as e:
            print(f"⚠️ Lỗi lưu settings: {e}")
    
    def bind_settings_changes(self):
        """Bind event để tự động lưu khi settings thay đổi"""
        # Bind cho speed, zoom variables
        self.speed_var.trace_add('write', lambda *args: self.save_user_settings())
        self.zoom_var.trace_add('write', lambda *args: self.save_user_settings())
        self.filter_var.trace_add('write', lambda *args: self.save_user_settings())
        
        # Bind cho custom params
        for param_var in self.custom_params.values():
            param_var.trace_add('write', lambda *args: self.save_user_settings())
    
    def on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        try:
            # Lưu settings trước khi đóng
            self.save_user_settings()
            
            # Xóa ảnh thumbnail trong folder pictures
            pictures_folder = Path("pictures")
            if pictures_folder.exists():
                for file in pictures_folder.glob("*thumb*"):
                    try:
                        if file.is_file():
                            file.unlink()
                            print(f"✅ Đã xóa thumbnail: {file.name}")
                    except Exception as e:
                        print(f"⚠️ Không thể xóa {file.name}: {e}")
            
            # Xóa tất cả video TRONG folder videos
            videos_folder = Path("videos")
            if videos_folder.exists():
                for file in videos_folder.iterdir():
                    try:
                        if file.is_file():
                            file.unlink()
                            print(f"✅ Đã xóa video: {file.name}")
                    except Exception as e:
                        print(f"⚠️ Không thể xóa {file.name}: {e}")
            
        except Exception as e:
            print(f"⚠️ Lỗi khi xóa file: {e}")
        
        # Đóng ứng dụng
        self.root.destroy()
    
    def check_ffmpeg(self):
        """Kiểm tra FFmpeg"""
        success, message = VideoProcessor.check_ffmpeg()
        if success:
            self.ffmpeg_status.config(
                text=f"✓ {message}",
                fg=COLORS['success']
            )
        else:
            self.ffmpeg_status.config(
                text=f"✗ {message}",
                fg=COLORS['danger']
            )
    
    def open_tiktok_folder(self):
        """Mở folder TikTok videos theo ngày"""
        try:
            from datetime import datetime
            import subprocess
            
            # Lấy ngày hiện tại (format: 20-Jan)
            today = datetime.now().strftime("%d-%b")
            
            # Thử mở folder theo ngày
            today_folder = Path(f"D:/Tools/TiktokVideoEdit/{today}")
            
            if today_folder.exists():
                target_folder = str(today_folder)
            else:
                # Nếu không có folder ngày hôm nay, mở folder chính
                base_folder = Path("D:/Tools/TiktokVideoEdit")
                if base_folder.exists():
                    target_folder = str(base_folder)
                else:
                    messagebox.showwarning(
                        "Thông báo", 
                        "Chưa có folder TikTok nào!\n\nFolder sẽ được tạo khi bạn tải video từ TikTok."
                    )
                    return
            
            # Mở folder
            if os.name == 'nt':  # Windows
                os.startfile(target_folder)
            else:  # macOS/Linux
                subprocess.run(['open', target_folder] if os.uname().sysname == 'Darwin' 
                             else ['xdg-open', target_folder])
            
            print(f"📁 Đã mở folder: {target_folder}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở folder:\n{str(e)}")
    
    def create_widgets(self):
        """Tạo giao diện"""
        
        # Container chính với padding
        main_frame = tk.Frame(self.root, bg=COLORS['white'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === HEADER ===
        header_frame = tk.Frame(main_frame, bg=COLORS['white'])
        header_frame.pack(fill="x", pady=(0, 15))
        
        # ICON MỞ FOLDER TIKTOK (GÓC TRÁI)
        folder_btn = tk.Button(
            header_frame,
            text="📁",
            font=('Segoe UI', 16),
            bg=COLORS['white'],
            fg=COLORS['primary'],
            cursor="hand2",
            bd=0,
            padx=5,
            pady=0,
            command=self.open_tiktok_folder
        )
        folder_btn.pack(side="left", anchor="nw")
        
        # Tooltip cho button
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(
                tooltip, 
                text="Mở folder TikTok videos", 
                background="#FFFFE0", 
                relief="solid", 
                borderwidth=1,
                font=FONTS['small']
            )
            label.pack()
            folder_btn.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(folder_btn, 'tooltip'):
                folder_btn.tooltip.destroy()
        
        folder_btn.bind("<Enter>", show_tooltip)
        folder_btn.bind("<Leave>", hide_tooltip)
        
        self.ffmpeg_status = tk.Label(
            header_frame,
            text="Đang kiểm tra FFmpeg...",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_light']
        )
        self.ffmpeg_status.pack(pady=(5, 0))
        
        # === PROCESS BUTTON VÀ PROGRESS ===
        top_frame = tk.Frame(main_frame, bg=COLORS['white'])
        top_frame.pack(fill="x", pady=(0, 15))
        
        self.process_btn = tk.Button(
            top_frame,
            text="🚀 Xử lý tất cả video",
            font=FONTS['button'],
            bg=COLORS['primary'],
            fg=COLORS['white'],
            padx=50,
            pady=15,
            cursor="hand2",
            bd=0,
            activebackground=COLORS['primary_dark'],
            activeforeground=COLORS['white'],
            command=self.start_processing,
            disabledforeground=COLORS['white'],
            state="disabled"
        )
        self.process_btn.pack()
        
        # Progress frame
        self.progress_frame = tk.Frame(top_frame, bg=COLORS['white'])
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=500
        )
        self.progress_bar.pack(fill="x", pady=(10, 5))
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_light']
        )
        self.progress_label.pack()
        
        # === LAYOUT 2 CỘT ===
        content_frame = tk.Frame(main_frame, bg=COLORS['white'])
        content_frame.pack(fill="both", expand=True)
        
        # Cột trái - Settings (với scrollbar)
        left_column = tk.Frame(content_frame, bg=COLORS['white'])
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Tạo canvas và scrollbar cho cột trái
        canvas = tk.Canvas(left_column, bg=COLORS['white'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_column, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['white'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Cột phải - Preview (NHỎ HƠN)
        right_column = tk.Frame(content_frame, bg=COLORS['white'], width=450)
        right_column.pack(side="right", fill="both", padx=(10, 0))
        right_column.pack_propagate(False)  # Giữ width cố định
        
        # === CỘT TRÁI - SETTINGS ===
        # Video Manager
        self.video_manager = VideoManager(
            scrollable_frame,
            self.video_files,
            self.on_videos_updated,
            self.on_video_preview
        )
        
        # Settings Manager
        self.settings_manager = SettingsManager(
            scrollable_frame,
            self.user_settings,
            self.custom_params,
            self.custom_presets,
            self.on_filter_changed,
            self.save_custom_presets_to_file,
            self.update_filter_preview_callback
        )
        
        # Lấy variables từ settings manager
        self.speed_var = self.settings_manager.speed_var
        self.zoom_var = self.settings_manager.zoom_var
        self.filter_var = self.settings_manager.filter_var
        self.custom_frame = self.settings_manager.custom_frame
        self.custom_value_labels = self.settings_manager.custom_value_labels
        
        # === CỘT PHẢI - PREVIEW (NHỎ HƠN) ===
        self.preview_panel = PreviewPanel(
            right_column, 
            self.filter_var,
            self.custom_params,
            self.update_filter_preview_callback,
            self.zoom_var,
            compact=True  # Chế độ compact
        )
    
    def on_videos_updated(self):
        """Callback khi danh sách video thay đổi"""
        if self.video_files:
            self.process_btn.config(state="normal", bg=COLORS['primary'])
        else:
            self.process_btn.config(state="disabled", bg=COLORS['text_light'])
    
    def on_video_preview(self, video_path):
        """Callback khi preview video"""
        # Extract frame và hiển thị
        threading.Thread(
            target=self._extract_video_frame, 
            args=(video_path,), 
            daemon=True
        ).start()
    
    def on_filter_changed(self):
        """Khi thay đổi filter"""
        filter_name = self.filter_var.get()
        
        if filter_name == "Custom":
            self.custom_frame.pack(fill="x", pady=(0, 15))
        else:
            self.custom_frame.pack_forget()
        
        self.preview_panel.update_preview()
    
    def update_filter_preview_callback(self, preview_image_path):
        """Callback khi chọn ảnh preview mới"""
        pass
    
    def load_custom_presets(self):
        """Load custom presets từ file"""
        try:
            import json
            preset_file = "custom_presets.json"
            if os.path.exists(preset_file):
                with open(preset_file, 'r', encoding='utf-8') as f:
                    self.custom_presets = json.load(f)
        except Exception as e:
            print(f"Không thể load presets: {e}")
            self.custom_presets = {}
    
    def save_custom_presets_to_file(self):
        """Lưu custom presets vào file"""
        try:
            import json
            preset_file = "custom_presets.json"
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Không thể lưu presets: {e}")
    
    def start_processing(self):
        """Bắt đầu xử lý"""
        if not self.video_files:
            messagebox.showwarning("Cảnh báo", "Chưa chọn video!")
            return
        
        if self.processing:
            return
        
        # Hiện progress frame
        self.progress_frame.pack(fill="x", pady=(10, 0))
        self.progress_bar['maximum'] = len(self.video_files)
        self.progress_bar['value'] = 0
        
        self.process_btn.config(state="disabled", bg=COLORS['text_light'])
        self.processing = True
        
        thread = threading.Thread(target=self.process_all_videos, daemon=True)
        thread.start()
    
    def _extract_video_frame(self, video_path):
        """Extract frame đầu tiên từ video"""
        try:
            import tempfile
            import subprocess
            
            temp_dir = tempfile.gettempdir()
            timestamp = int(__import__('time').time() * 1000)
            temp_image = os.path.join(temp_dir, f"ffmpeg_preview_{timestamp}.jpg")
            
            if os.path.exists(temp_image):
                try:
                    os.remove(temp_image)
                except:
                    pass
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                '-f', 'image2',
                '-y',
                temp_image
            ]
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                startupinfo=startupinfo, 
                timeout=15,
                text=True
            )
            
            import time
            max_wait = 3
            wait_time = 0
            while not os.path.exists(temp_image) and wait_time < max_wait:
                time.sleep(0.1)
                wait_time += 0.1
            
            if os.path.exists(temp_image) and os.path.getsize(temp_image) > 0:
                self.root.after(0, lambda: self.preview_panel.show_video_preview(temp_image))
                
        except Exception as e:
            print(f"❌ Lỗi preview video: {e}")
    
    def process_all_videos(self):
        """Xử lý tất cả video"""
        success_count = 0
        error_count = 0
        error_files = []
        
        speed = self.speed_var.get()
        zoom = self.zoom_var.get()
        filter_name = self.filter_var.get()
        
        custom_params = None
        if filter_name == "Custom":
            custom_params = {k: v.get() for k, v in self.custom_params.items()}
        
        selected_directory = None
        
        for index, video_file in enumerate(self.video_files):
            filename = os.path.basename(video_file)
            
            self.root.after(0, lambda i=index+1, f=filename:
                        self.progress_label.config(
                            text=f"⏳ Đang xử lý {i}/{len(self.video_files)}: {f}"
                        ))
            
            success, temp_file = VideoProcessor.process_video(
                video_file, speed, zoom, filter_name, custom_params
            )
            
            if success:
                if selected_directory is None:
                    from tkinter import filedialog
                    suggested_path = VideoProcessor.get_suggested_output_path(video_file)
                    
                    def ask_save_location():
                        save_path = filedialog.asksaveasfilename(
                            title=f"Chọn thư mục và tên cho video đầu tiên",
                            initialfile=os.path.basename(suggested_path),
                            initialdir=os.path.dirname(suggested_path),
                            defaultextension=os.path.splitext(video_file)[1],
                            filetypes=[
                                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                                ("All files", "*.*")
                            ]
                        )
                        return save_path
                    
                    result_queue = queue.Queue()
                    
                    def show_dialog():
                        path = ask_save_location()
                        result_queue.put(path)
                    
                    self.root.after(0, show_dialog)
                    save_path = result_queue.get()
                    
                    if not save_path:
                        if os.path.exists(temp_file):
                            try:
                                os.remove(temp_file)
                            except:
                                pass
                        break
                    
                    selected_directory = os.path.dirname(save_path)
                else:
                    input_path = Path(video_file)
                    timestamp = int(__import__('time').time())
                    new_filename = f"{input_path.stem}_processed_{timestamp}{input_path.suffix}"
                    save_path = os.path.join(selected_directory, new_filename)
                
                try:
                    shutil.move(temp_file, save_path)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    error_files.append(f"{filename} (Lỗi lưu: {str(e)})")
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
            else:
                error_count += 1
                error_files.append(filename)
            
            self.root.after(0, lambda v=index+1: self.progress_bar.config(value=v))
        
        self.root.after(0, lambda: self.processing_complete(
            success_count, error_count, error_files
        ))
    
    def processing_complete(self, success_count, error_count, error_files):
        """Hoàn thành xử lý"""
        self.processing = False
        self.progress_frame.pack_forget()
        
        message = f"✅ Hoàn thành!\n\n"
        message += f"Thành công: {success_count} video\n"
        
        if error_count > 0:
            message += f"Lỗi: {error_count} video\n\n"
            message += "File lỗi:\n"
            for file in error_files[:5]:
                message += f"  • {file}\n"
            if len(error_files) > 5:
                message += f"  ... và {len(error_files) - 5} file khác"
        else:
            message += "\n🎉 Tất cả video đã xử lý thành công!"
        
        message += f"\n\n📁 File được lưu trong folder 'edited'"
        
        messagebox.showinfo("Hoàn thành", message)
        self.process_btn.config(state="normal", bg=COLORS['primary'])