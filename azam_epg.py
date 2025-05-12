import requests
import json

# Request URL and Headers
url = "https://web1.azamtvltd.co.tz/api/method/azam_tv.azam_tv.api.get_show_by_date_and_country"

headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://www.azamtv.co.tz",
    "Referer": "https://www.azamtv.co.tz/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}

# Your payload (customize date and country if needed)
payload = {
    "date": "2025-04-27",
    "country": "TANZANIA"
}

# Mapping channels to channelId and logo
channel_mapping = {
    "117-Azam Sports 1 HD-TANZANIA": {
        "channelId": "azam_sports_1_hd",
        "urlLogo": "https://raw.githubusercontent.com/sinkalatz/my_tv/refs/heads/main/azam_sports_1_hd.png"
    },
    "188-Azam Sports 2 HD-TANZANIA": {
        "channelId": "azam_sports_2_hd",
        "urlLogo": "https://raw.githubusercontent.com/sinkalatz/my_tv/refs/heads/main/azam_sports_2_hd.png"
    }
}

# Send POST request
response = requests.post(url, headers=headers, json=payload)

# Check if request was successful
if response.status_code == 200:
    result = response.json()
    
    # Get the list of program_details
    program_details = result.get("message", {}).get("program_details", [])

    live_data = {}
    counter = 1

    # Process each program
    for program in program_details:
        if isinstance(program, dict):
            title = program.get("title", "")
            channel_name = program.get("channel_name", "")

            # Filter for "live" in title and specific channels
            if "live" in title.lower() and channel_name in channel_mapping:
                channel_info = channel_mapping[channel_name]

                live_data[str(counter)] = {
                    "title": title,
                    "since": program.get("since", ""),
                    "channel_name": channel_name,
                    "channelId": channel_info["channelId"],
                    "urlLogo": channel_info["urlLogo"]
                }
                counter += 1

    # Wrap inside "live" collection
    output = {"live": live_data}

    # Save to JSON file
    output_filename = "azam_tv_live_shows.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Filtered live shows saved to {output_filename}")

else:
    print(f"❌ Request failed with status: {response.status_code}")
    print(response.text)
