import sys
from playwright.sync_api import sync_playwright

def search_journal(page, query):
    """
    Searches for a journal on Scimago and returns a list of results.
    """
    print(f"Searching for '{query}'...")
    # Go to the search page directly with the query to save a step if possible, 
    # but the task asked to use the search box. 
    # Let's try the direct URL first as it's more robust, but fallback to home page if needed.
    # Actually, the user requirement was: "searches for the journal name I provide (using the search box)"
    # So I must follow that flow.
    
    page.goto("https://www.scimagojr.com/journalrank.php")
    
    # Sometimes there's a cloudflare check or simple redirect. 
    # The home page might be safer.
    if "journalrank.php" not in page.url and "scimagojr.com" not in page.url:
         page.goto("https://www.scimagojr.com/")

    # Wait for search input
    try:
        page.locator("#searchinput").wait_for(timeout=5000)
    except:
        print("Waiting for search input... Use the browser window to pass any Cloudflare checks.")
        page.locator("#searchinput").wait_for(timeout=60000)

    page.locator("#searchinput").fill(query)
    page.keyboard.press("Enter")
    
    print("Waiting for results... (Please solve any CAPTCHA if it appears)")
    
    # Wait for results
    # The results seem to appear in a list. 
    # URL changes to journalsearch.php?q=...
    try:
        page.wait_for_url("**/journalsearch.php?q=*", timeout=60000)
    except:
        print("Timed out waiting for URL change.")
    
    # Selectors for results
    # Based on investigation: a[href^="journalsearch.php"]
    
    # Wait for at least one result or "No results" message
    try:
        page.wait_for_selector(".search_results a", timeout=10000)
    except:
        pass

    results = page.locator("div.search_results > a").all()
    
    # If no results container found, maybe try a looser selector
    if not results:
         # Based on the browser subagent, the results were just links that looked like result items.
         # Let's try to grab all links that go to journalsearch.php with a query param (excluding the search itself)
         # Actually usually they are inside 'div.search_results' or similar. 
         # Let's grab all likely result links.
         results = page.locator("a[href^='journalsearch.php?q=']").all()

    parsed_results = []
    for res in results:
        text = res.inner_text().strip()
        href = res.get_attribute("href")
        if text and href:
            parsed_results.append({"title": text, "url": href})
            
    return parsed_results

def get_journal_metrics(page, url):
    """
    Navigates to the journal detail page and extracts metrics.
    """
    full_url = f"https://www.scimagojr.com/{url}"
    print(f"Navigating to {full_url}...")
    page.goto(full_url)
    
    # Wait for the metrics to load
    try:
        page.wait_for_selector(".hindexnumber", timeout=10000)
    except:
        print("Warning: H-index element not found, page might not have fully loaded.")
    
    # Extract H-Index
    # subagent said: .hindexnumber
    h_index = "N/A"
    try:
        h_index_el = page.locator(".hindexnumber")
        if h_index_el.count() > 0:
            h_index = h_index_el.inner_text()
    except:
        pass

    # Extract SJR
    # subagent said: .sjrnumber
    sjr = "N/A"
    try:
        # SJR might be in a different structure sometimes
        sjr_el = page.locator(".sjrnumber")
        if sjr_el.count() > 0:
            sjr = sjr_el.inner_text()
        else:
             # Try finding by text "SJR 20"
             sjr_el = page.locator("div", has_text="SJR 20").first
             if sjr_el.count() > 0:
                 # sibling or child?
                 # let's try a broad text search if class fails
                 pass
    except:
        pass
        
    # Extract Quartile
    # subagent said: .quartile or .Q1
    quartile = "N/A"
    try:
        # Check for specific Q classes
        q_loc = page.locator(".quartile, .Q1, .Q2, .Q3, .Q4").first
        if q_loc.count() > 0:
             quartile = q_loc.inner_text()
        
        # Fallback: look for table row with "Quartiles"
        if quartile == "N/A":
             # This is harder to genericize without seeing the DOM, but let's try
             pass
    except:
        pass

    return {
        "H-Index": h_index,
        "SJR": sjr,
        "Quartile": quartile
    }

def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter journal name to search: ")
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            results = search_journal(page, query)
            
            if not results:
                print("No results found.")
                return

            print(f"\nFound {len(results)} results:")
            for i, res in enumerate(results):
                print(f"{i+1}. {res['title']}")
                
            choice = input("\nEnter the number of the correct journal (or 0 to cancel): ")
            try:
                idx = int(choice) - 1
                if idx < 0:
                    print("Cancelled.")
                    return
                selected_journal = results[idx]
            except (ValueError, IndexError):
                print("Invalid selection.")
                return
                
            metrics = get_journal_metrics(page, selected_journal['url'])
            
            print("\n" + "="*30)
            print(f"Metrics for: {selected_journal['title']}")
            print("="*30)
            print(f"SJR:      {metrics['SJR']}")
            print(f"Quartile: {metrics['Quartile']}")
            print(f"H-Index:  {metrics['H-Index']}")
            print("="*30 + "\n")
            
        finally:
            browser.close()

if __name__ == "__main__":
    main()
