"""
FFmpeg Video Processor - Main Entry Point
Chương trình xử lý video hàng loạt với FFmpeg
"""

import tkinter as tk
from gui.main_window import FFmpegVideoProcessor

def main():
    """Khởi chạy ứng dụng"""
    root = tk.Tk()
    app = FFmpegVideoProcessor(root)
    root.mainloop()

if __name__ == "__main__":
    main()