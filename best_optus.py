import os
import requests
import time
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

input_folder = 'specialiptvs'
best_optus_channels_folder = 'best_channels'
optus_json_output_file = os.path.join(best_optus_channels_folder, 'optus.json')

# Ensure the best_channels folder exists
os.makedirs(best_optus_channels_folder, exist_ok=True)

def download_stream(url, duration=15):
    """Download test to see if the stream is active (short duration)"""
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
                # Check download speed after 3 seconds
                if elapsed_time > 3 and (total_downloaded / elapsed_time) < 30 * 1024:
                    valid = False
                    break
        return valid

    except Exception:
        return False

def extract_optus_entries(file_path):
    """Extract OPTUS entries like Optus 1, Optus 2, etc."""
    entries = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='iso-8859-1') as f:
            lines = f.readlines()

    for i in range(len(lines) - 1):
        # Filter for lines containing 'Optus' followed by a number (e.g., 'Optus 1', 'Optus 2', etc.)
        if lines[i].startswith("#EXTINF") and "OPTUS" in lines[i].upper() and any(f"optus {n}" in lines[i].lower() for n in range(1, 13)):
            url = lines[i + 1].strip()
            if url.startswith("http"):
                entries.append((lines[i], url))
    return entries

def get_channel_filename(channel_name):
    """Generate a filename for the channel based on its name."""
    channel_mapping = {
        "optus 1 hd": "optus_1_hd",
        "optus 2 hd": "optus_2_hd",
        "optus 3": "optus_3_hd",
        "optus 4": "optus_4_hd",
        "optus 5": "optus_5_hd",
        "optus 6": "optus_6_hd",
        "optus 7": "optus_7_hd",
        "optus 8": "optus_8_hd",
        "optus 9": "optus_9_hd",
        "optus 10": "optus_10_hd",
        "optus 11": "optus_11_hd",
        "optus 12": "optus_12_hd",
    }
    
    for key, value in channel_mapping.items():
        if key in channel_name.lower():
            return value + '.m3u'
    return None

def main():
    print("Searching for OPTUS channels...")
    optus_entries = []

    # Step 1: Scan all files for OPTUS entries (Optus 1, Optus 2, etc.)
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.m3u'):
            full_path = os.path.join(input_folder, file_name)
            optus_entries.extend(extract_optus_entries(full_path))

    print(f"Found {len(optus_entries)} OPTUS entries. Checking which ones are valid...")

    # Step 2: Validate entries concurrently
    valid_streams = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_entry = {executor.submit(download_stream, url): (info, url) for info, url in optus_entries}
        for future in tqdm(as_completed(future_to_entry), total=len(future_to_entry), desc="Validating OPTUS streams"):
            info, url = future_to_entry[future]
            try:
                if future.result():
                    valid_streams.append((info, url))
            except Exception as e:
                print(f"Error checking stream: {e}")

    # Step 3: Save valid streams to the appropriate .m3u files and JSON
    if valid_streams:
        optus_json_data = {}

        # Dictionary to store the streams for each channel
        channel_streams = {}

        for info, url in valid_streams:
            channel_name = info.strip().split(",")[1].strip()
            file_name = get_channel_filename(channel_name)

            if file_name:
                # If channel doesn't have an entry in channel_streams, create one
                if file_name not in channel_streams:
                    channel_streams[file_name] = []

                channel_streams[file_name].append(url)

                # Get the channel ID (e.g., optus_1_hd)
                channel_id = file_name.replace(".m3u", "")

                # Add to the JSON data with required fields
                optus_json_data[channel_id] = {
                    "categoryName": "Sports",
                    "channelName": channel_name,
                    "channelNumber": channel_id,
                    "groupName": "Optus",
                    "streamUrl": channel_streams[file_name],
                    "timestamp": int(time.time() * 1000),  # Current timestamp in milliseconds
                    "urlLogo": f"https://raw.githubusercontent.com/sinkalatz/my_tv/refs/heads/main/{channel_id}.png"  # Dynamic logo URL based on channel ID
                }

        # Step 4: Save the valid streams to the .m3u files in the best_channels folder
        for channel, streams in channel_streams.items():
            m3u_file_path = os.path.join(best_optus_channels_folder, channel)
            with open(m3u_file_path, "w", encoding="utf-8") as f:
                for info, url in valid_streams:
                    if get_channel_filename(info.strip().split(",")[1].strip()) == channel:
                        f.write(info.strip() + "\n")
                        f.write(url.strip() + "\n")
            print(f"✅ Saved valid streams to {m3u_file_path}")

        # Step 5: Save the data to a JSON file
        with open(optus_json_output_file, "w", encoding="utf-8") as f:
            json.dump({"channels": optus_json_data}, f, indent=4, ensure_ascii=False)
        print(f"✅ Saved OPTUS channel data to {optus_json_output_file}")
    else:
        print("\n❌ No valid OPTUS streams found.")

if __name__ == "__main__":
    main()
