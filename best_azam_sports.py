import os
import requests
import time
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

input_folder = 'specialiptvs'
best_azam_channels_folder = 'best_channels'
azam_sport_json_output_file = os.path.join(best_azam_channels_folder, 'azam_sport.json')

# Ensure the best_channels folder exists
os.makedirs(best_azam_channels_folder, exist_ok=True)

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

def extract_azam_sport_entries(file_path):
    """Extract AZAM SPORT-like entries from an .m3u file"""
    entries = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='iso-8859-1') as f:
            lines = f.readlines()

    for i in range(len(lines) - 1):
        if lines[i].startswith("#EXTINF") and "AZAM SPORT" in lines[i].upper():
            url = lines[i + 1].strip()
            if url.startswith("http"):
                entries.append((lines[i], url))
    return entries

def get_channel_filename(channel_name):
    """Generate a filename for the channel based on its name."""
    channel_mapping = {
        "azam sport 1": "azam_sports_1_hd",
        "azam sports 1": "azam_sports_1_hd",
        "azam sport 2": "azam_sports_2_hd",
        "azam sports 2": "azam_sports_2_hd",
        "azam sport 3": "azam_sports_3_hd",
        "azam sports 3": "azam_sports_3_hd",
        "azam sport 4": "azam_sports_4_hd",
        "azam sports 4": "azam_sports_4_hd",
        "azam sport 5": "azam_sports_5_hd",
        "azam sports 5": "azam_sports_5_hd",
        "azam sport 6": "azam_sports_6_hd",
        "azam sports 6": "azam_sports_6_hd",
        "azam sport 7": "azam_sports_7_hd",
        "azam sports 7": "azam_sports_7_hd",
        "azam sport 8": "azam_sports_8_hd",
        "azam sports 8": "azam_sports_8_hd",
        "azam sport 9": "azam_sports_9_hd",
        "azam sports 9": "azam_sports_9_hd",
        "azam sport 10": "azam_sports_10_hd",
        "azam sports 10": "azam_sports_10_hd",
        "azam sport 11": "azam_sports_11_hd",
        "azam sports 11": "azam_sports_11_hd",
        "azam sport 12": "azam_sports_12_hd",
        "azam sports 12": "azam_sports_12_hd",
    }
    
    for key, value in channel_mapping.items():
        if key in channel_name.lower():
            return value + '.m3u'
    return None

def main():
    print("Searching for AZAM SPORT streams...")
    azam_sport_entries = []

    # Step 1: Scan all files for AZAM_SPORT entries
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.m3u'):
            full_path = os.path.join(input_folder, file_name)
            azam_sport_entries.extend(extract_azam_sport_entries(full_path))

    print(f"Found {len(azam_sport_entries)} AZAM SPORT entries. Checking which ones are valid...")

    # Step 2: Validate entries concurrently
    valid_streams = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_entry = {executor.submit(download_stream, url): (info, url) for info, url in azam_sport_entries}
        for future in tqdm(as_completed(future_to_entry), total=len(future_to_entry), desc="Validating AZAM SPORT streams"):
            info, url = future_to_entry[future]
            try:
                if future.result():
                    valid_streams.append((info, url))
            except Exception as e:
                print(f"Error checking stream: {e}")

    # Step 3: Save valid streams to the appropriate .m3u files and JSON
    if valid_streams:
        azam_sport_json_data = {}

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

                # Get the channel ID (e.g., azam_sports_1_hd)
                channel_id = file_name.replace(".m3u", "")

                # Add to the JSON data with required fields
                azam_sport_json_data[channel_id] = {
                    "categoryName": "Sports",
                    "channelName": channel_name,
                    "groupName": "Azam",
                    "streamUrl": channel_streams[file_name],
                    "timestamp": int(time.time() * 1000),  # Current timestamp in milliseconds
                    "urlLogo": f"https://raw.githubusercontent.com/sinkalatz/my_tv/refs/heads/main/{channel_id}.png"  # Dynamic logo URL based on channel ID
                }

        # Step 4: Save the valid streams to the .m3u files in the best_channels folder
        for channel, streams in channel_streams.items():
            m3u_file_path = os.path.join(best_azam_channels_folder, channel)
            with open(m3u_file_path, "w", encoding="utf-8") as f:
                for info, url in valid_streams:
                    if get_channel_filename(info.strip().split(",")[1].strip()) == channel:
                        f.write(info.strip() + "\n")
                        f.write(url.strip() + "\n")
            print(f"✅ Saved valid streams to {m3u_file_path}")

        # Step 5: Save the data to a JSON file
        with open(azam_sport_json_output_file, "w", encoding="utf-8") as f:
            json.dump({"channels": azam_sport_json_data}, f, indent=4, ensure_ascii=False)
        print(f"✅ Saved AZAM SPORT channel data to {azam_sport_json_output_file}")
    else:
        print("\n❌ No valid AZAM SPORT streams found.")

if __name__ == "__main__":
    main()