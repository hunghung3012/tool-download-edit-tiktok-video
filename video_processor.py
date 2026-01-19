"""
FFmpeg Video Processor - Logic xử lý video
"""

import subprocess
import os
from pathlib import Path
import time
import tempfile
from config import FILTERS, FFMPEG_SETTINGS, CUSTOM_PARAMS

class VideoProcessor:
    """Class xử lý video với FFmpeg"""
    
    @staticmethod
    def check_ffmpeg():
        """Kiểm tra xem FFmpeg đã được cài đặt chưa"""
        try:
                        # Ẩn cửa sổ console
            startupinfo = None
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True, 
                timeout=5,
                startupinfo=startupinfo
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return True, version_line
            else:
                return False, "FFmpeg không hoạt động đúng"
        except FileNotFoundError:
            return False, "Không tìm thấy FFmpeg"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    @staticmethod
    def get_filter_command(filter_name, custom_params=None):
        """
        Lấy lệnh filter cho FFmpeg
        
        Args:
            filter_name: Tên filter
            custom_params: Dict các tham số custom (nếu filter_name == "Custom")
        """
        if filter_name == "Custom" and custom_params:
            # Xây dựng filter từ custom params
            filters = []
            
            # EQ filter cho brightness, contrast, saturation, gamma
            eq_params = []
            if custom_params.get('brightness', 0.0) != 0.0:
                eq_params.append(f"brightness={custom_params['brightness']:.2f}")
            if custom_params.get('contrast', 1.0) != 1.0:
                eq_params.append(f"contrast={custom_params['contrast']:.2f}")
            if custom_params.get('saturation', 1.0) != 1.0:
                eq_params.append(f"saturation={custom_params['saturation']:.2f}")
            if custom_params.get('gamma', 1.0) != 1.0:
                eq_params.append(f"gamma={custom_params['gamma']:.2f}")
            
            if eq_params:
                filters.append(f"eq={':'.join(eq_params)}")
            
            # Hue filter
            if custom_params.get('hue', 0) != 0:
                filters.append(f"hue=h={custom_params['hue']}")
            
            # Vibrance (dùng vibrance filter)
            vibrance = custom_params.get('vibrance', 1.0)
            if vibrance != 1.0:
                # Vibrance effect bằng cách điều chỉnh saturation có chọn lọc
                intensity = (vibrance - 1.0) * 0.5  # Scale to -0.5 to 0.5
                filters.append(f"eq=saturation={1.0 + intensity:.2f}")
            
            # ===== THÊM RGB CHANNELS (MỚI) =====
            red = custom_params.get('red', 1.0)
            green = custom_params.get('green', 1.0)
            blue = custom_params.get('blue', 1.0)
            
            # Chỉ thêm colorchannelmixer nếu có thay đổi
            if red != 1.0 or green != 1.0 or blue != 1.0:
                filters.append(f"colorchannelmixer=rr={red:.2f}:gg={green:.2f}:bb={blue:.2f}")
            # ===== KẾT THÚC PHẦN THÊM =====
            
            return ",".join(filters) if filters else ""
        
        return FILTERS.get(filter_name, "")
    
    @staticmethod
    def get_suggested_output_path(video_file):
        """
        Tạo đường dẫn output đề xuất (trong thư mục edited)
        
        Args:
            video_file: Đường dẫn file video gốc
            
        Returns:
            str: Đường dẫn file output được đề xuất
        """
        input_path = Path(video_file)
        parent_dir = input_path.parent
        edited_dir = parent_dir / "edited"
        
        # Tạo folder edited nếu chưa có
        edited_dir.mkdir(exist_ok=True)
        
        # Tạo tên file output
        timestamp = int(time.time())
        output_filename = f"{input_path.stem}_processed_{timestamp}{input_path.suffix}"
        return str(edited_dir / output_filename)
    
    @staticmethod
    def process_video(video_file, speed, zoom, filter_name, custom_params=None, progress_callback=None):
        """
        Xử lý một video (xử lý vào file TẠM, không lưu luôn)
        
        Args:
            video_file: Đường dẫn file video
            speed: Tốc độ (1.0 = bình thường)
            zoom: Mức zoom (1.0 = không zoom)
            filter_name: Tên filter
            custom_params: Dict tham số custom nếu dùng Custom filter
            progress_callback: Callback để báo tiến trình
            
        Returns:
            tuple: (success, temp_file_path hoặc error_message)
        """
        try:
            # Kiểm tra file input
            if not os.path.exists(video_file):
                return False, f"File không tồn tại: {video_file}"
            
            # Tạo file TẠM để xử lý
            input_path = Path(video_file)
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            temp_file = os.path.join(temp_dir, f"ffmpeg_temp_{timestamp}{input_path.suffix}")
            
            # Lấy filter command
            filter_cmd = VideoProcessor.get_filter_command(filter_name, custom_params)
            
            # Xây dựng filter chain
            filters = []
            
            # Speed filter
            if speed != 1.0:
                filters.append(f"setpts={1/speed}*PTS")
            
            # Zoom filter
            if zoom != 1.0:
                if zoom > 1:
                    # Zoom in: scale up và crop về kích thước gốc
                    filters.append(f"scale=iw*{zoom}:ih*{zoom},crop=iw/{zoom}:ih/{zoom}")
                else:
                    # Zoom out
                    filters.append(f"scale=iw*{zoom}:ih*{zoom}")
            
            # Color filter
            if filter_cmd:
                filters.append(filter_cmd)
            
            # Kết hợp filters
            vf_filter = ",".join(filters) if filters else None
            
            # Xây dựng lệnh FFmpeg
            cmd = ['ffmpeg', '-i', video_file, '-y']
            
            if vf_filter:
                cmd.extend(['-vf', vf_filter])
            
            # Audio speed
            if speed != 1.0:
                if 0.5 <= speed <= 2.0:
                    cmd.extend(['-af', f'atempo={speed}'])
                else:
                    # Xử lý tốc độ ngoài phạm vi 0.5-2.0
                    atempo_filters = []
                    remaining_speed = speed
                    
                    while remaining_speed > 2.0:
                        atempo_filters.append('atempo=2.0')
                        remaining_speed /= 2.0
                    
                    while remaining_speed < 0.5:
                        atempo_filters.append('atempo=0.5')
                        remaining_speed /= 0.5
                    
                    if remaining_speed != 1.0:
                        atempo_filters.append(f'atempo={remaining_speed:.2f}')
                    
                    cmd.extend(['-af', ','.join(atempo_filters)])
            
            # Video encoding settings
            cmd.extend([
                '-c:v', FFMPEG_SETTINGS['video_codec'],
                '-preset', FFMPEG_SETTINGS['preset'],
                '-crf', FFMPEG_SETTINGS['crf']
            ])
            
            cmd.append(temp_file)
            
            # Debug
            print(f"🔧 FFmpeg command: {' '.join(cmd)}")
            print(f"📁 Temp file: {temp_file}")
            
            # Chạy FFmpeg
            startupinfo = None
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"❌ FFmpeg error:\n{stderr}")
                # Xóa temp file nếu lỗi
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return False, f"Lỗi FFmpeg: {stderr[:200]}"
            
            print(f"✅ Processed successfully to temp: {temp_file}")
            return True, temp_file
            
        except Exception as e:
            error_msg = f"Lỗi xử lý video: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    @staticmethod
    def apply_filter_to_image(image_path, filter_name, output_path, custom_params=None):
        """
        Áp dụng filter lên ảnh để preview
        
        Args:
            image_path: Đường dẫn ảnh input
            filter_name: Tên filter
            output_path: Đường dẫn ảnh output
            custom_params: Dict tham số custom nếu dùng Custom filter
            
        Returns:
            bool: Thành công hay không
        """
        try:
            filter_cmd = VideoProcessor.get_filter_command(filter_name, custom_params)
            
            if not filter_cmd:
                # Không có filter, copy ảnh gốc
                import shutil
                shutil.copy(image_path, output_path)
                return True
            
            cmd = [
                'ffmpeg',
                '-i', image_path,
                '-vf', filter_cmd,
                '-y',
                output_path
            ]
            
            # Ẩn cửa sổ console
            startupinfo = None
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            result = subprocess.run(
                cmd, 
                capture_output=True, 
                timeout=10,
                startupinfo=startupinfo
            )
            return result.returncode == 0
            
        except Exception as e:
            print(f"Lỗi apply filter: {e}")
            return False