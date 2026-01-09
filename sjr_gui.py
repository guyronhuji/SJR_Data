import customtkinter as ctk
import threading
from sjr_scraper import search_journal, get_journal_metrics
from sjr_analytics import calculate_percentiles_from_metrics

class SJRApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SJR Scraper")
        self.geometry("600x500")
        
        # Layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Input Area
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.search_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter journal name...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=10)
        self.search_entry.bind("<Return>", self.start_search)
        
        # Year Input
        self.year_entry = ctk.CTkEntry(self.input_frame, width=60, placeholder_text="Year")
        self.year_entry.pack(side="left", padx=(0, 10), pady=10)
        self.year_entry.insert(0, "2022")
        
        self.search_button = ctk.CTkButton(self.input_frame, text="Search", command=self.start_search)
        self.search_button.pack(side="right", padx=(0, 10), pady=10)

        # Results Area
        self.results_frame = ctk.CTkScrollableFrame(self, label_text="Search Results")
        self.results_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        # Details Area
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.details_frame, text="Ready", text_color="gray")
        self.status_label.pack(pady=5)

        self.metrics_label = ctk.CTkLabel(self.details_frame, text="", font=("Arial", 14, "bold"))
        self.metrics_label.pack(pady=10)
        
        self.calc_button = ctk.CTkButton(self.details_frame, text="Calculate Percentiles", command=self.start_calculate, state="disabled")
        self.calc_button.pack(pady=10)
        
        self.current_journal_title = None
        self.current_metrics = None
        
        # Cleanup on exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.destroy()

    def start_search(self, event=None):
        query = self.search_entry.get()
        if not query:
            return
        
        self.status_label.configure(text=f"Searching for '{query}'...", text_color="blue")
        self.search_button.configure(state="disabled")
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Run search in thread
        threading.Thread(target=self.run_search, args=(query,), daemon=True).start()

    def run_search(self, query):
        try:
            results = search_journal(query)
            self.after(0, self.display_results, results)
        except Exception as e:
            self.after(0, self.status_label.configure, {"text": f"Error: {e}", "text_color": "red"})
            self.after(0, self.search_button.configure, {"state": "normal"})

    def display_results(self, results):
        self.search_button.configure(state="normal")
        if not results:
            self.status_label.configure(text="No results found.", text_color="red")
            return
        
        self.status_label.configure(text=f"Found {len(results)} results.", text_color="green")
        
        for res in results:
            btn = ctk.CTkButton(
                self.results_frame, 
                text=res['title'], 
                anchor="w",
                fg_color="transparent", 
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda url=res['url'], title=res['title']: self.start_get_metrics(url, title)
            )
            btn.pack(fill="x", padx=5, pady=2)

    def start_get_metrics(self, url, title):
        self.current_journal_title = title
        self.status_label.configure(text=f"Loading metrics for: {title}...", text_color="blue")
        self.metrics_label.configure(text="")
        self.calc_button.configure(state="disabled")
        
        threading.Thread(target=self.run_get_metrics, args=(url,), daemon=True).start()

    def run_get_metrics(self, url):
        try:
            metrics = get_journal_metrics(url)
            self.after(0, self.display_metrics, metrics)
        except Exception as e:
            self.after(0, self.status_label.configure, {"text": f"Error: {e}", "text_color": "red"})
            self.after(0, self.calc_button.configure, {"state": "normal"})

    def display_metrics(self, metrics):
        self.status_label.configure(text="Metrics loaded.", text_color="green")
        
        # Base metrics
        text_lines = [
            f"SJR: {metrics.get('SJR', 'N/A')}",
            f"Quartile: {metrics.get('Quartile', 'N/A')}",
            f"H-Index: {metrics.get('H-Index', 'N/A')}"
        ]
        
        # Categories
        cats = metrics.get("Categories", [])
        if cats:
            text_lines.append("\n--- Subject Areas & Categories ---")
            for cat in cats:
                text_lines.append(f"{cat['name']} ({cat['type']}): {cat['id']}")
        
        final_text = "\n".join(text_lines)
        self.metrics_label.configure(text=final_text)
        
        self.current_metrics = metrics
        self.calc_button.configure(state="normal")
        
    def start_calculate(self):
        year = self.year_entry.get()
        if not self.current_metrics or not self.current_journal_title:
            return
            
        self.status_label.configure(text="Calculating percentiles... (Check browser for CAPTCHA)", text_color="blue")
        self.calc_button.configure(state="disabled")
        
        threading.Thread(target=self.run_calculate, args=(self.current_journal_title, self.current_metrics, year), daemon=True).start()
        
    def run_calculate(self, title, metrics, year):
        try:
            logging.info(f"Starting calculation for {title}, year {year}")
            results = calculate_percentiles_from_metrics(title, metrics, year)
            logging.info(f"Calculation finished. Results found: {len(results) if results else 0}")
            self.after(0, self.display_percentiles, results)
        except Exception as e:
            logging.exception("Error during calculation:")
            self.after(0, self.status_label.configure, {"text": f"Error: {e}", "text_color": "red"})
            self.after(0, self.calc_button.configure, {"state": "normal"})
        
    def display_percentiles(self, results):
        self.calc_button.configure(state="normal")
        self.status_label.configure(text="Calculation complete.", text_color="green")
        
        if not results:
            return
            
        # Open new window
        top = ctk.CTkToplevel(self)
        top.title(f"Percentiles: {self.current_journal_title}")
        top.geometry("700x400")
        
        # Simple scrollable frame for results
        frame = ctk.CTkScrollableFrame(top)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Headers
        headers = ["Category", "Type", "Rank", "Total", "Percentile"]
        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(frame, text=h, font=("Arial", 12, "bold"))
            lbl.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            
        # Data
        for idx, row in enumerate(results):
            vals = [
                row['Category'],
                row['Type'],
                str(row['Rank']),
                str(row['Total Journals']),
                f"{row['Percentile']}%"
            ]
            for i, v in enumerate(vals):
                lbl = ctk.CTkLabel(frame, text=v)
                lbl.grid(row=idx+1, column=i, padx=5, pady=2, sticky="w")

if __name__ == "__main__":
    import os
    import sys
    import logging
    
    # Setup logging to file
    log_file = os.path.join(os.path.expanduser("~"), "sjr_gui.log")
    logging.basicConfig(filename=log_file, level=logging.DEBUG, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    
    try:
        logging.info("Starting SJR App...")
        
        if getattr(sys, 'frozen', False):
            logging.info("Running in frozen mode.")
            
            # Point to local user cache for browsers based on OS
            if sys.platform == "darwin":
                browser_path = os.path.join(os.path.expanduser("~"), "Library", "Caches", "ms-playwright")
            elif sys.platform == "win32":
                 browser_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright")
            else:
                 # Linux fallback
                 browser_path = os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright")
                 
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_path
            logging.info(f"Set PLAYWRIGHT_BROWSERS_PATH to: {browser_path}")
            
        # Initialize App
        c = SJRApp()
        c.mainloop()
    except Exception as e:
        logging.exception("Fatal error in main loop:")
