import requests
import json
import time
import re
import os
import shutil
from typing import Dict, Tuple, Optional, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

def print_colored(text: str, color: str) -> None:
    """
    Print colored text to the console.
    Args:
        text: The text to print
        color: The color to use (green, red, yellow, cyan, magenta, white)
    """
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "magenta": "\033[95m",
        "white": "\033[97m"
    }
    print(f"{colors.get(color.lower(), '')}{text}\033[0m")

def get_base_url_and_mac_from_file(file_path: str) -> List[Tuple[str, str]]:
    """
    Read base URLs and MAC addresses from a file.
    Args:
        file_path: Path to the input file
    Returns:
        List of (base_url, mac) tuples
    """
    base_urls_and_macs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('$')
                    if len(parts) == 2:
                        base_url, mac = parts
                        base_urls_and_macs.append((base_url.strip(), mac.strip().upper()))
    except Exception as e:
        print_colored(f"Error reading file: {e}", "red")
    return base_urls_and_macs

def get_token(session: requests.Session, base_url: str) -> Optional[str]:
    """
    Get authentication token from the portal.
    Args:
        session: Requests session
        base_url: Portal base URL
    Returns:
        Token string if successful, None otherwise
    """
    url = f"{base_url}/portal.php?action=handshake&type=stb&token=&JsHttpRequest=1-xml"
    try:
        res = session.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if res.status_code == 200:
            return res.json().get('js', {}).get('token')
    except Exception:
        return None

