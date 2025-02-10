import json
import time
import requests
from eth_account import Account
from eth_account.messages import encode_defunct
import secrets
from web3.auto import w3
import random
import sys
from datetime import datetime
from colorama import init, Fore, Style

init()

def print_banner():
    banner = f"""
{Fore.CYAN}
   ██████╗██╗   ██╗██╗  ████████╗   ██╗    ██╗ ██████╗ ██████╗ ██╗     ██████╗ 
  ██╔════╝██║   ██║██║  ╚══██╔══╝   ██║    ██║██╔═══██╗██╔══██╗██║     ██╔══██╗
  ██║     ██║   ██║██║     ██║      ██║ █╗ ██║██║   ██║██████╔╝██║     ██║  ██║
  ██║     ██║   ██║██║     ██║      ██║███╗██║██║   ██║██╔══██╗██║     ██║  ██║
  ╚██████╗╚██████╔╝███████╗██║      ╚███╔███╔╝╚██████╔╝██║  ██║███████╗██████╔╝
   ╚═════╝ ╚═════╝ ╚══════╝╚═╝       ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═════╝ 
                                                                       
{Fore.GREEN}╔══════════════════════════════════════════════════════════════════╗
║          Auto Referral Generator - Created by IM-Hanzou          ║
║                 https://github.com/IM-Hanzou                     ║
╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def load_proxies(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def save_wallet(private_key, address):
    with open('wallets.txt', 'a') as f:
        f.write(f"{private_key}:{address}\n")

def get_random_proxy(proxies):
    return random.choice(proxies)

def get_ip_info(proxy):
    try:
        response = requests.get('http://ip-api.com/json', 
                              proxies={'http': proxy, 'https': proxy}, 
                              timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"{data.get('query', 'Unknown')} ({data.get('country', 'Unknown')})"
    except:
        return "IP lookup failed"
    
def create_wallet():
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    acct = Account.from_key(private_key)
    return private_key, acct.address

def log_message(message, status="info"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status == "success":
        print(f"{Fore.GREEN}[{timestamp}] ✔ {message}{Style.RESET_ALL}")
    elif status == "error":
        print(f"{Fore.RED}[{timestamp}] ✖ {message}{Style.RESET_ALL}")
    elif status == "warning":
        print(f"{Fore.YELLOW}[{timestamp}] ⚠ {message}{Style.RESET_ALL}")
    else:
        print(f"{Fore.BLUE}[{timestamp}] ℹ {message}{Style.RESET_ALL}")

def get_challenge(address, proxy):
    url = "https://cults-apis-1181.ippcoin.com/auth/challenge"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://cult.world',
        'referer': 'https://cult.world/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0'
    }
    data = {"wallet_address": address}
    
    try:
        response = requests.post(url, headers=headers, json=data, proxies={'http': proxy, 'https': proxy})
        if response.status_code == 200:
            return response.json()['data']['challenge']
        return None
    except Exception as e:
        log_message(f"Error getting challenge: {e}", "error")
        return None

def sign_message(private_key, challenge):
    message = encode_defunct(text=challenge)
    signed_message = w3.eth.account.sign_message(message, private_key=private_key)
    return signed_message.signature.hex()

def login(address, challenge, signature, proxy, ref_code):
    url = "https://cults-apis-1181.ippcoin.com/auth/login"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://cult.world',
        'referer': 'https://cult.world/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0'
    }
    data = {
        "wallet_address": address,
        "challenge": challenge,
        "response": signature,
        "referral_code": ref_code
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, proxies={'http': proxy, 'https': proxy})
        return response.json()
    except Exception as e:
        log_message(f"Error logging in: {e}", "error")
        return None

def main():
    print_banner()
    
    ref_code = input(f"{Fore.CYAN}Please enter your referral code: {Style.RESET_ALL}").strip()
    
    if not ref_code:
        log_message("No referral code provided. Exiting...", "error")
        return

    proxies = load_proxies('proxies.txt')
    if not proxies:
        log_message("No proxies found in proxies.txt", "error")
        return

    log_message(f"Using referral code: {ref_code}", "info")
    log_message("Starting wallet generation and registration process...")
    log_message("Press Ctrl+C to stop", "warning")
    
    wallet_count = 0
    
    try:
        while True:
            wallet_count += 1
            proxy = get_random_proxy(proxies)
            ip_info = get_ip_info(proxy)
            private_key, address = create_wallet()
            
            log_message(f"Wallet #{wallet_count}")
            log_message(f"Address: {address}")
            log_message(f"IP: {ip_info}")
            
            challenge = get_challenge(address, proxy)
            if not challenge:
                log_message("Failed to get challenge, skipping wallet", "error")
                continue
                
            signature = sign_message(private_key, challenge)
            login_result = login(address, challenge, signature, proxy, ref_code)
            
            if login_result and login_result.get('status') == 200:
                log_message("Successfully registered wallet!", "success")
                save_wallet(private_key, address)
                log_message(f"Referral code: {login_result['data'].get('referral_code', 'N/A')}", "success")
                log_message("=" * 50)
            else:
                log_message("Failed to register wallet", "error")
                log_message("=" * 50)
            
    except KeyboardInterrupt:
        log_message("\nStopping wallet generation...", "warning")
        log_message(f"Total wallets processed: {wallet_count}", "info")
        sys.exit(0)
    except Exception as e:
        log_message(f"An error occurred: {e}", "error")

if __name__ == "__main__":
    main()
