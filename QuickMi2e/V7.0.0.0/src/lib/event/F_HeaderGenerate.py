import json
import os

class HeaderBuilder:
    def __init__(self):
        # Define all possible fields in order
        self.fields = [
            'WF', 'SL', 'TT', 'MFG',
            'MOD', 'PID', 'ASM','PCB'
        ]
        self.config_filename = r"{path}\configSetting\header_config.json".format(path=os.getcwd())

    def generate(self, selected: dict, values: dict, formatted_date_string: str = "NA") -> str:
        if selected.get('Default'):
            lot     = 'PT5381607235-E'
            subLot  = values.get('WF', 'NA')
            mfg     = values.get('MFG', 'NA')
            mod     = values.get('MOD', 'NA')
            wafer   = values.get('WF', 'NA')
            pid     = values.get('PID', 'NA')
            # date    = formatted_date_string or values.get('DateTime', 'NA')
            date    = '2024-06-30'

            return f"LOT[{lot}]_SL[{subLot}]_MFG[{mfg}]_MOD[{mod}]_WF[{wafer}]_PID[{pid}]_DateTime[{date}]"

        # Dynamic format
        lot_value = values.get('LOT', 'NA')
        parts = [f"LOT[{lot_value}]"]

        for key in self.fields:
            if selected.get(key):
                val = values.get(key, 'NA')
                parts.append(f"{key}[{val}]")

        # ✅ Ensure DateTime is appended if selected
        if selected.get('DateTime'):
            # Use 'DateTime' from values first, then formatted_date_string, then 'NA'
            date_val = values.get('DateTime') or formatted_date_string
            if not date_val: # Handle cases where both might be None or empty
                 date_val = 'NA'
            parts.append(f"DateTime[{date_val}]")

        return "_".join(parts)
    
    def getActualHeader(self,value):
        try:
            config = self.load_config()
            return self.generate(config, value)
        
        except Exception as e:
            print(e) 
        
    def DummyHeader(self,selected):       
            values = {
            'LOT': 'PT5381607235-E',
            'SL': '5',
            'MFG': '50152',
            'MOD': '36000060768',
            'WF': '1A',
            'PID': '9999',
            'TT': 'HT205T1_023_168',
            'ASM': 'AL22',
            'PCB': 'PCB1234',
            'DateTime':'2024-06-30'
            }
            return self.generate(selected, values) # Changed to self.generate


    def build_header_string(self, values: dict, config: dict) -> str:
        if config.get("Default", False):
            keys_to_include = ["LOT", "SL", "MFG", "MOD", "PID", "WF", "DateTime"]
        else:
            keys_to_include = [key for key, enabled in config.items() if enabled and key != "Default"]

        parts = [
            f"{key}[{values[key]}]"
            for key in keys_to_include
            if key in values and str(values[key]).strip().upper() != "NA" and str(values[key]).strip() != ""
        ]

        return "_".join(parts)


    def save_config(self,data: dict):
        """
        Saves a dictionary (e.g., a 'selected' configuration) to a JSON file.
        
        :param data: The dictionary to save.
        :param filename: The name of the file to save (e.g., "config.json").
        """
        try:
            filename=self.config_filename
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Successfully saved configuration to {filename}")
        except IOError as e:
            print(f"Error: Could not write to file {filename}. {e}")
        except TypeError as e:
            print(f"Error: Could not serialize data to JSON. {e}")


    def load_config(self):
        """
        Loads a dictionary from a JSON file.
        
        :param filename: The name of the file to load (e.g., "config.json").
        :return: A dictionary with the loaded data, or an empty dictionary on failure.
        """
        try:
            filename=self.config_filename
            with open(filename, 'r') as f:
                data = json.load(f)
                print(f"Successfully loaded configuration from {filename}")
                return data
        except FileNotFoundError:
            print(f"Error: Configuration file not found at {filename}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filename}. File may be corrupt.")
            return {}
        except IOError as e:
            print(f"Error: Could not read file {filename}. {e}")
            return {}

if __name__ == "__main__":
    builder = HeaderBuilder()

    values = {
    'LOT': 'PT5381607235-E',
    'SL': '5',
    'MFG': '50152',
    'MOD': '36000060768',
    'WF': '1A',
    'PID': '9999',
    'TT': 'HT205T1_023_168',
    'ASM': 'AL22',
    'PCB': 'PCB1234',
    'DateTime': '2024-06-30'
    }

    config = {
        "Default": False,
        "LOT": True,
        "SL": True,
        "MFG": False,
        "MOD": False,
        "WF": False,
        "PID": False,
        "TT": False,
        "ASM": False,
        "PCB": False,
        "DateTime": True
    }

    header = builder.build_header_string(values, config)
    print(header)
