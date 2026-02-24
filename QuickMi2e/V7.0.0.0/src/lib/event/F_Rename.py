import pandas as pd
import os
import re
from concurrent.futures import ThreadPoolExecutor
import logging

# --- Custom Logger Import ---
from lib.helper.Logger import LoggerSetup 

class DynamicRenamer:
    def __init__(self, src_path=None, setting_path=None):
        # --- Initialize Logger ---
        self.logger = LoggerSetup(
            log_name='DynamicRenamer', 
            log_dir_relative_path=r"output\Log"
        ).get_logger()

        # Handle paths with defaults if not provided
        self.src_path = src_path if src_path else r'{path}\dataset\results'.format(path=os.getcwd())
        self.setting_path = setting_path if setting_path else r'{path}\setting\CFG\ReplaceLot'.format(path=os.getcwd())
        
        self.rules = []
        
        self.logger.info(f"Initialized Renamer. Target: {self.src_path}")
        self.logger.info(f"Settings Path: {self.setting_path}")

    def load_rules(self):
        """
        Reads Overwrite.csv and generates find/replace pairs.
        """
        self.logger.info("Loading renaming rules...")
        csv_file = os.path.join(self.setting_path, "Overwrite.csv")
        
        if not os.path.exists(csv_file):
            self.logger.error(f"Settings file not found at {csv_file}")
            return

        try:
            df = pd.read_csv(csv_file)
            
            # Regex to capture the Key and the Value inside brackets
            parser_pattern = r"([a-zA-Z0-9]+)\[(.*?)\]"

            valid_rules = 0
            for index, row in df.iterrows():
                current_full_tag = str(row['Current']).strip() 
                new_inner_value = str(row['Replace With']).strip() 

                match = re.match(parser_pattern, current_full_tag)
                
                if match:
                    key = match.group(1) 
                    
                    # Construct full find/replace strings
                    find_str = current_full_tag
                    replace_str = f"{key}[{new_inner_value}]"
                    
                    self.rules.append({
                        'find': find_str,
                        'replace': replace_str,
                    })
                    valid_rules += 1
                else:
                    # Log warning for specific invalid rows (low volume, so safe to log)
                    self.logger.warning(f"Invalid format in CSV row {index}: {current_full_tag}")

            self.logger.info(f"Successfully loaded {valid_rules} rules.")

        except Exception as e:
            self.logger.critical(f"Critical Error reading CSV: {e}", exc_info=True)

    def process_file(self, file_info):
        """
        Worker function for ThreadPool.
        [PERFORMANCE CRITICAL] NO LOGGING HERE.
        Returns 1 if renamed, 0 if not, -1 if error.
        """
        try:
            directory, filename = file_info
            original_name = filename
            new_name = filename

            # Iteratively apply all loaded rules
            for rule in self.rules:
                if rule['find'] in new_name:
                    new_name = new_name.replace(rule['find'], rule['replace'])

            # Only rename if the name actually changed
            if new_name != original_name:
                old_full_path = os.path.join(directory, original_name)
                new_full_path = os.path.join(directory, new_name)
                
                os.rename(old_full_path, new_full_path)
                return 1 # Renamed
            
            return 0 # No change needed
            
        except Exception:
            return -1 # Error

    def execute(self):
        self.logger.info("Starting Rename Process...")
        
        self.load_rules()
        
        if not self.rules:
            self.logger.warning("No valid rules loaded. Aborting execution.")
            return

        # 1. Collect all files
        self.logger.info("Scanning directories...")
        all_files = []
        if not os.path.exists(self.src_path):
             self.logger.error(f"Source directory not found: {self.src_path}")
             return

        for root, dirs, files in os.walk(self.src_path):
            for file in files:
                if file.endswith(".csv"): 
                    all_files.append((root, file))

        self.logger.info(f"Found {len(all_files)} files. Starting parallel processing...")

        
        # 2. Parallel Processing
        renamed_count = 0
        error_count = 0
        
        # Adjust workers based on CPU
        with ThreadPoolExecutor(max_workers=os.cpu_count() * 4) as executor:
            # Map returns an iterator of results
            results = executor.map(self.process_file, all_files)
            
            # Aggregate results in main thread (fast operation)
            for res in results:
                if res == 1:
                    renamed_count += 1
                elif res == -1:
                    error_count += 1

        self.logger.info(f"Process Complete.")
        self.logger.info(f"Summary: {renamed_count} files renamed. {error_count} errors encountered.")

# --- Execution Block ---
if __name__ == "__main__":
    # Example Paths
    # Ensure these exist or code handles non-existence gracefully
    SRC = r'C:\Users\ro898771\Documents\QuickMi2e\dataset\results'
    CFG = r'C:\Users\ro898771\Documents\QuickMi2e\setting\CFG\ReplaceLot'
    
    app = DynamicRenamer(src_path=SRC, setting_path=CFG)
    app.execute()