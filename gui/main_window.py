import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
from pathlib import Path
from PIL import Image, ImageTk
import shutil
import queue
import requests
import re
from video_processor import VideoProcessor
from config import COLORS, FONTS, DEFAULT_SETTINGS, FILTERS, SUPPORTED_FORMATS, CUSTOM_PARAMS
from gui.preview_panel import PreviewPanel
import subprocess
class FFmpegVideoProcessor:
    """Class chính cho giao diện ứng dụng"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Bibi- Edit Video với FFmpeg")
        self.root.geometry("1100x870")
        self.root.configure(bg=COLORS['background'])
        
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # Biến lưu trữ
        self.video_files = []
        self.processing = False
        self.current_file_index = 0
        
        # TikTok API Configuration
        self.api_key = "33b0a76a43msha9299be208680fdp199451jsnb8d6ba77a30c"
        self.api_host = "tiktok-video-downloader-api.p.rapidapi.com"
        
        # Ảnh preview
        self.preview_image_path = None
        self.preview_image = None
        
        # Custom filter parameters
        # Custom filter parameters
        self.custom_params = {
            'brightness': tk.DoubleVar(value=CUSTOM_PARAMS['brightness'][2]),
            'contrast': tk.DoubleVar(value=CUSTOM_PARAMS['contrast'][2]),
            'saturation': tk.DoubleVar(value=CUSTOM_PARAMS['saturation'][2]),
            'gamma': tk.DoubleVar(value=CUSTOM_PARAMS['gamma'][2]),
            'hue': tk.DoubleVar(value=CUSTOM_PARAMS['hue'][2]),
            'vibrance': tk.DoubleVar(value=CUSTOM_PARAMS['vibrance'][2]),
            # THÊM RGB
            'red': tk.DoubleVar(value=CUSTOM_PARAMS['red'][2]),
            'green': tk.DoubleVar(value=CUSTOM_PARAMS['green'][2]),
            'blue': tk.DoubleVar(value=CUSTOM_PARAMS['blue'][2]),
        }
        
        # Lưu trữ custom presets
        self.custom_presets = {}
        self.load_custom_presets()
        
        # ===== THÊM EVENT KHI ĐÓNG ỨNG DỤNG =====
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Tạo giao diện
        self.create_widgets()
        
        # Kiểm tra FFmpeg
        self.check_ffmpeg()
    def on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        try:
            # Xóa ảnh thumbnail trong folder pictures (chỉ xóa file có "thumb" trong tên)
            pictures_folder = Path("pictures")
            if pictures_folder.exists():
                for file in pictures_folder.glob("*thumb*"):
                    try:
                        if file.is_file():
                            file.unlink()
                            print(f"✅ Đã xóa thumbnail: {file.name}")
                    except Exception as e:
                        print(f"⚠️ Không thể xóa {file.name}: {e}")
            
            # Xóa tất cả video TRONG folder videos (giữ lại folder)
            videos_folder = Path("videos")
            if videos_folder.exists():
                for file in videos_folder.iterdir():
                    try:
                        if file.is_file():
                            file.unlink()
                            print(f"✅ Đã xóa video: {file.name}")
                    except Exception as e:
                        print(f"⚠️ Không thể xóa {file.name}: {e}")
            
            # Xóa các folder tải TikTok theo ngày (nếu muốn)
            # Nếu muốn giữ lại video đã tải, comment dòng dưới
            # base_folder = Path("D:/Tools/TiktokVideoEdit")
            # if base_folder.exists():
            #     shutil.rmtree(base_folder)
            #     print("✅ Đã xóa folder TikTok videos")
            
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
    
    def create_widgets(self):
        """Tạo giao diện"""
        
        # Container chính với padding
        main_frame = tk.Frame(self.root, bg=COLORS['white'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === HEADER ===
        header_frame = tk.Frame(main_frame, bg=COLORS['white'])
        header_frame.pack(fill="x", pady=(0, 15))
        
        # title = tk.Label(
        #     header_frame,
        #     text="🎬 FFmpeg Video Processor + TikTok Downloader",
        #     font=FONTS['title'],
        #     bg=COLORS['white'],
        #     fg=COLORS['primary']
        # )
        # title.pack()
        
        self.ffmpeg_status = tk.Label(
            header_frame,
            text="Đang kiểm tra FFmpeg...",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_light']
        )
        self.ffmpeg_status.pack(pady=(5, 0))
        
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
        
        # Cột phải - Preview và buttons
        right_column = tk.Frame(content_frame, bg=COLORS['white'])
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # === CỘT TRÁI - SETTINGS ===
        self.create_video_upload_section(scrollable_frame)
        self.create_video_list_section(scrollable_frame)
        self.create_settings_section(scrollable_frame)
        self.create_custom_section(scrollable_frame)
        
        # === CỘT PHẢI - PREVIEW ===
        self.preview_panel = PreviewPanel(
            right_column, 
            self.filter_var,
            self.custom_params,
            self.update_filter_preview_callback,
            self.zoom_var
        )
        
        # === PROGRESS & BUTTON ===
        self.create_bottom_section(main_frame)
    
    def update_filter_preview_callback(self, preview_image_path):
        """Callback khi chọn ảnh preview mới"""
        self.preview_image_path = preview_image_path
    
    def create_video_upload_section(self, parent):
        """Tạo phần chọn video và TikTok links"""
        upload_frame = tk.LabelFrame(
            parent,
            text="📂 Chọn Video hoặc TikTok Links",
            font=FONTS['heading'],
            bg=COLORS['white'],
            fg=COLORS['primary'],
            padx=15,
            pady=10,
            relief="solid",
            bd=1
        )
        upload_frame.pack(fill="x", pady=(0, 15))
        
        # Tab-like buttons
        tab_frame = tk.Frame(upload_frame, bg=COLORS['white'])
        tab_frame.pack(fill="x", pady=(0, 10))
        
        self.upload_mode = tk.StringVar(value="tiktok")
        
        file_tab_btn = tk.Radiobutton(
            tab_frame,
            text="📁 Từ File",
            variable=self.upload_mode,
            value="file",
            font=FONTS['normal'],
            bg=COLORS['white'],
            fg=COLORS['primary'],
            selectcolor=COLORS['white'],  # Màu nền khi chọn (trắng)
            activebackground=COLORS['white'],  # Thêm dòng này
            command=self.toggle_upload_mode,
            cursor="hand2"
)
        file_tab_btn.pack(side="left", padx=(0, 20))
        
        tiktok_tab_btn = tk.Radiobutton(
    tab_frame,
    text="🎵 Từ TikTok",
    variable=self.upload_mode,
    value="tiktok",
    font=FONTS['normal'],
    bg=COLORS['white'],
    fg=COLORS['primary'],
    selectcolor=COLORS['white'],  # Màu nền khi chọn (trắng)
    activebackground=COLORS['white'],  # Thêm dòng này
    command=self.toggle_upload_mode,
    cursor="hand2"
)
        tiktok_tab_btn.pack(side="left")
        
        # === FILE MODE ===
        self.file_mode_frame = tk.Frame(upload_frame, bg=COLORS['white'])
        
        
        btn_container = tk.Frame(self.file_mode_frame, bg=COLORS['white'])
        btn_container.pack(fill="x")
        
        select_btn = tk.Button(
            btn_container,
            text="📂 Chọn Video",
            font=FONTS['normal'],
            bg=COLORS['primary'],
            fg=COLORS['white'],
            padx=20,
            pady=10,
            cursor="hand2",
            bd=0,
            activebackground=COLORS['primary_dark'],
            activeforeground=COLORS['white'],
            command=self.select_videos
        )
        select_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        clear_btn = tk.Button(
            btn_container,
            text="🗑 Xóa tất cả",
            font=FONTS['normal'],
            bg=COLORS['danger'],
            fg=COLORS['white'],
            padx=20,
            pady=10,
            cursor="hand2",
            bd=0,
            activebackground=COLORS['danger'],
            activeforeground=COLORS['white'],
            command=self.clear_all_videos
        )
        clear_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        # === TIKTOK MODE ===
        self.tiktok_mode_frame = tk.Frame(upload_frame, bg=COLORS['white'])
        self.tiktok_mode_frame.pack(fill="x")
        tk.Label(
            self.tiktok_mode_frame,
            text="Nhập các link TikTok (mỗi link một dòng):",
            font=FONTS['normal'],
            bg=COLORS['white']
        ).pack(anchor="w", pady=(0, 5))
        
        self.url_text = scrolledtext.ScrolledText(
            self.tiktok_mode_frame,
            width=50,
            height=8,
            font=FONTS['small'],
            wrap=tk.WORD
        )
        self.url_text.pack(fill="both", expand=True)
        
        # Bind events cho auto-parse
        # self.url_text.bind('<KeyRelease>', self.auto_parse_urls)
        self.url_text.bind('<<Paste>>', self.on_paste)
        
        tiktok_btn_frame = tk.Frame(self.tiktok_mode_frame, bg=COLORS['white'])
        tiktok_btn_frame.pack(fill="x", pady=(10, 0))
        
        add_tiktok_btn = tk.Button(
            tiktok_btn_frame,
            text="➕ Thêm vào danh sách",
            font=FONTS['normal'],
            bg=COLORS['success'],
            fg=COLORS['white'],
            padx=15,
            pady=8,
            cursor="hand2",
            bd=0,
            command=self.add_tiktok_links
        )
        add_tiktok_btn.pack(side="left", padx=(0, 5))
        
        clear_text_btn = tk.Button(
            tiktok_btn_frame,
            text="🗑 Xóa text",
            font=FONTS['normal'],
            bg=COLORS['warning'],
            fg=COLORS['white'],
            padx=15,
            pady=8,
            cursor="hand2",
            bd=0,
            command=lambda: self.url_text.delete("1.0", tk.END)
        )
        clear_text_btn.pack(side="left")
    
    def toggle_upload_mode(self):
        """Chuyển đổi giữa file mode và TikTok mode"""
        if self.upload_mode.get() == "file":
            self.tiktok_mode_frame.pack_forget()
            self.file_mode_frame.pack(fill="x")
        else:
            self.file_mode_frame.pack_forget()
            self.tiktok_mode_frame.pack(fill="x")
    
    def on_paste(self, event):
        """Schedule auto-parse after paste"""
        self.root.after(100, self.auto_parse_urls)
    
    def auto_parse_urls(self, event=None):
        """Tự động parse và format TikTok URLs"""
        text = self.url_text.get("1.0", tk.END)
        
        # Find all TikTok URLs
        url_pattern = r'https?://(?:www\.)?tiktok\.com/@[^/]+/video/\d+[^\s]*'
        urls = re.findall(url_pattern, text)
        
        if urls:
            # Clear and reformat
            self.url_text.delete("1.0", tk.END)
            self.url_text.insert("1.0", "\n".join(urls))
    def is_valid_tiktok_url(self, url):
        """Kiểm tra link TikTok có hợp lệ không"""
        pattern = r'^https?://(?:www\.)?tiktok\.com/@[^/]+/video/\d+.*$'
        return re.match(pattern, url) is not None
    def add_tiktok_links(self):
        """Thêm TikTok links vào danh sách để tải"""
        text = self.url_text.get("1.0", tk.END)
        urls = [url.strip() for url in text.split('\n') if url.strip()]
        
        if not urls:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một link TikTok!")
            return
        
        # Validate tất cả links trước
        invalid_links = []
        for url in urls:
            if not self.is_valid_tiktok_url(url):
                invalid_links.append(url)
        
        if invalid_links:
            msg = "Các link không hợp lệ:\n\n"
            for link in invalid_links[:5]:
                msg += f"• {link}\n"
            if len(invalid_links) > 5:
                msg += f"... và {len(invalid_links) - 5} link khác"
            messagebox.showerror("Link không hợp lệ", msg)
            return
        
        # Hiện thông báo đang tải
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Đang tải TikTok videos...")
        progress_dialog.geometry("400x150")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        
        tk.Label(
            progress_dialog,
            text="Đang tải video từ TikTok...",
            font=FONTS['normal']
        ).pack(pady=(20, 10))
        
        progress_bar = ttk.Progressbar(
            progress_dialog,
            mode='indeterminate',
            length=300
        )
        progress_bar.pack(pady=10)
        progress_bar.start()
        
        status_label = tk.Label(
            progress_dialog,
            text="",
            font=FONTS['small']
        )
        status_label.pack()
        
        # Download trong thread
        def download_worker():
            # TẠO FOLDER THEO NGÀY THÁNG
            from datetime import datetime
            today = datetime.now().strftime("%d-%b")  # Format: 19-Jan
            videos_folder = Path(f"D:/Tools/TiktokVideoEdit/{today}")
            videos_folder.mkdir(parents=True, exist_ok=True)  # Tạo cả parent folders nếu chưa có
            
            success_count = 0
            failed_count = 0
            
            for i, url in enumerate(urls, 1):
                try:
                    self.root.after(0, lambda i=i: status_label.config(
                        text=f"Đang tải video {i}/{len(urls)}..."
                    ))
                    
                    # Get download URL và thumbnail
                    download_url, thumbnail_url = self.get_tiktok_download_url(url)
                    
                    # Extract video ID
                    video_id = self.extract_video_id(url)
                    filename = f"tiktok_{video_id}_{i}.mp4" if video_id else f"tiktok_video_{i}.mp4"
                    filepath = videos_folder / filename
                    
                    # Download video
                    self.download_tiktok_video(download_url, filepath)
                    
                    # Download thumbnail nếu có
                    if thumbnail_url:
                        pictures_folder = Path("pictures")
                        pictures_folder.mkdir(exist_ok=True)
                        
                        thumb_filename = f"tiktok_{video_id}_{i}_thumb.jpg"
                        thumb_path = pictures_folder / thumb_filename
                        try:
                            self.download_tiktok_video(thumbnail_url, thumb_path)
                            self.root.after(0, lambda: self.preview_panel.load_pictures())
                            print(f"✅ Đã lưu thumbnail: {thumb_path}")
                        except Exception as e:
                            print(f"⚠️ Không tải được thumbnail: {e}")
                    
                    # Add to video list
                    self.root.after(0, lambda f=str(filepath): self.video_files.append(f))
                    self.root.after(0, lambda f=str(filepath): self.add_video_item(f))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"Lỗi tải video {i}: {error_msg}")
                    
                    # Đóng dialog và show error ngay
                    self.root.after(0, progress_dialog.destroy)
                    self.root.after(0, lambda msg=error_msg, idx=i: messagebox.showerror(
                        "Lỗi tải video",
                        f"Lỗi tại video {idx}:\n{msg}\n\nĐã dừng tải."
                    ))
                    return
            
            # Close dialog và update UI
            self.root.after(0, progress_dialog.destroy)
            self.root.after(0, self.update_info_label)
            self.root.after(0, lambda: self.process_btn.config(state="normal", bg=COLORS['primary']))
            
            # Clear textarea
            self.root.after(0, lambda: self.url_text.delete("1.0", tk.END))
            
            # Show result với thông tin folder
            msg = f"Hoàn thành!\n\nThành công: {success_count}\nThất bại: {failed_count}\n\n📁 Đã lưu vào: {videos_folder}"
            self.root.after(0, lambda: messagebox.showinfo("Kết quả", msg))
        
        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()
    
    def get_tiktok_download_url(self, video_url):
        """Dùng TikWM làm chính, RapidAPI làm backup"""
        
        # Thử TikWM trước (free + nhanh)
        try:
            response = requests.post(
                "https://tikwm.com/api/",
                json={'url': video_url, 'hd': 1},
                timeout=15,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    video_data = data.get('data', {})
                    download_url = video_data.get('hdplay') or video_data.get('play')
                    thumbnail_url = video_data.get('cover')
                    
                    if download_url:
                        print("✅ Dùng TikWM API")
                        return (download_url, thumbnail_url)
        except Exception as e:
            print(f"⚠️ TikWM failed: {e}, chuyển sang RapidAPI...")
        
        # Nếu TikWM fail → dùng RapidAPI (backup)
        try:
            response = requests.get(
                "https://tiktok-video-downloader-api.p.rapidapi.com/media",
                headers={
                    "x-rapidapi-key": self.api_key,
                    "x-rapidapi-host": self.api_host
                },
                params={"videoUrl": video_url},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            download_url = data.get('downloadUrl') or data.get('data', {}).get('downloadUrl')
            thumbnail_url = (data.get('thumbnail') or 
                            data.get('data', {}).get('thumbnail') or 
                            data.get('cover') or 
                            data.get('data', {}).get('cover'))
            
            if download_url:
                print("✅ Dùng RapidAPI (backup)")
                return (download_url, thumbnail_url)
            
            raise Exception("Không tìm thấy URL download")
            
        except Exception as e:
            raise Exception(f"Tất cả APIs thất bại: {str(e)}")
    def download_tiktok_video(self, download_url, filepath):
        """Download video từ URL - TỐI ƯU NHANH"""
        try:
            response = requests.get(
                download_url,
                timeout=30,
                stream=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://www.tiktok.com/'
                }
            )
            response.raise_for_status()
            
            # Ghi file với chunk lớn hơn = nhanh hơn
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
            
            return True
        except Exception as e:
            raise Exception(f"Lỗi tải video: {str(e)}")
    
    def extract_video_id(self, url):
        """Extract video ID từ TikTok URL"""
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    def create_video_list_section(self, parent):
        """Tạo danh sách video với scrollbar ngang và dọc"""
        list_frame = tk.LabelFrame(
            parent,
            text="🎞 Danh sách video",
            font=FONTS['heading'],
            bg=COLORS['white'],
            fg=COLORS['primary'],
            padx=15,
            pady=10,
            relief="solid",
            bd=1
        )
        list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        container = tk.Frame(list_frame, bg=COLORS['white'])
        container.pack(fill="both", expand=True)
        
        v_scrollbar = ttk.Scrollbar(container, orient="vertical")
        v_scrollbar.pack(side="right", fill="y")
        
        h_scrollbar = ttk.Scrollbar(container, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")
        
        video_canvas = tk.Canvas(
            container,
            bg=COLORS['background'],
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            highlightthickness=0,
            height=150
        )
        video_canvas.pack(side="left", fill="both", expand=True)
        
        v_scrollbar.config(command=video_canvas.yview)
        h_scrollbar.config(command=video_canvas.xview)
        
        self.video_items_frame = tk.Frame(video_canvas, bg=COLORS['background'])
        video_canvas.create_window((0, 0), window=self.video_items_frame, anchor="nw")
        
        def configure_scroll(event):
            video_canvas.configure(scrollregion=video_canvas.bbox("all"))
        
        self.video_items_frame.bind("<Configure>", configure_scroll)
        
        def on_mouse_wheel(event):
            video_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def on_enter(event):
            video_canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        def on_leave(event):
            video_canvas.unbind_all("<MouseWheel>")

        video_canvas.bind("<Enter>", on_enter)
        video_canvas.bind("<Leave>", on_leave)
        
        self.video_canvas = video_canvas
        
        self.info_label = tk.Label(
            list_frame,
            text="Chưa có video nào được chọn",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_light']
        )
        self.info_label.pack(pady=(8, 0))
    def preview_video_thumbnail(self, video_path, item_frame):
        """Preview video bằng cách extract frame đầu tiên"""
        # Highlight item được chọn
        if hasattr(self, 'selected_video_item'):
            self.selected_video_item.config(bg=COLORS['white'])
            for child in self.selected_video_item.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=COLORS['white'])
        
        item_frame.config(bg=COLORS['secondary'])
        for child in item_frame.winfo_children():
            if isinstance(child, tk.Label):
                child.config(bg=COLORS['secondary'])
        
        self.selected_video_item = item_frame
        
        # Extract frame từ video và hiển thị
        threading.Thread(target=self._extract_video_frame, args=(video_path,), daemon=True).start()

    def play_video(self, video_path):
        """Phát video bằng trình phát mặc định"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(video_path)
            elif os.name == 'posix':  # macOS/Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', video_path])
                else:  # Linux
                    subprocess.run(['xdg-open', video_path])
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở video:\n{str(e)}")
    def add_video_item(self, filepath):
        """Thêm một video item vào danh sách"""
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath) / (1024 * 1024)
        
        # Tách tên và đuôi file
        name_without_ext = os.path.splitext(filename)[0]
        file_ext = os.path.splitext(filename)[1]
        
        item_frame = tk.Frame(
            self.video_items_frame,
            bg=COLORS['white'],
            relief="solid",
            bd=1
        )
        item_frame.pack(fill="x", pady=2, padx=2)
        
        # Lưu filepath vào dict để có thể update
        item_frame.current_filepath = filepath
        
        # Container cho tên file + extension (GIỮ CHO ENTRY DÀI RA)
        name_container = tk.Frame(item_frame, bg=COLORS['white'])
        name_container.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        
        # Entry để edit tên file (KHÔNG có đuôi) - Ở chế độ readonly
        name_var = tk.StringVar(value=name_without_ext)
        
        entry = tk.Entry(
            name_container,
            textvariable=name_var,
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_dark'],
            relief="flat",
            state="readonly",  # Mặc định readonly
            readonlybackground=COLORS['white'],
            cursor="arrow"
        )
        entry.pack(side="left", fill="x", expand=True)
        
        # Label hiển thị đuôi file (BÊN CẠNH ENTRY)
        ext_label = tk.Label(
            name_container,
            text=file_ext,
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['primary']
        )
        ext_label.pack(side="left", padx=(2, 0))
        
        # Label hiển thị size
        size_label = tk.Label(
            item_frame,
            text=f"({filesize:.1f} MB)",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_light']
        )
        size_label.pack(side="left", padx=5)
        
        # Bind click vào entry để preview (CHỈ KHI READONLY)
        def preview_video(event=None):
            if entry['state'] == 'readonly':
                self.preview_video_thumbnail(item_frame.current_filepath, item_frame)
        
        entry.bind("<Button-1>", preview_video)
        item_frame.bind("<Button-1>", preview_video)
        
        # NÚT EDIT/SAVE
        edit_save_btn = tk.Button(
            item_frame,
            text="✏️",
            font=FONTS['small'],
            bg=COLORS['warning'],
            fg=COLORS['white'],
            padx=8,
            pady=2,
            cursor="hand2",
            bd=0
        )
        edit_save_btn.pack(side="right", padx=2)
        
        def toggle_edit_save():
            """Chuyển giữa Edit và Save"""
            if entry['state'] == 'readonly':
                # Chuyển sang EDIT mode
                entry.config(state="normal", cursor="xterm")
                edit_save_btn.config(text="💾", bg=COLORS['success'])
                entry.focus_set()
                entry.icursor(tk.END)
            else:
                # Chuyển sang SAVE mode
                rename_file()
                entry.config(state="readonly", cursor="arrow")
                edit_save_btn.config(text="✏️", bg=COLORS['warning'])
        
        edit_save_btn.config(command=toggle_edit_save)
        
        # Bind Enter để save khi đang edit
        def on_enter(event):
            if entry['state'] == 'normal':
                toggle_edit_save()
        
        entry.bind("<Return>", on_enter)
        
        # Bind Escape để cancel edit
        def on_escape(event):
            if entry['state'] == 'normal':
                name_var.set(name_without_ext)
                entry.config(state="readonly", cursor="arrow")
                edit_save_btn.config(text="✏️", bg=COLORS['warning'])
        
        entry.bind("<Escape>", on_escape)
        
        # Hàm rename file
        def rename_file(event=None):
            new_name = name_var.get().strip()
            old_name_without_ext = os.path.splitext(os.path.basename(item_frame.current_filepath))[0]
            
            if new_name and new_name != old_name_without_ext:
                try:
                    old_path = Path(item_frame.current_filepath)
                    new_filename = new_name + file_ext  # Tự động thêm lại đuôi
                    new_path = old_path.parent / new_filename
                    
                    # Kiểm tra file mới đã tồn tại chưa
                    if new_path.exists():
                        messagebox.showerror("Lỗi", f"File '{new_filename}' đã tồn tại!")
                        name_var.set(old_name_without_ext)
                        return
                    
                    # Rename file
                    old_path.rename(new_path)
                    
                    # Update filepath trong list
                    old_filepath = item_frame.current_filepath
                    new_filepath = str(new_path)
                    
                    if old_filepath in self.video_files:
                        idx = self.video_files.index(old_filepath)
                        self.video_files[idx] = new_filepath
                    
                    # Update current filepath
                    item_frame.current_filepath = new_filepath
                    item_frame.filepath = new_filepath
                    
                    print(f"✅ Đã đổi tên: {old_name_without_ext}{file_ext} → {new_filename}")
                    
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể đổi tên:\n{str(e)}")
                    name_var.set(old_name_without_ext)
        
        # NÚT PLAY VIDEO
        play_btn = tk.Button(
            item_frame,
            text="▶",
            font=FONTS['small'],
            bg=COLORS['success'],
            fg=COLORS['white'],
            padx=8,
            pady=2,
            cursor="hand2",
            bd=0,
            command=lambda: self.play_video(item_frame.current_filepath)
        )
        play_btn.pack(side="right", padx=2)
        
        # NÚT XÓA
        delete_btn = tk.Button(
            item_frame,
            text="🗑",
            font=FONTS['small'],
            bg=COLORS['danger'],
            fg=COLORS['white'],
            padx=8,
            pady=2,
            cursor="hand2",
            bd=0,
            command=lambda: self.delete_video_item(item_frame.current_filepath, item_frame)
        )
        delete_btn.pack(side="right", padx=2)
        
        item_frame.filepath = filepath
    def delete_video_item(self, filepath, item_frame):
        """Xóa một video item"""
        if self.processing:
            messagebox.showwarning("Cảnh báo", "Đang xử lý video!")
            return
        
        if filepath in self.video_files:
            self.video_files.remove(filepath)
        
        item_frame.destroy()
        self.update_info_label()
        
        if not self.video_files:
            self.process_btn.config(state="disabled", bg=COLORS['text_light'])
    
    def create_settings_section(self, parent):
        """Tạo phần cài đặt"""
        settings_frame = tk.LabelFrame(
            parent,
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
        
        self.speed_var = tk.DoubleVar(value=DEFAULT_SETTINGS['speed'])
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
            text=f"{DEFAULT_SETTINGS['speed']:.1f}x",
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
        
        self.zoom_var = tk.DoubleVar(value=DEFAULT_SETTINGS['zoom'])
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
            text=f"{DEFAULT_SETTINGS['zoom']:.1f}x",
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
        
        self.filter_var = tk.StringVar(value=DEFAULT_SETTINGS['filter'])
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=list(FILTERS.keys()),
            state="readonly",
            font=FONTS['small']
        )
        filter_combo.pack(side="left", fill="x", expand=True, padx=10)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.on_filter_changed())
        
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
    
    def create_custom_section(self, parent):
        """Tạo section cho custom filter"""
        self.custom_frame = tk.LabelFrame(
            parent,
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
            # THÊM RGB
            'red': 'Red Channel',
            'green': 'Green Channel',
            'blue': 'Blue Channel',
        }
        
        self.custom_value_labels = {}
        
        for param_name, (min_val, max_val, default_val) in CUSTOM_PARAMS.items():
            frame = tk.Frame(self.custom_frame, bg=COLORS['white'])
            frame.pack(fill="x", pady=3)
            
            # Tạo label với màu tương ứng cho RGB
            label_text = param_labels[param_name] + ":"
            label_fg = COLORS['text_dark']
            
            # Đổi màu label cho RGB
            if param_name == 'red':
                label_fg = '#FF0000'  # Màu đỏ
            elif param_name == 'green':
                label_fg = '#00AA00'  # Màu xanh lá
            elif param_name == 'blue':
                label_fg = '#0000FF'  # Màu xanh dương
            
            tk.Label(
                frame,
                text=label_text,
                font=FONTS['small'],
                bg=COLORS['white'],
                fg=label_fg,  # Màu label
                width=15,  # Tăng width vì "Green Channel" dài hơn
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
            
            value_label = tk.Label(
                frame,
                text=f"{default_val:.2f}",
                font=FONTS['small'],
                bg=COLORS['white'],
                width=6,
                fg=COLORS['primary']
            )
            value_label.pack(side="right")
            
            self.custom_value_labels[param_name] = value_label
            
            scale.configure(command=lambda v, p=param_name: self.update_custom_param(p, v))
        
        # Buttons (giữ nguyên)
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
    
    def on_filter_changed(self):
        """Khi thay đổi filter"""
        filter_name = self.filter_var.get()
        
        if filter_name == "Custom":
            self.custom_frame.pack(fill="x", pady=(0, 15))
        else:
            self.custom_frame.pack_forget()
        
        self.preview_panel.update_preview()
    
    def update_custom_param(self, param_name, value):
        """Cập nhật giá trị custom parameter"""
        val = float(value)
        self.custom_value_labels[param_name].config(text=f"{val:.2f}")
        self.preview_panel.update_preview()
    
    def save_custom_preset(self):
        """Lưu custom preset"""
        from gui.preset_manager import PresetManager
        PresetManager.save_preset_dialog(self.root, self.custom_params, self.custom_presets, self.save_custom_presets_to_file)
    
    def manage_presets(self):
        """Quản lý custom presets"""
        from gui.preset_manager import PresetManager
        PresetManager.manage_presets_dialog(
            self.root,
            self.custom_presets,
            self.custom_params,
            self.custom_value_labels,
            self.save_custom_presets_to_file,
            self.preview_panel.update_preview
        )
    
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
    
    def reset_custom_params(self):
        """Reset custom parameters về default"""
        for param_name, (min_val, max_val, default_val) in CUSTOM_PARAMS.items():
            self.custom_params[param_name].set(default_val)
            self.custom_value_labels[param_name].config(text=f"{default_val:.2f}")
        
        self.preview_panel.update_preview()
    
    def create_bottom_section(self, parent):
        """Tạo phần bottom với progress và button"""
        bottom_frame = tk.Frame(parent, bg=COLORS['white'])
        bottom_frame.pack(fill="x", pady=(15, 0))
        
        self.progress_frame = tk.Frame(bottom_frame, bg=COLORS['white'])
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=500
        )
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_light']
        )
        self.progress_label.pack()
        
        self.process_btn = tk.Button(
            bottom_frame,
            text="🚀 Xử lý tất cả video",
            font=FONTS['button'],
            bg=COLORS['primary'],
            fg=COLORS['white'],
            padx=50,
            pady=15,
            cursor="hand2",
            bd=0,
            activebackground=COLORS['white'],
            activeforeground=COLORS['white'],
            command=self.start_processing,
            disabledforeground=COLORS['white'],
            state="disabled"
        )
        self.process_btn.pack(pady=(10, 0))
    
    def update_speed_label(self, value):
        """Cập nhật label tốc độ"""
        speed = float(value)
        self.speed_label.config(text=f"{speed:.1f}x")
    
    def update_zoom_label(self, value):
        """Cập nhật label zoom"""
        zoom = float(value)
        self.zoom_label.config(text=f"{zoom:.1f}x")
        if hasattr(self, 'preview_panel'):
            self.preview_panel.update_preview()
    
    def select_videos(self):
        """Chọn video"""
        files = filedialog.askopenfilenames(
            title="Chọn video",
            filetypes=SUPPORTED_FORMATS
        )
        
        if files:
            for file in files:
                if file not in self.video_files:
                    self.video_files.append(file)
                    self.add_video_item(file)
            
            self.update_info_label()
            self.process_btn.config(state="normal", bg=COLORS['primary'])
    
    def clear_all_videos(self):
        """Xóa tất cả video"""
        if self.processing:
            messagebox.showwarning("Cảnh báo", "Đang xử lý video!")
            return
        
        self.video_files.clear()
        
        for widget in self.video_items_frame.winfo_children():
            widget.destroy()
        
        self.update_info_label()
        self.process_btn.config(state="disabled", bg=COLORS['text_light'])
    
    def update_info_label(self):
        """Cập nhật info"""
        count = len(self.video_files)
        if count == 0:
            self.info_label.config(text="Chưa có video nào")
        else:
            total_size = sum(os.path.getsize(f) for f in self.video_files) / (1024 * 1024)
            self.info_label.config(
                text=f"📊 Tổng: {count} video • {total_size:.1f} MB"
            )
    
    def start_processing(self):
        """Bắt đầu xử lý"""
        if not self.video_files:
            messagebox.showwarning("Cảnh báo", "Chưa chọn video!")
            return
        
        if self.processing:
            return
        
        self.progress_frame.pack(fill="x", pady=(10, 10), before=self.process_btn)
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
            
            # Tạo file temp với tên KHÁC NHAU mỗi lần
            temp_dir = tempfile.gettempdir()
            timestamp = int(__import__('time').time() * 1000)  # Milliseconds
            temp_image = os.path.join(temp_dir, f"ffmpeg_preview_{timestamp}.jpg")
            
            # Xóa file cũ nếu tồn tại
            if os.path.exists(temp_image):
                try:
                    os.remove(temp_image)
                except:
                    pass
            
            print(f"🔧 Extracting frame to: {temp_image}")
            
            # Dùng FFmpeg extract frame đầu tiên
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                '-f', 'image2',  # THÊM format
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
                timeout=15,  # Tăng timeout
                text=True
            )
            
            # Debug
            if result.returncode != 0:
                print(f"❌ FFmpeg error: {result.stderr}")
            else:
                print(f"✅ FFmpeg success")
            
            # Đợi file được ghi xong
            import time
            max_wait = 3  # Đợi tối đa 3 giây
            wait_time = 0
            while not os.path.exists(temp_image) and wait_time < max_wait:
                time.sleep(0.1)
                wait_time += 0.1
            
            if os.path.exists(temp_image) and os.path.getsize(temp_image) > 0:
                print(f"✅ Frame extracted: {temp_image} ({os.path.getsize(temp_image)} bytes)")
                # Hiển thị trực tiếp trong preview
                self.root.after(0, lambda: self._show_video_preview(temp_image))
            else:
                print(f"❌ File không tồn tại hoặc rỗng: {temp_image}")
                
        except subprocess.TimeoutExpired:
            print("❌ FFmpeg timeout khi extract frame")
        except Exception as e:
            print(f"❌ Lỗi preview video: {e}")
    def _show_video_preview(self, image_path):
        """Hiển thị video preview trực tiếp"""
        try:
            # Kiểm tra file tồn tại
            if not os.path.exists(image_path):
                print(f"❌ File không tồn tại: {image_path}")
                return
            
            if os.path.getsize(image_path) == 0:
                print(f"❌ File rỗng: {image_path}")
                return
            
            # Bỏ highlight thumbnail cũ (KIỂM TRA AN TOÀN)
            try:
                if hasattr(self.preview_panel, 'selected_thumbnail') and self.preview_panel.selected_thumbnail:
                    if self.preview_panel.selected_thumbnail.winfo_exists():
                        self.preview_panel.selected_thumbnail.config(
                            relief="solid",
                            bd=2,
                            highlightbackground="#DFE6E9",
                            highlightthickness=2
                        )
                    self.preview_panel.selected_thumbnail = None
            except Exception as e:
                print(f"⚠️ Không thể reset thumbnail: {e}")
                self.preview_panel.selected_thumbnail = None
            
            # LƯU preview image path để có thể apply filter
            self.preview_panel.preview_image_path = image_path
            self.preview_panel.callback(image_path)
            
            # Load ảnh
            print(f"📸 Loading image: {image_path}")
            img = Image.open(image_path)
            print(f"✅ Image loaded: {img.size}")
            
            # Lấy zoom level
            zoom_level = self.zoom_var.get() if hasattr(self, 'zoom_var') else 1.0
            
            # Resize để fit canvas
            canvas_width = 500
            canvas_height = 300
            
            img_ratio = img.width / img.height
            canvas_ratio = canvas_width / canvas_height
            
            if img_ratio > canvas_ratio:
                new_width = int(canvas_width * zoom_level)
                new_height = int((canvas_width * zoom_level) / img_ratio)
            else:
                new_height = int(canvas_height * zoom_level)
                new_width = int((canvas_height * zoom_level) * img_ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Hiển thị trong preview panel
            self.preview_panel.preview_image = photo
            self.preview_panel.preview_canvas.delete("all")
            
            x = canvas_width // 2
            y = canvas_height // 2
            self.preview_panel.preview_canvas.create_image(x, y, image=photo)
            
            # Update status với filter hiện tại
            filter_name = self.filter_var.get()
            zoom_text = f" • Zoom: {zoom_level:.1f}x" if zoom_level != 1.0 else ""
            self.preview_panel.preview_status.config(
                text=f"🎬 Video Preview • Filter: {filter_name}{zoom_text}"
            )
            
            print("✅ Preview displayed successfully")
            
        except Exception as e:
            print(f"❌ Lỗi hiển thị preview: {e}")
            import traceback
            traceback.print_exc()
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
                    suggested_path = VideoProcessor.get_suggested_output_path(video_file)
                    
                    def ask_save_location():
                        save_path = filedialog.asksaveasfilename(
                            title=f"Chọn thư mục và tên cho video đầu tiên (các video sau sẽ lưu vào cùng thư mục này)",
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
                        print(f"⚠️ Người dùng hủy, dừng xử lý")
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
                    print(f"✅ Đã lưu: {save_path}")
                except Exception as e:
                    error_count += 1
                    error_files.append(f"{filename} (Lỗi lưu: {str(e)})")
                    print(f"❌ Lỗi lưu file: {e}")
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