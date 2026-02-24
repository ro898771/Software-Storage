"""S-Parameter interpolation utilities for frequency domain analysis."""

import numpy as np
import pandas as pd


class Interpolation:
    """Provides interpolation functions for S-parameter data."""

    def __init__(self):
        """Initialize Interpolation."""
        pass

    def interpolate_sparam(
        self,
        sparam_data,
        start_freq_mhz,
        stop_freq_mhz,
        num_points,
        search_method=None
    ):
        """
        Interpolate S-parameter data over a specified frequency range.

        This function calculates S-parameter values at the start and stop frequencies
        using linear interpolation with the nearest bracketing data points.
        
        Bracketing Logic:
        - For start frequency: Use nearest data point <= start (or nearest > start if none below)
        - For stop frequency: Use nearest data point >= stop (or nearest < stop if none above)
        - If a requested frequency exists in data, use it directly
        - Calculate values at start and stop frequencies only (num_points is ignored for now)

        Args:
            sparam_data: DataFrame or dict with 'frequency' and 'value' keys.
                        - If DataFrame: must contain columns for frequency
                          (e.g., 'freq[HZ]', 'Freq', 'Frequency') and the
                          S-parameter values.
                        - If dict: must have 'frequency' (array-like in Hz)
                          and 'value' (array-like) keys.
            start_freq_mhz: Start frequency in MHz (float or int)
            stop_freq_mhz: Stop frequency in MHz (float or int)
            num_points: Number of interpolation points (int) - currently not used
            search_method: Optional search method (str or None)
                          - 'MIN' or 'min': Return minimum value between start and stop
                          - 'MAX' or 'max': Return maximum value between start and stop
                          - None or '': Return values at start and stop frequencies

        Returns:
            If search_method is None or '':
                dict: {
                    'frequency': numpy array with [start_freq, stop_freq] in Hz,
                    'value': numpy array with values at [start_freq, stop_freq]
                }
            If search_method is 'MIN' or 'min':
                dict: {
                    'frequency': frequency at minimum value (Hz),
                    'value': minimum S-parameter value (comparing start and stop)
                }
            If search_method is 'MAX' or 'max':
                dict: {
                    'frequency': frequency at maximum value (Hz),
                    'value': maximum S-parameter value (comparing start and stop)
                }

        Raises:
            ValueError: If input data is invalid or insufficient for interpolation
            TypeError: If input types are incorrect

        Examples:
            >>> # Using DataFrame input
            >>> df = pd.DataFrame({
            ...     'freq[HZ]': [330e6, 340e6, 350e6],
            ...     'S21': [-64.127, -71.571, -75.2]
            ... })
            >>> interp = Interpolation()
            >>> # Request 330-335 MHz: 330 exists, 335 needs interpolation using 330 and 340
            >>> result = interp.interpolate_sparam(
            ...     sparam_data=df,
            ...     start_freq_mhz=330,
            ...     stop_freq_mhz=335,
            ...     num_points=100,
            ...     search_method='MAX'
            ... )
            >>> print(result)
            {'frequency': 335000000.0, 'value': -67.849}
        """
        # --- Convert frequencies from MHz to Hz ---
        start_freq_hz = start_freq_mhz * 1e6
        stop_freq_hz = stop_freq_mhz * 1e6
        tolerance = 1e-3  # 1 Hz tolerance for exact match

        # --- Special case: Start and Stop are the same ---
        if abs(start_freq_mhz - stop_freq_mhz) < 1e-6:
            # Find the value at this single frequency point
            freq_array, value_array = self._extract_data(sparam_data)
            
            if len(freq_array) < 1:
                raise ValueError("Insufficient data points for interpolation")
            
            # Sort data by frequency
            sort_indices = np.argsort(freq_array)
            freq_sorted = freq_array[sort_indices]
            value_sorted = value_array[sort_indices]
            
            # Check if frequency exists in data
            exact_match = np.abs(freq_sorted - start_freq_hz) < tolerance
            if np.any(exact_match):
                # Frequency exists - use it directly
                value = value_sorted[exact_match][0]
            else:
                # Frequency not in data - interpolate
                below = freq_sorted[freq_sorted <= start_freq_hz]
                above = freq_sorted[freq_sorted > start_freq_hz]
                
                if len(below) > 0 and len(above) > 0:
                    bracket_low_freq = below.max()
                    bracket_high_freq = above.min()
                elif len(below) >= 2:
                    sorted_below = np.sort(below)
                    bracket_low_freq = sorted_below[-2]
                    bracket_high_freq = sorted_below[-1]
                elif len(above) >= 2:
                    sorted_above = np.sort(above)
                    bracket_low_freq = sorted_above[0]
                    bracket_high_freq = sorted_above[1]
                else:
                    raise ValueError(f"Cannot interpolate frequency {start_freq_mhz} MHz - insufficient data")
                
                bracket_low_value = value_sorted[freq_sorted == bracket_low_freq][0]
                bracket_high_value = value_sorted[freq_sorted == bracket_high_freq][0]
                value = np.interp(start_freq_hz, [bracket_low_freq, bracket_high_freq], 
                                [bracket_low_value, bracket_high_value])
            
            # Return single point (ignore search method)
            return {
                'frequency': float(start_freq_hz),
                'value': float(value)
            }

        # --- Input Validation ---
        if start_freq_mhz >= stop_freq_mhz:
            raise ValueError(
                "start_freq_mhz must be less than stop_freq_mhz"
            )

        # --- Extract frequency and value arrays ---
        freq_array, value_array = self._extract_data(sparam_data)

        # --- Validate extracted data ---
        if len(freq_array) < 1:
            raise ValueError(
                "Insufficient data points for interpolation "
                "(need at least 1 point)"
            )

        if len(freq_array) != len(value_array):
            raise ValueError(
                "Frequency and value arrays must have the same length"
            )

        # Sort data by frequency
        sort_indices = np.argsort(freq_array)
        freq_sorted = freq_array[sort_indices]
        value_sorted = value_array[sort_indices]

        # --- Calculate value at START frequency ---
        start_exact_match = np.abs(freq_sorted - start_freq_hz) < tolerance
        if np.any(start_exact_match):
            # Start frequency exists in data - use it directly
            start_value = value_sorted[start_exact_match][0]
            start_is_data_point = True
        else:
            # Start frequency not in data - need to interpolate
            # Find bracketing points for start frequency
            below_start = freq_sorted[freq_sorted <= start_freq_hz]
            above_start = freq_sorted[freq_sorted > start_freq_hz]
            
            if len(below_start) > 0 and len(above_start) > 0:
                # Have points on both sides - use nearest on each side
                bracket_low_freq = below_start.max()
                bracket_high_freq = above_start.min()
            elif len(below_start) > 0:
                # Only have points below - use two nearest below
                if len(below_start) >= 2:
                    sorted_below = np.sort(below_start)
                    bracket_low_freq = sorted_below[-2]
                    bracket_high_freq = sorted_below[-1]
                else:
                    raise ValueError(f"Cannot interpolate start frequency {start_freq_mhz} MHz - insufficient data")
            elif len(above_start) > 0:
                # Only have points above - use two nearest above
                if len(above_start) >= 2:
                    sorted_above = np.sort(above_start)
                    bracket_low_freq = sorted_above[0]
                    bracket_high_freq = sorted_above[1]
                else:
                    raise ValueError(f"Cannot interpolate start frequency {start_freq_mhz} MHz - insufficient data")
            else:
                raise ValueError(f"No data points available for interpolation")
            
            # Get values at bracketing frequencies
            bracket_low_value = value_sorted[freq_sorted == bracket_low_freq][0]
            bracket_high_value = value_sorted[freq_sorted == bracket_high_freq][0]
            
            # Linear interpolation
            start_value = np.interp(start_freq_hz, [bracket_low_freq, bracket_high_freq], 
                                   [bracket_low_value, bracket_high_value])
            start_is_data_point = False

        # --- Calculate value at STOP frequency ---
        stop_exact_match = np.abs(freq_sorted - stop_freq_hz) < tolerance
        if np.any(stop_exact_match):
            # Stop frequency exists in data - use it directly
            stop_value = value_sorted[stop_exact_match][0]
            stop_is_data_point = True
        else:
            # Stop frequency not in data - need to interpolate
            # Find bracketing points for stop frequency
            below_stop = freq_sorted[freq_sorted < stop_freq_hz]
            above_stop = freq_sorted[freq_sorted >= stop_freq_hz]
            
            if len(below_stop) > 0 and len(above_stop) > 0:
                # Have points on both sides - use nearest on each side
                bracket_low_freq = below_stop.max()
                bracket_high_freq = above_stop.min()
            elif len(below_stop) > 0:
                # Only have points below - use two nearest below
                if len(below_stop) >= 2:
                    sorted_below = np.sort(below_stop)
                    bracket_low_freq = sorted_below[-2]
                    bracket_high_freq = sorted_below[-1]
                else:
                    raise ValueError(f"Cannot interpolate stop frequency {stop_freq_mhz} MHz - insufficient data")
            elif len(above_stop) > 0:
                # Only have points above - use two nearest above
                if len(above_stop) >= 2:
                    sorted_above = np.sort(above_stop)
                    bracket_low_freq = sorted_above[0]
                    bracket_high_freq = sorted_above[1]
                else:
                    raise ValueError(f"Cannot interpolate stop frequency {stop_freq_mhz} MHz - insufficient data")
            else:
                raise ValueError(f"No data points available for interpolation")
            
            # Get values at bracketing frequencies
            bracket_low_value = value_sorted[freq_sorted == bracket_low_freq][0]
            bracket_high_value = value_sorted[freq_sorted == bracket_high_freq][0]
            
            # Linear interpolation
            stop_value = np.interp(stop_freq_hz, [bracket_low_freq, bracket_high_freq], 
                                  [bracket_low_value, bracket_high_value])
            stop_is_data_point = False

        # --- Apply search method ---
        if search_method is None or search_method == '':
            # Return values at both start and stop frequencies
            return {
                'frequency': np.array([start_freq_hz, stop_freq_hz]),
                'value': np.array([start_value, stop_value])
            }
        elif search_method.upper() == 'MIN':
            # Return minimum value between start and stop (include all points)
            if start_value <= stop_value:
                return {'frequency': float(start_freq_hz), 'value': float(start_value)}
            else:
                return {'frequency': float(stop_freq_hz), 'value': float(stop_value)}
                    
        elif search_method.upper() == 'MAX':
            # Return maximum value between start and stop (include all points)
            if start_value >= stop_value:
                return {'frequency': float(start_freq_hz), 'value': float(start_value)}
            else:
                return {'frequency': float(stop_freq_hz), 'value': float(stop_value)}
        else:
            raise ValueError(
                f"Invalid search_method: '{search_method}'. "
                f"Must be 'MIN', 'MAX', or None/empty string."
            )

    def interpolate_frequency_at_db(
        self,
        sparam_data,
        start_freq_mhz,
        stop_freq_mhz,
        target_db,
        search_direction='LEFT'
    ):
        """
        Find frequency where S-parameter reaches a target dB value.
        
        This function searches for the frequency at which the S-parameter value
        crosses or equals the target dB level.
        
        Search Direction Behavior:
        - 'LEFT': Scans from LOWEST frequency in dataset → towards HIGH frequency
                  Returns the FIRST crossing point found (earliest frequency)
                  Works for both increasing and decreasing signal crossings
        - 'RIGHT': Scans from HIGHEST frequency in dataset → towards LOW frequency
                   Returns the FIRST crossing point found (latest frequency)
                   Works for both increasing and decreasing signal crossings
        
        Args:
            sparam_data: DataFrame or dict with 'frequency' and 'value' keys
            start_freq_mhz: Start frequency in MHz (defines search range, can be None for full range)
            stop_freq_mhz: Stop frequency in MHz (defines search range, can be None for full range)
            target_db: Target dB value to find (e.g., -50.0)
            search_direction: 'LEFT' or 'RIGHT'
                - 'LEFT': Search from lowest freq → high freq (first crossing)
                - 'RIGHT': Search from highest freq → low freq (first crossing)
        
        Returns:
            dict: {
                'frequency': frequency in Hz where target_db is reached,
                'value': actual dB value at that frequency (should be close to target_db)
            }
            
        Raises:
            ValueError: If target dB is not found within the range
            
        Example:
            >>> # Find frequency where S21 reaches -50 dB, searching from left (low freq)
            >>> result = interp.interpolate_frequency_at_db(
            ...     sparam_data=df,
            ...     start_freq_mhz=None,  # Use full range
            ...     stop_freq_mhz=None,   # Use full range
            ...     target_db=-50.0,
            ...     search_direction='LEFT'
            ... )
            >>> print(f"S21 reaches -50 dB at {result['frequency']/1e6:.2f} MHz")
        """
        # --- Input Validation ---
        if search_direction.upper() not in ['LEFT', 'RIGHT']:
            raise ValueError("search_direction must be 'LEFT' or 'RIGHT'")
        
        # --- Extract frequency and value arrays ---
        freq_array, value_array = self._extract_data(sparam_data)
        
        # --- Validate extracted data ---
        if len(freq_array) < 2:
            raise ValueError("Insufficient data points for interpolation (need at least 2 points)")
        
        # --- Sort data by frequency ---
        sort_indices = np.argsort(freq_array)
        freq_sorted = freq_array[sort_indices]
        value_sorted = value_array[sort_indices]
        
        # --- Filter data within the specified frequency range (if provided) ---
        if start_freq_mhz is not None and stop_freq_mhz is not None:
            if start_freq_mhz >= stop_freq_mhz:
                raise ValueError("start_freq_mhz must be less than stop_freq_mhz")
            
            start_freq_hz = start_freq_mhz * 1e6
            stop_freq_hz = stop_freq_mhz * 1e6
            
            mask = (freq_sorted >= start_freq_hz) & (freq_sorted <= stop_freq_hz)
            freq_filtered = freq_sorted[mask]
            value_filtered = value_sorted[mask]
            
            if len(freq_filtered) < 2:
                raise ValueError(
                    f"Insufficient data points within frequency range "
                    f"{start_freq_mhz}-{stop_freq_mhz} MHz. Need at least 2 points."
                )
        else:
            # Use full data range
            freq_filtered = freq_sorted
            value_filtered = value_sorted
            start_freq_mhz = freq_sorted.min() / 1e6
            stop_freq_mhz = freq_sorted.max() / 1e6
        
        # --- Search for target dB value ---
        # LEFT: Scan from low freq → high freq, find FIRST crossing point
        # RIGHT: Scan from high freq → low freq, find FIRST crossing point
        
        if search_direction.upper() == 'LEFT':
            # Search from low frequency to high frequency
            search_freq = freq_filtered
            search_value = value_filtered
        else:  # RIGHT
            # Search from high frequency to low frequency
            search_freq = freq_filtered[::-1]
            search_value = value_filtered[::-1]
        
        # Find where the value crosses the target_db
        found_frequency = None
        found_value = None
        
        for i in range(len(search_value) - 1):
            val1 = search_value[i]
            val2 = search_value[i + 1]
            freq1 = search_freq[i]
            freq2 = search_freq[i + 1]
            
            # Check if target_db is between val1 and val2
            if (val1 <= target_db <= val2) or (val2 <= target_db <= val1):
                # Found a crossing point - interpolate to find exact frequency
                # Linear interpolation to find exact frequency
                if abs(val2 - val1) < 1e-10:  # Avoid division by zero
                    # Values are essentially the same, use midpoint
                    found_frequency = (freq1 + freq2) / 2
                    found_value = target_db
                else:
                    # Interpolate frequency at target_db
                    t = (target_db - val1) / (val2 - val1)
                    found_frequency = freq1 + t * (freq2 - freq1)
                    found_value = target_db
                break
        
        if found_frequency is None:
            # Target dB not found in range
            raise ValueError(
                f"Target dB value {target_db} not found within frequency range "
                f"{start_freq_mhz:.2f}-{stop_freq_mhz:.2f} MHz. "
                f"Value range in data: {value_filtered.min():.2f} to {value_filtered.max():.2f} dB"
            )
        
        return {
            'frequency': float(found_frequency),
            'value': float(found_value)
        }

    def _extract_data(self, sparam_data):
        """
        Extract frequency and value arrays from input data.

        Args:
            sparam_data: DataFrame or dict containing frequency and value data

        Returns:
            tuple: (freq_array, value_array) as numpy arrays

        Raises:
            TypeError: If input type is not supported
            ValueError: If required columns/keys are not found
        """
        if isinstance(sparam_data, pd.DataFrame):
            # Extract from DataFrame
            freq_array = self._extract_frequency_from_df(sparam_data)
            value_array = self._extract_value_from_df(sparam_data)

        elif isinstance(sparam_data, dict):
            # Extract from dictionary
            if 'frequency' not in sparam_data:
                raise ValueError(
                    "Dictionary must contain 'frequency' key"
                )
            if 'value' not in sparam_data:
                raise ValueError(
                    "Dictionary must contain 'value' key"
                )

            freq_array = np.array(sparam_data['frequency'], dtype=float)
            value_array = np.array(sparam_data['value'], dtype=float)

        else:
            raise TypeError(
                "sparam_data must be a pandas DataFrame or dict. "
                f"Got {type(sparam_data)}"
            )

        # Remove NaN values
        valid_mask = ~(np.isnan(freq_array) | np.isnan(value_array))
        freq_array = freq_array[valid_mask]
        value_array = value_array[valid_mask]

        return freq_array, value_array

    def _extract_frequency_from_df(self, df):
        """
        Extract frequency column from DataFrame.

        Searches for common frequency column names.

        Args:
            df: pandas DataFrame

        Returns:
            numpy array of frequency values

        Raises:
            ValueError: If no frequency column is found
        """
        # Common frequency column names
        freq_column_names = [
            'freq[HZ]', 'Freq', 'Frequency', 'frequency',
            'FREQ', 'freq', 'Freq[Hz]', 'Freq[HZ]'
        ]

        for col_name in freq_column_names:
            if col_name in df.columns:
                return np.array(df[col_name], dtype=float)

        # If exact match not found, try case-insensitive search
        for col in df.columns:
            if 'freq' in col.lower():
                return np.array(df[col], dtype=float)

        raise ValueError(
            f"No frequency column found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )

    def _extract_value_from_df(self, df):
        """
        Extract S-parameter value column from DataFrame.

        Assumes the S-parameter column is the second column or
        searches for columns matching S-parameter patterns.

        Args:
            df: pandas DataFrame

        Returns:
            numpy array of S-parameter values

        Raises:
            ValueError: If no suitable value column is found
        """
        # First, try to find S-parameter columns
        sparam_columns = [
            col for col in df.columns
            if col.startswith('S') or col.startswith('dB:S')
        ]

        if sparam_columns:
            # Use the first S-parameter column found
            return np.array(df[sparam_columns[0]], dtype=float)

        # If no S-parameter column, use the second column
        # (assuming first is frequency)
        if len(df.columns) >= 2:
            # Skip frequency column and use next numeric column
            for col in df.columns[1:]:
                try:
                    return np.array(df[col], dtype=float)
                except (ValueError, TypeError):
                    continue

        raise ValueError(
            f"No suitable value column found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )


if __name__ == "__main__":
    # Example usage and testing
    interp = Interpolation()

    # Test with DataFrame
    print("=" * 60)
    print("Test 1: DataFrame input with MIN search")
    print("=" * 60)
    df_test = pd.DataFrame({
        'freq[HZ]': [3e9, 3.3e9, 3.6e9, 3.9e9, 4.2e9],
        'S11': [-10.5, -15.2, -12.8, -8.3, -11.1]
    })
    result_min = interp.interpolate_sparam(
        sparam_data=df_test,
        start_freq_mhz=3300,
        stop_freq_mhz=4200,
        num_points=100,
        search_method='MIN'
    )
    print(f"Minimum value: {result_min['value']:.2f} dB")
    print(f"At frequency: {result_min['frequency']/1e6:.2f} MHz")
    print()

    # Test with MAX search
    print("=" * 60)
    print("Test 2: DataFrame input with MAX search")
    print("=" * 60)
    result_max = interp.interpolate_sparam(
        sparam_data=df_test,
        start_freq_mhz=3300,
        stop_freq_mhz=4200,
        num_points=100,
        search_method='MAX'
    )
    print(f"Maximum value: {result_max['value']:.2f} dB")
    print(f"At frequency: {result_max['frequency']/1e6:.2f} MHz")
    print()

    # Test with all values
    print("=" * 60)
    print("Test 3: DataFrame input returning all values")
    print("=" * 60)
    result_all = interp.interpolate_sparam(
        sparam_data=df_test,
        start_freq_mhz=3300,
        stop_freq_mhz=4200,
        num_points=10,
        search_method=None
    )
    print(f"Number of interpolated points: {len(result_all['frequency'])}")
    print(f"Frequency range: {result_all['frequency'][0]/1e6:.2f} - "
          f"{result_all['frequency'][-1]/1e6:.2f} MHz")
    print(f"Value range: {result_all['value'].min():.2f} - "
          f"{result_all['value'].max():.2f} dB")
    print()

    # Test with dict input
    print("=" * 60)
    print("Test 4: Dictionary input")
    print("=" * 60)
    dict_test = {
        'frequency': [500e6, 1e9, 1.5e9, 2e9, 2.5e9],
        'value': [-20, -25, -22, -18, -21]
    }
    result_dict = interp.interpolate_sparam(
        sparam_data=dict_test,
        start_freq_mhz=500,
        stop_freq_mhz=2500,
        num_points=50,
        search_method='MIN'
    )
    print(f"Minimum value: {result_dict['value']:.2f} dB")
    print(f"At frequency: {result_dict['frequency']/1e6:.2f} MHz")
    print()

    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

