import re
import os
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

def handle_interstitials(page):
    """
    Checks for and handles interstitials like Cloudflare challenges and Ad overlays.
    """
    # 1. Google Vignette Ads
    try:
        for frame in page.frames:
             if "google_ads" in frame.name or "aswift" in frame.name:
                 close_btn = frame.locator("#dismiss-button, [aria-label='Close ad'], div[aria-label='Close ad']").first
                 if close_btn.count() > 0 and close_btn.is_visible():
                     print("Found Google Vignette ad. Closing...")
                     close_btn.click()
                     page.wait_for_timeout(1000) 
                     return 
    except Exception as e:
        print(f"Error handling ads: {e}")

    # 2. Cloudflare
    try:
        cf_frames = [f for f in page.frames if "cloudflare" in f.url or "turnstile" in f.url]
        for frame in cf_frames:
             checkbox = frame.locator("input[type='checkbox'], .ctp-checkbox-label").first
             if checkbox.count() > 0 and checkbox.is_visible():
                 print("Found Cloudflare challenge. Attempting to click...")
                 checkbox.click()
                 page.wait_for_timeout(2000)
                 return
    except Exception as e:
        print(f"Error handling Cloudflare: {e}")

def search_journal(query):
    """
    Searches for a journal on Scimago and returns a list of results.
    Returns a list of dicts: {'title': str, 'url': str}
    """
    results_data = []
    print(f"Searching for: {query}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto("https://www.scimagojr.com/")
            handle_interstitials(page)
            
            # Search Input
            try:
                page.locator("#searchinput").wait_for(timeout=5000)
            except:
                print("Search input not found.")
                return []

            page.locator("#searchinput").fill(query)
            page.keyboard.press("Enter")
            
            # Wait for results
            try:
                page.wait_for_url("**/journalsearch.php?q=*", timeout=30000)
            except:
                print("Timeout waiting for search results URL.")
                pass
            
            handle_interstitials(page)

            # Extract results
            result_elements = page.locator("div.search_results > a").all()
            if not result_elements:
                 result_elements = page.locator("a[href^='journalsearch.php?q=']").all()

            for res in result_elements:
                text = res.inner_text().strip()
                href = res.get_attribute("href")
                if text and href:
                    title = text.split('\n')[0].strip()
                    results_data.append({"title": title, "url": href})
                    
        except Exception as e:
            print(f"Error during search: {e}")
        finally:
            browser.close()
            
    return results_data

def get_journal_metrics(url_suffix):
    """
    Navigates to the journal detail page and extracts metrics.
    """
    metrics = {"H-Index": "N/A", "SJR": "N/A", "Quartile": "N/A"}
    
    if url_suffix.startswith("http"):
        full_url = url_suffix
    else:
        if url_suffix.startswith("/"):
            full_url = f"https://www.scimagojr.com{url_suffix}"
        else:
            full_url = f"https://www.scimagojr.com/{url_suffix}"
            
    print(f"Navigating to {full_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(full_url, timeout=60000)
            handle_interstitials(page)
            
            # Wait/Check H-index
            try:
                page.wait_for_selector(".hindexnumber", timeout=30000)
            except:
                pass
            
            handle_interstitials(page)

            try:
                # SJR
                sjr_el = page.locator(".content-hindex span.hsjr").first
                if sjr_el.count() > 0:
                    metrics["SJR"] = sjr_el.inner_text()
                else:
                    sjr_el = page.locator(".sjrnumber").first
                    if sjr_el.count() > 0:
                         metrics["SJR"] = sjr_el.inner_text()
            except: pass

            try:
                # Quartile
                q_loc = page.locator(".content-hindex .hindexnumber span[class^='Q']").first
                if q_loc.count() > 0:
                    metrics["Quartile"] = q_loc.inner_text()
            except: pass

            try:
                # H-Index
                h_box = page.locator(".cuadrado", has_text="H-Index").first
                if h_box.count() > 0:
                    h_index_el = h_box.locator(".hindexnumber").first
                    if h_index_el.count() > 0:
                         metrics["H-Index"] = h_index_el.inner_text()
            except: pass
            
            try:
                # ISSN
                issn_el = page.get_by_text(re.compile(r"ISSN"), exact=False).first
                if issn_el.count() > 0:
                    text_content = issn_el.inner_text()
                    issn_matches = re.findall(r"\d{8}", text_content)
                    if issn_matches:
                         metrics["ISSN"] = issn_matches
            except: pass

            try:
                # Categories
                links_data = page.evaluate("""
                    () => {
                        const h2s = Array.from(document.querySelectorAll('h2'));
                        const targetH2 = h2s.find(h => h.textContent.includes('Subject Area and Category'));
                        
                        if (!targetH2) return [];
                        const container = targetH2.parentElement;
                        if (!container) return [];

                        const links = container.querySelectorAll('a');
                        return Array.from(links).map(link => ({
                            text: link.textContent.trim(),
                            href: link.href
                        }));
                    }
                """)
                
                categories = []
                for link in links_data:
                    text = link['text']
                    href = link['href']
                    area_match = re.search(r'area=(\d+)', href)
                    if area_match:
                        categories.append({"name": text, "type": "Subject Area", "id": area_match.group(1)})
                        continue
                    cat_match = re.search(r'category=(\d+)', href)
                    if cat_match:
                        categories.append({"name": text, "type": "Category", "id": cat_match.group(1)})
                        continue
                
                metrics["Categories"] = categories
            except Exception as e:
                print(f"Error extracting categories: {e}")
                
        except Exception as e:
            print(f"Error getting metrics: {e}")
        finally:
            browser.close()
            
    return metrics

def download_journal_rankings(year, id_value, type_str):
    """
    Downloads the journal ranking Excel file.
    """
    if type_str not in ['area', 'category']:
        raise ValueError("type_str must be 'area' or 'category'")
        
    page_url = f"https://www.scimagojr.com/journalrank.php?{type_str}={id_value}&year={year}"
    print(f"Navigating to rankings: {page_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(page_url, timeout=60000)
            handle_interstitials(page)
            
            # Wait for download button
            try:
                download_selector = 'a.button[href*="out=xls"]'
                print("Waiting up to 5 minutes for download button (solve CAPTCHA now if needed)...")
                page.wait_for_selector(download_selector, state="visible", timeout=300000)
            except:
                print("Download button not found (timeout).")
                page.screenshot(path=f"debug_ranking_fail_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
                return None

            # Click and wait for download
            with page.expect_download(timeout=60000) as download_info:
                try:
                    print("Clicking download button...")
                    page.click(download_selector)
                except Exception as e:
                    print(f"Error clicking download button: {e}")
                    raise e
            
            download = download_info.value
            import tempfile
            tmp_path = os.path.join(tempfile.gettempdir(), f"temp_sjr_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx")
            download.save_as(tmp_path)
            print(f"File downloaded to {tmp_path}")
            
            # Read into DataFrame
            try:
                # Try Excel 
                df = pd.read_excel(tmp_path, engine='openpyxl')
            except Exception as excel_err:
                print(f"Excel read failed, trying CSV...")
                try:
                    df = pd.read_csv(tmp_path, sep=';', quotechar='"', on_bad_lines='skip')
                except Exception as csv_err:
                     print(f"CSV read failed: {csv_err}")
                     raise excel_err
            
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            
            return df
            
        except Exception as e:
            print(f"Error downloading ranking data: {e}")
            return None
        finally:
            browser.close()
