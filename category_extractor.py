import re
from playwright.sync_api import sync_playwright

def extract_categories(journal_name="BIOETHICS"):
    """
    Extracts Subject Area and Category numbers from the Scimago Journal page for a given journal.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Searching for journal: {journal_name}...")
        try:
            # 1. Go to Scimago
            page.goto("https://www.scimagojr.com/", timeout=60000)
            
            # 2. Search
            search_input = page.locator("input[name='q']")
            search_input.fill(journal_name)
            search_input.press("Enter")
            
            # 3. Wait for results and click the first valid journal link
            # The results are usually in .search_results class or similar, but often just a list of <a> tags
            # We wait for the specific result structure.
            # Based on inspection, results are often <a> tags with class 'journal_link' or simply in a list.
            # Let's wait for the search results page to load.
            page.wait_for_selector(".search_results a", timeout=10000)
            
            # Click the first result that looks like a journal link (not an ad)
            # We can be more specific if needed, but first result is usually best for exact match
            first_result = page.locator(".search_results a").first
            print(f"Navigating to: {first_result.inner_text()}")
            first_result.click()
            
            # 4. Wait for journal page to load
            page.wait_for_selector(".cellgrid", timeout=10000)
            
            # 5. Find "Subject Area and Category" section
            # It's usually a text node "Subject Area and Category" followed by links
            # We can find the container.
            # JS execution found it in a .cellgrid that contains text "Subject Area and Category"
            
            # Get all links in the section that headers "Subject Area and Category"
            # Since structure varies, we iterate over cell grids
            
            print("Extracting categories...")
            
            links_data = page.evaluate("""
                () => {
                    const sections = document.querySelectorAll('.cellgrid');
                    let targetSection = null;
                    for (const section of sections) {
                        if (section.textContent.includes('Subject Area and Category')) {
                            targetSection = section;
                            break;
                        }
                    }
                    
                    if (!targetSection) return [];
                    
                    const links = targetSection.querySelectorAll('a');
                    return Array.from(links).map(a => ({
                        text: a.textContent.trim(),
                        href: a.href
                    }));
                }
            """)
            
            results = {}
            
            for link in links_data:
                text = link['text']
                href = link['href']
                
                # Check for Area
                area_match = re.search(r'area=(\d+)', href)
                if area_match:
                    results[text] = {"type": "Subject Area", "id": area_match.group(1)}
                    continue
                
                # Check for Category
                cat_match = re.search(r'category=(\d+)', href)
                if cat_match:
                    results[text] = {"type": "Category", "id": cat_match.group(1)}
                    continue
            
            # Print results nicely
            print("-" * 40)
            for name, data in results.items():
                print(f"{name} ({data['type']}): {data['id']}")
            print("-" * 40)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    extract_categories()
