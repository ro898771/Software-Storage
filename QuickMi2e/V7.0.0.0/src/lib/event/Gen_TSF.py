"""TSF (Test Specification File) generation module."""

import os
import re

import pandas as pd


class TSFGen:
    """Generate TSF spec line files from TSF and trace data."""

    def __init__(self, tsf_path, trace_path, progress_callback=None):
        """
        Initialize TSFGen with TSF and trace file paths.

        Args:
            tsf_path: Path to the TSF file
            trace_path: Path to the trace file
            progress_callback: Optional callback function for progress updates
        """
        self.tsf_path = tsf_path
        self.progress_callback = progress_callback
        print(trace_path)
        
        if self.progress_callback:
            self.progress_callback("Loading TSF and trace files...", 5)

        self.tsf_df = pd.read_csv(tsf_path)
        self.dataframe2 = pd.read_csv(trace_path)
        
        if self.progress_callback:
            self.progress_callback("Files loaded successfully", 10)

    def find_row_position(self, value):
        first_column = self.tsf_df.iloc[:, 0]
        row_index = first_column[first_column == value].index
        return row_index[0] if len(row_index) > 0 else None

    def find_column_and_neighbors(self, df, column_header):
        column_position = df.columns.get_loc(column_header)
        if column_position < len(df.columns) - 1:
            column_values = df.iloc[:, column_position]
            next_column_values = df.iloc[:, column_position + 1]
            return column_values, next_column_values, column_position
        else:
            return None, None, column_position

    def extract_frequencies(self, param):
        if isinstance(param, str):
            # Match both the numeric value and the unit, excluding 'Hz'
            # freqs = re.findall(r'(\d+)([a-zA-Z])Hz', param)
            freqs = re.findall(r'(\d+(?:\.\d+)?)([a-zA-Z])Hz', param)

            multiplier = {'M': 1e6, 'G': 1e9}
            if len(freqs) == 2:
                # Convert frequencies based on their units to numeric values
                freq_values = [float(freq[0]) * multiplier[freq[1]] for freq in freqs]
                start, stop = sorted(freq_values)
                return (start, stop)
            elif len(freqs) == 1:
                # Only one frequency found - put it in StartFreq, leave StopFreq blank
                freq_value = float(freqs[0][0]) * multiplier[freqs[0][1]]
                return (freq_value, None)
        return [None, None]

    def process_data(self, value_to_find, header_to_find):
        row_position = self.find_row_position(value_to_find)

        if row_position is not None:
            # Capture DataFrame starting from row_position onward and set row_position as header
            new_df = self.tsf_df.iloc[row_position:].reset_index(drop=True)
            new_df.columns = new_df.iloc[0]
            new_df = new_df[1:].reset_index(drop=True)
            
            new_df2 = self.tsf_df.iloc[row_position-1:].reset_index(drop=True)
            new_df2.columns = new_df2.iloc[0]
            new_df2 = new_df2[1:].reset_index(drop=True)

            # Find the column position and get its values along with the next column
            col_values, next_col_values, col_position = self.find_column_and_neighbors(new_df2, header_to_find)

            if col_values is not None and next_col_values is not None:
                result_df = pd.DataFrame({header_to_find: col_values, new_df2.columns[col_position + 1]: next_col_values})
                result_df.columns = result_df.iloc[0]
                result_df = result_df[1:].reset_index(drop=True)

                joined_df = pd.concat([new_df["TestParameter"], result_df], axis=1)
                joined_df = joined_df[joined_df['TestParameter'].str.contains('F_', na=True)].reset_index(drop=True)
                return joined_df
            else:
                return None
        else:
            print(f'The value "{value_to_find}" is not found in the first column.')
            return None


    def find_matches(self, column1_value, search_rows, dataframe2):
        column1_value = str(column1_value)
        matches = []
        for i, search_values in enumerate(search_rows):
            # Check if all non-empty values in the search row are substrings in the column1_value
            if all(str(value) in column1_value for value in search_values if pd.notna(value) and value != ''):
                matches.append(i)  # Store the index instead of the folder name
           
        return matches

    def process_and_save_results(self, triggerSwapFlag=False):
        try:
            if self.progress_callback:
                self.progress_callback("Processing TSF data...", 15)
            
            result = self.process_data('TestNumber', '1')

            if result is None:
                return

            # Process S-Parameter column from TestParameter
            if self.progress_callback:
                self.progress_callback("Extracting S-Parameters...", 30)
            
            original_s_param = result['TestParameter'].str.extract(r'(S\d+)')
            result['S-Parameter'] = original_s_param + "_Mag"
            result = result[result["S-Parameter"].notna()]
            result = result[~result['TestParameter'].str.contains(r'(KFAC|F_NF)', na=False)]
            result = result[~result['TestParameter'].str.contains(r'F_F(\d+)', na=False)]
            result = result[result['TestParameter'].str.contains('Hz', case=False, na=True)].reset_index(drop=True)
            result[['StartFreq', 'StopFreq']] = result['TestParameter'].apply(lambda x: pd.Series(self.extract_frequencies(x)))

            # Ensure Min and Max columns are float type
            result['Min'] = result['Min'].astype(float)
            result['Max'] = result['Max'].astype(float)
            
            minRemove=result['Min'].min()
            maxRemove=result['Max'].max()

            # Replace extreme values with None
            result['Min'] = result['Min'].replace(minRemove, None)
            result['Max'] = result['Max'].replace(maxRemove, None)

            # Store the original S-Parameter back for matching
            result['Original_S_Parameter'] = original_s_param

            # Select relevant columns
            if self.progress_callback:
                self.progress_callback("Processing Min/Max values...", 45)
            
            self.dataframe2 = self.dataframe2[[
                "Filtered Folder", "S-Parameter", "Channel Number", "Switch_ANT",
                "Switch_In", "Switch_Out", "Power_Mode", "BAND", "N-Parameter-Class", 
                "Absolute Value", "Non_Inverted", "Search_Method", "Start_Freq", "Stop_Freq"
            ]]

            # Convert to DataFrame
            previous_table = pd.DataFrame(result.drop(columns=['Original_S_Parameter']))
            new_table = pd.DataFrame(self.dataframe2)

            # Get column headers for matching - only include parameters that are in TestParameter string
            # Exclude: Filtered Folder, N-Parameter-Class, Absolute Value, Non_Inverted, Search_Method (these are metadata, not in TestParameter)
            # Include: Start_Freq, Stop_Freq (these are string values that should be in TestParameter)
            mapping_keys = [col for col in new_table.columns 
                          if col not in ["Filtered Folder", "N-Parameter-Class", "Absolute Value", "Non_Inverted", "Search_Method"]]

            # Initialize new columns
            new_table["Matched TestParameter"] = None
            new_table["Valid_Mapping_Count"] = 0  # Track valid mapping keys

            if self.progress_callback:
                self.progress_callback("Matching test parameters...", 60)

            # Iterate over new_table rows and count non-empty mapping keys
            total_rows = len(new_table.index)
            for row_idx, i in enumerate(new_table.index):
                valid_keys = [key for key in mapping_keys if pd.notna(new_table.loc[i, key])]  # ✅ Only non-empty keys
                new_table.loc[i, "Valid_Mapping_Count"] = len(valid_keys)  # ✅ Store count
                
                # Get the N-Parameter-Class and Search_Method from new_table
                n_param_class = new_table.loc[i, "N-Parameter-Class"]
                search_method = new_table.loc[i, "Search_Method"]
                
                # Find matching TestParameter only if there are valid keys
                for test_param in previous_table["TestParameter"]:
                    # Check if all valid keys match AND N-Parameter-Class AND Search_Method are in TestParameter
                    # Start_Freq and Stop_Freq are now treated as strings and matched like other parameters
                    keys_match = all(str(new_table.loc[i, key]) in test_param for key in valid_keys)
                    n_param_match = pd.notna(n_param_class) and str(n_param_class) in test_param
                    search_method_match = pd.notna(search_method) and str(search_method) in test_param
                    
                    if keys_match and n_param_match and search_method_match:
                        new_table.loc[i, "Matched TestParameter"] = test_param
                        break  # Stop after finding the first match
                
                # Update progress during matching
                if self.progress_callback and total_rows > 0 and row_idx % 10 == 0:
                    progress = 60 + int((row_idx + 1) / total_rows * 20)  # 60% to 80%
                    self.progress_callback(f"Matching row {row_idx + 1}/{total_rows}...", progress)

            # Display results
            # print(new_table[["Matched TestParameter", "Valid_Mapping_Count"]])
            # print(new_table)

            # Check for unmapped rows and print details
            unmapped_rows = new_table[new_table["Matched TestParameter"].isna()]
            if not unmapped_rows.empty:
                print("\n" + "="*80)
                print(f"WARNING: {len(unmapped_rows)} row(s) failed to map to TestParameter!")
                print("="*80)
                
                for idx in unmapped_rows.index:
                    print(f"\n--- Unmapped Row {idx + 1} ---")
                    print(f"Filtered Folder: {new_table.loc[idx, 'Filtered Folder']}")
                    
                    # Show all the parameters that were being searched for
                    print("\nParameters from trace file:")
                    for key in mapping_keys:
                        value = new_table.loc[idx, key]
                        if pd.notna(value):
                            print(f"  - {key}: '{value}'")
                    
                    # Show metadata parameters
                    n_param = new_table.loc[idx, "N-Parameter-Class"]
                    search_method = new_table.loc[idx, "Search_Method"]
                    if pd.notna(n_param):
                        print(f"  - N-Parameter-Class: '{n_param}'")
                    if pd.notna(search_method):
                        print(f"  - Search_Method: '{search_method}'")
                    
                    print("\nPossible reasons for mismatch:")
                    print("  1. No TestParameter contains ALL of the above values")
                    print("  2. TestParameter format in TSF file doesn't match expected pattern")
                    print("  3. Frequency values (Start_Freq/Stop_Freq) don't match any TestParameter")
                    print("  4. N-Parameter-Class or Search_Method not found in TestParameter")
                
                print("\n" + "="*80)
                print(f"Available TestParameters in TSF (first 10):")
                print("="*80)
                for i, test_param in enumerate(previous_table["TestParameter"].head(10)):
                    print(f"  {i+1}. {test_param}")
                if len(previous_table) > 10:
                    print(f"  ... and {len(previous_table) - 10} more")
                print("="*80 + "\n")

            if self.progress_callback:
                self.progress_callback("Merging tables...", 82)

            # Merge tables based on matched TestParameter
            merged_df = new_table.merge(previous_table, left_on="Matched TestParameter", right_on="TestParameter", how="left")
            # merged_df=merged_df.drop(columns=['Matched TestParameter'])
            merged_df['Enable']='v'
            merged_df = merged_df[[
                "Enable",
                # 'Matched TestParameter',
                "TestParameter",
                "Filtered Folder",    
                "S-Parameter_x", 
                "Channel Number",
                "Switch_ANT",
                "Switch_In",
                "Switch_Out",
                "Power_Mode",
                "BAND" ,
                "N-Parameter-Class",
                "Absolute Value",
                "Non_Inverted",
                "Search_Method",
                "StartFreq",
                "StopFreq",
                "Min",
                "Max"      
            ]]

            merged_df = merged_df.rename(columns={"S-Parameter_x": "S-Parameter", "Filtered Folder": "Channel Group"})
            merged_df['S-Parameter'] = merged_df['S-Parameter'] +"_Mag"

            if self.progress_callback:
                self.progress_callback("Applying final formatting...", 90)

            # Apply triggerSwapFlag logic if enabled
            if triggerSwapFlag:
                # Identify rows where (Absolute Value == "v") OR (Non_Inverted is blank/not "v")
                condition = (merged_df['Absolute Value'] == 'v') | (merged_df['Non_Inverted'] != 'v')
                
                # For rows meeting the condition:
                # 1. Multiply Min and Max by -1
                # 2. Swap Min and Max values
                for idx in merged_df[condition].index:
                    min_val = merged_df.at[idx, 'Min']
                    max_val = merged_df.at[idx, 'Max']
                    
                    # Only process if values are not None/NaN
                    if pd.notna(min_val) and pd.notna(max_val):
                        # Multiply by -1 and swap
                        merged_df.at[idx, 'Min'] = max_val * -1
                        merged_df.at[idx, 'Max'] = min_val * -1

            merged_df.to_csv(r"{path}\setting\CFG\SpecLine\SpecLine.csv".format(path=os.getcwd()),index=False)
            # print(merged_df)
            
            if self.progress_callback:
                self.progress_callback("SpecLine file generated successfully!", 100)

        except Exception as e:
            print(f"Error in process_and_save_results: {e}")

if __name__ == "__main__":
    
    # Example usage
    tsf_path = r'C:\Users\ro898771\Documents\QuickMi2e\setting\CFG\TSF\Dugout-AFEM-8266-AP1-RF2_B1A_PROD_TSF_Rev003.csv'
    trace_path = r'C:\Users\ro898771\Documents\QuickMi2e\setting\CFG\Batch\Dugout_20250509_213346.csv'
    processor = TSFGen(tsf_path, trace_path)
    processor.process_and_save_results()
