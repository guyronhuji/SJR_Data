from playwright.sync_api import sync_playwright
import os
import sys

def test_browser():
    print("Testing Playwright...")
    try:
        with sync_playwright() as p:
            print(f"Playwright version: {p}")
            print("Launching chromium...")
            browser = p.chromium.launch(headless=False)
            print("Browser launched successfully.")
            page = browser.new_page()
            page.goto("https://example.com")
            print("Navigated to example.com")
            browser.close()
            print("Browser closed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_browser()
