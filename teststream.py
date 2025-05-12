import os
import requests
import shutil
import time
import psutil
from tqdm import tqdm

# مسیر پوشه‌ای که فایل‌های m3u در آن قرار دارند
input_folder = 'specialiptvs'
# مسیر پوشه‌ای که فایل‌های معتبر در آن قرار می‌گیرند
valid_folder = 'validm3ufiles'

# ایجاد پوشه validm3ufiles اگر وجود نداشته باشد
if not os.path.exists(valid_folder):
    os.makedirs(valid_folder)

def download_stream(url, duration=5):
    start_time = time.time()
    total_downloaded = 0
    start_net_io = psutil.net_io_counters().bytes_recv

    try:
        response = requests.get(url, stream=True, timeout=duration)
        response.raise_for_status()

        file_size = int(response.headers.get('content-length', 0))
        chunk_size = 1024
        progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc="Downloading")

        for chunk in response.iter_content(chunk_size=chunk_size):
            if time.time() - start_time >= duration:
                break
            if chunk:
                progress_bar.update(len(chunk))
                total_downloaded += len(chunk)

        progress_bar.close()
        end_net_io = psutil.net_io_counters().bytes_recv
        total_consumed = (end_net_io - start_net_io) / 1024 / 1024  # تبدیل به مگابایت

        return total_consumed >= 1  # اگر بیشتر از 1 مگابایت مصرف شده باشد، True برگردانید

    except Exception as e:
        print(f"Error downloading stream: {e}")
        return False

def process_m3u_file(file_path):
    try:
        # ابتدا با UTF-8 امتحان کنید
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        try:
            # اگر UTF-8 کار نکرد، با ISO-8859-1 امتحان کنید
            with open(file_path, 'r', encoding='iso-8859-1') as file:
                lines = file.readlines()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return

    if len(lines) >= 15:
        stream_url = lines[14].strip()  # خط 15 (شاخص 14 در لیست)
        if stream_url.startswith('http'):
            print(f"\nProcessing file: {os.path.basename(file_path)}")
            print(f"Stream URL: {stream_url}")
            if download_stream(stream_url):
                print("Stream is valid. Moving to validm3ufiles folder.")
                shutil.move(file_path, os.path.join(valid_folder, os.path.basename(file_path)))
            else:
                print("Stream is invalid. Ignoring file.")
        else:
            print("Invalid stream URL. Ignoring file.")
    else:
        print(f"File {os.path.basename(file_path)} does not have 15 lines. Ignoring file.")

def main():
    # لیست تمام فایل‌های m3u در پوشه ورودی
    m3u_files = [f for f in os.listdir(input_folder) if f.endswith('.m3u')]
    
    for filename in m3u_files:
        file_path = os.path.join(input_folder, filename)
        process_m3u_file(file_path)

if __name__ == "__main__":
    main()
