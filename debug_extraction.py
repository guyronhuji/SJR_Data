from sjr_scraper import get_journal_metrics
import sys

# URL suffix for Bioethics (approximate, usually what search returns)
# trying a known one, or I can mock the search if needed.
# From previous subagent trace: https://www.scimagojr.com/journalsearch.php?q=22258&tip=sid&clean=0
test_url = "journalsearch.php?q=22258&tip=sid&clean=0"

print(f"Testing extraction for: {test_url}")
metrics = get_journal_metrics(test_url)

print("\n--- Extracted Metrics ---")
print(metrics)

if "Categories" in metrics:
    print(f"\nFound {len(metrics['Categories'])} categories.")
    for cat in metrics['Categories']:
        print(cat)
else:
    print("\nNO 'Categories' key found in metrics.")
