from sjr_scraper import SJRScraper
import pandas as pd

def test_download():
    # Test case: Bioethics (or similar area)
    # Area: 1200 (Arts and Humanities), Year: 2022
    print("Testing download_journal_rankings for Area 1200, Year 2022...")
    
    scraper = SJRScraper(headless=False)
    try:
        df = scraper.download_journal_rankings(year="2022", id_value="1200", type_str="area")
    finally:
        scraper.close()
    
    if df is not None:
        print("\nDownload Successful!")
        print(f"DataFrame Shape: {df.shape}")
        print("\nColumns:")
        print(df.columns.tolist())
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Verify specific columns exist
        expected = ["Rank", "Title", "SJR", "H index"]
        missing = [c for c in expected if c not in df.columns]
        if missing:
            print(f"\nWARNING: Missing columns: {missing}")
        else:
            print(f"\nVerification Passed: All expected columns {expected} found.")
    else:
        print("\nDownload Failed.")

if __name__ == "__main__":
    test_download()
