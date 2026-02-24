import pandas as pd
import re
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import numpy as np


# --- Assuming these modules exist in your environment ---
from lib.helper.Directory import Directory
from lib.helper.Feature import Feature
from lib.event.F_HeaderGenerate import HeaderBuilder
# --------------------------------------------------------

from lib.helper.Logger import LoggerSetup 

class TigerOrCntrace:
    def __init__(self):
        # Initialize Logger
        self.logger = LoggerSetup(
            log_name='Tiger-Cntrace Compilation', 
            log_dir_relative_path=r"output\Log"
        ).get_logger()
        
        self.logger.info("Initializing TigerOrCntrace class.")
        
        self.__savePath = None
        self.__tracePath = None
        self.__rootName = None  
        
        try:
            self.__CHParamRegex = Feature().get_Header_Regex() 
        except Exception as e:
            self.logger.critical(f"Failed to get Header Regex from Feature module: {e}")
            raise

        self.__MetaRegex = r'---([\a-zA-Z]+):'             
        self.__IdPattern = r'([a-zA-Z]+)_(-?\w+)'
        self.__fileRegex = r'([a-zA-Z0-9\-_.]+)(\.cntracer)'  
        self.__fileRecord = dict()
        self.__dataFrame = dict()
        self.__headerInfo = dict()
        self.__emptyFlag = False
        self.__lock = threading.Lock() 
        
        try:
            self.__Header = HeaderBuilder()
            self.__loadHeaderConfig = self.__Header.load_config()
        except Exception as e:
            self.logger.critical(f"Failed to load HeaderBuilder config: {e}")
            raise
            
        self.Normalize = 0
        self.DataProcessFlag = False
        self.__max_file_records = 6969 

    def convert_datetime(self, date_str):
        """Converts date string formats to a standardized format."""
        try:
            if '-' in date_str and ':' in date_str:
                formatted_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d-%H%M%S")
            elif '_' in date_str and ':' in date_str:
                formatted_date = datetime.strptime(date_str, "%Y_%m_%d %H:%M:%S").strftime("%Y%m%d-%H%M%S")
            else:
                raise ValueError(f"Unknown date format for string: {date_str}")
            return formatted_date
        except ValueError as e:
            # Kept as warning (rare occurrence)
            self.logger.warning(f"Date conversion failed for '{date_str}': {e}")
            return str(e)

    def set_path(self, tracePath, savepath):
        """Sets trace and save paths and checks for existence of .cntracer files."""
        self.logger.info(f"Setting trace path: {tracePath} and save path: {savepath}")
        try:
            self.__tracePath = tracePath
            self.__savePath = savepath
            
            if not os.path.isdir(self.__tracePath):
                raise FileNotFoundError(f"Trace directory not found: {self.__tracePath}")
                
            pattern = re.compile(self.__fileRegex)
            cnfile = [file for file in os.listdir(self.__tracePath) if pattern.match(file)]
            self.__rootName = [os.path.join(self.__tracePath, x) for x in cnfile]

            if not self.__rootName:
                self.__emptyFlag = True
                raise ValueError(f"No .cntracer files found in directory: {self.__tracePath},\nPlease Check your file Type selection//File Format")
            
            self.logger.info(f"Found {len(self.__rootName)} files to process.")

        except Exception as e:
            self.__emptyFlag = True
            self.logger.error(f"Set_path Error: {e}")
            raise

    @property
    def get_path(self):
        return self.__savePath

    # Convert data into DataFrame
    def Convert2DataFrame(self):
        self.logger.info("Starting Convert2DataFrame...")
        try:
            if self.__emptyFlag or not self.__rootName:
                raise ValueError("Empty Trace Directory! set_path must be called successfully first.")

            def process_file(sample):
                file_name = os.path.basename(sample)
                try:
                    with open(sample, 'r', encoding='utf-8-sig') as file:
                        content = file.readlines()
                        single_column_data = [line.strip() for line in content]
                    df = pd.DataFrame(single_column_data, columns=['StartHeader'])
                    with self.__lock:
                        self.__dataFrame[file_name] = df
                    
                    # [OPTIMIZATION] Removed per-file logging
                    # self.logger.debug(f"Successfully converted {file_name} to DataFrame.")
                    
                except Exception as e:
                    self.logger.error(f"Error converting file {file_name} to DataFrame: {e}")

            with ThreadPoolExecutor(max_workers=os.cpu_count() * 5) as executor:
                executor.map(process_file, self.__rootName)
            
            self.logger.info(f"Finished Convert2DataFrame. Loaded {len(self.__dataFrame)} DataFrames.")

        except Exception as e:
            self.logger.error(f"Convert2DataFrame Error: {e}")
            raise

    # Get Meta Header Position
    def MetaHeaderPos(self):
        self.logger.info("Starting MetaHeaderPos identification...")
        try:
            if not self.__dataFrame:
                raise ValueError("No DataFrames loaded. Run Convert2DataFrame first.")
                
            def process_dataFrame(item):
                key, df = item
                headerPos = {}
                try:
                    meta_matches = df["StartHeader"].str.match(self.__MetaRegex, na=False)
                    matching_rows = df[meta_matches]
                    
                    for index, row in matching_rows["StartHeader"].items():
                        match = re.match(self.__MetaRegex, row.strip())
                        if match:
                            header_key = match.group(1).strip()
                            headerPos[header_key] = index
                            
                    with self.__lock:
                        self.__headerInfo[key] = headerPos
                    
                    # [OPTIMIZATION] Removed per-file logging
                    # self.logger.debug(f"Found {len(headerPos)} metadata headers in {key}.")
                    
                except Exception as e:
                    self.logger.error(f"Error processing headers for file {key}: {e}")

            with ThreadPoolExecutor(max_workers=os.cpu_count() * 5) as executor:
                executor.map(process_dataFrame, self.__dataFrame.items())
            
            self.logger.info("Finished MetaHeaderPos identification.")

        except Exception as e:
            self.logger.error(f"MetaHeaderPos Error: {e}")
            raise

    # Get Meta Parameter Reading
    def GetHeaderParam(self, fileName=None, Key=None):
        try:
            if not self.__headerInfo or fileName not in self.__headerInfo:
                # Kept warning as it indicates logic failure, not volume data
                self.logger.warning(f"File '{fileName}' or header info not available.")
                return None, None
            
            fileUnitObj = self.__headerInfo[fileName]
            ReadData = self.__dataFrame[fileName]
            key_list = list(fileUnitObj.keys())

            try:
                startPos = fileUnitObj[Key]
                HeaderKey = key_list.index(Key)
            except KeyError:
                # Kept warning (specific data issue)
                self.logger.warning(f"Key '{Key}' not found in file '{fileName}' headers.")
                return None, None
            
            maxLength = len(key_list) - 1
            if HeaderKey < maxLength:
                nextHeader = key_list[HeaderKey + 1]
                endPost = fileUnitObj[nextHeader]
            else:
                end_indices = ReadData[ReadData["StartHeader"].str.contains(r'\*{2}')].index
                if not end_indices.empty and end_indices[0] > startPos:
                    endPost = end_indices[0]
                else:
                    endPost = ReadData.index[-1] + 1 

            ExtractData = ReadData["StartHeader"][startPos + 1:endPost]

            split_data = ExtractData.str.split(',', expand=True)
            split_data.columns = [f"Col_{i}" for i in range(split_data.shape[1])]
            
            return ReadData, split_data

        except Exception as e:
            self.logger.error(f"GetHeaderParam Error for file '{fileName}' and key '{Key}': {e}")
            raise

    def getID(self, fileName):
        filtered_pairs = []
        try:
            ReadData = self.__dataFrame[fileName]
            id_indices = ReadData[ReadData["StartHeader"].str.contains(r'\*{2}', regex=True)].index
            
            if id_indices.empty:
                return None

            id_index = id_indices[0] - 1
            if id_index < 0:
                return None

            getID = ReadData["StartHeader"][id_index].split(',')
            
            for variable in getID:
                match = re.match(self.__IdPattern, variable.strip())
                if match:
                    id_value = match.group(1)
                    int_value = match.group(2)
                    filtered_pairs.append([id_value, int_value])

            return dict(filtered_pairs) if filtered_pairs else None
        
        except Exception as e:
            self.logger.error(f"getID Error for file '{fileName}': {e}")
            raise
    
    def checkHeaderRegex(self):
        self.logger.info("Starting header regex validation...")
        try:
            if not self.__dataFrame:
                raise ValueError("No data frames loaded for regex check.")
                
            file = list(self.__dataFrame.keys())[0]
            
            mainData, _ = self.GetHeaderParam(file, 'Global Info')
            if mainData is None:
                raise ValueError(f"'Global Info' header missing in file {file}.")

            start_header = mainData["StartHeader"]
            mainPosition = [
                (index, row) for index, row in start_header.items()
                if re.match(self.__CHParamRegex, row)
            ]

            if not mainPosition:
                raise ValueError(f"No channel data found using regex '{self.__CHParamRegex}'.")
            
            self.logger.info("Header regex validation successful.")

        except Exception as e:
            self.logger.error(f"checkHeaderRegex Error: {e}")
            raise

    def Dataprocessing(self):
        """
        Processes all files in parallel. 
        [OPTIMIZED]: Removed per-file logging to improve speed.
        """
        self.logger.info("Starting parallel Dataprocessing...")
        try:
            self.checkHeaderRegex()
            
            if not self.__dataFrame:
                raise ValueError("No data frames to process.")
                
            self.DataProcessFlag = True
            
            def process_file(file):
                try: 
                    mainData, Paramdata = self.GetHeaderParam(file, 'Global Info')
                    mainData2, Paramdata2 = self.GetHeaderParam(file, 'ConditionName')
                    id_map = self.getID(file)
                    
                    if mainData is None or mainData2 is None:
                        raise ValueError("Required metadata headers missing.")
        
                    def extract_param(df, col_0_val):
                        if df is None: return "NA"
                        # Case-insensitive matching: convert both to lowercase for comparison
                        df_filtered = df[df['Col_0'].str.lower() == col_0_val.lower()]["Col_1"]
                        return df_filtered.to_string(index=False).strip() if not df_filtered.empty else "NA"

                    LOT = extract_param(Paramdata, 'Lot')
                    SL = extract_param(Paramdata, 'Sublot')
                    TT = extract_param(Paramdata, 'TesterName')
                    ASM = extract_param(Paramdata2, 'AssemblyLot')
                    PCB = extract_param(Paramdata2, 'PcbLot')
                    PID = extract_param(Paramdata2, 'PID')
                    
                    MFG = str(id_map.get("MfgID", "NA")).strip() if id_map and str(id_map.get("MfgID", "NA")).strip().upper() not in ["NA", ""] else "NA"
                    MOD = str(id_map.get("ModuleID", "NA")).strip() if id_map and str(id_map.get("ModuleID", "NA")).strip().upper() not in ["NA", ""] else "NA"
                    WF = str(id_map.get("WaferID", "NA")).strip() if id_map and str(id_map.get("WaferID", "NA")).strip().upper() not in ["NA", ""] else "NA"
                    
                    DateTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    formatted_date_string = self.convert_datetime(DateTime)

                    value = {
                        'LOT': LOT, 'SL': SL, 'MFG': MFG, 'MOD': MOD,
                        'WF': WF, 'PID': PID, 'TT': TT, 'ASM': ASM,
                        'PCB': PCB, 'DateTime': formatted_date_string
                    }
                    
                    baseCapturedLabel = self.__Header.build_header_string(value, self.__loadHeaderConfig)
                    
                    mainPosition = [(index, row) for index, row in mainData["StartHeader"].items() if re.match(self.__CHParamRegex, row)]
                    dataRange = [position[0] for position in mainPosition]

                    if not dataRange:
                        # Kept warning (data specific)
                        self.logger.warning(f"No channel data blocks found in file {file}. Skipping.")
                        return 

                    for position in range(len(dataRange)):
                        start = dataRange[position]
                        Label = mainData["StartHeader"][start] 

                        header = mainData["StartHeader"][start + 1]
                        headerLabel = [x.strip() for x in header.split(',') if x.strip()]
                        
                        if position != len(dataRange) - 1:
                            end = dataRange[position + 1]
                            data = mainData["StartHeader"][start + 2:end]
                        else:
                            end_of_file_data = mainData.index[-1] + 1
                            data = mainData["StartHeader"][start + 2:end_of_file_data]

                        split_data = [row.split(',') for row in data]
                        extractFile = file.split('.')[0]
                        
                        finalCapturedLabel = baseCapturedLabel
                        location = Feature().get_default_value().upper()
                        if location == "SEOUL" or location == "PENANG":
                            if location == "SEOUL":
                                match = re.search(r'^(.*?)\|', Label)
                                if match:
                                    Label = match.group(1).strip()
                            finalCapturedLabel = f'{Label}/{baseCapturedLabel}'
                        
                        tempRecord = f'{extractFile}/{finalCapturedLabel}'

                        padded_data = [row + [np.nan] * (len(headerLabel) - len(row)) for row in split_data]
                        df = pd.DataFrame(padded_data, columns=headerLabel)

                        with self.__lock:
                            self.__fileRecord[tempRecord] = df
                            b = len(self.__fileRecord)
                            self.Normalize = int(((b / self.__max_file_records) * (70 - 25)) + 25)
                    
                    # [OPTIMIZATION] Removed the success log per file
                    # self.logger.info(f"Successfully processed {file}.")

                except Exception as e:
                    self.logger.error(f"FAILED to process {file}: {e}", exc_info=True)
            
            with ThreadPoolExecutor(max_workers=os.cpu_count() * 5) as executor:
                executor.map(process_file, list(self.__dataFrame.keys()))

            self.logger.info("Parallel Dataprocessing finished.")

        except Exception as e:
            self.logger.critical(f"Dataprocessing Setup Error: {e}")
            raise ValueError(f"Dataprocessing Setup Error: {e}")

    def getNormalize(self):
        return self.Normalize

    def saveFile(self):
        self.logger.info("Starting parallel saveFile operation...")
        extractRegex = r'(.+)/(.+)/(.+)'
        self.count = 0
        
        if not self.__fileRecord:
            self.logger.warning("No files in __fileRecord to save. Skipping saveFile.")
            return
            
        total_records = len(self.__fileRecord)

        def process_item(key_items):
            key, items = key_items
            try:
                match = re.match(extractRegex, key)
                if not match:
                    raise ValueError(f"Key '{key}' does not match the expected pattern.")
    
                channel = match.group(2)
                fileLabel = match.group(3)
                
                dirPath = os.path.join(self.get_path, channel)
                os.makedirs(dirPath, exist_ok=True)
                tn_number = re.search(r'TN\d+', channel).group()
                # print(tn_number)
                filePath = os.path.join(dirPath, f"{fileLabel}-{tn_number}.csv")
                
                items.to_csv(filePath, index=False)

                with self.__lock:
                    self.count += 1
                    self.Normalize = int(((self.count / total_records) * (100 - 70)) + 70)
                    if self.Normalize >= 100:
                        self.DataProcessFlag = False
                        
                # [OPTIMIZATION] Removed per-file logging
                # self.logger.debug(f"Saved: {filePath}")

            except Exception as e:
                self.logger.error(f"SaveFile Error for key '{key}': {e}")

        with ThreadPoolExecutor(max_workers=os.cpu_count() * 5) as executor:
            executor.map(process_item, self.__fileRecord.items())
        
        self.logger.info(f"Finished saveFile. Saved {self.count} records.")

