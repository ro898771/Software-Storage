import pandas as pd
import os
import re
from collections import defaultdict # Import defaultdict

class extractLotData:
    def __init__(self, base_dir=r'dataset/results'):
        self.base_dir = base_dir

    def extract_lot_dataframe(self):
        # Handle both absolute and relative paths correctly
        if os.path.isabs(self.base_dir):
            base_path = self.base_dir
        else:
            base_path = os.path.join(os.getcwd(), self.base_dir)
        
        # This is the new dynamic pattern we discussed.
        # _?            - Matches an optional leading underscore (and doesn't capture it)
        # ([A-Za-z0-9]+) - Capture Group 1: The key (letters/numbers only)
        # \[            - A literal opening bracket
        # ([^\]]*)      - Capture Group 2: The value (anything not a closing bracket)
        # \]            - A literal closing bracket
        dynamic_pattern = r'_?([A-Za-z0-9]+)\[([^\]]*)\]'

        # Use a defaultdict to automatically create a new set for any new key
        key_value_sets = defaultdict(set)

        # Walk through all subfolders and files
        for dirpath, _, filenames in os.walk(base_path):
            for file in filenames:
                
                # Use re.findall to get all key-value pairs
                pairs = re.findall(dynamic_pattern, file)
                
                # If 'pairs' is not empty, the file matched our format
                if pairs:
                    # Convert the list of (key, value) tuples into a dictionary
                    header_data = dict(pairs)
                    
                    # --- NEW LOGIC ---
                    # Instead of just getting 'LOT', add all keys and values
                    for key, value in header_data.items():
                        if value: # Only add if the value is not empty (e.g. from 'KEY[]')
                            key_value_sets[key].add(value)
                
                # else:
                    # The file (e.g., "README.txt", ".DS_Store") did not match.
                    # We correctly ignore it instead of raising an error.
                    pass

        # Check if any keys were found at all
        if not key_value_sets:
            print(f"Warning: No files with 'KEY[...]' format found in {base_path}")
            # Return an empty DataFrame
            return pd.DataFrame()

        # --- MODIFIED LOGIC ---
        # Loop over all found keys, create a separate DF for each, and add to a list
        
        list_of_dfs = [] # Store all generated DataFrames in a list
        
        # Create a more general output directory
        output_dir = os.path.join(os.getcwd(), r"setting\CFG\LotArrangementAuto")
        # os.makedirs(output_dir, exist_ok=True)
        
        print(f"Found keys: {list(key_value_sets.keys())}")

        for key, value_set in key_value_sets.items():
            
            # Define column names, e.g., 'LOT' and 'LOT_Index'
            key_col = key
            index_col = f"{key}_Index"
            
            # --- MODIFICATION HERE ---
            # Get the total number of unique values
            num_values = len(value_set)
            
            # Create a list of indices from 1 to num_values,
            # but use min(i, 23) to cap any number > 23 at 23.
            # Example: If num_values is 25, this creates:
            # [1, 2, ..., 22, 23, 23, 23]
            index_values = [min(i, 23) for i in range(1, num_values + 1)]
            # --- END MODIFICATION ---

            # Convert the set of unique values to a DataFrame
            df = pd.DataFrame({
                key_col: sorted(list(value_set)),
                index_col: index_values  # Use the new capped list
            })
            
            # Add the new DataFrame to our list
            list_of_dfs.append(df)

        # Concatenate all DataFrames horizontally (axis=1)
        # This will put all columns side-by-side
        # Columns with different lengths will be filled with NaN
        merged_df = pd.concat(list_of_dfs, axis=1)

        # Save the single merged DataFrame to its own CSV file
        output_filename = "lot_arrangement.csv"
        output_path = os.path.join(output_dir, output_filename)
        
        # Create the directory if it doesn't exist *before* saving
        os.makedirs(output_dir, exist_ok=True) 
        
        merged_df.to_csv(output_path, index=False)
        
        print(f"✅ Created merged CSV: {output_path} with {len(merged_df)} rows (max).")

        return merged_df

if __name__ == "__main__":
    print("Starting data extraction...")
    extractor = extractLotData()
    # The function now returns a single merged DataFrame
    merged_df = extractor.extract_lot_dataframe()
    
    if not merged_df.empty:
        print("\n--- Extracted Data Summary (Merged) ---")
        # Print a summary of what was found
        print(f"Total columns: {len(merged_df.columns)}")
        print(f"Total rows (max): {len(merged_df)}")
        print("First 5 rows:")
        print(merged_df.head())
        print("...")
        
        # Check and print last 5 rows to verify capping if there are enough rows
        if len(merged_df) > 20:
             print("\nLast 5 rows (to check capping):")
             print(merged_df.tail())
        
        print(f"\n✅ Data extraction complete. Merged CSV file created at {os.path.join(os.getcwd(), r'setting\CFG\LotArrangementAuto\lot_arrangement.csv')}")
    else:
        print("\nNo data extracted.")