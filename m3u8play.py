import os
import time

# Path to your folder containing .ts files
ts_folder_path = "/Users/amanisinkala/Downloads/m3u-main"

# Output m3u8 playlist file
playlist_file = "playlist.m3u8"

# Function to generate the playlist
def generate_playlist():
    # Open the .m3u8 file to write
    with open(playlist_file, 'w') as f:
        # Write m3u8 header
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        f.write("#EXT-X-TARGETDURATION:10\n")
        f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
        
        # Iterate over each .ts file in the folder and write it to the playlist
        ts_files = sorted([f for f in os.listdir(ts_folder_path) if f.endswith('.ts')])
        for ts_file in ts_files:
            ts_file_path = os.path.join(ts_folder_path, ts_file)
            f.write(f"#EXTINF:10,\n{ts_file_path}\n")
        
        # End the playlist
        f.write("#EXT-X-ENDLIST\n")

    print(f"Generated playlist: {playlist_file}")

# Function to append new .ts files to the playlist
def append_to_playlist():
    existing_files = set()  # Keep track of already included files in the playlist
    while True:
        # Get the current set of .ts files in the directory
        current_files = set(f for f in os.listdir(ts_folder_path) if f.endswith('.ts'))

        # Check for any new files that haven't been added to the playlist yet
        new_files = current_files - existing_files

        if new_files:
            # Open the playlist in append mode
            with open(playlist_file, 'a') as f:
                for ts_file in sorted(new_files):
                    ts_file_path = os.path.join(ts_folder_path, ts_file)
                    f.write(f"#EXTINF:10,\n{ts_file_path}\n")
                    print(f"Appended: {ts_file_path}")

            # Update the set of existing files
            existing_files.update(new_files)

        # Wait for some time before checking again
        time.sleep(10)

# Initialize the playlist
generate_playlist()

# Start appending new files to the playlist
append_to_playlist()
