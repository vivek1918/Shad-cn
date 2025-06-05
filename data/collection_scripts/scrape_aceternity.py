import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import os
import time
from urllib.parse import urljoin
from typing import List, Dict, Set

class AceternityComponentScraper:
    def __init__(self):
        self.base_url = "https://ui.aceternity.com"
        self.components_url = "https://ui.aceternity.com/components"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def discover_components(self) -> List[str]:
        """Discover available components using multiple methods"""
        print("Discovering Aceternity components...")
        components = set()

        # Method 1: Try scraping the components page
        try:
            print("Attempting to scrape components page...")
            response = self.session.get(self.components_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try multiple selector patterns
            selectors = [
                'a[href^="/components/"]',  # Links starting with /components/
                'a.group.relative',         # Component card class
                '.grid a',                  # Links in grid layout
                'a[href*="components"]'     # Any link with "components"
            ]

            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href', '')
                    if '/components/' in href and not href.endswith('/components/'):
                        component_name = href.split('/')[-1].split('#')[0].split('?')[0]
                        if component_name and len(component_name) > 2:  # Filter out short names
                            components.add(component_name)
                            print(f"Found via {selector}: {component_name}")

        except Exception as e:
            print(f"Error scraping components page: {str(e)}")

        # Method 2: Test known component URLs
        known_components = [
            'animated-cursor',
            'animated-gradient-text',
            'background-beams',
            'background-dots',
            'border-beam',
            'animated-tooltip',
            'sparkles',
            'text-reveal',
            'animated-shiny-text',
            'glowing-stars',
            'animated-list',
            'animated-grid-pattern'
        ]

        print("\nTesting known components...")
        for component in known_components:
            try:
                test_url = f"{self.base_url}/components/{component}"
                test_response = self.session.head(test_url, timeout=5)
                if test_response.status_code == 200:
                    components.add(component)
                    print(f"✓ Found: {component}")
                else:
                    print(f"✗ Not found: {component}")
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                print(f"✗ Error testing {component}: {str(e)}")

        if not components:
            print("\nWarning: No components discovered, using fallback list")
            components.update(known_components[:5])  # Use first 5 as fallback

        return sorted(list(components))

    def extract_code_content(self, soup: BeautifulSoup) -> str:
        """Extract code content from various possible locations"""
        code_selectors = [
            'pre code',
            'pre',
            '.code-block',
            '[data-language]',
            '.shiki',
            'div[class*="code"]',
            'div[class*="Code"]',
            'div[class*="preview"] + pre',  # Code block after preview
            'div.relative pre'              # Common code block wrapper
        ]

        for selector in code_selectors:
            element = soup.select_one(selector)
            if element:
                code = element.get_text('\n')
                if len(code.strip()) > 50:  # Minimum code length
                    return code.strip()
        return None

    def create_component_template(self, component_name: str, description: str = "") -> str:
        """Create a basic component template when code isn't found"""
        component_class = ''.join(word.capitalize() for word in component_name.split('-'))
        
        return f'''import {{ cn }} from "@/lib/utils";
import {{ ReactNode }} from "react";

interface {component_class}Props {{
  className?: string;
  children?: ReactNode;
}}

export default function {component_class}({{
  className,
  children,
  ...props
}}: {component_class}Props) {{
  return (
    <div
      className={{cn(
        "relative",
        className
      )}}
      {{...props}}
    >
      {{children}}
    </div>
  );
}}'''

    def scrape_component(self, component_name: str) -> Dict:
        """Scrape a single component with improved error handling"""
        print(f"\nScraping {component_name}...")
        component_url = urljoin(self.base_url, f"/components/{component_name}")
        
        try:
            response = self.session.get(component_url, timeout=15)
            response.raise_for_status()
            
            if response.status_code != 200:
                print(f"HTTP {response.status_code} for {component_url}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = component_name.replace('-', ' ').title()
            title_selectors = ['h1', 'h2', '.title', '[data-title]', 'header h1', 'title']
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title_text = element.get_text(strip=True)
                    if title_text and len(title_text) < 100:  # Reasonable length
                        title = title_text
                        break

            # Extract description
            description = f"An interactive {component_name.replace('-', ' ')} component"
            desc_selectors = [
                'meta[name="description"]',
                'p:first-of-type',
                '.prose p',
                '[data-description]',
                'article p',
                'div[class*="description"]'
            ]
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    desc_text = element.get('content', '') if selector.startswith('meta') else element.get_text(strip=True)
                    if desc_text and 20 < len(desc_text) < 200:  # Reasonable length
                        description = desc_text
                        break

            # Extract code
            code = self.extract_code_content(soup)
            if not code:
                print(f"⚠ No code found for {component_name}, using template")
                code = self.create_component_template(component_name, description)

            # Create component data structure
            component_data = {
                "$schema": "https://ui.shadcn.com/schema/registry-item.json",
                "name": component_name,
                "type": "registry:ui",
                "title": title,
                "description": description,
                "files": [{
                    "path": f"registry/aceternity/{component_name}.tsx",
                    "content": code,
                    "type": "registry:ui",
                    "target": f"components/aceternity/{component_name}.tsx"
                }]
            }

            return {
                "prompt": f"Generate a UI component like {title}",
                "completion": json.dumps(component_data, indent=2)
            }

        except Exception as e:
            print(f"Error scraping {component_name}: {str(e)}")
            return None

    def scrape_all_components(self) -> List[Dict]:
        """Scrape all discovered components with progress tracking"""
        components = self.discover_components()
        if not components:
            print("No components to scrape!")
            return []

        data = []
        print(f"\nStarting to scrape {len(components)} components...")
        
        for i, component in enumerate(components, 1):
            print(f"\n[{i}/{len(components)}] Processing {component}")
            try:
                component_data = self.scrape_component(component)
                if component_data:
                    data.append(component_data)
                    print(f"✓ Successfully scraped {component}")
                else:
                    print(f"✗ Failed to scrape {component}")
                
                time.sleep(1)  # Respectful delay
                
            except KeyboardInterrupt:
                print("\nScraping interrupted by user")
                break
            except Exception as e:
                print(f"⚠ Unexpected error with {component}: {str(e)}")
                continue
        
        return data

    def save_data(self, data: List[Dict], filename: str = 'aceternity.json'):
        """Save data with proper directory creation"""
        os.makedirs('data/raw', exist_ok=True)
        filepath = Path('data/raw') / filename
        
        try:
            with filepath.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nData successfully saved to {filepath}")
        except Exception as e:
            print(f"\nError saving data: {str(e)}")

def main():
    scraper = AceternityComponentScraper()
    
    try:
        data = scraper.scrape_all_components()
        
        if data:
            scraper.save_data(data)
            print(f"\n🎉 Successfully scraped {len(data)} components!")
        else:
            print("\n❌ No components were scraped")
            
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")

if __name__ == "__main__":
    main()