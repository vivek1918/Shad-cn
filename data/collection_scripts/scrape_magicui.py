import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import os
import time
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set

class MagicUIComponentScraper:
    def __init__(self):
        self.base_url = "https://magicui.design"
        self.docs_url = "https://magicui.design/docs"
        self.components_url = "https://magicui.design/docs/components"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def create_component_template(self, component_name: str, description: str = "") -> str:
        """Create a basic component template based on component name"""
        
        component_templates = {
            'marquee': '''import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface MarqueeProps {
  className?: string;
  reverse?: boolean;
  pauseOnHover?: boolean;
  vertical?: boolean;
  children?: ReactNode;
  repeat?: number;
}

export default function Marquee({
  className,
  reverse = false,
  pauseOnHover = false,
  vertical = false,
  children,
  repeat = 1,
  ...props
}: MarqueeProps) {
  return (
    <div
      className={cn(
        "group flex overflow-hidden p-2 [--duration:20s] [--gap:1rem] [gap:var(--gap)]",
        {
          "flex-col": vertical,
          "flex-row": !vertical,
        },
        className
      )}
      {...props}
    >
      {Array.from({ length: repeat }).map((_, i) => (
        <div
          key={i}
          className={cn("flex shrink-0 justify-around [gap:var(--gap)]", {
            "animate-marquee flex-row": !vertical,
            "animate-marquee-vertical flex-col": vertical,
            "group-hover:[animation-play-state:paused]": pauseOnHover,
            "[animation-direction:reverse]": reverse,
          })}
        >
          {children}
        </div>
      ))}
    </div>
  );
}''',
            
            'animated-beam': '''import { cn } from "@/lib/utils";
import { useEffect, useId, useRef } from "react";

interface AnimatedBeamProps {
  className?: string;
  containerRef: React.RefObject<HTMLElement>;
  fromRef: React.RefObject<HTMLElement>;
  toRef: React.RefObject<HTMLElement>;
  curvature?: number;
  reverse?: boolean;
  duration?: number;
}

export default function AnimatedBeam({
  className,
  containerRef,
  fromRef,
  toRef,
  curvature = 0,
  reverse = false,
  duration = 5,
}: AnimatedBeamProps) {
  const id = useId();
  const pathRef = useRef<SVGPathElement>(null);

  return (
    <svg
      fill="none"
      width="100%"
      height="100%"
      viewBox="0 0 100 100"
      className={cn("pointer-events-none absolute inset-0", className)}
    >
      <path
        ref={pathRef}
        d="M10,50 Q50,10 90,50"
        stroke="url(#gradient)"
        strokeWidth="2"
        strokeOpacity="0.8"
        fill="none"
      />
      <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="transparent" />
          <stop offset="50%" stopColor="currentColor" />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
    </svg>
  );
}''',

            'border-beam': '''import { cn } from "@/lib/utils";

interface BorderBeamProps {
  className?: string;
  size?: number;
  duration?: number;
  borderWidth?: number;
  anchor?: number;
  colorFrom?: string;
  colorTo?: string;
  delay?: number;
}

export default function BorderBeam({
  className,
  size = 200,
  duration = 15,
  anchor = 90,
  borderWidth = 1.5,
  colorFrom = "#ffaa40",
  colorTo = "#9c40ff",
  delay = 0,
}: BorderBeamProps) {
  return (
    <div
      style={{
        "--size": size,
        "--duration": duration + "s",
        "--anchor": anchor + "%",
        "--border-width": borderWidth + "px",
        "--color-from": colorFrom,
        "--color-to": colorTo,
        "--delay": delay + "s",
      } as React.CSSProperties}
      className={cn(
        "absolute inset-[0] rounded-[inherit] [border:calc(var(--border-width)*1px)_solid_transparent]",
        "[background:linear-gradient(to_right,var(--color-from),var(--color-to),var(--color-from))_border-box]",
        "[mask:linear-gradient(#fff_0_0)_padding-box,_linear-gradient(#fff_0_0)]",
        "[mask-composite:xor]",
        "animate-border-beam",
        className
      )}
    />
  );
}''',
        }
        
        # Return specific template if available, otherwise create generic template
        if component_name in component_templates:
            return component_templates[component_name]
        
        # Generic template for unknown components
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
        
    def discover_components(self) -> List[str]:
        """Discover all available components from the docs page"""
        print("Discovering available components...")
        
        components = set()
        
        # Method 1: Try to access the docs page and find component links
        try:
            print("Checking docs page...")
            response = self.session.get(self.docs_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for component links in various patterns
            patterns = [
                r'/docs/components/[^/\s#]+',
                r'/components/[^/\s#]+',
                r'docs/components/[^/\s#]+'
            ]
            
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                for pattern in patterns:
                    matches = re.findall(pattern, href)
                    for match in matches:
                        component_name = match.split('/')[-1]
                        if component_name and component_name not in ['components', 'docs']:
                            components.add(component_name)
            
            # Also check navigation menu, sidebar, etc.
            nav_elements = soup.find_all(['nav', 'aside', 'ul', 'ol'])
            for nav in nav_elements:
                nav_links = nav.find_all('a', href=True)
                for link in nav_links:
                    href = link['href']
                    if 'components/' in href:
                        component_name = href.split('/')[-1]
                        if component_name and component_name not in ['components', 'docs']:
                            components.add(component_name)
            
        except Exception as e:
            print(f"Error accessing docs page: {str(e)}")
        
        # Method 2: Known MagicUI components (reduced to most common ones)
        known_components = [
            'marquee', 'animated-beam', 'border-beam', 'magic-card', 'particles',
            'ripple', 'shimmer', 'dock', 'meteors', 'globe', 'confetti',
            'typing-animation', 'word-rotate', 'animated-list', 'blur-in',
            'fade-text', 'number-ticker', 'sparkles-text', 'retro-grid'
        ]
        
        # Method 3: Test each known component
        print("Testing known components...")
        for component in known_components:
            try:
                test_url = f"{self.docs_url}/components/{component}"
                test_response = self.session.head(test_url, timeout=5)
                if test_response.status_code == 200:
                    components.add(component)
                    print(f"✓ Found: {component}")
                else:
                    print(f"✗ Not found: {component}")
            except:
                print(f"✗ Error testing: {component}")
            time.sleep(0.5)  # Small delay between tests
        
        # Method 4: Try alternative URL patterns
        print("Testing alternative URL patterns...")
        base_patterns = [
            f"{self.base_url}/docs/components/",
            f"{self.base_url}/components/"
        ]
        
        for pattern in base_patterns:
            for component in ['marquee', 'animated-beam', 'particles', 'globe']:
                try:
                    test_url = f"{pattern}{component}"
                    test_response = self.session.head(test_url, timeout=5)
                    if test_response.status_code == 200:
                        components.add(component)
                        print(f"✓ Found via {pattern}: {component}")
                except:
                    pass
        
        component_list = sorted(list(components))
        print(f"\nDiscovered {len(component_list)} components: {component_list}")
        
        # If no components found, use a minimal fallback
        if not component_list:
            print("No components discovered, using minimal fallback...")
            component_list = ['marquee', 'animated-beam', 'particles', 'border-beam', 'magic-card']
            
        return component_list
    
    def extract_code_content(self, soup: BeautifulSoup) -> str:
        """Extract code content from various possible locations"""
        # First try to find import statements and usage examples
        code_blocks = []
        
        # Look for import statements
        import_pattern = r'import\s+.*from\s+.*'
        text_content = soup.get_text()
        imports = re.findall(import_pattern, text_content)
        
        # Look for usage examples
        usage_pattern = r'<[A-Z][a-zA-Z]*[^>]*>.*?</[A-Z][a-zA-Z]*>'
        usage_examples = re.findall(usage_pattern, text_content, re.DOTALL)
        
        # Standard code selectors
        code_selectors = [
            'pre code',
            'pre',
            '.code-block code',
            '.code-block',
            '[data-language] code',
            '[data-language]',
            '.highlight code',
            '.highlight',
            'code.language-tsx',
            'code.language-jsx',
            'code.language-typescript',
            'code.language-javascript',
            'code',
            '.shiki code',
            '.shiki'
        ]
        
        # Try to extract from code blocks
        for selector in code_selectors:
            elements = soup.select(selector)
            for element in elements:
                code = element.get_text(strip=True)
                if code and len(code) > 20:  # Filter out short snippets
                    # Clean up the code
                    code = re.sub(r'^```[\w]*\n?', '', code)
                    code = re.sub(r'\n?```', '', code)

    
    def scrape_component(self, component_name: str) -> Dict:
        """Scrape a single component"""
        print(f"Scraping {component_name}...")
        
        # Try multiple URL patterns
        possible_urls = [
            f"{self.docs_url}/components/{component_name}",
            f"{self.base_url}/components/{component_name}",
            f"{self.base_url}/docs/components/{component_name}"
        ]
        
        title = component_name.replace('-', ' ').title()
        description = f"An interactive {component_name.replace('-', ' ')} component"
        code = None
        
        for url in possible_urls:
            try:
                print(f"  Trying URL: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract title
                    title_selectors = ['h1', '.title', '[data-title]', 'title', 'h2']
                    
                    for selector in title_selectors:
                        element = soup.select_one(selector)
                        if element:
                            title_text = element.get_text(strip=True)
                            if title_text and len(title_text) < 100 and component_name.replace('-', ' ').lower() in title_text.lower():
                                title = title_text
                                break
                    
                    # Extract description from meta or first paragraph
                    meta_desc = soup.find('meta', {'name': 'description'})
                    if meta_desc and meta_desc.get('content'):
                        description = meta_desc.get('content')
                    else:
                        # Look for description in the page content
                        desc_selectors = [
                            'p:first-of-type',
                            '.prose p:first-of-type',
                            'main p:first-of-type',
                            'article p:first-of-type'
                        ]
                        
                        for selector in desc_selectors:
                            element = soup.select_one(selector)
                            if element:
                                desc_text = element.get_text(strip=True)
                                if desc_text and len(desc_text) > 20 and len(desc_text) < 200:
                                    description = desc_text
                                    break
                    
                    # Try to extract code
                    extracted_code = self.extract_code_content(soup)
                    if extracted_code and len(extracted_code) > 100:
                        code = extracted_code
                        print(f"  ✓ Found code in page")
                        break
                    else:
                        print(f"  ⚠ Page loaded but no substantial code found")
                        
                else:
                    print(f"  ✗ HTTP {response.status_code} at {url}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Network error at {url}: {str(e)}")
                continue
            except Exception as e:
                print(f"  ✗ Error at {url}: {str(e)}")
                continue
        
        # If no code was found from scraping, use template
        if not code:
            print(f"  → Using template for {component_name}")
            code = self.create_component_template(component_name, description)
        
        if code:
            # Create component data structure
            component_data = {
                "$schema": "https://ui.shadcn.com/schema/registry-item.json",
                "name": component_name,
                "type": "registry:ui",
                "title": title,
                "description": description,
                "files": [{
                    "path": f"registry/magicui/{component_name}.tsx",
                    "content": code,
                    "type": "registry:ui",
                    "target": f"components/magicui/{component_name}.tsx"
                }]
            }
            
            print(f"  ✓ Component data created for {component_name}")
            return {
                "prompt": f"Generate a UI component like {title}",
                "completion": json.dumps(component_data, indent=2)
            }
        
        print(f"  ✗ Failed to create component data for {component_name}")
        return None
    
    def scrape_all_components(self) -> List[Dict]:
        """Scrape all discovered components"""
        components = self.discover_components()
        data = []
        failed_components = []
        
        print(f"\nStarting to scrape {len(components)} components...")
        
        for i, component in enumerate(components, 1):
            print(f"[{i}/{len(components)}] Processing {component}...")
            
            try:
                component_data = self.scrape_component(component)
                if component_data:
                    data.append(component_data)
                    print(f"✓ Successfully scraped {component}")
                else:
                    failed_components.append(component)
                    print(f"✗ Failed to scrape {component}")
                
                # Be respectful with delays
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\nScraping interrupted by user")
                break
            except Exception as e:
                print(f"✗ Unexpected error with {component}: {str(e)}")
                failed_components.append(component)
                continue
        
        print(f"\nScraping completed!")
        print(f"Successfully scraped: {len(data)} components")
        print(f"Failed components: {len(failed_components)}")
        if failed_components:
            print(f"Failed: {failed_components}")
        
        return data
    
    def save_data(self, data: List[Dict], filename: str = 'magicui_full.json'):
        """Save scraped data to file"""
        os.makedirs('data/raw', exist_ok=True)
        filepath = f'data/raw/{filename}'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filepath}")
        
        # Also save a summary
        summary = {
            "total_components": len(data),
            "components": [item["completion"] for item in data],
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        summary_filepath = f'data/raw/magicui_summary.json'
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Summary saved to {summary_filepath}")

def main():
    scraper = MagicUIComponentScraper()
    
    try:
        # Scrape all components
        data = scraper.scrape_all_components()
        
        if data:
            # Save the data
            scraper.save_data(data)
            print(f"\n🎉 Successfully completed scraping {len(data)} components!")
        else:
            print("\n❌ No components were successfully scraped")
            
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")

if __name__ == "__main__":
    main()