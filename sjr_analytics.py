import pandas as pd
import re
from sjr_scraper import search_journal, get_journal_metrics, download_journal_rankings

def get_journal_percentiles(journal_name, year="2022"):
    """
    Calculates the percentile of a journal in all its subject areas and categories.
    """
    # 1. Search
    print(f"Searching for '{journal_name}'...")
    results = search_journal(journal_name)
    if not results:
        print("Journal not found.")
        return None
    
    # Assume first result is the target
    target_journal = results[0]
    print(f"Found: {target_journal['title']}")
    
    # 2. Get Metrics (Categories & ISSN)
    print(f"Extracting metrics from {target_journal['url']}...")
    metrics = get_journal_metrics(target_journal['url'])
    
    return calculate_percentiles_from_metrics(target_journal['title'], metrics, year)

def calculate_percentiles_from_metrics(journal_title, metrics, year="2022"):
    """
    Calculates percentiles given already extracted metrics (categories, ISSNs).
    """
    categories = metrics.get("Categories", [])
    issns = metrics.get("ISSN", [])
    
    if not categories:
        print("No categories found for this journal.")
        return []

    percentile_data = []
    
    # Process each category
    for cat in categories:
        cat_name = cat['name']
        cat_type = cat['type'] 
        cat_id = cat['id']
        type_str = 'area' if cat_type == 'Subject Area' else 'category'
        
        print(f"\nProcessing {cat_type}: {cat_name} (ID: {cat_id})...")
        
        try:
            # Use standalone function
            df = download_journal_rankings(year, cat_id, type_str)
            if df is None:
                print(f"Failed to download data for {cat_name}")
                continue
                
            # Match Logic
            match_row = None
            
            def clean_issn(s):
                return str(s).replace('-', '').replace(' ', '')
            
            if issns:
                for idx, row in df.iterrows():
                    row_issn_raw = str(row.get('Issn', ''))
                    row_issns_list = [clean_issn(x) for x in row_issn_raw.split(',')]
                    target_issns_clean = [clean_issn(i) for i in issns]
                    
                    if any(t_issn in r_issn for r_issn in row_issns_list for t_issn in target_issns_clean):
                        match_row = row
                        break
            
            if match_row is None:
                print("ISSN match failed/skipped. Trying Title match...")
                target_title = journal_title.lower().strip()
                for idx, row in df.iterrows():
                    row_title = str(row['Title']).lower().strip()
                    if row_title == target_title:
                        match_row = row
                        break
            
            if match_row is not None:
                rank = match_row['Rank']
                total = len(df)
                percentile = ((total - rank + 0.5) / total) * 100
                
                result = {
                    "Category": cat_name,
                    "Type": cat_type,
                    "Rank": rank,
                    "Total Journals": total,
                    "Percentile": round(percentile, 2),
                    "SJR": match_row.get('SJR', 'N/A'),
                    "Quartile": match_row.get('SJR Best Quartile', 'N/A')
                }
                percentile_data.append(result)
                print(f"  -> Rank: {rank}/{total}, Percentile: {round(percentile, 2)}%")
            else:
                print(f"  -> Journal not found in ranking list for {cat_name}")
                
        except Exception as e:
            print(f"Error processing {cat_name}: {e}")
            
    return percentile_data

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Get Scimago Journal Percentiles')
    parser.add_argument('journal', help='Name of the journal')
    parser.add_argument('--year', default='2022', help='Year for ranking data')
    
    args = parser.parse_args()
    
    results = get_journal_percentiles(args.journal, args.year)
    
    if results:
        print("\n=== Summary Results ===")
        df_res = pd.DataFrame(results)
        print(df_res[['Category', 'Type', 'Rank', 'Total Journals', 'Percentile']].to_string(index=False))
