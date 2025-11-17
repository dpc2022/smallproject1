#!/usr/bin/env python3
import requests
try:
    import cloudscraper
except ImportError:
    cloudscraper = None
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time

def download_website(url, output_dir='.'):
    """Clone a website with all its assets"""

    # Create a cloudscraper session to bypass bot protection
    if cloudscraper:
        session = cloudscraper.create_scraper()
    else:
        session = requests.Session()

    # Browser-like headers to avoid blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
    }

    print(f"Fetching main page: {url}")

    try:
        # Fetch the main HTML page
        response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()

        print(f"Status code: {response.status_code}")
        print(f"Content length: {len(response.content)} bytes")

        # Save the HTML
        html_content = response.text

        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Save the main HTML file
        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Saved: index.html")

        # Create directories for assets
        os.makedirs(os.path.join(output_dir, 'css'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'js'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'assets'), exist_ok=True)

        # Download CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                download_asset(urljoin(url, link['href']), output_dir, 'css', headers, session)
                time.sleep(0.5)  # Be polite

        # Download JavaScript files
        for script in soup.find_all('script', src=True):
            if script.get('src'):
                download_asset(urljoin(url, script['src']), output_dir, 'js', headers, session)
                time.sleep(0.5)

        # Download images
        for img in soup.find_all('img', src=True):
            if img.get('src'):
                download_asset(urljoin(url, img['src']), output_dir, 'images', headers, session)
                time.sleep(0.5)

        # Download background images from style attributes
        for elem in soup.find_all(style=True):
            style = elem['style']
            if 'url(' in style:
                # Simple extraction of URL from style
                import re
                urls = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', style)
                for asset_url in urls:
                    download_asset(urljoin(url, asset_url), output_dir, 'images', headers, session)
                    time.sleep(0.5)

        print("\nWebsite cloning completed!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error fetching website: {e}")
        return False

def download_asset(asset_url, base_dir, asset_type, headers, session):
    """Download a single asset (CSS, JS, image, etc.)"""
    try:
        print(f"Downloading: {asset_url}")

        # Update headers for asset requests
        asset_headers = headers.copy()
        if asset_type == 'css':
            asset_headers['Accept'] = 'text/css,*/*;q=0.1'
        elif asset_type == 'js':
            asset_headers['Accept'] = '*/*'
        elif asset_type == 'images':
            asset_headers['Accept'] = 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'

        response = session.get(asset_url, headers=asset_headers, timeout=30)
        response.raise_for_status()

        # Get filename from URL
        parsed_url = urlparse(asset_url)
        filename = os.path.basename(parsed_url.path)

        if not filename:
            filename = 'index'

        # Handle query strings in filename
        if '?' in filename:
            filename = filename.split('?')[0]

        # Save the asset
        filepath = os.path.join(base_dir, asset_type, filename)

        # Ensure we don't overwrite files with the same name
        counter = 1
        base_filename, ext = os.path.splitext(filename)
        while os.path.exists(filepath):
            filename = f"{base_filename}_{counter}{ext}"
            filepath = os.path.join(base_dir, asset_type, filename)
            counter += 1

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"  Saved: {asset_type}/{filename} ({len(response.content)} bytes)")
        return True

    except Exception as e:
        print(f"  Failed to download {asset_url}: {e}")
        return False

if __name__ == '__main__':
    url = 'https://draftr-wbs.framer.website/'
    download_website(url, '.')
