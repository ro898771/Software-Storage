"""TCF batch file generation module."""

import os
import re
from datetime import datetime

import pandas as pd

from lib.helper.Logger import LoggerSetup


class Genbatch:
    """Generate batch files from TCF (Test Configuration File) data."""

    def __init__(self, file_path, progress_callback=None):
        """
        Initialize Genbatch with TCF file path.

        Args:
            file_path: Path to the TCF file
            progress_callback: Optional callback function for progress updates

        Raises:
            ValueError: If file path is invalid or file not found
        """
        # Initialize Logger
        self.logger = LoggerSetup(
            log_name='TCFBatch',
            log_dir_relative_path=r"output\Log"
        ).get_logger()

        self.logger.info("Initializing Genbatch class...")
        self.progress_callback = progress_callback

        try:
            if file_path:
                self.path = file_path
                self.result_path = os.path.join(
                    os.getcwd(), 'dataset', 'results'
                )
                # Safety check for file existence
                if not os.path.exists(self.path):
                    raise FileNotFoundError(
                        f"Input file not found: {self.path}"
                    )

                self.file_name = (
                    os.path.basename(self.path).split('_')[0].split('-')[0]
                )
                self.logger.info(f"Target File: {self.file_name}")
                self.logger.info(f"Results Directory: {self.result_path}")
            else:
                self.logger.error("No TCF file path provided.")
                raise ValueError("No TCF file is found!")

        except Exception as e:
            self.logger.critical(f"Initialization Failed: {e}")
            raise ValueError(f"{e}")

    def get_range(self):
        """
        Extract TN ranges and parameters from TCF file.

        Returns:
            Tuple of (result_dict, dataframe) containing TN ranges and
            filtered parameters
        """
        self.logger.info("Starting get_range operation...")
        if self.progress_callback:
            self.progress_callback("Extracting TN ranges from TCF...", 10)
        try:
            # Pattern for Seoul format
            pattern = re.compile(r'(TN)(\d+)')
            raw_results = []

            # First collect all results
            if not os.path.exists(self.result_path):
                raise FileNotFoundError(
                    f"Result directory does not exist: {self.result_path}"
                )

            sample = os.listdir(self.result_path)
            self.logger.info(
                f"Scanning {len(sample)} files in result directory."
            )

            for x in sample:
                match = pattern.search(x)
                if match:
                    # Convert to integer for easier processing
                    item2 = int(match.group(2))
                    raw_results.append((x, item2))

            # Sort results by TN number
            raw_results.sort(key=lambda x: x[1])

            # Create dictionary with filename as key and TN number pairs
            result_dict = {}
            for i, (filename, tn_num) in enumerate(raw_results):
                if i < len(raw_results) - 1:
                    # For all entries except the last one, include current
                    # and next TN number
                    next_tn = raw_results[i + 1][1]
                    result_dict[filename] = [tn_num, next_tn]
                else:
                    # For the last entry, include only its own TN number
                    result_dict[filename] = [tn_num]

            focus_header = [
                '#Start', 'Test Parameter', 'N-Parameter-Class',
                'S-Parameter', 'BAND', 'Power_Mode', 'Switch_ANT',
                'Switch_In', 'Switch_Out', 'Channel Number',
                'Absolute Value', 'Non_Inverted', 'Search_Method',
                'Start_Freq', 'Stop_Freq'
            ]

            self.logger.info(
                f"Reading Excel file: {self.path} (Sheet: Condition_FBAR)"
            )
            if self.progress_callback:
                self.progress_callback("Reading Excel file...", 30)
            df = pd.read_excel(
                self.path, sheet_name="Condition_FBAR",
                index_col=False, header=1
            )[focus_header]

            df = df[df["Test Parameter"].isin(["MAG_AT", "MAG_BETWEEN"])]

            # Remove spaces from frequency columns (e.g., "500 M" -> "500M")
            if 'Start_Freq' in df.columns:
                df['Start_Freq'] = df['Start_Freq'].astype(str).str.replace(' ', '', regex=False)
                df['Start_Freq'] = df['Start_Freq'].replace('nan', None)
            if 'Stop_Freq' in df.columns:
                df['Stop_Freq'] = df['Stop_Freq'].astype(str).str.replace(' ', '', regex=False)
                df['Stop_Freq'] = df['Stop_Freq'].replace('nan', None)

            df['#Start'] = pd.to_numeric(df['#Start'], errors='coerce')
            df['Channel Number'] = pd.to_numeric(
                df['Channel Number'], errors='coerce'
            )

            df = df.dropna(subset=['#Start', 'Channel Number', 'S-Parameter'])
            df = df[df['#Start'] != 'x']

            df['#Start'] = df['#Start'].astype(int)
            df['Channel Number'] = df['Channel Number'].astype(int)

            # Process each TN range
            for key, value in result_dict.items():
                if len(value) == 2:
                    filtered_df = df[
                        (df['#Start'] >= value[0]) &
                        (df['#Start'] <= value[1])
                    ]
                else:
                    filtered_df = df[(df['#Start'] >= value[0])]

                sample = filtered_df["BAND"].unique()
                ch = filtered_df["Channel Number"].unique().tolist()

                result_dict[key] = [value, list(sample), ch]

            self.logger.info("get_range operation completed successfully.")
            if self.progress_callback:
                self.progress_callback("TN range extraction completed", 50)
            return result_dict, df

        except Exception as e:
            self.logger.error(f"Error in get_range: {e}", exc_info=True)
            print(e)
            return {}, pd.DataFrame()  # Return safe empty objects on failure

    def processing(self, TCFConfig):
        self.logger.info("Starting Batch Processing...")
        if self.progress_callback:
            self.progress_callback("Starting batch processing...", 5)
        try:
            items, df = self.get_range()
            
            if not items or df.empty:
                self.logger.warning("getRange returned empty data. Aborting processing.")
                raise ValueError("No data found to process.")

            all_results = []

            filterHeader = [
            'Group Name',
            'Enb Scrip',
            'Filtered Folder',
            '# Num Plot',
            '# Pos Location',
            'X-Step',
            'Y-Step',
            'User_StartFreq',
            'User_StopFreq',
            'Plot Title',
            'S-Parameter',
            'Channel Number',
            'Switch_ANT',
            'Switch_In',
            'Switch_Out',
            'BAND',
            'Power_Mode',
            'N-Parameter-Class',
            'Absolute Value',
            'Non_Inverted',
            'Search_Method',
            'Start_Freq',
            'Stop_Freq',
            'TN'
            ]

            df = df[df['S-Parameter'].str.contains(r'S(?:\d+)', regex=True)]

            self.logger.info(f"Processing {len(items)} file groups...")
            if self.progress_callback:
                self.progress_callback(f"Processing {len(items)} file groups...", 55)

            # [PERFORMANCE] Main data processing loop - Logging skipped here
            total_items = len(items)
            for idx, (key, value) in enumerate(items.items()):
                df["Filtered Folder"] = key
                for band in value[1]:
                    
                    if len(value[0]) == 2:
                        filtered_df = df[(df['#Start'] >= value[0][0]) & 
                        (df['#Start'] <= value[0][1]) & 
                        (df['BAND'] == band)     
                        ]    
                    else:
                        filtered_df = df[(df['#Start'] >= value[0][0]) & 
                        
                                    (df['BAND'] == band)                                     
                                            ]
                    filtered_df = filtered_df.copy()
                    
                    # Get the rows that will be kept (first occurrences without N-Parameter-Class)
                    kept_df = filtered_df.drop_duplicates(subset=['Channel Number','Switch_ANT','Switch_Out',
                                                                'Switch_In','Power_Mode','S-Parameter'], keep='first')
                    kept_df['is_first'] = True
                    
                    # Get the rows that were dropped (duplicates when NOT considering N-Parameter-Class)
                    # But keep them if they have different N-Parameter-Class
                    mask = filtered_df.duplicated(subset=['Channel Number','Switch_ANT','Switch_Out',
                                                          'Switch_In','Power_Mode','S-Parameter'], keep='first')
                    additional_df = filtered_df[mask].copy()
                    additional_df['is_first'] = False
                    
                    # Combine both: original kept rows + additional rows with different N-Parameter-Class
                    combined_df = pd.concat([kept_df, additional_df], ignore_index=True)
                    all_results.append(combined_df)
                
                # Update progress during processing
                if self.progress_callback and total_items > 0:
                    progress = 55 + int((idx + 1) / total_items * 25)  # 55% to 80%
                    self.progress_callback(f"Processing group {idx + 1}/{total_items}...", progress)
            
            if not all_results:
                 raise ValueError("No matching results found after filtering.")

            combined_results = pd.concat(all_results, ignore_index=True)
            
            if self.progress_callback:
                self.progress_callback("Applying filters and formatting...", 82)

            combined_results["Folder_CH_Num"] = (
                combined_results["Filtered Folder"]
                .astype(str)
                .str.extract(r"CH(\d+)")[0]  # capture only digits after CH
                .astype(float)               # float so NaN is allowed
            )

            combined_results = combined_results[combined_results["Folder_CH_Num"].isna() | (combined_results["Folder_CH_Num"] == combined_results["Channel Number"])]

            # Drop helper column
            combined_results = combined_results.drop(columns=["Folder_CH_Num"])
            
            # Set "Enb Scrip" based on whether it's the first occurrence (considering N-Parameter-Class)
            combined_results["Enb Scrip"] = combined_results["is_first"].apply(lambda x: "v" if x else "")
            combined_results = combined_results.drop(columns=["is_first"])

            # [PERFORMANCE] Lambda application - Logging skipped
            combined_results["Group Name"] = combined_results.apply(
                lambda row: f"CH{row['Channel Number']}_{row['BAND']}_{row['Power_Mode']}_{row['Switch_ANT']}_{'' if pd.isna(row['Switch_In']) else row['Switch_In']}_{'' if pd.isna(row['Switch_Out']) else row['Switch_Out']}",
                axis=1
            )

            # Initialize a dictionary to keep track of counts for each group
            if TCFConfig:
                # combined_results['Group Name'] = combined_results['Group Name'] + '#1'
                combined_results['suffix'] = combined_results.groupby('Group Name').cumcount() // 4 + 1
                combined_results['Group Name'] = combined_results['Group Name'] + '#' + combined_results['suffix'].astype(str)

                folder_counts = {}
                
                
                # Pos Location
                for index, row in combined_results.iterrows():
                    folder = row['Group Name']
                    if folder not in folder_counts:
                        folder_counts[folder] = 0
                    folder_counts[folder] += 1
                    combined_results.at[index, '# Pos Location'] = (folder_counts[folder] - 1) % 4 + 1

                max_counts = {}

                # Num Plot
                for index, row in combined_results.iterrows():
                    folder = row['Filtered Folder']
                    count = int(row['Group Name'].split('#')[-1])
                    if folder not in max_counts or count > max_counts[folder]:
                        max_counts[folder] = count

                combined_results['# Num Plot'] = 4

            else:
                group_counts = {}
                # Group Name
                for index, row in combined_results.iterrows():
                    group_name = row['Group Name']
                    if group_name not in group_counts:
                        group_counts[group_name] = 0
                    group_counts[group_name] += 1
                    combined_results.at[index, 'Group Name'] = f"{group_name}#{group_counts[group_name]}"


                # Create the new column based on the highest integer found
                combined_results['# Num Plot'] = 1
                combined_results['# Pos Location'] = 1

            
            # Create Plot Title with dynamic handling for None or nan values
            combined_results["Plot Title"] = combined_results.apply(
                lambda row: f"S[{row['S-Parameter']}]BAND[{row['BAND']}]PWR[{row['Power_Mode']}]ANT[{row['Switch_ANT']}]IN[{'' if pd.isna(row['Switch_In']) else row['Switch_In']}]OUT[{'' if pd.isna(row['Switch_Out']) else row['Switch_Out']}]",
                axis=1
            )

            combined_results['Plot Title'] = combined_results['Plot Title']+ "-" +"TN["+combined_results['Filtered Folder'].str.extract(r'TN(\d+)', expand=False)+"]"+"CH["+combined_results['Filtered Folder'].str.extract(r'CH(\d+)', expand=False)+"]"


            # Initialize X-Step and Y-Step columns with empty values for user input
            combined_results['X-Step'] = ''
            combined_results['Y-Step'] = ''
            
            # Initialize User_StartFreq and User_StopFreq columns with empty values for user input
            combined_results['User_StartFreq'] = ''
            combined_results['User_StopFreq'] = ''
            
            # Move the specified columns to match the required sequence
            # Exact column order as specified
            cols = [
                'Group Name', 'Enb Scrip', 'Filtered Folder', '# Num Plot', '# Pos Location', 
                'X-Step', 'Y-Step', 'User_StartFreq', 'User_StopFreq', 'Plot Title', 
                'S-Parameter', 'Channel Number', 'Switch_ANT', 'Switch_In', 'Switch_Out', 
                'BAND', 'Power_Mode', 'N-Parameter-Class', 'Absolute Value', 'Non_Inverted', 
                'Search_Method', 'Start_Freq', 'Stop_Freq'
            ]
            # Add any remaining columns that might exist but weren't specified
            remaining_cols = [col for col in combined_results.columns if col not in cols]
            cols = cols + remaining_cols
            combined_results = combined_results[cols]

            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            combined_results["TN"]=combined_results['Filtered Folder'].str.extract(r'(TN\d+)', expand=False)

            # Update the 'Channel Number' column
            combined_results['Channel Number'] = 'CH' + combined_results['Channel Number'].astype(str)
            
            if self.progress_callback:
                self.progress_callback("Finalizing batch file...", 90)

            if combined_results["Filtered Folder"].empty:
                raise ValueError("No Filtered Folder is found! Please Check your TCF file format.")

            # Final deduplication: Remove duplicates based on all key parameters including frequencies
            combined_results = combined_results.drop_duplicates(
                subset=['S-Parameter', 'Channel Number', 'Switch_ANT', 'Switch_In', 'Switch_Out', 
                        'BAND', 'Power_Mode', 'N-Parameter-Class', 'Start_Freq', 'Stop_Freq', 'TN'], 
                keep='first'
            )

            combined_results = combined_results[combined_results['Enb Scrip'] == 'v']


            self.logger.info(f"Final output contains {len(combined_results)} unique rows after deduplication.")

            if self.file_name:
                save_path = r"{path}\setting\CFG\Batch\{file}_{time}.csv".format(time=now,path=os.getcwd(),file=self.file_name)
            else:
                save_path = r"{path}\setting\CFG\Batch\Module_{time}.csv".format(time=now,path=os.getcwd())
                
            
            combined_results[filterHeader].to_csv(save_path, index=False)
            self.logger.info(f"Batch file generated successfully at: {save_path}")
            
            if self.progress_callback:
                self.progress_callback("Batch file generated successfully!", 100)

        except Exception as e: 
            self.logger.error(f"Error in processing the TCF file: {e}", exc_info=True)
            raise ValueError(f"Error in processing the TCF file! Please check the file format.\n{e}")

if __name__ == "__main__":
    buster= r'C:\Users\ro898771\Documents\QuickMi2e\setting\CFG\TCF\Buster-ENGR-8268-AP1-RF2EVAL_TCF_P2A_A4B_rev002.xlsx'
    dugout= r'C:\Users\ro898771\Documents\QuickMi2e\setting\CFG\TCF\Dugout-ENGR-8266-AP1-RF2_B1A_TCF_Rev0005c.xlsx'
    
    # Simple try-except in main to catch initialization errors before the object is created
    try:
        test = Genbatch(buster)
        test.processing(False)
    except Exception as e:
        print(f"Execution failed: {e}")