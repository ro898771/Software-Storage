"""Feature utilities for data processing and analysis."""

import json
import os
import re
import threading

import numpy as np
import pandas as pd


class Feature:
    """Provides utility functions for data processing and analysis."""

    def __init__(self):
        """Initialize Feature."""
        pass

    def get_unit_list(self, path):
        """
        Get list of unit names from files in directory.

        Args:
            path: Directory path containing unit files

        Returns:
            List of unit names (filenames without extensions)
        """
        sample = [sample.split(".")[0] for sample in os.listdir(path)]
        return sample
    
    def get_unique_headers2(self, flag, folder_path):
        """
        Get unique headers from CSV files, optionally filtering S-parameters.

        Args:
            flag: If True, filter for S-parameter headers only
            folder_path: Directory containing CSV files

        Returns:
            List of unique headers
        """
        unique_headers = set()

        # Iterate through each file in the folder
        for filename in os.listdir(folder_path):
            if filename.endswith('.csv'):
                file_path = os.path.join(folder_path, filename)
                df = pd.read_csv(file_path)
                all_zeros_mask = (df == 0).all()
                valid_headers = df.columns[~all_zeros_mask]
                unique_headers.update(valid_headers)

        if flag:
            pattern = re.compile(
                r"(S\d+)(?<!_Phase)$|(S\d+)_Mag$|"
                r"(dB:S\d+)(?<!_Phase)$|(dB:S\d+)_Mag$"
            )
            unique_headers = [
                x for x in list(unique_headers) if pattern.match(x)
            ]
            unique_headers.sort()

        return unique_headers
    
    def get_unique_headers(self, s_only_flag, formula_only_flag, folder_path):
        """
        Get unique headers from CSV files with advanced filtering.

        Filters out all-zero columns, complex number columns, and
        frequency-related columns. Optionally filters for S-parameters
        and/or formulas.

        Args:
            s_only_flag: If True, include only S-parameter headers
            formula_only_flag: If True, include only formula headers
            folder_path: Directory containing CSV files

        Returns:
            Sorted list of unique headers
        """
        unique_headers = set()
        # Regex to detect bracketed complex numbers like "(a+bj)" or "(a-bj)"
        complex_str_pattern = re.compile(
            r"^\(\s*-?\d+(\.\d+)?\s*[\+\-]\s*\d+(\.\d+)?j\s*\)$"
        )

        for filename in os.listdir(folder_path):
            if filename.endswith('.csv'):
                file_path = os.path.join(folder_path, filename)
                df = pd.read_csv(file_path)

                # Mask for all-zero columns (numeric only)
                all_zeros_mask = (df == 0).all()

                # Mask for columns where all values match complex string pattern
                all_bracketed_complex_mask = df.apply(
                    lambda col: col.apply(
                        lambda x: isinstance(x, str) and
                        complex_str_pattern.match(x)
                    ).all()
                )

                # Mask for frequency-related headers (case-insensitive)
                freq_mask = df.columns.str.contains(
                    r"freq|frequency|hz", case=False, regex=True
                )

                # Combine masks: exclude all-zero, all-complex-string,
                # and frequency-related columns
                valid_mask = (~all_zeros_mask & ~all_bracketed_complex_mask &
                              ~freq_mask)
                valid_headers = df.columns[valid_mask]
                unique_headers.update(valid_headers)

        # Apply filtering based on flags
        if s_only_flag and formula_only_flag:
            # Combine both regex patterns with '|' (OR operator)
            pattern = re.compile(
                r"(S\d+)(?<!_Phase)$|(S\d+)_Mag$|"
                r"(dB:S\d+)(?<!_Phase)$|(dB:S\d+)_Mag$|^F\|.*"
            )
            unique_headers = [
                x for x in list(unique_headers) if pattern.match(x)
            ]
            unique_headers.sort()
        elif s_only_flag:
            # Check S-Parameters only
            pattern = re.compile(
                r"(S\d+)(?<!_Phase)$|(S\d+)_Mag$|"
                r"(dB:S\d+)(?<!_Phase)$|(dB:S\d+)_Mag$"
            )
            unique_headers = [
                x for x in list(unique_headers) if pattern.match(x)
            ]
            unique_headers.sort()
        elif formula_only_flag:
            # Check Formulas only
            pattern = re.compile(r"^F\|.*")
            unique_headers = [
                x for x in list(unique_headers) if pattern.match(x)
            ]
            unique_headers.sort()

        return unique_headers


    def convert_seconds(self, seconds):
        """
        Convert seconds to human-readable time format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted string (hours, minutes, or seconds)
        """
        if seconds >= 3600:  # Convert to hours
            return f"{seconds / 3600:.2f} hours"
        elif seconds >= 60:  # Convert to minutes
            return f"{seconds / 60:.2f} minutes"
        else:  # Return seconds
            return f"{seconds:.2f} seconds"

    def convert_to_smith_data(self, magnitude, phase):
        """
        Convert magnitude and phase to Smith chart data.

        Args:
            magnitude: Magnitude value
            phase: Phase value in degrees

        Returns:
            Tuple of (real, imaginary) normalized impedance values
        """
        s_param = magnitude * np.exp(1j * np.deg2rad(phase))
        normalized_impedance = (1 + s_param) / (1 - s_param)
        real = np.real(normalized_impedance)
        imag = np.imag(normalized_impedance)
        return real, imag

    def format_frequency(self, freq):
        """
        Format frequency with SI suffix.

        Args:
            freq: Frequency value in Hz

        Returns:
            Formatted string (e.g., "2.5G", "100M")
        """
        if freq >= 1e9:
            return f"{freq / 1e9:.3f}G"
        elif freq >= 1e6:
            return f"{freq / 1e6:.3f}M"
        else:
            return str(freq)


    def IntergerValueConverter(self, val):
        """
        Convert input with SI suffixes or scientific notation to float.

        Examples:
            '10G' → 1e10
            '2.5M' → 2.5e6
            '1e9' → 1e9
            1e6 → 1e6
            '10' → 10.0
            10 → 10.0
            '5m' → 0.005

        Args:
            val: Value to convert (string or numeric)

        Returns:
            Float value

        Raises:
            ValueError: If string format is unrecognized
            TypeError: If input type is invalid
        """
        si_multipliers = {
            'K': 1e3,
            'M': 1e6,
            'G': 1e9,
            'T': 1e12,
            'P': 1e15,
            'E': 1e18,
            'm': 1e-3  # millies (lowercase 'm')
        }

        if isinstance(val, str):
            val = val.strip()
            match = re.match(
                r'^(\d+(?:\.\d+)?)([KMGTPEm])$', val, re.IGNORECASE
            )
            if match:
                num, suffix = match.groups()
                multiplier = si_multipliers.get(suffix)
                if multiplier is not None:
                    return float(num) * multiplier
            try:
                return float(val)  # Handles '1e9', '10.5', etc.
            except ValueError:
                raise ValueError(f"Unrecognized format: {val}")
        elif isinstance(val, (int, float)):
            return float(val)
        else:
            raise TypeError("Input must be a string or numeric type")


    def process_spec_fig_in_background(self, fig, spec_flag, spec_df,
                                       base_name, selected_items,
                                       spec_fig_func, spec_line_checkbox):
        """
        Process spec lines in a separate thread to avoid UI blocking.

        Args:
            fig: The Plotly figure object
            spec_flag: Boolean to check if spec processing is enabled
            spec_df: DataFrame containing spec information
            base_name: Base name of the current group
            selected_items: List of selected items to process
            spec_fig_func: Function to process the spec lines
            spec_line_checkbox: Checkbox control to determine display

        Returns:
            Thread object
        """
        def worker():
            """Worker function to process spec lines."""
            try:
                if spec_flag:
                    for s_item in selected_items:
                        filtered_spec_df = spec_df[
                            (spec_df['Channel Group'] == base_name) &
                            (spec_df['S-Parameter'] == s_item)
                        ]
                        spec_fig_func(
                            fig, spec_line_checkbox.isChecked(),
                            filtered_spec_df, s_item
                        )
            except Exception as e:
                print(f"Error in process_spec_fig_in_background: {e}")

        thread = threading.Thread(target=worker)
        thread.start()
        return thread
    
    @property
    def ColorReference(self):
        """
        Load color reference from JSON file.

        Returns:
            Dictionary of color references
        """
        file_path = os.path.join(
            os.getcwd(), 'setting', 'CFG', 'DefineUnitColor',
            'colorReference.json'
        )
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

    @property
    def ExtractUnitColorData(self):
        """
        Extract unit color data from CSV file.

        Returns:
            Dictionary mapping units to color codes

        Raises:
            ValueError: If error occurs during extraction
        """
        try:
            file_path = os.path.join(
                os.getcwd(), 'setting', 'CFG', 'DefineUnitColor',
                'unit_color.csv'
            )
            df = pd.read_csv(file_path)
            df = df[df["ColorSelect"].notnull()]

            # Convert ColorSelect values to corresponding color codes
            df["ColorSelect"] = df["ColorSelect"].apply(
                lambda x: self.ColorReference[str(int(x))]
            )

            # Convert the DataFrame to a dictionary
            color_select_dict = dict(zip(df["Unit"], df["ColorSelect"]))

            return color_select_dict
        except Exception as e:
            raise ValueError(str(e))

    def get_unique_csv_basenames(self, root_path):
        """
        Get unique CSV file basenames from directory tree.

        Args:
            root_path: Root directory to search

        Returns:
            Sorted list of unique basenames (without .csv extension)
        """
        unique_names = set()
        for dirpath, _, filenames in os.walk(root_path):
            for file in filenames:
                if file.lower().endswith('.csv'):
                    base_name = os.path.splitext(file)[0]  # Remove .csv
                    unique_names.add(base_name)

        return sorted(unique_names)

    def get_unique_csv(self, root_path):
        """
        Get unique CSV file basenames from directory tree.

        Args:
            root_path: Root directory to search

        Returns:
            Sorted list of unique basenames (without .csv extension)
        """
        unique_names = set()
        for dirpath, _, filenames in os.walk(root_path):
            for file in filenames:
                if file.lower().endswith('.csv'):
                    # base_name = os.path.splitext(file)[0]  # Remove .csv
                    unique_names.add(file)

        return sorted(unique_names)


    def get_development_list(self, file_path=None):
        """
        Get development list from configuration JSON.

        Args:
            file_path: Path to JSON file (default: configSetting/TP.json)

        Returns:
            List of development items, or empty list if error
        """
        if file_path is None:
            file_path = os.path.join(os.getcwd(), "configSetting", "TP.json")

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            return data.get("Development", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON: {e}")
            return []

    def get_default_value(self, json_path=None):
        """
        Get default value from configuration JSON.

        Args:
            json_path: Path to JSON file (default: configSetting/TP.json)

        Returns:
            Default value, or None if error
        """
        if json_path is None:
            json_path = os.path.join(os.getcwd(), "configSetting", "TP.json")

        try:
            with open(json_path, 'r') as file:
                data = json.load(file)
            default_value = data.get("Default", None)
            return default_value
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading JSON: {e}")
            return None

    def get_Header_Regex(self, json_path=None):
        """
        Get header regex pattern from configuration JSON.

        Args:
            json_path: Path to JSON file (default: configSetting/TP.json)

        Returns:
            Regex pattern string, or None if error
        """
        try:
            if json_path is None:
                json_path = os.path.join(
                    os.getcwd(), "configSetting", "TP.json"
                )

            with open(json_path, 'r') as file:
                config_data = json.load(file)

            default_site = config_data.get("Default")
            regex_pattern = config_data.get("Regex", {}).get(default_site)

            return regex_pattern
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[get_Header_Regex] Error reading JSON file: {e}")
            return None

    def set_default_value(self, new_values, json_path=None):
        """
        Set default value in configuration JSON.

        Args:
            new_values: New default value to set
            json_path: Path to JSON file (default: configSetting/TP.json)
        """
        if json_path is None:
            json_path = os.path.join(os.getcwd(), "configSetting", "TP.json")

        try:
            # Load existing data
            try:
                with open(json_path, 'r') as file:
                    data = json.load(file)
            except FileNotFoundError:
                data = {}

            # Overwrite the "Default" key
            data["Default"] = new_values

            # Save back to file
            with open(json_path, 'w') as file:
                json.dump(data, file, indent=2)
        except Exception as e:
            print(f"Error writing JSON: {e}")


if __name__ == "__main__":
    # Example usage
    test = Feature()
    print(test.convert_to_smith_data(28.986, 1.23972482935037))
    


