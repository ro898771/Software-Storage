"""CSV file processor for extracting metadata from filenames."""

import os
import re


class CsvFileProcessor:
    """
    Scan directory for CSV filenames and extract metadata.

    Checks for keys in filenames (e.g., "LOT[...]") and extracts
    their unique values.
    """

    def __init__(self, directory_path: str):
        """
        Initialize the processor with a target directory.

        Args:
            directory_path: The path to the directory to scan

        Raises:
            FileNotFoundError: If directory_path does not exist or is not
                a directory
        """
        if not os.path.isdir(directory_path):
            raise FileNotFoundError(
                f"Directory not found at path: {directory_path}"
            )
        self.directory_path = directory_path
        self._csv_files = self._get_csv_files()

    def _get_csv_files(self) -> list:
        """
        Get a list of all filenames ending in .csv in the directory.

        Returns:
            List of CSV filenames

        Raises:
            IOError: If directory cannot be read
        """
        try:
            all_files = os.listdir(self.directory_path)
            return [f for f in all_files if f.lower().endswith('.csv')]
        except Exception as e:
            raise IOError(f"Could not read directory: {e}")

    def _get_unique_values(self, argument: str) -> set:
        """
        Scan CSV filenames and return set of all found values.

        Args:
            argument: Key to search for (e.g., "LOT", "SL")

        Returns:
            Set of unique values found
        """
        # Dynamically build the regex pattern, e.g., 'LOT\[([^\]]+)\]'
        pattern = re.compile(rf'{re.escape(argument)}\[([^\]]+)\]')

        found_values = set()

        # Scan only the .csv files found during initialization
        for f in self._csv_files:
            matches = pattern.findall(f)
            found_values.update(matches)

        return found_values

    def check_key_availability(self, argument: str) -> bool:
        """
        Check if the given key exists in any .csv filename.

        Args:
            argument: The key to search for (e.g., "LOT", "SL")

        Raises:
            ValueError: If the key is not found in any .csv filename

        Returns:
            True if the key is found
        """
        print(f"Checking for key '{argument}' in .csv files...")
        found_values = self._get_unique_values(argument)
        if found_values:
            return True
        else:
            raise ValueError(
                f"FAILED: The key '{argument}' was not found in any "
                f".csv filenames."
            )

    def get_key_values_string(self, argument: str):
        """
        Get unique values for a key and return pipe-separated strings.

        Returns two pipe-separated strings: one for values, one for
        1-based indices. The indices string is capped at a maximum of 23.

        Args:
            argument: The key to search for (e.g., "LOT", "SL")

        Raises:
            ValueError: If the key is not found

        Returns:
            Tuple of two strings:
                1. Values string (e.g., "Value1|Value2|...|ValueN|")
                2. Indices string (e.g., "1|2|...|23|")
        """
        found_values = self._get_unique_values(argument)

        if not found_values:
            raise ValueError(
                f"FAILED: The key '{argument}' was not found, "
                f"so no string can be generated."
            )

        # Sort the list to ensure a consistent output order
        sorted_values = sorted(list(found_values))

        # Create the values string (no leading pipe)
        values_string = "|".join(sorted_values) + "|"

        # Create the corresponding indices string, CAPPED at 23
        num_items = len(sorted_values)

        # Determine the number of indices to generate (max of 23)
        num_indices_to_generate = min(num_items, 23)

        indices_list = [
            str(i) for i in range(1, num_indices_to_generate + 1)
        ]
        indices_string = "|".join(indices_list) + "|"

        return values_string, indices_string

if __name__ == "__main__":
    # Example usage
    project_root = os.getcwd()
    test_dir = os.path.join(
        project_root, 'dataset', 'results',
        'TN136_TR3_CH3_B1_IN-TX1_ANTL_OUT3_G1_x'
    )

    print(f"--- Running Test on '{test_dir}' ---")

    try:
        processor = CsvFileProcessor(test_dir)

        try:
            processor.check_key_availability("LOT")

            # Get both strings
            lot_values_string, lot_indices_string = (
                processor.get_key_values_string("LOT")
            )

            print(f"\n--- LOT Values ---")
            print(f"Values string: {lot_values_string}")

            print(f"\n--- LOT Indices (Capped at 23) ---")
            print(f"Indices string: {lot_indices_string}")

        except ValueError as e:
            print(e)

    except FileNotFoundError as e:
        print(e)
        print("\nNOTE: The script failed because the directory "
              "was not found.")