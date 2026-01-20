"""
Preview Panel - Quản lý preview filter (Compact Version)
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
import threading
from pathlib import Path
from PIL import Image, ImageTk

from config import COLORS, FONTS
from video_processor import VideoProcessor


class PreviewPanel:
    """Panel để preview filter với ảnh mẫu - Phiên bản compact"""
    
    def __init__(self, parent, filter_var, custom_params, callback, zoom_var=None, compact=False):
        self.parent = parent
        self.filter_var = filter_var
        self.custom_params = custom_params
        self.callback = callback
        self.zoom_var = zoom_var
        self.compact = compact  # Chế độ compact
        
        self.preview_image_path = None
        self.preview_image = None
        self.selected_thumbnail = None
        
        # Tạo folder pictures nếu chưa có
        self.pictures_folder = Path("pictures")
        self.pictures_folder.mkdir(exist_ok=True)
        
        # Kích thước canvas tùy theo mode
        if compact:
            self.canvas_width = 350
            self.canvas_height = 200  # Giảm từ 220 xuống 200
            self.thumb_width = 100
            self.thumb_height = 70
        else:
            self.canvas_width = 500
            self.canvas_height = 300
            self.thumb_width = 140
            self.thumb_height = 100
        
        # Tạo UI
        self.create_ui()
        
        # Load ảnh từ folder
        self.load_pictures()
    
    def create_ui(self):
        """Tạo giao diện preview panel"""
        preview_frame = tk.LabelFrame(
            self.parent,
            text="👁 Preview Filter",
            font=FONTS['heading'] if not self.compact else FONTS['normal'],
            bg=COLORS['white'],
            fg=COLORS['primary'],
            padx=10 if self.compact else 15,
            pady=10 if self.compact else 15,
            relief="solid",
            bd=1
        )
        preview_frame.pack(fill="both", expand=True)
        
        # Button chọn ảnh
        choose_img_btn = tk.Button(
            preview_frame,
            text="🖼 Chọn ảnh",
            font=FONTS['small'] if self.compact else FONTS['normal'],
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            padx=15 if self.compact else 20,
            pady=6 if self.compact else 10,
            cursor="hand2",
            bd=0,
            command=self.choose_preview_image
        )
        choose_img_btn.pack(pady=(0, 8))
        
        # Canvas để hiển thị ảnh - COMPACT
        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=COLORS['background'],
            highlightthickness=0
        )
        self.preview_canvas.pack()
        
        # Label status
        self.preview_status = tk.Label(
            preview_frame,
            text="Chưa chọn ảnh preview",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_light']
        )
        self.preview_status.pack(pady=(6, 0))
        
        # Separator
        ttk.Separator(preview_frame, orient="horizontal").pack(fill="x", pady=8)
        
        # Label cho thư viện
        tk.Label(
            preview_frame,
            text="📚 Thư viện ảnh mẫu",
            font=FONTS['normal'] if self.compact else FONTS['heading'],
            bg=COLORS['white'],
            fg=COLORS['primary']
        ).pack(pady=(5, 8))
        
        # Frame cho thumbnail gallery với scrollbar NGANG
        gallery_container = tk.Frame(preview_frame, bg=COLORS['white'])
        gallery_container.pack(fill="both", expand=True)
        
        # Canvas cho thumbnails - NHỎ HƠN
        self.gallery_canvas = tk.Canvas(
            gallery_container,
            bg=COLORS['background'],
            highlightthickness=0,
            height=100 if self.compact else 150  # Giảm từ 110 xuống 100
        )
        
        # Scrollbar NGANG
        h_scrollbar = ttk.Scrollbar(
            gallery_container,
            orient="horizontal",
            command=self.gallery_canvas.xview
        )
        
        self.gallery_canvas.configure(xscrollcommand=h_scrollbar.set)
        
        # Frame chứa thumbnails
        self.thumbnails_frame = tk.Frame(self.gallery_canvas, bg=COLORS['background'])
        self.gallery_canvas.create_window((0, 0), window=self.thumbnails_frame, anchor="nw")
        
        self.gallery_canvas.pack(side="top", fill="both", expand=True)
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Bind scroll
        def configure_scroll(event):
            self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))
        
        self.thumbnails_frame.bind("<Configure>", configure_scroll)
        
        # Mouse wheel - cuộn NGANG
        def on_mousewheel(event):
            self.gallery_canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        
        self.gallery_canvas.bind("<Enter>", lambda e: self.gallery_canvas.bind_all("<MouseWheel>", on_mousewheel))
        self.gallery_canvas.bind("<Leave>", lambda e: self.gallery_canvas.unbind_all("<MouseWheel>"))
        
        # Lưu thumbnails để tránh garbage collection
        self.thumbnail_images = []
    
    def load_pictures(self):
        """Load tất cả ảnh từ folder pictures"""
        # Xóa thumbnails cũ
        for widget in self.thumbnails_frame.winfo_children():
            widget.destroy()
        
        self.thumbnail_images.clear()
        
        # Supported formats
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        
        # Lấy tất cả ảnh
        image_files = []
        for file in self.pictures_folder.iterdir():
            if file.suffix.lower() in image_extensions:
                image_files.append(file)
        
        if not image_files:
            tk.Label(
                self.thumbnails_frame,
                text="Chưa có ảnh nào trong folder 'pictures'",
                font=FONTS['small'],
                bg=COLORS['background'],
                fg=COLORS['text_light'],
                pady=20
            ).pack()
            return
        
        # Tạo row của thumbnails
        row_frame = tk.Frame(self.thumbnails_frame, bg=COLORS['background'])
        row_frame.pack(fill="x", pady=5)
        
        for idx, img_path in enumerate(image_files):
            self.create_thumbnail(row_frame, img_path)
    
    def create_thumbnail(self, parent, img_path):
        """Tạo thumbnail cho một ảnh - COMPACT"""
        try:
            # Load ảnh
            img = Image.open(img_path)
            
            # Tính toán resize giữ nguyên tỷ lệ
            img_ratio = img.width / img.height
            target_ratio = self.thumb_width / self.thumb_height
            
            if img_ratio > target_ratio:
                new_width = self.thumb_width
                new_height = int(self.thumb_width / img_ratio)
            else:
                new_height = self.thumb_height
                new_width = int(self.thumb_height * img_ratio)
            
            # Resize giữ tỷ lệ
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_images.append(photo)
            
            # Frame cho thumbnail - COMPACT
            frame_width = self.thumb_width + 10
            frame_height = self.thumb_height + 30
            
            thumb_frame = tk.Frame(
                parent,
                bg=COLORS['white'],
                relief="solid",
                bd=0,
                cursor="hand2",
                width=frame_width,
                height=frame_height,
                highlightbackground="#DFE6E9",
                highlightthickness=2
            )
            thumb_frame.pack(side="left", padx=3 if self.compact else 5)
            thumb_frame.pack_propagate(False)
            
            # Container cho ảnh
            img_container = tk.Frame(thumb_frame, bg=COLORS['white'])
            img_container.pack(expand=True)
            
            # Label hiển thị ảnh
            label = tk.Label(
                img_container,
                image=photo,
                bg=COLORS['white']
            )
            label.pack()
            
            # Tên file - RÚT NGẮN HƠN
            filename = img_path.name
            max_len = 12 if self.compact else 18
            if len(filename) > max_len:
                filename = filename[:max_len-3] + "..."
            
            name_label = tk.Label(
                thumb_frame,
                text=filename,
                font=FONTS['small'],
                bg=COLORS['white'],
                fg=COLORS['text_dark']
            )
            name_label.pack(side="bottom", pady=2)
            
            # Click để chọn
            def select_image(event=None):
                self.select_thumbnail_image(str(img_path), thumb_frame)
            
            thumb_frame.bind("<Button-1>", select_image)
            label.bind("<Button-1>", select_image)
            name_label.bind("<Button-1>", select_image)
            img_container.bind("<Button-1>", select_image)
            
        except Exception as e:
            print(f"Lỗi load thumbnail {img_path}: {e}")
    
    def select_thumbnail_image(self, image_path, thumb_frame):
        """Chọn thumbnail và hiển thị preview"""
        try:
            # Bỏ highlight thumbnail cũ
            if hasattr(self, 'selected_thumbnail') and self.selected_thumbnail:
                if self.selected_thumbnail.winfo_exists():
                    self.selected_thumbnail.config(
                        relief="solid",
                        bd=2,
                        highlightbackground="#DFE6E9",
                        highlightthickness=2
                    )
                self.selected_thumbnail = None
            
            # Highlight thumbnail mới
            thumb_frame.config(
                relief="solid",
                bd=3,
                highlightbackground="#3498DB",
                highlightthickness=3
            )
            self.selected_thumbnail = thumb_frame
            
            # Load và hiển thị ảnh
            self.preview_image_path = image_path
            self.callback(image_path)
            self.update_preview()
            
        except Exception as e:
            print(f"Lỗi select thumbnail: {e}")
    
    def choose_preview_image(self):
        """Chọn ảnh từ file dialog"""
        file = filedialog.askopenfilename(
            title="Chọn ảnh preview",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file:
            self.preview_image_path = file
            
            # Bỏ highlight thumbnail cũ
            if self.selected_thumbnail:
                self.selected_thumbnail.config(
                    relief="solid",
                    bd=2,
                    highlightbackground="#DFE6E9",
                    highlightthickness=2
                )
                self.selected_thumbnail = None
            
            filename = os.path.basename(file)
            max_len = 30 if self.compact else 40
            if len(filename) > max_len:
                filename = filename[:max_len-3] + "..."
            self.preview_status.config(text=f"📷 {filename}")
            
            self.callback(file)
            self.update_preview()
    
    def update_preview(self):
        """Cập nhật preview khi thay đổi filter"""
        if not self.preview_image_path or not os.path.exists(self.preview_image_path):
            return
        
        # Chạy trong thread
        threading.Thread(target=self._apply_filter_preview, daemon=True).start()
    
    def _apply_filter_preview(self):
        """Apply filter lên ảnh mẫu"""
        try:
            filter_name = self.filter_var.get()
            
            # Lấy custom params nếu là Custom filter
            custom_params = None
            if filter_name == "Custom":
                custom_params = {k: v.get() for k, v in self.custom_params.items()}
            
            # Tạo file temp
            import tempfile
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, "ffmpeg_preview.jpg")
            
            # Apply filter
            success = VideoProcessor.apply_filter_to_image(
                self.preview_image_path,
                filter_name,
                output_path,
                custom_params
            )
            
            if success:
                # Load ảnh
                img = Image.open(output_path)
                
                # Lấy zoom level
                zoom_level = self.zoom_var.get() if self.zoom_var else 1.0
                
                # Resize giữ tỷ lệ để fit vào canvas
                img_ratio = img.width / img.height
                canvas_ratio = self.canvas_width / self.canvas_height
                
                if img_ratio > canvas_ratio:
                    new_width = int(self.canvas_width * zoom_level)
                    new_height = int((self.canvas_width * zoom_level) / img_ratio)
                else:
                    new_height = int(self.canvas_height * zoom_level)
                    new_width = int((self.canvas_height * zoom_level) * img_ratio)
                
                # Resize với zoom
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Update UI
                self.parent.after(0, lambda: self._display_preview(photo, filter_name, new_width, new_height))
            else:
                self.parent.after(0, lambda: self.preview_status.config(
                    text="Lỗi apply filter"
                ))
        except Exception as e:
            print(f"Lỗi preview: {e}")
    
    def _display_preview(self, photo, filter_name, img_width, img_height):
        """Hiển thị preview image - center trong canvas"""
        self.preview_image = photo
        self.preview_canvas.delete("all")
        
        # Lấy zoom level
        zoom_level = self.zoom_var.get() if self.zoom_var else 1.0
        
        # Tính toán vị trí center
        x = self.canvas_width // 2
        y = self.canvas_height // 2
        
        # Vẽ ảnh ở giữa canvas
        self.preview_canvas.create_image(x, y, image=self.preview_image)
        
        # Update status
        current_text = self.preview_status.cget("text")
        if "📷" in current_text:
            filename = current_text.split("📷")[1].strip()
            zoom_text = f" • Zoom: {zoom_level:.1f}x" if zoom_level != 1.0 else ""
            filter_text = f" • {filter_name}" if not self.compact else ""
            self.preview_status.config(text=f"📷 {filename}{filter_text}{zoom_text}")
    
    def show_video_preview(self, image_path):
        """Hiển thị video preview trực tiếp (được gọi từ main_window)"""
        try:
            if not os.path.exists(image_path):
                return
            
            if os.path.getsize(image_path) == 0:
                return
            
            # Bỏ highlight thumbnail cũ
            try:
                if hasattr(self, 'selected_thumbnail') and self.selected_thumbnail:
                    if self.selected_thumbnail.winfo_exists():
                        self.selected_thumbnail.config(
                            relief="solid",
                            bd=2,
                            highlightbackground="#DFE6E9",
                            highlightthickness=2
                        )
                    self.selected_thumbnail = None
            except:
                self.selected_thumbnail = None
            
            # Lưu preview image path
            self.preview_image_path = image_path
            self.callback(image_path)
            
            # Load ảnh
            img = Image.open(image_path)
            
            # Lấy zoom level
            zoom_level = self.zoom_var.get() if self.zoom_var else 1.0
            
            # Resize để fit canvas
            img_ratio = img.width / img.height
            canvas_ratio = self.canvas_width / self.canvas_height
            
            if img_ratio > canvas_ratio:
                new_width = int(self.canvas_width * zoom_level)
                new_height = int((self.canvas_width * zoom_level) / img_ratio)
            else:
                new_height = int(self.canvas_height * zoom_level)
                new_width = int((self.canvas_height * zoom_level) * img_ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Hiển thị trong preview panel
            self.preview_image = photo
            self.preview_canvas.delete("all")
            
            x = self.canvas_width // 2
            y = self.canvas_height // 2
            self.preview_canvas.create_image(x, y, image=photo)
            
            # Update status
            filter_name = self.filter_var.get()
            zoom_text = f" • Zoom: {zoom_level:.1f}x" if zoom_level != 1.0 else ""
            filter_text = f" • {filter_name}" if not self.compact else ""
            self.preview_status.config(
                text=f"🎬 Video Preview{filter_text}{zoom_text}"
            )
            
        except Exception as e:
            print(f"❌ Lỗi hiển thị preview: {e}")