def get_channel_list(session: requests.Session, base_url: str, token: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get the channel list from the portal.
    Args:
        session: Requests session
        base_url: Portal base URL
        token: Authentication token
    Returns:
        List of channels if successful, None otherwise
    """
    endpoints = [
        f"{base_url}/portal.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml",
        f"{base_url}/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml",
        f"{base_url}/stalker_portal/server/load.php?type=itv&action=get_all_channels&JsHttpRequest=1-xml"
    ]
    
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}
    
    for url in endpoints:
        try:
            res = session.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json().get('js', {})
                if 'data' in data:
                    return data['data']
        except Exception:
            continue
    
    return None

def get_genre_list(session: requests.Session, base_url: str, token: str) -> Dict[int, str]:
    """
    Get the genre/group list from the portal.
    Args:
        session: Requests session
        base_url: Portal base URL
        token: Authentication token
    Returns:
        Dictionary of {group_id: group_name}
    """
    endpoints = [
        f"{base_url}/server/load.php?type=itv&action=get_genres&JsHttpRequest=1-xml",
        f"{base_url}/stalker_portal/server/load.php?type=itv&action=get_genres&JsHttpRequest=1-xml"
    ]
    
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}
    
    for url in endpoints:
        try:
            res = session.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json().get('js', [])
                return {group['id']: group['title'] for group in data}
        except Exception:
            continue
    
    return {}

def sort_groups(group_names: List[str]) -> List[str]:
    """
    Sort groups based on specific priority rules:
    1. First priority (exact order):
       - Groups containing 'iran' (case insensitive)
       - Then groups containing 'persian' 
       - Then groups containing 'ir' (but not as part of 'iraq' or 'ireland')
    2. Second priority (exact order):
       - Groups containing 'bein'
       - Then 'sport'
       - Then 'spor'
       - Then 'canal+'
       - Then 'dazn'
       - Then 'paramount'
    3. All other groups in their original order
    
    Args:
        group_names: List of group names to sort
    Returns:
        Sorted list of group names
    """
    lower_groups = [g.lower() for g in group_names]
    priority1_groups = []
    priority2_groups = []
    
    # Priority 1: iran -> persian -> ir (excluding iraq and ireland)
    for i, group in enumerate(lower_groups):
        if 'iran' in group:
            priority1_groups.append(group_names[i])
    
    for i, group in enumerate(lower_groups):
        if ('persian' in group and 
            group_names[i] not in priority1_groups):
            priority1_groups.append(group_names[i])
    
    for i, group in enumerate(lower_groups):
        if ('ir' in group and 
            'iraq' not in group and 
            'ireland' not in group and 
            group_names[i] not in priority1_groups):
            priority1_groups.append(group_names[i])
    
    # Priority 2: bein -> sport -> spor -> canal+ -> dazn -> paramount
    for i, group in enumerate(lower_groups):
        if ('bein' in group and 
            group_names[i] not in priority1_groups):
            priority2_groups.append(group_names[i])
    
    for i, group in enumerate(lower_groups):
        if ('sport' in group and 
            group_names[i] not in priority1_groups and 
            group_names[i] not in priority2_groups):
            priority2_groups.append(group_names[i])
    
    for i, group in enumerate(lower_groups):
        if ('spor' in group and 
            group_names[i] not in priority1_groups and 
            group_names[i] not in priority2_groups):
            priority2_groups.append(group_names[i])
    
    for i, group in enumerate(lower_groups):
        if ('canal+' in group and 
            group_names[i] not in priority1_groups and 
            group_names[i] not in priority2_groups):
            priority2_groups.append(group_names[i])
    
    for i, group in enumerate(lower_groups):
        if ('dazn' in group and 
            group_names[i] not in priority1_groups and 
            group_names[i] not in priority2_groups):
            priority2_groups.append(group_names[i])
    
    for i, group in enumerate(lower_groups):
        if ('paramount' in group and 
            group_names[i] not in priority1_groups and 
            group_names[i] not in priority2_groups):
            priority2_groups.append(group_names[i])
    
    # Other groups maintain original order
    other_groups = [
        g for g in group_names 
        if g not in priority1_groups and g not in priority2_groups
    ]
    
    return priority1_groups + priority2_groups + other_groups

def save_channel_list(base_url: str, mac: str, channels_data: List[Dict[str, Any]], 
                     group_info: Dict[int, str], mac_counter: int) -> None:
    """
    Save the channel list to an M3U file with proper grouping.
    Args:
        base_url: Portal base URL
        mac: MAC address
        channels_data: List of channel data
        group_info: Dictionary of group information
        mac_counter: Counter for file naming
    """
    output_folder = "specialiptvs"
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        with open(f"{output_folder}/MAC{mac_counter}.m3u", 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            
            # Get all unique groups and sort them
            all_groups = set()
            for channel in channels_data:
                group_id = channel.get('tv_genre_id', -1)
                group_name = group_info.get(group_id, "General")
                all_groups.add(group_name)
            
            sorted_groups = sort_groups(list(all_groups))
            
            # Write channels in sorted group order
            for group in sorted_groups:
                for channel in channels_data:
                    group_id = channel.get('tv_genre_id', -1)
                    current_group = group_info.get(group_id, "General")
                    
                    if current_group == group:
                        name = channel.get('name', 'Unnamed Channel')
                        logo = channel.get('logo', '')
                        cmd = channel.get('cmd', '')
                        
                        if 'cmds' in channel and len(channel['cmds']) > 0:
                            cmd = channel['cmds'][0]['url'].replace('ffmpeg ', '')
                        
                        if "localhost" in cmd:
                            if match := re.search(r'/ch/(\d+)_', cmd):
                                cmd = f"{base_url}/play/live.php?mac={mac}&stream={match.group(1)}&extension=ts"
                        
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{current_group}",{name}\n{cmd}\n')
    except Exception as e:
        print_colored(f"Error saving channel list: {e}", "red")

def process_mac(base_url: str, mac: str, mac_counter: int) -> None:
    """
    Process a single MAC address to extract its channel list.
    Args:
        base_url: Portal base URL
        mac: MAC address
        mac_counter: Counter for file naming
    """
    session = requests.Session()
    session.cookies.update({'mac': mac})
    
    print_colored(f"\nProcessing MAC: {mac}", "cyan")
    
    # Get authentication token
    token = get_token(session, base_url)
    if not token:
        print_colored("Failed to get token", "red")
        return
    
    # Get channel list
    channels = get_channel_list(session, base_url, token)
    if not channels:
        print_colored("Failed to get channel list", "red")
        return
    
    # Get genre/group list
    genres = get_genre_list(session, base_url, token)
    
    # Save to M3U file
    save_channel_list(base_url, mac, channels, genres, mac_counter)
    print_colored(f"Successfully saved MAC{mac_counter}.m3u", "green")
    time.sleep(0.5)  # Rate limiting

def main() -> None:
    """
    Main function to process all MAC addresses from the input file.
    """
    try:
        print_colored("Starting IPTV channel list extraction...", "magenta")
        
        # Read input file
        base_urls_and_macs = get_base_url_and_mac_from_file("fixmac.txt")
        if not base_urls_and_macs:
            print_colored("No valid MAC addresses found in input file", "red")
            return
        
        # Prepare output directory
        shutil.rmtree("specialiptvs", ignore_errors=True)
        os.makedirs("specialiptvs", exist_ok=True)
        
        # Process all MACs in parallel (limited to 300 concurrent)
        with ThreadPoolExecutor(max_workers=300) as executor:
            futures = [
                executor.submit(process_mac, base_url, mac, idx+1)
                for idx, (base_url, mac) in enumerate(base_urls_and_macs)
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print_colored(f"Error processing MAC: {str(e)}", "red")
        
        print_colored("\nAll MAC addresses processed successfully", "green")
    
    except KeyboardInterrupt:
        print_colored("\nProcess interrupted by user", "yellow")
    except Exception as e:
        print_colored(f"Fatal error: {str(e)}", "red")

if __name__ == "__main__":
    main()
