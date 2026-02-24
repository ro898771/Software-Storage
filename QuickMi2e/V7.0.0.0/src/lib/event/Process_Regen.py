"""Regeneration processor for S-parameter interpolation."""

import os
import pandas as pd
import numpy as np
from lib.helper.Interpolation import Interpolation
from lib.helper.Logger import LoggerSetup


class RegenProcessor:
    """Process S-parameter data using interpolation based on Regen configuration."""

    def __init__(self, progress_callback=None):
        """
        Initialize RegenProcessor.

        Args:
            progress_callback: Optional callback function for progress updates
                              Signature: callback(message: str, progress: int)
        """
        self.progress_callback = progress_callback
        self.interpolator = Interpolation()
        self.logger = LoggerSetup('regen processor').logger

    def process_regen_file(self, regen_csv_path, dataset_results_path, output_path):
        """
        Process regeneration file and generate interpolated results.

        Args:
            regen_csv_path: Path to the Regen configuration CSV file
            dataset_results_path: Path to the dataset/results directory
            output_path: Path where the output CSV should be saved

        Returns:
            bool: True if successful, False otherwise

        Raises:
            FileNotFoundError: If regen CSV or data folders not found
            ValueError: If configuration is invalid
        """
        try:
            # Update progress
            self._update_progress("Loading Regen configuration...", 5)

            # Read the Regen configuration file
            if not os.path.exists(regen_csv_path):
                raise FileNotFoundError(f"Regen file not found: {regen_csv_path}")

            regen_df = pd.read_csv(regen_csv_path)
            self.logger.info(f"Loaded Regen config: {regen_csv_path}")
            self._update_progress(f"Loaded {len(regen_df)} configurations", 10)

            # Validate required columns (Number Point is now optional)
            required_columns = [
                'Enb Script', 'Filter Folder', 'S-Param',
                'StartFreq[MHz]', 'StopFreq[MHz]', 'Search Method', 'Parameter Name'
            ]
            missing_columns = [col for col in required_columns if col not in regen_df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            # Prepare results storage
            results = []

            # Process each row in the configuration
            total_rows = len(regen_df)
            for idx, row in regen_df.iterrows():
                try:
                    # Check if script is enabled
                    if pd.isna(row['Enb Script']) or str(row['Enb Script']).strip().lower() != 'v':
                        self.logger.info(f"Skipping row {idx + 1}: Script not enabled")
                        continue

                    # Update progress
                    progress = 10 + int((idx / total_rows) * 80)
                    self._update_progress(
                        f"Processing {idx + 1}/{total_rows}: {row['Parameter Name']}",
                        progress
                    )

                    # Process this configuration (returns list of results, one per file)
                    config_results = self._process_single_config(
                        row, dataset_results_path, idx + 1
                    )

                    if config_results:
                        # Extend results with all files processed for this config
                        results.extend(config_results)

                except Exception as e:
                    self.logger.error(f"Error processing row {idx + 1}: {e}")
                    self._update_progress(f"Error in row {idx + 1}: {str(e)}", progress)
                    # Continue processing other rows
                    continue

            # Create output DataFrame
            if not results:
                raise ValueError("No valid results generated")

            output_df = pd.DataFrame(results)
            self._update_progress("Saving results...", 90)

            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                self.logger.info(f"Created output directory: {output_dir}")

            # Save results
            output_df.to_csv(output_path, index=False)
            self.logger.info(f"Results saved to: {output_path}")
            self._update_progress(f"Completed! Results saved to: {output_path}", 100)

            return True

        except Exception as e:
            error_msg = f"Error in process_regen_file: {str(e)}"
            self.logger.error(error_msg)
            self._update_progress(error_msg, 0)
            raise

    def _process_single_config(self, row, dataset_results_path, row_number):
        """
        Process a single configuration row.

        Args:
            row: Pandas Series containing configuration
            dataset_results_path: Path to dataset/results directory
            row_number: Row number for logging

        Returns:
            dict: Result dictionary with filename, Parameter Name, frequencies, and Value
        """
        try:
            # Extract configuration parameters
            filter_folder = str(row['Filter Folder']).strip()
            sparam = str(row['S-Param']).strip()
            test_parameter = str(row['Test Parameter']).strip().upper() if 'Test Parameter' in row else 'MAG'
            # num_points is no longer used - we only calculate at start and stop frequencies
            num_points = 2  # Default value (not used in new logic)
            parameter_name = str(row['Parameter Name']).strip()

            # For FREQ type, get additional parameters
            if test_parameter == 'FREQ':
                # FREQ type: Find frequency at target dB value
                search_value_db = float(row['Search Value[dB]']) if 'Search Value[dB]' in row and not pd.isna(row['Search Value[dB]']) else None
                search_direction = str(row['Search Direction']).strip().upper() if 'Search Direction' in row and not pd.isna(row['Search Direction']) else 'LEFT'
                
                if search_value_db is None:
                    raise ValueError(f"Search Value[dB] is required for FREQ type in row {row_number}")
                
                # For FREQ, StartFreq and StopFreq are optional (will use full data range if not specified)
                start_freq_mhz = float(row['StartFreq[MHz]']) if not pd.isna(row['StartFreq[MHz]']) else None
                stop_freq_mhz = float(row['StopFreq[MHz]']) if not pd.isna(row['StopFreq[MHz]']) else None
                search_method = None  # Not used for FREQ type
                
                direction_text = "first->last row" if search_direction == 'LEFT' else "last->first row"
                self.logger.info(
                    f"Row {row_number}: Processing {parameter_name} (FREQ) - "
                    f"Finding frequency where {sparam} = {search_value_db} dB "
                    f"(searching {search_direction}: {direction_text} in data file)"
                )
            elif test_parameter == 'RIPPLE':
                # RIPPLE type: Calculate delta between MAX and MIN in frequency range
                search_value_db = None
                search_direction = None
                search_method = 'RIPPLE'  # Special method for ripple calculation
                
                # Read StartFreq and StopFreq (required for RIPPLE type)
                start_freq_mhz = float(row['StartFreq[MHz]'])
                stop_freq_mhz = float(row['StopFreq[MHz]'])
                
                self.logger.info(
                    f"Row {row_number}: Processing {parameter_name} (RIPPLE) - "
                    f"Calculating MAX-MIN delta for {sparam} from {start_freq_mhz} to {stop_freq_mhz} MHz"
                )
            else:
                # MAG type (default)
                search_value_db = None
                search_direction = None
                
                # Read StartFreq and StopFreq (required for MAG type)
                start_freq_mhz = float(row['StartFreq[MHz]'])
                stop_freq_mhz = float(row['StopFreq[MHz]'])
                
                # Handle blank/NaN search method
                search_method = row['Search Method']
                if pd.isna(search_method) or str(search_method).strip() == '':
                    search_method = None
                else:
                    search_method = str(search_method).strip().upper()

                self.logger.info(
                    f"Row {row_number}: Processing {parameter_name} (MAG) - "
                    f"{sparam} from {start_freq_mhz} to {stop_freq_mhz} MHz"
                )

            # Construct path to data folder
            data_folder_path = os.path.join(dataset_results_path, filter_folder)

            if not os.path.exists(data_folder_path):
                raise FileNotFoundError(
                    f"Data folder not found: {data_folder_path}"
                )

            # Find CSV files in the folder
            csv_files = [f for f in os.listdir(data_folder_path) if f.endswith('.csv')]

            if not csv_files:
                raise FileNotFoundError(
                    f"No CSV files found in: {data_folder_path}"
                )

            self.logger.info(f"Found {len(csv_files)} CSV files in folder")

            # Process each CSV file in the folder
            results_for_config = []
            
            for csv_file_name in csv_files:
                csv_file_path = os.path.join(data_folder_path, csv_file_name)
                self.logger.info(f"Processing file: {csv_file_name}")

                # Read the data file
                data_df = pd.read_csv(csv_file_path)

                # Find the S-parameter column
                sparam_column = self._find_sparam_column(data_df, sparam)

                if sparam_column is None:
                    self.logger.warning(
                        f"S-parameter '{sparam}' not found in {csv_file_name}. "
                        f"Skipping this file."
                    )
                    continue

                self.logger.info(f"Using S-parameter column: {sparam_column}")

                # === FREQ TYPE: Find frequency at target dB ===
                if test_parameter == 'FREQ':
                    # Prepare data for frequency interpolation
                    interp_data = data_df[['Freq', sparam_column]].copy()
                    
                    # Log the frequency range being used
                    if start_freq_mhz is None or stop_freq_mhz is None:
                        freq_min_mhz = data_df['Freq'].min() / 1e6
                        freq_max_mhz = data_df['Freq'].max() / 1e6
                        self.logger.info(
                            f"Using full data frequency range: {freq_min_mhz:.1f} - {freq_max_mhz:.1f} MHz"
                        )
                    else:
                        self.logger.info(
                            f"Using specified frequency range: {start_freq_mhz:.1f} - {stop_freq_mhz:.1f} MHz"
                        )
                    
                    try:
                        # Find frequency where S-parameter reaches target dB
                        # Pass None to use full data range, or actual values to limit range
                        result = self.interpolator.interpolate_frequency_at_db(
                            sparam_data=interp_data,
                            start_freq_mhz=start_freq_mhz,
                            stop_freq_mhz=stop_freq_mhz,
                            target_db=search_value_db,
                            search_direction=search_direction
                        )
                        
                        calculated_value = result['frequency'] / 1e6  # Convert Hz to MHz
                        freq_at_value = result['frequency']
                        
                        self.logger.info(
                            f"FREQ found: {sparam} reaches {search_value_db} dB at "
                            f"{calculated_value:.3f} MHz (searching {search_direction})"
                        )
                        
                        # Add result for this file
                        # For FREQ type, Start/Stop Frequency are always empty in output
                        results_for_config.append({
                            'File Name': csv_file_name,
                            'Parameter Name': parameter_name,
                            'Start Frequency[MHz]': '',  # Always empty for FREQ type
                            'Stop Frequency[MHz]': '',   # Always empty for FREQ type
                            'Calculated Value': float(calculated_value),
                            'Unit': 'MHz',  # FREQ type returns frequency in MHz
                            'S-Parameter': sparam,
                            'Search Method': f'FREQ@{search_value_db}dB_{search_direction}'
                        })
                        
                        continue  # Move to next file
                        
                    except ValueError as e:
                        self.logger.warning(f"FREQ search failed for {csv_file_name}: {str(e)}")
                        continue  # Skip this file
                
                # === RIPPLE TYPE: Calculate MAX - MIN delta ===
                if test_parameter == 'RIPPLE':
                    self.logger.info(f"=== RIPPLE CALCULATION START for {csv_file_name} ===")
                    self.logger.info(f"Frequency range: {start_freq_mhz} - {stop_freq_mhz} MHz")
                    
                    # Convert frequencies to Hz for comparison
                    start_freq_hz = start_freq_mhz * 1e6
                    stop_freq_hz = stop_freq_mhz * 1e6
                    
                    self.logger.info(f"Data file has {len(data_df)} total rows")
                    self.logger.info(f"Frequency column range: {data_df['Freq'].min()/1e6:.1f} - {data_df['Freq'].max()/1e6:.1f} MHz")
                    
                    # Filter data within frequency range
                    freq_mask = (data_df['Freq'] >= start_freq_hz) & (data_df['Freq'] <= stop_freq_hz)
                    filtered_data = data_df[freq_mask].copy()
                    
                    self.logger.info(f"Filtered data has {len(filtered_data)} rows in range")
                    
                    # If insufficient direct points, use interpolation to get MAX and MIN
                    if len(filtered_data) < 2:
                        self.logger.info(
                            f"Insufficient direct data points ({len(filtered_data)}), using interpolation for RIPPLE"
                        )
                        
                        # Prepare data for interpolation
                        interp_data = data_df[['Freq', sparam_column]].copy()
                        
                        # Get MAX value in range using interpolation
                        try:
                            max_result = self.interpolator.interpolate_sparam(
                                sparam_data=interp_data,
                                start_freq_mhz=start_freq_mhz,
                                stop_freq_mhz=stop_freq_mhz,
                                num_points=100,
                                search_method='MAX'
                            )
                            max_value = max_result['value']
                            self.logger.info(f"MAX value (interpolated): {max_value:.3f} dB")
                        except Exception as e:
                            self.logger.warning(f"Failed to interpolate MAX for RIPPLE: {e}")
                            continue
                        
                        # Get MIN value in range using interpolation
                        try:
                            min_result = self.interpolator.interpolate_sparam(
                                sparam_data=interp_data,
                                start_freq_mhz=start_freq_mhz,
                                stop_freq_mhz=stop_freq_mhz,
                                num_points=100,
                                search_method='MIN'
                            )
                            min_value = min_result['value']
                            self.logger.info(f"MIN value (interpolated): {min_value:.3f} dB")
                        except Exception as e:
                            self.logger.warning(f"Failed to interpolate MIN for RIPPLE: {e}")
                            continue
                        
                        ripple_value = max_value - min_value
                        self.logger.info(f"RIPPLE calculated (interpolated): {ripple_value:.3f} dB")
                    else:
                        # Enough direct points - use them directly
                        max_value = filtered_data[sparam_column].max()
                        min_value = filtered_data[sparam_column].min()
                        ripple_value = max_value - min_value
                        
                        self.logger.info(
                            f"RIPPLE calculated (direct): MAX={max_value:.3f} dB, MIN={min_value:.3f} dB, "
                            f"RIPPLE={ripple_value:.3f} dB"
                        )
                    
                    # Add result for this file
                    result_entry = {
                        'File Name': csv_file_name,
                        'Parameter Name': parameter_name,
                        'Start Frequency[MHz]': start_freq_mhz,
                        'Stop Frequency[MHz]': stop_freq_mhz,
                        'Calculated Value': float(ripple_value),
                        'Unit': 'dB',
                        'S-Parameter': sparam,
                        'Search Method': 'RIPPLE'
                    }
                    results_for_config.append(result_entry)
                    self.logger.info(f"RIPPLE result added to results: {result_entry}")
                    self.logger.info(f"=== RIPPLE CALCULATION END ===")
                    
                    continue  # Move to next file
                
                # === MAG TYPE: Find dB value at frequency (original logic) ===
                # Convert frequencies to Hz for comparison
                start_freq_hz = start_freq_mhz * 1e6
                stop_freq_hz = stop_freq_mhz * 1e6

                # Check if we need interpolation or can use direct values
                # Filter data within frequency range
                freq_mask = (data_df['Freq'] >= start_freq_hz) & (data_df['Freq'] <= stop_freq_hz)
                filtered_data = data_df[freq_mask].copy()

                # If insufficient points within range, check if we can interpolate using bracketing points
                if len(filtered_data) < 2:
                    # Check if we have data points that bracket the range
                    # Use points at or before start, and at or after stop for optimal linear interpolation
                    at_or_before_start = data_df[data_df['Freq'] <= start_freq_hz]
                    at_or_after_stop = data_df[data_df['Freq'] >= stop_freq_hz]
                    
                    if len(at_or_before_start) > 0 and len(at_or_after_stop) > 0:
                        # We can interpolate using the closest bracketing points
                        nearest_before = at_or_before_start['Freq'].max()
                        nearest_after = at_or_after_stop['Freq'].min()
                        self.logger.info(
                            f"Only {len(filtered_data)} points in range, but can interpolate using "
                            f"closest bracketing points ({nearest_before/1e6:.1f} MHz "
                            f"and {nearest_after/1e6:.1f} MHz)"
                        )
                        # Continue processing with interpolation
                    else:
                        self.logger.warning(
                            f"Insufficient data points in {csv_file_name} within frequency range "
                            f"{start_freq_mhz}-{stop_freq_mhz} MHz and no bracketing points available. "
                            f"Skipping this file."
                        )
                        continue
                

                # Find nearest data points that bracket the requested range
                # Get data points before start frequency
                before_start = data_df[data_df['Freq'] <= start_freq_hz]
                # Get data points after stop frequency
                after_stop = data_df[data_df['Freq'] >= stop_freq_hz]
                
                # Check if we have data points that bracket the range
                has_data_before_start = len(before_start) > 0
                has_data_after_stop = len(after_stop) > 0
                
                # Check if exact start and stop frequencies exist in the data
                start_exists = (data_df['Freq'] == start_freq_hz).any()
                stop_exists = (data_df['Freq'] == stop_freq_hz).any()

                # Determine if we need interpolation
                need_interpolation = False
                
                if search_method in ['MIN', 'MAX']:
                    # For MIN/MAX, we need to check all points in range
                    # Always use interpolation if:
                    # 1. We don't have exact start/stop frequencies, OR
                    # 2. We want more resolution than existing data
                    if not (start_exists and stop_exists) or len(filtered_data) < num_points:
                        # Check if we can interpolate (need data points around the range)
                        if has_data_before_start and has_data_after_stop:
                            need_interpolation = True
                            self.logger.info(
                                f"Using interpolation for {search_method} search "
                                f"(nearest points: {before_start['Freq'].iloc[-1]/1e6:.1f} MHz "
                                f"to {after_stop['Freq'].iloc[0]/1e6:.1f} MHz)"
                            )
                        elif len(filtered_data) >= 2:
                            # Use existing data points within range
                            need_interpolation = False
                            self.logger.info(f"Using existing {len(filtered_data)} data points for {search_method} search")
                        else:
                            raise ValueError(
                                f"Cannot interpolate: insufficient data points around "
                                f"{start_freq_mhz}-{stop_freq_mhz} MHz range"
                            )
                    else:
                        self.logger.info(f"Using existing {len(filtered_data)} data points for {search_method} search")
                else:
                    # For single point or blank search method
                    # Use interpolation if exact frequencies don't exist
                    if not (start_exists and stop_exists):
                        if has_data_before_start and has_data_after_stop:
                            need_interpolation = True
                            self.logger.info(
                                f"Exact frequencies not found, using interpolation "
                                f"(nearest points: {before_start['Freq'].iloc[-1]/1e6:.1f} MHz "
                                f"to {after_stop['Freq'].iloc[0]/1e6:.1f} MHz)"
                            )
                        else:
                            raise ValueError(
                                f"Cannot interpolate: no data points around "
                                f"{start_freq_mhz}-{stop_freq_mhz} MHz range"
                            )
                    else:
                        self.logger.info("Exact frequencies found, using direct values")

                # Process based on whether interpolation is needed
                if need_interpolation:
                    # Prepare data for interpolation
                    # Use data points that bracket the requested range for better accuracy
                    # Get points before start, within range, and after stop
                    interp_mask = (
                        (data_df['Freq'] <= start_freq_hz) |  # Points before/at start
                        ((data_df['Freq'] >= start_freq_hz) & (data_df['Freq'] <= stop_freq_hz)) |  # Points in range
                        (data_df['Freq'] >= stop_freq_hz)  # Points after/at stop
                    )
                    
                    # Get at least one point before start and one after stop if available
                    if has_data_before_start:
                        # Include the nearest point before start
                        nearest_before = before_start['Freq'].iloc[-1]
                        interp_mask |= (data_df['Freq'] == nearest_before)
                    
                    if has_data_after_stop:
                        # Include the nearest point after stop
                        nearest_after = after_stop['Freq'].iloc[0]
                        interp_mask |= (data_df['Freq'] == nearest_after)
                    
                    interp_data = data_df[interp_mask][['Freq', sparam_column]].copy()
                    
                    self.logger.info(
                        f"Interpolating using {len(interp_data)} data points "
                        f"(range: {interp_data['Freq'].min()/1e6:.1f} - {interp_data['Freq'].max()/1e6:.1f} MHz)"
                    )

                    # Perform interpolation
                    result = self.interpolator.interpolate_sparam(
                        sparam_data=interp_data,
                        start_freq_mhz=start_freq_mhz,
                        stop_freq_mhz=stop_freq_mhz,
                        num_points=num_points,
                        search_method=search_method
                    )

                    # Format output based on search method
                    if search_method in ['MIN', 'MAX']:
                        calculated_value = result['value']
                        freq_at_value = result['frequency']
                    else:
                        # Blank search method
                        # Check if result is a single value or array
                        if isinstance(result['value'], np.ndarray):
                            # Array returned (start != stop) - skip this entry
                            self.logger.info("Blank search method with different start/stop - skipping")
                            continue
                        else:
                            # Single value returned (start == stop)
                            calculated_value = result['value']
                            freq_at_value = result['frequency']

                else:
                    # Use direct values from data (no interpolation needed)
                    if search_method == 'MIN':
                        min_idx = filtered_data[sparam_column].idxmin()
                        calculated_value = filtered_data.loc[min_idx, sparam_column]
                        freq_at_value = filtered_data.loc[min_idx, 'Freq']
                        self.logger.info(f"MIN value found: {calculated_value} at {freq_at_value/1e6} MHz")
                    elif search_method == 'MAX':
                        max_idx = filtered_data[sparam_column].idxmax()
                        calculated_value = filtered_data.loc[max_idx, sparam_column]
                        freq_at_value = filtered_data.loc[max_idx, 'Freq']
                        self.logger.info(f"MAX value found: {calculated_value} at {freq_at_value/1e6} MHz")
                    else:
                        # Blank search method
                        if start_freq_mhz != stop_freq_mhz:
                            # Different start and stop with blank search - skip
                            self.logger.info("Blank search method with different start/stop - skipping")
                            continue
                        else:
                            # Same start and stop - get value at that frequency
                            start_row = data_df[data_df['Freq'] == start_freq_hz].iloc[0]
                            calculated_value = start_row[sparam_column]
                            freq_at_value = start_freq_hz

                # Add result for this file
                results_for_config.append({
                    'File Name': csv_file_name,
                    'Parameter Name': parameter_name,
                    'Start Frequency[MHz]': start_freq_mhz,
                    'Stop Frequency[MHz]': stop_freq_mhz,
                    'Calculated Value': float(calculated_value),
                    'Unit': 'dB',  # MAG type returns dB value
                    'S-Parameter': sparam,
                    'Search Method': search_method if search_method else 'DIRECT'
                })

            # Return all results for this configuration
            return results_for_config

        except Exception as e:
            self.logger.error(f"Error in _process_single_config: {e}")
            raise

    def _find_sparam_column(self, df, sparam):
        """
        Find the S-parameter column in the DataFrame.

        Tries multiple variations: S21, S21_dB, S21_Mag, dB:S21, dB:S21_Mag

        Args:
            df: DataFrame to search
            sparam: S-parameter name (e.g., 'S21', 'S21_dB')

        Returns:
            str: Column name if found, None otherwise
        """
        # Remove any existing suffixes from sparam to get base name
        base_sparam = sparam.replace('_Mag', '').replace('_Phase', '').replace('dB:', '').replace('_dB', '')

        # Try different variations (order matters - try exact match first)
        variations = [
            sparam,                          # Try exact match first (e.g., 'S21_dB')
            base_sparam,                     # Base name (e.g., 'S21')
            f"{base_sparam}_dB",             # With _dB suffix
            f"{base_sparam}_Mag",            # With _Mag suffix
            f"dB:{base_sparam}",             # With dB: prefix
            f"dB:{base_sparam}_Mag",         # With dB: prefix and _Mag suffix
            f"dB:{base_sparam}_dB"           # With dB: prefix and _dB suffix
        ]

        for var in variations:
            if var in df.columns:
                return var

        # Case-insensitive search as fallback
        for col in df.columns:
            if col.upper() == sparam.upper():
                return col
            if col.upper() == base_sparam.upper():
                return col
            if col.upper() == f"{base_sparam.upper()}_DB":
                return col
            if col.upper() == f"{base_sparam.upper()}_MAG":
                return col

        return None

    def _update_progress(self, message, progress):
        """
        Update progress via callback.

        Args:
            message: Progress message
            progress: Progress percentage (0-100)
        """
        if self.progress_callback:
            try:
                self.progress_callback(message, progress)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")


if __name__ == "__main__":
    # Test the processor
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    print("=" * 60)
    print("RegenProcessor Test")
    print("=" * 60)

    def progress_callback(message, progress):
        print(f"[{progress}%] {message}")

    processor = RegenProcessor(progress_callback=progress_callback)

    # Test paths (adjust as needed)
    regen_csv = "setting/CFG/Regen/MirabeauRegen.csv"
    dataset_path = "dataset/results"
    output_path = "output/Regen/Regenoutput.csv"

    try:
        success = processor.process_regen_file(
            regen_csv_path=regen_csv,
            dataset_results_path=dataset_path,
            output_path=output_path
        )
        if success:
            print("\n" + "=" * 60)
            print("Processing completed successfully!")
            print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")

