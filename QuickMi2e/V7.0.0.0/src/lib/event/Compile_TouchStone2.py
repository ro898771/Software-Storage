import os
import re
import pandas as pd
import numpy as np
from itertools import cycle
import math
import time
import concurrent.futures


# --- Custom Logger Import ---
from lib.helper.Logger import LoggerSetup 

class TouchStone:
    def __init__(self):
        # --- Initialize Logger ---
        self.logger = LoggerSetup(
            log_name='TouchStone compilation', 
            log_dir_relative_path=r"output\Log"
        ).get_logger()
        
        self.logger.info("Initializing TouchStone class...")
        
        self.start = None
        self.__srcPath = None
        self.__tempRecord = dict()

    def get_unique_list(self, data_list):
        output = []
        for x in data_list:
            if x not in output:
                output.append(x)
        return output

    def getTotalSparamTotalCol(self, filepath):
        try:
            total_ports = re.search(r's(\w)p', os.path.splitext(filepath)[1], re.IGNORECASE).group(1)
            if total_ports.isnumeric():
                # check if file extension carries number of ports data (".s2p", ."s3p" etc)
                total_sparam = int(total_ports) ** 2
                total_col = 2 * total_sparam + 1
                total_ports = int(total_ports)
            else:
                with open(filepath, 'r') as f:
                    # if file extension is ".snp" then read the last line of the snp file to determine number of columns
                    last_line = f.readlines()[-1].split()
                    total_col = len(last_line)
                    total_sparam = int((total_col - 1) / 2)
                    total_ports = int(math.sqrt(total_sparam))
            return total_ports, total_sparam, total_col
        except Exception as e:
            self.logger.error(f"Error determining S-param columns for {filepath}: {e}")
            raise

    def getFormatCol(self, header_fmt):
        header_fmt = header_fmt.upper()
        if header_fmt == 'DB':
            fmt = ['dB:', 'ang:']
        elif header_fmt == 'RI':
            fmt = ['Re:', 'Im:']
        elif header_fmt == 'MA':
            fmt = ['mag:', 'ang:']
        else:
            fmt = ['', '']
        return fmt

    def get_snp_header(self, file):
        # Get snp type from '#' option line in touchstone file
        try:
            with open(file, 'r') as lines:
                for line in lines:
                    if line[0] == '#':
                        parts = line.strip().split()
                        # Safety check for line length
                        if len(parts) >= 6:
                            _, header_hz, _, header_fmt, _, header_z0 = parts
                            return header_hz, header_fmt, header_z0
            
            # If loop finishes without returning
            return '', '', ''
        except Exception as e:
            self.logger.warning(f'Touchstone file headers not found for {os.path.basename(file)}: {e}')
            return '', '', ''

    def get_snp_sparam_old(self, file):
        # Generate S-Parameter Header by scanning touchstone files
        try:
            total_ports = re.search(r's(\w)p', os.path.splitext(file)[1], re.IGNORECASE).group(1)
            sparam = []
            with open(file, 'r') as lines:
                for line in lines:
                    if line[0] == '!':
                        if total_ports.isnumeric():
                            x = re.findall(r'S\d+(?:\_)?\d+', line)
                            if x != []:
                                sparam = sparam + x
                    x = re.search(r'^\!?freq\w*', line, re.I)
                
                    if x:
                        templine = line.strip().split()
                        if list(filter(lambda x: re.match(r'^\!?freq\w*$', x, re.I), templine)):
                            templine.pop(0)
                            sparam = templine

            sparam = [item.split(':')[0] for item in sparam]
            sparam = self.get_unique_list(sparam)
        
            return sparam
        except Exception as e:
            self.logger.error(f"Error extracting S-params from {file}: {e}")
            return []

    def get_snp_sparam(self, file):
        try:
            # Generate S-Parameter Header by scanning touchstone files
            total_ports = re.search(r's(\w)p', os.path.splitext(file)[1], re.IGNORECASE).group(1)
            sparam = []
            with open(file, 'r') as lines:
                for line in lines:
                    if line[0] == '!':
                        if total_ports.isnumeric():
                            x = re.findall(r'S\d+(?:\_)?\d+', line)
                            if x != []:
                                sparam = sparam + x
                    x = re.search(r'^\!?freq\w*', line, re.I)
                
                    if x:
                        templine = line.strip().split()
                        if list(filter(lambda x: re.match(r'^\!?freq\w*$', x, re.I), templine)):
                            templine.pop(0)
                        for line in templine: 
                            x = re.findall(r'(S\d+(?:\_)?\d+)',line)
                            if x != []:
                                sparam = sparam + x

            sparam = self.get_unique_list(sparam)
        
            return sparam

        except Exception as e:
            self.logger.error(f"Error extracting S-params from {file}: {e}")
            return []

    def generate_sparam(self, total_ports):
        sparam = []
        self.logger.warning('Unable to scan touchstone files for S-Parameter definition')
        print('Unable to scan touchstone files for S-Parameter definition')
        ports = input('Please key in port number separated by space (expected %d ports): ' % total_ports).split()
        ports = list(map(int, ports))
        ports.sort()
        sparam = []
        for i in ports:
            for j in ports:
                sp = 'S%d%d' % (i, j)
                sparam.append(sp)
        return sparam

    def reduce_mem_usage(self, df):
        start_mem = df.memory_usage().sum() / 1024 ** 3
        
        for col in df.select_dtypes(include=['number'], exclude=['datetime', 'timedelta']).columns:
            col_type = df[col].dtype

            if col_type != object and col_type.name != 'category':
                c_min = df[col].min()
                c_max = df[col].max()
                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                    elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                        df[col] = df[col].astype(np.int64)
                else:
                    if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                        df[col] = df[col].astype(np.float16)
                    elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        df[col] = df[col].astype(np.float32)
                    else:
                        df[col] = df[col].astype(np.float64)

        end_mem = df.memory_usage().sum() / 1024 ** 3
        # Logging reduction summary instead of printing per file
        # self.logger.debug('Memory optimization: {:.2f} MB -> {:.2f} MB'.format(start_mem, end_mem))

        return df

    def convertSNPdf(self, df, header_fmt):
        df_conv = pd.DataFrame()
        df_conv[df.columns[0]] = df[df.columns[0]]
        
        sparam = re.findall(r'S\d+(?:\_)?\d+', ' '.join(df.columns))
        if sparam != []:
            sparam = self.get_unique_list(sparam)

        if header_fmt == 'RI':
            for sp in sparam:
                df_conv['dB:' + sp] = 20 * np.log10(np.sqrt(df['Re:' + sp] ** 2 + df['Im:' + sp] ** 2))
                df_conv['ang:' + sp] = np.arctan2(df['Im:' + sp], df['Re:' + sp])
        else:
            for sp in sparam:
                df_conv['dB:' + sp] = df['dB:' + sp]
                df_conv['ang:' + sp] = df['ang:' + sp]
                
        return df_conv

    def getSNPdf(self, filepath):
        # Heavy processing function
        try:
            df = pd.DataFrame()
            header_hz, header_fmt, header_z0 = self.get_snp_header(filepath)
    
            if not header_hz:
                self.logger.debug(f'Using default "HZ"/"DB" for {os.path.basename(filepath)}')
                header_hz = 'HZ'
                header_fmt = 'DB'
                
            total_ports, total_sparam, total_col = self.getTotalSparamTotalCol(filepath)
            sparam = self.get_snp_sparam(filepath)

            if len(sparam) < total_sparam:
                # Fallback logic could go here, currently just passing
                pass

            if len(sparam) == total_sparam:
                col = [j for i in zip(sparam, sparam) for j in i]
                col = [i + j for i, j in zip(cycle(self.getFormatCol(header_fmt)), col)]
                col = ['freq[' + header_hz.upper() + ']'] + col

                output = []
                ls_freq = []
                
                # [PERFORMANCE] Reading loop - No logging here
                with open(filepath, 'r') as lines:
                    for line in lines:
                        if line[0] not in ['!', '#'] and line.split() != [] and not re.search(r'^\!?freq\w*', line, re.I):
                            if len(ls_freq) < len(col):
                                ls_freq = ls_freq + line.split()
                            if len(ls_freq) == len(col):
                                output.append(ls_freq)
                                ls_freq = []
        
                if output != []:
                    df = pd.DataFrame(output)
                    df = df.apply(pd.to_numeric)
                    df.loc[:, df.columns[(df == 0).all()]] = np.nan
                    try:
                        df.columns = col
                    except ValueError:
                        self.logger.error(
                            f'Unable to define columns for {filepath}. Check if S-parameters are defined in headers.'
                        )
                
                df = self.convertSNPdf(df, header_fmt)
                # df = self.reduce_mem_usage(df) # Optional optimization

            return df
        except Exception as e:
            self.logger.error(f"Failed to parse {filepath}: {e}")
            return pd.DataFrame() # Return empty DF on failure

    def setpath(self, srcPath, savePath):
        try:
            self.logger.info(f"Setting paths. Source: {srcPath}, Save: {savePath}")
            self.__savePath = savePath
            self.__srcPath = srcPath
        except Exception as e:
            self.logger.critical(f"setpath Error: {e}")
            raise ValueError(f"Error: {e}")

    def DataProcessing(self):
        self.logger.info("Starting DataProcessing...")
        try:
            regexPattern = re.compile(r'^(.*)\.(s\d+p)$', re.IGNORECASE)

            if not os.path.exists(self.__srcPath):
                 raise FileNotFoundError(f"Source path does not exist: {self.__srcPath}")

            joinPath = [
                os.path.join(self.__srcPath, p)
                for p in os.listdir(self.__srcPath)
                if regexPattern.match(p)
            ]

            self.logger.info(f"Found {len(joinPath)} Touchstone files to process.")

            if len(joinPath) == 0:
                raise ValueError(f"No SNP files were found in '{self.__srcPath}'.\nPlease Check your file Type selection//File Format")
            
            # [PERFORMANCE] Worker function - Logging skipped for success path
            def process_sample(sample):
                try:
                    match = re.match(regexPattern, os.path.basename(sample))
                    if match:
                        unitName = match.group(1)
                        # Heavy lifting happens here
                        df = self.getSNPdf(sample)
                        if not df.empty:
                            self.__tempRecord[os.path.basename(unitName)] = df
                except Exception as inner_e:
                    self.logger.error(f"Error processing file {sample}: {inner_e}")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(process_sample, joinPath)
            
            self.logger.info(f"DataProcessing complete. Loaded {len(self.__tempRecord)} records.")

        except Exception as e:
            self.logger.error(f"DataProcessing Error: {e}", exc_info=True)
            raise ValueError(f"Error: {e}")

    def saveData(self):
        self.logger.info("Starting saveData...")
        try:
            def save_item(key, item):
                try:
                    target_dir = os.path.join(self.__savePath, key)
                    os.makedirs(target_dir, exist_ok=True)
                    target_file = os.path.join(target_dir, f'{key}.csv')
                    item.to_csv(target_file, index=False)
                except Exception as inner_e:
                    self.logger.error(f"Failed to save {key}: {inner_e}")
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(lambda kv: save_item(*kv), self.__tempRecord.items())
            
            self.logger.info("saveData complete.")

        except Exception as e:
            self.logger.critical(f"saveData Error: {e}")
            raise ValueError(f"Error: {e}")


if __name__ == "__main__":
    start_time = time.time()
    
    # Define paths
    fileName = r"C:\Users\ro898771\Documents\85C" # This is treated as source path in original logic
    savePath = r"C:\Users\ro898771\Documents\QuickMi2e\dataset\results"
    
    try:
        Test1 = TouchStone()
        # Corrected usage: setpath takes (src, dest) based on class definition
        Test1.setpath(fileName, savePath)
        
        # Corrected usage: DataProcessing takes no args based on class definition
        Test1.DataProcessing() 
        
        Test1.saveData()

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Merged Completed!!\nElapsed Time: {elapsed_time:.2f}s")
    except Exception as e:
        print(f"Execution failed: {e}")