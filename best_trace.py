import os
import requests
import time
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

input_folder = 'specialiptvs'
best_trace_channels_folder = 'best_channels'
trace_json_output_file = os.path.join(best_trace_channels_folder, 'trace.json')

# Ensure the output folder exists
os.makedirs(best_trace_channels_folder, exist_ok=True)

def download_stream(url, duration=15):
    """Download a small sample of the stream to verify it works."""
    start_time = time.time()
    total_downloaded = 0
    valid = True

    try:
        response = requests.get(url, stream=True, timeout=duration)
        response.raise_for_status()

        chunk_size = 1024
        for chunk in response.iter_content(chunk_size=chunk_size):
            elapsed_time = time.time() - start_time
            if elapsed_time >= duration:
                break
            if chunk:
                total_downloaded += len(chunk)
                # If after 3 seconds, download speed is too low, mark as invalid
                if elapsed_time > 3 and (total_downloaded / elapsed_time) < 30 * 1024:
                    valid = False
                    break
        return valid

    except Exception:
        return False

def extract_trace_entries(file_path):
    """Extract all entries that contain 'TRACE'."""
    entries = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='iso-8859-1') as f:
            lines = f.readlines()

    for i in range(len(lines) - 1):
        if lines[i].startswith("#EXTINF") and "TRACE" in lines[i].upper():
            url = lines[i + 1].strip()
            if url.startswith("http"):
                entries.append((lines[i], url))
    return entries

def get_channel_filename(channel_name):
    """Generate a safe filename for the channel based on its name."""
    channel_mapping = {
        "trace mziki": "trace_mziki",
        "trace urban": "trace_urban",
        "trace caribbean": "trace_caribbean",
        "trace tropical": "trace_tropical",
        "trace gospel": "trace_gospel",
        "trace africa": "trace_africa",
        "trace latin": "trace_latin",
        "trace naija": "trace_nigeria",
    }

    channel_name_lower = channel_name.lower()

    for key, value in channel_mapping.items():
        if key in channel_name_lower:
            return value + '.m3u'
    
    # Fallback if no match: clean the name
    fallback_name = channel_name_lower.replace(" ", "_").replace("/", "_").replace("\\", "_")
    return fallback_name + '.m3u'

def main():
    print("🔎 Searching for TRACE channels...")
    trace_entries = []

    # Step 1: Scan all files for TRACE entries
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.m3u'):
            full_path = os.path.join(input_folder, file_name)
            trace_entries.extend(extract_trace_entries(full_path))

    print(f"🎯 Found {len(trace_entries)} TRACE entries. Validating streams...")

    # Step 2: Validate entries concurrently
    valid_streams = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_entry = {executor.submit(download_stream, url): (info, url) for info, url in trace_entries}
        for future in tqdm(as_completed(future_to_entry), total=len(future_to_entry), desc="Validating TRACE streams"):
            info, url = future_to_entry[future]
            try:
                if future.result():
                    valid_streams.append((info, url))
            except Exception as e:
                print(f"⚠️ Error checking stream: {e}")

    # Step 3: Save valid streams into files and JSON
    if valid_streams:
        trace_json_data = {}
        channel_streams = {}

        for info, url in valid_streams:
            try:
                channel_name = info.strip().split(",")[1].strip()
            except IndexError:
                continue  # Malformed line, skip

            file_name = get_channel_filename(channel_name)
            channel_id = file_name.replace(".m3u", "")

            # Add to grouped streams for M3U saving
            if file_name not in channel_streams:
                channel_streams[file_name] = []
            channel_streams[file_name].append((info, url))

            # Add to JSON
            if channel_id not in trace_json_data:
                trace_json_data[channel_id] = {
                    "categoryName": "Music",
                    "channelName": channel_name,
                    "channelNumber": channel_id,
                    "groupName": "Trace",
                    "streamUrl": [],
                    "timestamp": int(time.time() * 1000),
                    "urlLogo": f"https://raw.githubusercontent.com/sinkalatz/my_tv/refs/heads/main/{channel_id}.png"
                }
            
            trace_json_data[channel_id]["streamUrl"].append(url)

        # Step 4: Save the .m3u files
        for channel, streams in channel_streams.items():
            m3u_file_path = os.path.join(best_trace_channels_folder, channel)
            with open(m3u_file_path, "w", encoding="utf-8") as f:
                for info, url in streams:
                    f.write(info.strip() + "\n")
                    f.write(url.strip() + "\n")
            print(f"✅ Saved valid streams to {m3u_file_path}")

        # Step 5: Save the JSON output
        with open(trace_json_output_file, "w", encoding="utf-8") as f:
            json.dump({"channels": trace_json_data}, f, indent=4, ensure_ascii=False)
        print(f"✅ Saved TRACE channel data to {trace_json_output_file}")

    else:
        print("\n❌ No valid TRACE streams found.")

if __name__ == "__main__":
    main()
