import os
import re
import pandas as pd
import numpy as np
from itertools import cycle
import math
import time
import concurrent.futures

class TouchStone:
    def __init__(self):
        self.start=None
        self.__srcPath=None
        self.__tempRecord=dict()

    def get_unique_list(self, data_list):
        output = []
        for x in data_list:
            if x not in output:
                output.append(x)
        return output

    def getTotalSparamTotalCol(self, filepath):
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
        with open(file, 'r') as lines:
            for line in lines:
                if line[0] == '#':
                    _, header_hz, _, header_fmt, _, header_z0 = line.strip().split()
        try:
            return header_hz, header_fmt, header_z0
        except NameError:
            print('Touchstone file headers not found.')
            return '', '', ''

    def get_snp_sparam(self, file):

        # Generate S-Parameter Header by scanning touchstone files
        total_ports = re.search(r's(\w)p',os.path.splitext(file)[1],re.IGNORECASE).group(1)
        sparam = []
        with open(file, 'r') as lines:
            for line in lines:
                if line[0] == '!':
                    if total_ports.isnumeric():
                        x = re.findall(r'(S\d+(?:\_)?\d+)',line)
                        if x != []:
                            sparam = sparam + x
                x = re.search(r'^\!?freq\w*', line, re.I)
                if x: 
                    sparam = []
                    templine = line.strip().split()
                    if list(filter(lambda x: re.match(r'^\!?freq\w*$', x, re.I), templine)):
                        templine.pop(0)
                    for line in templine: 
                        x = re.findall(r'(S\d+(?:\_)?\d+)',line)
                        if x != []:
                            sparam = sparam + x
        sparam = self.get_unique_list(sparam)
        return sparam

    def generate_sparam(self, total_ports):
        sparam = []
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
        # print('Memory usage of dataframe is {:.2f} MB'.format(start_mem))

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
        print('Memory usage after optimization is: {:.2f} MB'.format(end_mem))
        print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem)/ start_mem))

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
                df_conv['ang:' + sp] = np.arctan(df['Im:' + sp] / df['Re:' + sp])
                 
        elif header_fmt == 'MA':
            # Undeveloped yet
            for sp in sparam:
                df_conv['dB:' + sp] = 20 * np.log10(np.sqrt(df['Re:' + sp] ** 2 + df['Im:' + sp] ** 2))
                df_conv['ang:' + sp] = np.arctan(df['Im:' + sp] / df['Re:' + sp])
                               
        else:
            for sp in sparam:
                df_conv['dB:' + sp] = df['dB:' + sp]
                df_conv['ang:' + sp] = df['ang:' + sp]
                
        return df_conv

    def getSNPdf(self, filepath):
        df = pd.DataFrame()
        header_hz, header_fmt, header_z0 = self.get_snp_header(filepath)
  
        if not header_hz:
            print('Using "HZ" for frequency unit. "DB" for touchstone format.')
            header_hz = 'HZ'
            header_fmt = 'DB'
        total_ports, total_sparam, total_col = self.getTotalSparamTotalCol(filepath)
        sparam = self.get_snp_sparam(filepath)


        if len(sparam) < total_sparam:
            print(f"Warning: Found {len(sparam)} S-parameters but expected {total_sparam}")
            # sparam = self.generate_sparam(total_ports)

        if len(sparam) == total_sparam or len(sparam) > 0:
            # print('S-Parameters:',sparam)
            col = [j for i in zip(sparam, sparam) for j in i]
            col = [i + j for i, j in zip(cycle(self.getFormatCol(header_fmt)), col)]
            col = ['freq[' + header_hz.upper() + ']'] + col

            output = []
            ls_freq = []
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
                except NameError:
                    print(
                        'Unable to define column, '
                        'check snp file if S-parameters are defined in headers (starting with "!")')
            df = self.convertSNPdf(df, header_fmt)
            # df = self.reduce_mem_usage(df)
        return df
    
    def setpath(self,srcPath,savePath):
        try:
            self.__savePath= savePath
            self.__srcPath= srcPath

        except Exception as e:
            raise ValueError(f"Error: {e}")

    def DataProcessing(self):
        try:
            regexPattern = r'^(.*)\.(s\d+p)$'
            joinPath = [os.path.join(self.__srcPath, p) for p in os.listdir(self.__srcPath) if re.match(regexPattern, p)]

            if len(joinPath) == 0:
                raise ValueError(f"No files were found in '{self.__srcPath}'.")
            
            def process_sample(sample):
                match = re.match(regexPattern, sample)
                if match:
                    unitName = match.group(1)
                    self.__tempRecord[os.path.basename(unitName)] = self.getSNPdf(sample)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(process_sample, joinPath)

        except Exception as e:
            raise ValueError(f"Error: {e}")

    def saveData(self):
        try:
            def save_item(key, item):
                os.makedirs(r'{path}/{Label}'.format(path=self.__savePath, Label=key), exist_ok=True)
                item.to_csv(r'{path}/{Label}/{Label}.csv'.format(path=self.__savePath, Label=key), index=False)
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(lambda kv: save_item(*kv), self.__tempRecord.items())

        except Exception as e:
            raise ValueError(f"Error: {e}")


if __name__ == "__main__":
    start_time = time.time()
    fileName = r"C:\Users\ro898771\Documents\85C"
    savePath = r"C:\Users\ro898771\Documents\QuickMi2e\dataset\results"
    
    Test1 = TouchStone()
    Test1.setpath(savePath)
    Test1.DataProcessing(fileName)
    Test1.saveData()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Merged Completed!!\nElapsed Time: {elapsed_time}")