# ... (The main execution block below remains unchanged) ...
if __name__ == "__main__":
    
    # Ensure these paths are correct in your environment
    base_dir = r'C:\Users\ro898771\Documents\QuickMi2e'
    savepath = os.path.join(base_dir, r'dataset\results')
    datasrc = r'C:\Users\ro898771\Box\Buster 2did SKEW Trace\SamplingTesting-QuickMi2ce\tiger' # Source folder
    copysrc = os.path.join(base_dir, r'dataset\cntrace\zip')
    dest = os.path.join(base_dir, r'dataset\cntrace\trace') # Trace folder

    # Ensure output directories exist for the Directory module operations
    os.makedirs(savepath, exist_ok=True)
    os.makedirs(copysrc, exist_ok=True)
    os.makedirs(dest, exist_ok=True)

    try:
        start_time = time.time()
        dir = Directory()
        dir.delete_all_files_and_subfolders(copysrc)
        dir.delete_all_files_and_subfolders(dest)
        dir.delete_all_files_and_subfolders(savepath)
        dir.copy_file(datasrc) # Assuming copy_file handles zip/file copies
        dir.rename_and_unzip(copysrc, dest) # Assuming this extracts to dest
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Files Orientation Elapsed Time: {elapsed_time:.2f} seconds")

        start_time1 = time.time()
        obj = TigerOrCntrace()
        obj.set_path(dest, savepath)
        obj.Convert2DataFrame()
        end_time1 = time.time()
        elapsed_time1 = end_time1 - start_time1
        print(f"Convert2DataFrame Elapsed Time: {elapsed_time1:.2f} seconds")

        start_time2 = time.time()
        obj.MetaHeaderPos()
        end_time2 = time.time()
        elapsed_time2 = end_time2 - start_time2
        print(f"MetaHeaderPos Elapsed Time: {elapsed_time2:.2f} seconds")

        start_time3 = time.time()
        obj.Dataprocessing()
        end_time3 = time.time()
        elapsed_time3 = end_time3 - start_time3
        print(f"Dataprocessing Elapsed Time: {elapsed_time3:.2f} seconds")

        start_time4 = time.time()
        obj.saveFile()
        end_time4 = time.time()
        elapsed_time4 = end_time4 - start_time4
        print(f"SaveFile Elapsed Time: {elapsed_time4:.2f} seconds")

        totalTime = elapsed_time1 + elapsed_time2 + elapsed_time3 + elapsed_time4
        print(f"Total Processing Time: {totalTime:.2f} seconds, {totalTime/60:.2f} min")

    except Exception as final_e:
        # Catch any exceptions raised from inside the class methods
        print(f"\n[FATAL ERROR] The main process failed. Check 'output/Log/tigerorcntrace.log' for details. Error: {final_e}")