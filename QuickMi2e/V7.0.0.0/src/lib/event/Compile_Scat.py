import os
import re
import time
from lib.helper.Directory import Directory
import shutil
import threading
import concurrent.futures 
import logging

# --- Custom Logger Import ---
from lib.helper.Logger import LoggerSetup 

class Scat:
    def __init__(self):
        # --- Initialize Logger ---
        self.logger = LoggerSetup(
            log_name='Scat compilation', 
            log_dir_relative_path=r"output\Log"
        ).get_logger()
        
        self.logger.info("Initializing Scat class...")
        self.dataDict = dict()

    def setPath(self, destPath, savePath):
        self.logger.info(f"Setting paths... Source: {destPath}, Destination: {savePath}")
        try:
            self.__savePath = savePath
            self.__destPath = destPath
            
            if not os.path.exists(self.__destPath):
                 raise FileNotFoundError(f"Source path does not exist: {self.__destPath}")
                 
            self.__data = os.listdir(self.__destPath)
            self.logger.info(f"Found {len(self.__data)} initial items in source directory.")

        except Exception as e:
            self.logger.critical(f"setPath failed: {e}")
            raise ValueError(f"\nError: {e}")

    def convert2DataFrame(self):
        self.logger.info("Starting directory scanning (convert2DataFrame)...")
        try:
            if len(os.listdir(self.__destPath)) == 0:
                raise ValueError(f"No scat files were found in '{self.__destPath}'.\nPlease Check your file Type selection//File Format")
            
            # Worker function (Logging skipped here for performance)
            def process_sample(sample):
                sample_path = os.path.join(self.__destPath, sample)
                if os.path.isdir(sample_path):
                    filterFiles = [x for x in os.listdir(sample_path) if x.endswith(".csv")]
                    
                    if len(filterFiles) == 0:
                        # You might want to skip raising error here to keep other threads alive
                        # raise ValueError(f"No files with the extension 'csv' were found in '{sample}'.")
                        pass 
                    else:
                        self.dataDict[sample] = filterFiles

            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(process_sample, self.__data)

            self.logger.info(f"Directory scanning complete. Found valid data in {len(self.dataDict)} folders.")

        except Exception as e:
            self.logger.error(f"convert2DataFrame failed: {e}", exc_info=True)
            raise ValueError(f"Error: {e}")

    def extractData(self):
        self.logger.info("Starting data extraction and file reorganization...")
        try:
            regexPattern = r'(\w+)_(\w+)_(\w+)\.csv'
            threads = []

            # Worker function (Logging skipped for success cases)
            def processFile(key, sample, regexPattern):
                try:
                    match = re.match(regexPattern, sample)
                    if match:
                        Ch = match.group(1)
                        S_param = match.group(2)
                        
                        # Source path
                        src_path = os.path.join(self.__destPath, key, sample)
                        
                        # Destination directory (create it if it doesn't exist)
                        dest_dir = os.path.join(self.__savePath, Ch)
                        
                        # Note: makedirs is thread-safe in Python 3.2+
                        os.makedirs(dest_dir, exist_ok=True)
                        
                        # Destination path
                        dest_path = os.path.join(dest_dir, f'{key}_{S_param}.csv')
                        
                        # Move and rename the file
                        shutil.move(src_path, dest_path)
                    else:
                        # Log warning only on failure (low frequency expected)
                        self.logger.warning(f"File '{sample}' does not match regex pattern. Skipping.")
                except Exception as inner_e:
                    self.logger.error(f"Failed to move file {sample}: {inner_e}")

            # [PERFORMANCE] Loop to spawn threads - No logging inside loop
            for key, value in self.dataDict.items():
                for sample in value:
                    thread = threading.Thread(target=processFile, args=(key, sample, regexPattern))
                    threads.append(thread)
                    thread.start()

            # Wait for all threads to finish
            for thread in threads:
                thread.join()
            
            self.logger.info(f"Extraction complete. Processed {len(threads)} file operations.")

        except Exception as e:
            self.logger.error(f"extractData failed: {e}", exc_info=True)
            raise ValueError(f"Error: {e}")
        

    @property
    def getSpecHeader(self):
        try:
            self.__specPath = r"{path}\dataset\cntrace\zip".format(path=os.getcwd())
            if not self.__specPath or not os.path.exists(self.__specPath):
                self.logger.warning(f"Spec path not found: {self.__specPath}")
                return []
            
            headers = [
                os.path.splitext(filename)[0]
                for filename in os.listdir(self.__specPath)
                if filename.lower().endswith('.zip')
            ]
            self.logger.info(f"Retrieved {len(headers)} spec headers.")
            return headers
        except Exception as e:
            self.logger.error(f"Error getting spec headers: {e}")
            return []


if __name__ == "__main__":
    # Setup Paths
    savepath = r'C:\Users\ro898771\Documents\QuickMi2e\dataset\results'
    datasrc = r'C:\Users\ro898771\Box\Buster 2did SKEW Trace\New'
    copysrc = r'C:\Users\ro898771\Documents\QuickMi2e\dataset\cntrace\zip'
    dest = r'C:\Users\ro898771\Documents\QuickMi2e\dataset\cntrace\trace'

    print("Starting Main Process...") # Console feedback

    try:
        start_time = time.time()

        # Initialize Directory Helper
        dir = Directory()
        
        # Clean up directories
        dir.delete_all_files_and_subfolders(savepath)
        dir.delete_all_files_and_subfolders(copysrc)
        dir.delete_all_files_and_subfolders(dest)

        # Copy and Unzip
        dir.copy_file(datasrc)
        dir.rename_and_unzip_scat(copysrc, dest)

        # Scat Processing
        scat_process = Scat()
        
        # 1. Set Path
        scat_process.setPath(dest, savepath)
        
        # 2. Convert to DF (Scan directories)
        scan_start = time.time()
        scat_process.convert2DataFrame()
        print(f"Directory Scan Time: {time.time() - scan_start:.2f}s")
        
        # 3. Extract Data (Move files)
        extract_start = time.time()
        scat_process.extractData()
        print(f"Extraction Time: {time.time() - extract_start:.2f}s")

        # Cleanup
        dir.delete_all_files_and_subfolders(dest)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Merged Completed!!\nTotal Elapsed Time: {elapsed_time:.2f}s")

    except Exception as e:
        print(f"\n[FATAL ERROR] Main process failed: {e}")