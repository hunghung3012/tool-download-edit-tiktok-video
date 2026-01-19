"""
Preview Panel - Quản lý preview filter
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
    """Panel để preview filter với ảnh mẫu"""
    
    def __init__(self, parent, filter_var, custom_params, callback, zoom_var=None):
        self.parent = parent
        self.filter_var = filter_var
        self.custom_params = custom_params
        self.callback = callback
        self.zoom_var = zoom_var  # Thêm zoom_var
        
        self.preview_image_path = None
        self.preview_image = None
        self.selected_thumbnail = None
        
        # Tạo folder pictures nếu chưa có
        self.pictures_folder = Path("pictures")
        self.pictures_folder.mkdir(exist_ok=True)
        
        # Tạo UI
        self.create_ui()
        
        # Load ảnh từ folder
        self.load_pictures()
    
    def create_ui(self):
        """Tạo giao diện preview panel"""
        preview_frame = tk.LabelFrame(
            self.parent,
            text="👁 Preview Filter",
            font=FONTS['heading'],
            bg=COLORS['white'],
            fg=COLORS['primary'],
            padx=15,
            pady=15,
            relief="solid",
            bd=1
        )
        preview_frame.pack(fill="both", expand=True)
        
        # Button chọn ảnh
        choose_img_btn = tk.Button(
            preview_frame,
            text="🖼 Chọn ảnh",
            font=FONTS['normal'],
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            padx=20,
            pady=10,
            cursor="hand2",
            bd=0,
            command=self.choose_preview_image
        )
        choose_img_btn.pack(pady=(0, 10))
        
        # Canvas để hiển thị ảnh - TO HƠN
        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=500,
            height=300,
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
        self.preview_status.pack(pady=(8, 0))
        
        # Separator
        ttk.Separator(preview_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Label cho thư viện
        tk.Label(
            preview_frame,
            text="📚 Thư viện ảnh mẫu",
            font=FONTS['heading'],
            bg=COLORS['white'],
            fg=COLORS['primary']
        ).pack(pady=(5, 10))
        
        # Frame cho thumbnail gallery với scrollbar NGANG
        gallery_container = tk.Frame(preview_frame, bg=COLORS['white'])
        gallery_container.pack(fill="both", expand=True)
        
        # Canvas cho thumbnails
        self.gallery_canvas = tk.Canvas(
            gallery_container,
            bg=COLORS['background'],
            highlightthickness=0,
            height=150
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
                text="Chưa có ảnh nào trong folder 'pictures'\nHãy thêm ảnh vào folder để hiển thị",
                font=FONTS['small'],
                bg=COLORS['background'],
                fg=COLORS['text_light'],
                pady=20
            ).pack()
            return
        
        # Tạo grid của thumbnails - KHÔNG giới hạn số ảnh/hàng
        # Sẽ tự động wrap khi hết chỗ
        row_frame = tk.Frame(self.thumbnails_frame, bg=COLORS['background'])
        row_frame.pack(fill="x", pady=5)
        
        for idx, img_path in enumerate(image_files):
            self.create_thumbnail(row_frame, img_path)
    
    def create_thumbnail(self, parent, img_path):
        """Tạo thumbnail cho một ảnh"""
        try:
            # Load ảnh
            img = Image.open(img_path)
            
            # Tính toán resize giữ nguyên tỷ lệ
            target_width = 140
            target_height = 100
            
            # Tính tỷ lệ
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                # Ảnh rộng hơn
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                # Ảnh cao hơn
                new_height = target_height
                new_width = int(target_height * img_ratio)
            
            # Resize giữ tỷ lệ
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_images.append(photo)
            
            # Frame cho thumbnail - fixed size
            thumb_frame = tk.Frame(
                parent,
                bg=COLORS['white'],
                relief="solid",
                bd=0,                       
                cursor="hand2",
                width=150,
                height=130,
                highlightbackground="#DFE6E9",    
                highlightthickness=2               
            )
            thumb_frame.pack(side="left", padx=5)
            thumb_frame.pack_propagate(False)  # Giữ kích thước cố định
            
            # Container cho ảnh (để center)
            img_container = tk.Frame(thumb_frame, bg=COLORS['white'])
            img_container.pack(expand=True)
            
            # Label hiển thị ảnh
            label = tk.Label(
                img_container,
                image=photo,
                bg=COLORS['white']
            )
            label.pack()
            
            # Tên file
            filename = img_path.name
            if len(filename) > 18:
                filename = filename[:15] + "..."
            
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
            # Bỏ highlight thumbnail cũ (KIỂM TRA TỒN TẠI TRƯỚC)
            if hasattr(self, 'selected_thumbnail') and self.selected_thumbnail:
                # THÊM KIỂM TRA NÀY
                if self.selected_thumbnail.winfo_exists():
                    self.selected_thumbnail.config(
                        relief="solid",
                        bd=2,
                        highlightbackground="#DFE6E9",
                        highlightthickness=2
                    )
                # Reset reference
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
            if len(filename) > 40:
                filename = filename[:37] + "..."
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
                
                # Resize giữ tỷ lệ để fit vào canvas 500x300
                canvas_width = 500
                canvas_height = 300
                
                # Tính tỷ lệ
                img_ratio = img.width / img.height
                canvas_ratio = canvas_width / canvas_height
                
                if img_ratio > canvas_ratio:
                    # Ảnh rộng hơn canvas
                    new_width = int(canvas_width * zoom_level)
                    new_height = int((canvas_width * zoom_level) / img_ratio)
                else:
                    # Ảnh cao hơn canvas
                    new_height = int(canvas_height * zoom_level)
                    new_width = int((canvas_height * zoom_level) * img_ratio)
                
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
            self.parent.after(0, lambda: self.preview_status.config(
                text="Preview"
            ))
    
    def _display_preview(self, photo, filter_name, img_width, img_height):
        """Hiển thị preview image - center trong canvas"""
        self.preview_image = photo
        self.preview_canvas.delete("all")
        
        # Lấy zoom level
        zoom_level = self.zoom_var.get() if self.zoom_var else 1.0
        
        # Tính toán vị trí center
        canvas_width = 500
        canvas_height = 300
        x = canvas_width // 2
        y = canvas_height // 2
        
        # Vẽ ảnh ở giữa canvas (ảnh đã được zoom trong _apply_filter_preview)
        self.preview_canvas.create_image(x, y, image=self.preview_image)
        
        # Update status
        current_text = self.preview_status.cget("text")
        if "📷" in current_text:
            # Giữ tên file, thêm filter và zoom
            filename = current_text.split("📷")[1].strip()
            zoom_text = f" • Zoom: {zoom_level:.1f}x" if zoom_level != 1.0 else ""
            self.preview_status.config(text=f"📷 {filename} • Filter: {filter_name}{zoom_text}")
        
        # Hiển thị kích thước ảnh
        size_text = f"{img_width}x{img_height}"
        self.preview_canvas.create_text(
            canvas_width - 5,
            canvas_height - 5,
            text=size_text,
            anchor="se",
            fill=COLORS['text_light'],
            font=FONTS['small']
        )