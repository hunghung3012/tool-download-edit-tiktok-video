"""
Configuration và Constants cho FFmpeg Video Processor
"""

# Màu sắc giao diện
COLORS = {
    'primary': '#6C5CE7',      # Purple chính
    'primary_dark': '#5B4BC4',  # Purple đậm
    'secondary': '#A29BFE',     # Purple nhạt
    'success': '#00B894',       # Xanh lá
    'danger': '#FF7675',        # Đỏ
    'warning': '#FDCB6E',       # Vàng
    'background': '#F5F6FA',    # Nền nhạt
    'white': '#FFFFFF',
    'text_dark': '#2D3436',
    'text_light': '#636E72',
    'border': '#DFE6E9'
}

# Font chữ
FONTS = {
    'title': ('Segoe UI', 24, 'bold'),
    'subtitle': ('Segoe UI', 11),
    'heading': ('Segoe UI', 12, 'bold'),
    'normal': ('Segoe UI', 10),
    'small': ('Segoe UI', 9),
    'button': ('Segoe UI', 11, 'bold')
}

# Cài đặt mặc định
DEFAULT_SETTINGS = {
    'speed': 1.2,
    'zoom': 1.2,
    'filter': 'Custom1'
}

# Các filter có sẵn
FILTERS = {
    "Không filter": "",
    "Custom1": "eq=brightness=0.06:contrast=1.12:saturation=1.18,colortemperature=5500,unsharp=5:5:0.9:5:5:0.0",
    "Grayscale (Đen trắng)": "hue=s=0",
    # "Sepia (Màu nâu cổ điển)": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
    "Blur (Làm mờ)": "boxblur=2:1",
    "Sharpen (Sắc nét)": "unsharp=5:5:1.0:5:5:0.0",
    "Brightness (Sáng hơn)": "eq=brightness=0.1",
    "Contrast (Tương phản)": "eq=contrast=1.2",
    "Saturation (Bão hòa)": "eq=saturation=1.5",
    "Vintage (Cổ điển)": "curves=vintage",
    "Cool (Lạnh)": "colortemperature=10000",
    "Custom": "custom"  # Đánh dấu để hiện custom controls
}

# Custom filter parameters (min, max, default)
# Custom filter parameters (min, max, default)
CUSTOM_PARAMS = {
    'brightness': (-1.0, 1.0, 0.0),
    'contrast': (0.0, 3.0, 1.0),
    'saturation': (0.0, 3.0, 1.0),
    'gamma': (0.1, 3.0, 1.0),
    'hue': (-180, 180, 0),
    'vibrance': (0.0, 2.0, 1.0),
    # THÊM RGB
    'red': (0.0, 2.0, 1.0),      # Kênh đỏ
    'green': (0.0, 2.0, 1.0),    # Kênh xanh lá
    'blue': (0.0, 2.0, 1.0),     # Kênh xanh dương
}

# Định dạng video hỗ trợ
SUPPORTED_FORMATS = [
    ("Video files", "*.mp4 *.mov *.avi *.mkv *.webm"),
    ("All files", "*.*")
]

# URL ảnh mẫu để preview filter
SAMPLE_IMAGE_URL = "https://picsum.photos/400/300"

# Cài đặt FFmpeg
FFMPEG_SETTINGS = {
    'preset': 'medium',
    'crf': '23',
    'video_codec': 'libx264'
}