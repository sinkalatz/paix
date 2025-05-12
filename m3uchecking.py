import os
import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import sys

def print_colored(text, color):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
    }
    reset = "\033[0m"
    print(f"{colors.get(color, '')}{text}{reset}")

def download_with_progress(url, timeout=20):
    try:
        start_time = time.time()
        downloaded_bytes = 0
        
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            progress_bar = tqdm(
                total=total_size, 
                unit='B', 
                unit_scale=True,
                desc=f"Checking {url[:30]}...",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}] {postfix}"
            )
            
            content = bytearray()
            for chunk in r.iter_content(chunk_size=8192):
                if time.time() - start_time > timeout:
                    raise TimeoutError("Timeout reached")
                
                if chunk:
                    downloaded_bytes += len(chunk)
                    content.extend(chunk)
                    progress_bar.update(len(chunk))
                    
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 0:
                        current_speed = downloaded_bytes / elapsed_time
                        progress_bar.set_postfix({"speed": f"{current_speed/1024:.1f} KB/s"})
                        
                        if elapsed_time > 1 and current_speed < 100 * 1024:
                            raise ValueError("Speed too slow")
            
            progress_bar.close()
            return content.decode('utf-8', errors='ignore')
        
    except Exception as e:
        return str(e)

def filter_and_sort_channels(m3u_content):
    """فیلتر و مرتب‌سازی کانال‌ها بر اساس اولویت‌های مشخص"""
    if not m3u_content:
        return None
    
    # گروه‌های با اولویت بالا
    ir_keywords = ['ir', 'iran', 'persian', 'فارسی', 'پرس']
    sport_keywords = ['sport', 'spor', 'bein', 'dazn', 'canal+', 'paramount', 'ورزش']
    
    lines = m3u_content.split('\n')
    channels = []
    current_channel = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF'):
            current_channel = {'extinf': line}
            # استخراج group-title
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                current_channel['group'] = group_match.group(1).lower()
            else:
                current_channel['group'] = ''
        elif line.startswith('http'):
            current_channel['url'] = line
            channels.append(current_channel)
            current_channel = {}
    
    # دسته‌بندی کانال‌ها
    ir_channels = []
    sport_channels = []
    other_channels = []
    
    for channel in channels:
        group = channel.get('group', '')
        
        if any(keyword in group for keyword in ir_keywords):
            ir_channels.append(channel)
        elif any(keyword in group for keyword in sport_keywords):
            sport_channels.append(channel)
        else:
            other_channels.append(channel)
    
    # ساخت محتوای جدید با ترتیب مطلوب
    sorted_content = ['#EXTM3U']
    
    # اضافه کردن کانال‌های ایرانی
    if ir_channels:
        sorted_content.append('\n# Iranian Channels\n')
        for channel in ir_channels:
            sorted_content.append(channel['extinf'])
            sorted_content.append(channel['url'])
    
    # اضافه کردن کانال‌های ورزشی
    if sport_channels:
        sorted_content.append('\n# Sports Channels\n')
        for channel in sport_channels:
            sorted_content.append(channel['extinf'])
            sorted_content.append(channel['url'])
    
    # اضافه کردن سایر کانال‌ها
    if other_channels:
        sorted_content.append('\n# Other Channels\n')
        for channel in other_channels:
            sorted_content.append(channel['extinf'])
            sorted_content.append(channel['url'])
    
    return '\n'.join(sorted_content)

def check_and_save_m3u(url, index):
    try:
        os.makedirs("bestm3u", exist_ok=True)
        
        content = download_with_progress(url)
        if isinstance(content, str) and content.startswith('#EXTM3U'):
            # فیلتر و مرتب‌سازی کانال‌ها
            filtered_content = filter_and_sort_channels(content)
            
            if filtered_content:
                filename = f"bestm3u/best{index}.m3u"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(filtered_content)
                
                # بررسی تعداد کانال‌های ایرانی و ورزشی
                ir_count = filtered_content.count('\n# Iranian Channels\n')
                sport_count = filtered_content.count('\n# Sports Channels\n')
                
                print_colored(f"✓ Saved: {filename} (Iranian: {ir_count}, Sports: {sport_count})", "green")
                return True
        
        print_colored(f"✗ Invalid or low-quality: {url}", "red")
        return False
        
    except Exception as e:
        print_colored(f"✗ Error processing {url}: {str(e)}", "red")
        return False

def process_m3u_links(file_path):
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        
        m3u_links = []
        current_comment = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                current_comment = line
            elif line.startswith("http"):
                m3u_links.append((current_comment, line))
                current_comment = ""
        
        if not m3u_links:
            print_colored("No M3U links found in the file.", "yellow")
            return
        
        print_colored(f"Found {len(m3u_links)} M3U links to check...", "cyan")
        
        valid_count = 0
        for idx, (comment, url) in enumerate(m3u_links, 1):
            if comment:
                print_colored(f"\n{comment}", "blue")
            
            if check_and_save_m3u(url, idx):
                valid_count += 1
        
        print_colored(f"\nProcessing complete! {valid_count} valid M3U files saved in 'bestm3u' folder.", "magenta")
        
    except Exception as e:
        print_colored(f"Error processing file: {str(e)}", "red")

if __name__ == "__main__":
    print_colored("=== Advanced M3U Checker & Sorter ===", "blue")
    print_colored("Checking and sorting M3U links from m3ulinks.txt...\n", "cyan")
    
    if not os.path.exists("m3ulinks.txt"):
        print_colored("Error: m3ulinks.txt file not found!", "red")
        sys.exit(1)
    
    process_m3u_links("m3ulinks.txt")
