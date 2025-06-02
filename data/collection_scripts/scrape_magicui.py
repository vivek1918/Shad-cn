import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import os
import time

def scrape_magicui_components():
    base_url = "https://magicui.design/components"
    components = ["marquee", "card", "button"]  # Example components
    
    data = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for component in components:
        try:
            print(f"Scraping {component}...")
            url = f"{base_url}/{component}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Check for HTTP errors
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # More flexible element finding
            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else component.title()
            
            # Try multiple ways to find description
            description = ""
            for selector in ['.prose', '.description', 'p']:
                if soup.select_one(selector):
                    description = soup.select_one(selector).get_text(strip=True)
                    break
            
            # Try to find code blocks
            code = ""
            for code_selector in ['pre', 'code', '.code-block']:
                if soup.select_one(code_selector):
                    code = soup.select_one(code_selector).get_text(strip=True)
                    break
            
            if not code:
                print(f"Warning: No code found for {component}")
                continue

            component_data = {
                "$schema": "https://ui.shadcn.com/schema/registry-item.json",
                "name": component,
                "type": "registry:ui",
                "title": title,
                "description": description or f"An interactive {component} component",
                "files": [{
                    "path": f"registry/magicui/{component}.tsx",
                    "content": code,
                    "type": "registry:ui",
                    "target": f"components/magicui/{component}.tsx"
                }]
            }
            
            data.append({
                "prompt": f"Generate a UI component like {title}",
                "completion": json.dumps(component_data, indent=2)
            })
            
            # Be polite with delays
            time.sleep(2)
            
        except Exception as e:
            print(f"Error scraping {component}: {str(e)}")
            continue
    
    # Save results
    os.makedirs('data/raw', exist_ok=True)
    with open('data/raw/magicui.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Successfully scraped {len(data)} components")
    return data

if __name__ == "__main__":
    scrape_magicui_components()