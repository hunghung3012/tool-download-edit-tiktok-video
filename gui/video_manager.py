"""
Video Manager - Quản lý danh sách video và TikTok downloads
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import re
import requests
from pathlib import Path
from datetime import datetime

from config import COLORS, FONTS, SUPPORTED_FORMATS


class VideoManager:
    """Class quản lý video list và TikTok downloads"""
    
    def __init__(self, parent, video_files, update_callback, preview_callback):
        self.parent = parent
        self.video_files = video_files
        self.update_callback = update_callback
        self.preview_callback = preview_callback
        
        # TikTok API Configuration
        self.api_key = "33b0a76a43msha9299be208680fdp199451jsnb8d6ba77a30c"
        self.api_host = "tiktok-video-downloader-api.p.rapidapi.com"
        
        self.selected_video_item = None
        
        # Tạo UI
        self.create_upload_section()
        self.create_video_list_section()
    
    def create_upload_section(self):
        """Tạo phần chọn video và TikTok links"""
        upload_frame = tk.LabelFrame(
            self.parent,
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
        
        # Tab buttons
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
            selectcolor=COLORS['white'],
            activebackground=COLORS['white'],
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
            selectcolor=COLORS['white'],
            activebackground=COLORS['white'],
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
            height=6,  # Giảm từ 8 xuống 6
            font=FONTS['small'],
            wrap=tk.WORD
        )
        self.url_text.pack(fill="both", expand=True)
        
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
        self.parent.after(100, self.auto_parse_urls)
    
    def auto_parse_urls(self, event=None):
        """Tự động parse và format TikTok URLs"""
        text = self.url_text.get("1.0", tk.END)
        url_pattern = r'https?://(?:www\.)?tiktok\.com/@[^/]+/video/\d+[^\s]*'
        urls = re.findall(url_pattern, text)
        
        if urls:
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
        progress_dialog = tk.Toplevel(self.parent)
        progress_dialog.title("Đang tải TikTok videos...")
        progress_dialog.geometry("400x150")
        progress_dialog.transient(self.parent)
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
            today = datetime.now().strftime("%d-%b")
            videos_folder = Path(f"D:/Tools/TiktokVideoEdit/{today}")
            videos_folder.mkdir(parents=True, exist_ok=True)
            
            success_count = 0
            failed_count = 0
            
            for i, url in enumerate(urls, 1):
                try:
                    self.parent.after(0, lambda i=i: status_label.config(
                        text=f"Đang tải video {i}/{len(urls)}..."
                    ))
                    
                    download_url, thumbnail_url = self.get_tiktok_download_url(url)
                    video_id = self.extract_video_id(url)
                    filename = f"tiktok_{video_id}_{i}.mp4" if video_id else f"tiktok_video_{i}.mp4"
                    filepath = videos_folder / filename
                    
                    self.download_tiktok_video(download_url, filepath)
                    
                    if thumbnail_url:
                        pictures_folder = Path("pictures")
                        pictures_folder.mkdir(exist_ok=True)
                        
                        thumb_filename = f"tiktok_{video_id}_{i}_thumb.jpg"
                        thumb_path = pictures_folder / thumb_filename
                        try:
                            self.download_tiktok_video(thumbnail_url, thumb_path)
                        except:
                            pass
                    
                    self.parent.after(0, lambda f=str(filepath): self.video_files.append(f))
                    self.parent.after(0, lambda f=str(filepath): self.add_video_item(f))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    self.parent.after(0, progress_dialog.destroy)
                    self.parent.after(0, lambda msg=error_msg, idx=i: messagebox.showerror(
                        "Lỗi tải video",
                        f"Lỗi tại video {idx}:\n{msg}\n\nĐã dừng tải."
                    ))
                    return
            
            self.parent.after(0, progress_dialog.destroy)
            self.parent.after(0, self.update_info_label)
            self.parent.after(0, self.update_callback)
            self.parent.after(0, lambda: self.url_text.delete("1.0", tk.END))
            
            msg = f"Hoàn thành!\n\nThành công: {success_count}\nThất bại: {failed_count}\n\n📁 Đã lưu vào: {videos_folder}"
            self.parent.after(0, lambda: messagebox.showinfo("Kết quả", msg))
        
        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()
    
    def get_tiktok_download_url(self, video_url):
        """Dùng TikWM làm chính, RapidAPI làm backup"""
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
                        return (download_url, thumbnail_url)
        except Exception as e:
            print(f"⚠️ TikWM failed: {e}")
        
        # Fallback to RapidAPI
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
                            data.get('data', {}).get('thumbnail'))
            
            if download_url:
                return (download_url, thumbnail_url)
            
            raise Exception("Không tìm thấy URL download")
            
        except Exception as e:
            raise Exception(f"Tất cả APIs thất bại: {str(e)}")
    
    def download_tiktok_video(self, download_url, filepath):
        """Download video từ URL"""
        response = requests.get(
            download_url,
            timeout=30,
            stream=True,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.tiktok.com/'
            }
        )
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
    
    def extract_video_id(self, url):
        """Extract video ID từ TikTok URL"""
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else None
    
    def create_video_list_section(self):
        """Tạo danh sách video với scrollbar"""
        list_frame = tk.LabelFrame(
            self.parent,
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
            height=120  # Giảm từ 150 xuống 120
        )
        video_canvas.pack(side="left", fill="both", expand=True)
        
        v_scrollbar.config(command=video_canvas.yview)
        h_scrollbar.config(command=video_canvas.xview)
        
        self.video_items_frame = tk.Frame(video_canvas, bg=COLORS['background'])
        video_canvas.create_window((0, 0), window=self.video_items_frame, anchor="nw")
        
        self.video_items_frame.bind("<Configure>", 
            lambda e: video_canvas.configure(scrollregion=video_canvas.bbox("all")))
        
        def on_mouse_wheel(event):
            video_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        video_canvas.bind("<Enter>", lambda e: video_canvas.bind_all("<MouseWheel>", on_mouse_wheel))
        video_canvas.bind("<Leave>", lambda e: video_canvas.unbind_all("<MouseWheel>"))
        
        self.info_label = tk.Label(
            list_frame,
            text="Chưa có video nào được chọn",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_light']
        )
        self.info_label.pack(pady=(8, 0))
    
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
            self.update_callback()
    
    def clear_all_videos(self):
        """Xóa tất cả video"""
        self.video_files.clear()
        
        for widget in self.video_items_frame.winfo_children():
            widget.destroy()
        
        self.update_info_label()
        self.update_callback()
    
    def add_video_item(self, filepath):
        """Thêm một video item vào danh sách"""
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath) / (1024 * 1024)
        
        name_without_ext = os.path.splitext(filename)[0]
        file_ext = os.path.splitext(filename)[1]
        
        item_frame = tk.Frame(
            self.video_items_frame,
            bg=COLORS['white'],
            relief="solid",
            bd=1
        )
        item_frame.pack(fill="x", pady=2, padx=2)
        item_frame.current_filepath = filepath
        
        # Name container
        name_container = tk.Frame(item_frame, bg=COLORS['white'])
        name_container.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        
        name_var = tk.StringVar(value=name_without_ext)
        
        entry = tk.Entry(
            name_container,
            textvariable=name_var,
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_dark'],
            relief="flat",
            state="readonly",
            readonlybackground=COLORS['white'],
            cursor="arrow"
        )
        entry.pack(side="left", fill="x", expand=True)
        
        ext_label = tk.Label(
            name_container,
            text=file_ext,
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['primary']
        )
        ext_label.pack(side="left", padx=(2, 0))
        
        size_label = tk.Label(
            item_frame,
            text=f"({filesize:.1f} MB)",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_light']
        )
        size_label.pack(side="left", padx=5)
        
        # Preview on click
        def preview_video(event=None):
            if entry['state'] == 'readonly':
                self.preview_video_thumbnail(item_frame.current_filepath, item_frame)
        
        entry.bind("<Button-1>", preview_video)
        item_frame.bind("<Button-1>", preview_video)
        
        # Edit/Save button
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
            if entry['state'] == 'readonly':
                entry.config(state="normal", cursor="xterm")
                edit_save_btn.config(text="💾", bg=COLORS['success'])
                entry.focus_set()
                entry.icursor(tk.END)
            else:
                rename_file()
                entry.config(state="readonly", cursor="arrow")
                edit_save_btn.config(text="✏️", bg=COLORS['warning'])
        
        edit_save_btn.config(command=toggle_edit_save)
        
        entry.bind("<Return>", lambda e: toggle_edit_save())
        entry.bind("<Escape>", lambda e: (
            name_var.set(name_without_ext),
            entry.config(state="readonly", cursor="arrow"),
            edit_save_btn.config(text="✏️", bg=COLORS['warning'])
        ))
        
        def rename_file(event=None):
            new_name = name_var.get().strip()
            old_name_without_ext = os.path.splitext(os.path.basename(item_frame.current_filepath))[0]
            
            if new_name and new_name != old_name_without_ext:
                try:
                    old_path = Path(item_frame.current_filepath)
                    new_filename = new_name + file_ext
                    new_path = old_path.parent / new_filename
                    
                    if new_path.exists():
                        messagebox.showerror("Lỗi", f"File '{new_filename}' đã tồn tại!")
                        name_var.set(old_name_without_ext)
                        return
                    
                    old_path.rename(new_path)
                    
                    old_filepath = item_frame.current_filepath
                    new_filepath = str(new_path)
                    
                    if old_filepath in self.video_files:
                        idx = self.video_files.index(old_filepath)
                        self.video_files[idx] = new_filepath
                    
                    item_frame.current_filepath = new_filepath
                    item_frame.filepath = new_filepath
                    
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể đổi tên:\n{str(e)}")
                    name_var.set(old_name_without_ext)
        
        # Play button
        import subprocess
        def play_video():
            try:
                if os.name == 'nt':
                    os.startfile(item_frame.current_filepath)
                else:
                    subprocess.run(['open', item_frame.current_filepath])
            except:
                pass
        
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
            command=play_video
        )
        play_btn.pack(side="right", padx=2)
        
        # Delete button
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
        if filepath in self.video_files:
            self.video_files.remove(filepath)
        
        item_frame.destroy()
        self.update_info_label()
        self.update_callback()
    
    def preview_video_thumbnail(self, video_path, item_frame):
        """Preview video bằng cách highlight và gọi callback"""
        if hasattr(self, 'selected_video_item') and self.selected_video_item:
            self.selected_video_item.config(bg=COLORS['white'])
            for child in self.selected_video_item.winfo_children():
                if isinstance(child, (tk.Label, tk.Frame)):
                    try:
                        child.config(bg=COLORS['white'])
                    except:
                        pass
        
        item_frame.config(bg=COLORS['secondary'])
        for child in item_frame.winfo_children():
            if isinstance(child, (tk.Label, tk.Frame)):
                try:
                    child.config(bg=COLORS['secondary'])
                except:
                    pass
        
        self.selected_video_item = item_frame
        self.preview_callback(video_path)
    
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