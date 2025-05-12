import requests
import time

# Base URL where the m3u8 files are hosted
base_url = 'http://185.243.7.47'

# URL to fetch the m3u8 playlist
m3u8_url = 'http://epg.protv.cc:80/play/live.php?mac=00:1A:79:C8:04:A0&stream=1118130&extension=m3u8&play_token=ms5kvKr28O'

# Set headers to simulate browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    'Referer': 'http://zonalresults.totalh.net/',
    'Origin': 'http://zonalresults.totalh.net',
}

# Function to fetch and update the playlist
def update_playlist():
    # Send GET request to fetch the M3U8 content
    response = requests.get(m3u8_url, headers=headers)

    if response.status_code == 200:
        print("M3U8 playlist loaded successfully.")

        # Split the content by lines
        m3u8_content = response.text.splitlines()

        # Open the azam.m3u8 file in append mode to keep adding new segments
        with open("azam.m3u8", "a") as f:
            # Iterate over each line in the M3U8 content
            for line in m3u8_content:
                # If the line contains a segment path (i.e., .ts file)
                if line and line.startswith('/hls/'):
                    segment_url = base_url + line
                    f.write(f"#EXTINF:10,\n{segment_url}\n")  # Write segment URL to the m3u8 file
                    print(f"Added Segment URL: {segment_url}")
                    
                    # Optional: Download the segment
                    segment_response = requests.get(segment_url)
                    if segment_response.status_code == 200:
                        with open(f"segment_{line.split('/')[-1]}", 'wb') as seg_file:
                            seg_file.write(segment_response.content)
                            print(f"Downloaded: {line.split('/')[-1]}")
                    else:
                        print(f"Failed to download segment: {segment_url}")
    else:
        print(f"Failed to load M3U8 playlist. Status Code: {response.status_code}")

# Set the interval time (e.g., 5 seconds = 5)
interval = 5  # seconds

while True:
    update_playlist()  # Update the playlist and download new segments
    time.sleep(interval)  # Wait for the specified interval before checking again
