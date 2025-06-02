import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import os

def scrape_aceternity_components():
    base_url = "https://ui.aceternity.com/components"
    data = []
    
    try:
        response = requests.get(base_url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all component links - adjust selector as needed
        components = soup.select('a[href^="/components/"]')
        
        for comp in components[:3]:  # Just get first 3 for demo
            comp_name = comp.text.strip()
            comp_url = f"https://ui.aceternity.com{comp['href']}"
            
            try:
                comp_response = requests.get(comp_url)
                comp_soup = BeautifulSoup(comp_response.text, 'html.parser')
                
                # Extract details - adjust selectors
                title = comp_name
                description = comp_soup.find('p').text if comp_soup.find('p') else f"{comp_name} component"
                code = comp_soup.find('pre').text if comp_soup.find('pre') else f"// {comp_name} code placeholder"
                
                component_data = {
                    "$schema": "https://ui.shadcn.com/schema/registry-item.json",
                    "name": comp_name.lower().replace(' ', '-'),
                    "type": "registry:ui",
                    "title": title,
                    "description": description,
                    "files": [{
                        "path": f"registry/aceternity/{comp_name.lower()}.tsx",
                        "content": code,
                        "type": "registry:ui",
                        "target": f"components/aceternity/{comp_name.lower()}.tsx"
                    }]
                }
                
                data.append({
                    "prompt": f"Generate a UI component like {title}",
                    "completion": json.dumps(component_data, indent=2)
                })
                
            except Exception as e:
                print(f"Error scraping {comp_name}: {str(e)}")
                continue
    
    except Exception as e:
        print(f"Error accessing Aceternity: {str(e)}")
    
    os.makedirs('data/raw', exist_ok=True)
    Path("data/raw/aceternity.json").write_text(json.dumps(data, indent=2))
    return data

if __name__ == "__main__":
    scrape_aceternity_components()