import os
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time
import json
from functools import lru_cache

# --- Custom Modules ---
from lib.helper.Feature import Feature
from lib.event.F_HeaderGenerate import HeaderBuilder
from lib.helper.Logger import LoggerSetup  # Imported based on previous context

class ModuleGenerator:
    """
    A class to generate Plotly HTML and Image files based on processed CSV data.
    It handles specific coloring logic (by Lot or Unit) and specification limit lines.
    """

    def __init__(self, refer, dataSrc, htmlPath, imgPath, SpecFlag, lotFlag, unitFlag, GeneratorGroup):
        # --- Initialize Logger ---
        self.logger = LoggerSetup(
            log_name='Tiger-Cntrace ModuleGenerator', 
            log_dir_relative_path=r"output\Log"
        ).get_logger()

        self.logger.info("Initializing ModuleGenerator...")

        try:
            # --- Assignment of configuration variables ---
            self.refer = refer
            self.dataSrc = dataSrc
            self.htmlPath = htmlPath
            self.imagePath = imgPath
            self.SpecFlag = SpecFlag
            self.lotFlag = lotFlag
            self.unitFlag = unitFlag
            self.GeneratorGroup = str(GeneratorGroup)
            
            # --- Load Control File ---
            # Reading the main control CSV that dictates which plots to generate
            self.df = pd.read_csv(self.refer)
            
            # Construct full paths for the filtered folders
            self.df['Filtered Folder'] = self.df['Filtered Folder'].apply(lambda x: os.path.join(self.dataSrc, x))
            
            # Filter to process only enabled scripts ("v")
            self.df = self.df[self.df["Enb Scrip"] == "v"]
            
            self.config = HeaderBuilder()
            self.legendBuffer = []

            # --- Load Configuration Files ---
            cwd = os.getcwd()
            
            # Load Color Reference JSON
            color_json_path = os.path.join(cwd, r"setting\CFG\DefineUnitColor\colorReference.json")
            with open(color_json_path, "r") as file:
                self.colorData = json.load(file)

            # Load Lot Arrangement CSV
            lot_cfg_path = os.path.join(cwd, r"setting\CFG\LotArrangementAuto\lot_arrangement.csv")
            self.colordf = pd.read_csv(lot_cfg_path)
            self.lotList = self.colordf['LOT'].tolist()

            # Load Unit Color Dictionary from Feature helper
            # Cache Feature instance to avoid repeated object creation
            self.feature_instance = Feature()
            self.unitDic = self.feature_instance.ExtractUnitColorData

            # --- Load Spec Lines (If available) ---
            spec_dir = os.path.join(cwd, r"setting\CFG\SpecLine")
            spec_file = os.path.join(spec_dir, "SpecLine.csv")
            
            if os.path.exists(spec_dir) and os.listdir(spec_dir):
                if os.path.exists(spec_file):
                    self.spec_df = pd.read_csv(spec_file)
                    # Note: Enable filtering is done in specFig method
                else:
                    self.spec_df = pd.DataFrame() # Empty DF if file missing
            else:
                self.spec_df = pd.DataFrame()

            # Pre-compile regex pattern for better performance
            self.filename_pattern = re.compile(r'(\w+)\[([^\]]*)\]')

            self.logger.info("ModuleGenerator initialized successfully.")

        except Exception as e:
            self.logger.critical(f"Failed to initialize ModuleGenerator: {e}", exc_info=True)
            # Re-raise to stop execution if init fails
            raise

    def specFig(self, fig, show_spec_lines, spec_df, current_s_parameter):
        """
        Adds Min/Max specification lines to the Plotly figure.
        Uses markers (dots) for visualization - large dots for single points, dense dots for ranges.
        Shows in legend with naming: Search_Method + N-Parameter-Class.
        """
        try:
            if show_spec_lines:
                if not spec_df.empty:
                    # Filter by Enable column - only plot rows with "v"
                    if 'Enable' in spec_df.columns:
                        spec_df = spec_df[spec_df['Enable'] == 'v']
                    
                    if spec_df.empty:
                        self.logger.info(f"No enabled spec lines to plot for {current_s_parameter}")
                        return
                    
                    # Track unique legend entries to avoid duplicates
                    spec_legends_shown = set()
                    
                    # Iterate through each row to plot spec lines
                    for idx, row in spec_df.iterrows():
                        start_freq = row['StartFreq']
                        stop_freq = row['StopFreq']
                        min_val = row['Min']
                        max_val = row['Max']
                        test_param = row.get('TestParameter', 'N/A')  # Get TestParameter if exists
                        
                        # Create legend name from Search_Method + N-Parameter-Class
                        search_method = row.get('Search_Method', 'N/A')
                        n_param_class = row.get('N-Parameter-Class', 'N/A')
                        
                        # Create separate legend names for MIN and MAX
                        min_legend_name = f"MIN_LSL_{search_method}_{n_param_class}"
                        max_legend_name = f"MAX_USL_{search_method}_{n_param_class}"
                        
                        # Check if single frequency point (stop_freq is None or same as start_freq)
                        is_single_point = pd.isna(stop_freq) or (start_freq == stop_freq)
                        
                        if pd.notna(min_val):
                            # Determine if MIN legend should be shown (only once per unique min_legend_name)
                            show_min_legend = min_legend_name not in spec_legends_shown
                            
                            if is_single_point:
                                # Single point - use triangle pointing up (arrow at 90 degrees)
                                fig.add_trace(go.Scatter(
                                    x=[start_freq],
                                    y=[min_val],
                                    mode='markers',
                                    marker=dict(
                                        color="Black",
                                        size=9,
                                        symbol='triangle-up'
                                    ),
                                    name=min_legend_name,
                                    legendgroup=min_legend_name,
                                    hoverinfo='text',
                                    text=f"Min Spec ({current_s_parameter})<br>TestParameter: {test_param}<br>Value: {min_val} dB<br>Freq: {self.feature_instance.format_frequency(start_freq)}",
                                    showlegend=show_min_legend
                                ))
                            else:
                                # Frequency range - use dash line
                                fig.add_trace(go.Scatter(
                                    x=[start_freq, stop_freq],
                                    y=[min_val, min_val],
                                    mode='lines',
                                    line=dict(
                                        color="Black",
                                        width=2,
                                        dash='dash'
                                    ),
                                    name=min_legend_name,
                                    legendgroup=min_legend_name,
                                    hoverinfo='text',
                                    text=f"Min Spec ({current_s_parameter})<br>TestParameter: {test_param}<br>Value: {min_val} dB<br>Start: {self.feature_instance.format_frequency(start_freq)}<br>Stop: {self.feature_instance.format_frequency(stop_freq)}",
                                    showlegend=show_min_legend
                                ))
                            
                            # Mark MIN legend as shown
                            spec_legends_shown.add(min_legend_name)

                        if pd.notna(max_val):
                            # Determine if MAX legend should be shown (only once per unique max_legend_name)
                            show_max_legend = max_legend_name not in spec_legends_shown
                            
                            if is_single_point:
                                # Single point - use triangle pointing down (arrow at 90 degrees)
                                fig.add_trace(go.Scatter(
                                    x=[start_freq],
                                    y=[max_val],
                                    mode='markers',
                                    marker=dict(
                                        color="Red",
                                        size=9,
                                        symbol='triangle-down'
                                    ),
                                    name=max_legend_name,
                                    legendgroup=max_legend_name,
                                    hoverinfo='text',
                                    text=f"Max Spec ({current_s_parameter})<br>TestParameter: {test_param}<br>Value: {max_val} dB<br>Freq: {self.feature_instance.format_frequency(start_freq)}",
                                    showlegend=show_max_legend
                                ))
                            else:
                                # Frequency range - use dash line
                                fig.add_trace(go.Scatter(
                                    x=[start_freq, stop_freq],
                                    y=[max_val, max_val],
                                    mode='lines',
                                    line=dict(
                                        color="Red",
                                        width=2,
                                        dash='dash'
                                    ),
                                    name=max_legend_name,
                                    legendgroup=max_legend_name,
                                    hoverinfo='text',
                                    text=f"Max Spec ({current_s_parameter})<br>TestParameter: {test_param}<br>Value: {max_val} dB<br>Start: {self.feature_instance.format_frequency(start_freq)}<br>Stop: {self.feature_instance.format_frequency(stop_freq)}",
                                    showlegend=show_max_legend
                                ))
                            
                            # Mark MAX legend as shown
                            spec_legends_shown.add(max_legend_name)

        except Exception as e:
            self.logger.error(f"Error in specFig for {current_s_parameter}: {e}")

    def generate_regex_from_header(self, header: str) -> str:
        """Escapes brackets in header strings to create valid Regex patterns."""
        pattern = re.sub(r'\[.*?\]', r'\\[(.*?)\\]', header)
        return rf"{pattern}"

    def process_row(self, row):
        """
        Worker function: Processes a single row from the control CSV.
        Generates one plot (HTML + PNG) containing traces for all units in that folder.
        """
        try:
            # --- Setup Figure ---
            figFlag = True
            fig = go.Figure()
            
            Title = row['Plot Title']
            Param = row["S-Parameter"]
            path = row["Filtered Folder"]
            base_name = os.path.basename(path)
            
            # --- Read X-Step, Y-Step, and User Frequency Range from batch file ---
            x_step_raw = row.get('X-Step', '')
            y_step_raw = row.get('Y-Step', '')
            user_start_freq_raw = row.get('User_StartFreq', '')
            user_stop_freq_raw = row.get('User_StopFreq', '')
            
            # Convert using Feature().IntergerValueConverter or use as raw integer
            x_step = None
            y_step = None
            user_start_freq = None
            user_stop_freq = None
            
            if not pd.isna(x_step_raw) and str(x_step_raw).strip():
                try:
                    x_step = Feature().IntergerValueConverter(x_step_raw)
                except:
                    # If conversion fails, try as raw integer
                    try:
                        x_step = float(x_step_raw)
                    except:
                        x_step = None
            
            if not pd.isna(y_step_raw) and str(y_step_raw).strip():
                try:
                    y_step = Feature().IntergerValueConverter(y_step_raw)
                except:
                    # If conversion fails, try as raw integer
                    try:
                        y_step = float(y_step_raw)
                    except:
                        y_step = None
            
            # Parse User_StartFreq (handle pandas NaN values)
            if not pd.isna(user_start_freq_raw) and str(user_start_freq_raw).strip():
                try:
                    user_start_freq = Feature().IntergerValueConverter(user_start_freq_raw)
                except:
                    # If conversion fails, try as raw integer
                    try:
                        user_start_freq = float(user_start_freq_raw)
                    except:
                        user_start_freq = None
            
            # Parse User_StopFreq (handle pandas NaN values)
            if not pd.isna(user_stop_freq_raw) and str(user_stop_freq_raw).strip():
                try:
                    user_stop_freq = Feature().IntergerValueConverter(user_stop_freq_raw)
                except:
                    # If conversion fails, try as raw integer
                    try:
                        user_stop_freq = float(user_stop_freq_raw)
                    except:
                        user_stop_freq = None
            
            colorCount = 1

            # --- Filter Spec Limits for this specific plot ---
            if self.SpecFlag:
                MapParam = Param + "_Mag"
                filtered_spec_df = self.spec_df[
                    (self.spec_df['Channel Group'] == base_name) &
                    (self.spec_df['S-Parameter'] == MapParam)
                ]
            
            # Use sets for O(1) lookup instead of O(n) list lookup
            tempLotSet = set()
            tempUnitSet = set()
            
            # Pre-filter and cache CSV files to avoid repeated file system calls
            csv_files = [f for f in os.listdir(path) if f.lower().endswith('.csv')]
            
            # --- Iterate through all CSV files in the target folder ---
            # NOTE: Logging is excluded here to maximize performance in this tight loop
            for unit in csv_files:
                # Regex to extract key-value pairs from filename (e.g., Lot[A]_Unit[1])
                new_string = "_".join(unit.split('.csv')[0].split('_')[:-1])
                # Use pre-compiled regex pattern
                pairs = self.filename_pattern.findall(new_string)
                cleaned_data = {k.lstrip('_'): v for k, v in dict(pairs).items()}
                
                # Reconstruct string for display name
                result_string = "_".join([f"{key}[{value}]" for key, value in cleaned_data.items()])
                
                lot = cleaned_data.get(self.GeneratorGroup, 'NA')
                plotPath = os.path.join(self.dataSrc, path, unit)
                
                # Read Data (I/O Intensive) with encoding fallback
                try:
                    plotDf = pd.read_csv(plotPath, index_col=False, encoding='utf-8', on_bad_lines='skip')
                except UnicodeDecodeError:
                    try:
                        plotDf = pd.read_csv(plotPath, index_col=False, encoding='latin-1', on_bad_lines='skip')
                    except UnicodeDecodeError:
                        plotDf = pd.read_csv(plotPath, index_col=False, encoding='cp1252', on_bad_lines='skip')
                
                # --- Filter Data by User-Defined Frequency Range ---
                # Apply filter if either User_StartFreq OR User_StopFreq is defined
                if user_start_freq is not None or user_stop_freq is not None:
                    if 'Freq' in plotDf.columns:
                        # Apply frequency range filter
                        if user_start_freq is not None and user_stop_freq is not None:
                            # Both start and stop defined
                            plotDf = plotDf[(plotDf['Freq'] >= user_start_freq) & (plotDf['Freq'] <= user_stop_freq)]
                        elif user_start_freq is not None:
                            # Only start defined - filter from start frequency onwards
                            plotDf = plotDf[plotDf['Freq'] >= user_start_freq]
                        elif user_stop_freq is not None:
                            # Only stop defined - filter up to stop frequency
                            plotDf = plotDf[plotDf['Freq'] <= user_stop_freq]

                # --- Trace Logic: By Lot ---
                if self.lotFlag:
                    # Find color index based on Lot configuration
                    try:
                        lot_match = self.colordf[self.colordf[self.GeneratorGroup].astype(str).str.contains(lot, na=False)]
                        if not lot_match.empty:
                            color_idx = int(lot_match[f'{self.GeneratorGroup}_Index'].iloc[0])
                        else:
                            color_idx = 1 # Default
                    except Exception:
                        color_idx = 1
                    
                    # Use set for O(1) lookup - show legend only once per group
                    legendFlag = lot not in tempLotSet
                    legend_group_name = f"Group-[{lot}]"
                    # legend_group_name = f"{self.GeneratorGroup}[{lot}]"
                    
                    fig.add_trace(go.Scatter(
                        x=plotDf["Freq"],
                        y=plotDf[f"{Param}_Mag"],
                        mode='lines',
                        name=legend_group_name,
                        legendgroup=legend_group_name,  # Group all traces with same lot
                        showlegend=legendFlag,                      
                        line=dict(color=self.colorData.get(str(color_idx), 'black')),
                        hovertemplate=(
                            f"<b>{Param}-{lot}</b><br>" +
                            "Frequency: %{x}<br>" +
                            f"{Param}: %{{y}}<extra></extra>"
                        )
                    ))
                    tempLotSet.add(lot)

                # --- Trace Logic: By Unit ---
                elif self.unitFlag:
                    unitCheck = unit.split('.csv')[0]
                    # Use set for O(1) lookup - show legend only once per unit
                    legendFlag = unitCheck not in tempUnitSet
                    
                    # Fetch color from unit dictionary, default to black if missing
                    unit_color = self.unitDic.get(str(unitCheck), 'black')
                    
                    fig.add_trace(go.Scatter(
                        x=plotDf["Freq"],
                        y=plotDf[f"{Param}_Mag"],
                        mode='lines',
                        name=f"{result_string}",
                        legendgroup=result_string,  # Group all traces with same unit
                        showlegend=legendFlag,
                        line=dict(color=unit_color),                      
                        hovertemplate=(
                            f"<b>{Param}-{unitCheck}</b><br>" +
                            "Frequency: %{x}<br>" +
                            f"{Param}: %{{y}}<extra></extra>"
                        )
                    ))
                    tempUnitSet.add(unitCheck)
    
                # --- Trace Logic: Default (Sequential Color) ---
                else:              
                    fig.add_trace(go.Scatter(
                        x=plotDf["Freq"],
                        y=plotDf[f"{Param}_Mag"],
                        mode='lines',
                        name=result_string,
                        line=dict(color=self.colorData.get(str(colorCount), 'black')),
                        hovertemplate=(
                            f"<b>{Param}-{result_string}</b><br>" +
                            "Frequency: %{x}<br>" +
                            f"{Param}: %{{y}}<extra></extra>"
                        )  
                    ))
                    
                    colorCount += 1
                    if colorCount > len(self.colorData):
                        colorCount = 1

            # --- Add Spec Lines ---
            if self.SpecFlag:   
                self.specFig(fig, True, filtered_spec_df, MapParam)

            # --- Update Layout (Axis, Titles) ---
            if figFlag:
                # Determine ranges from data if available, else standard
                xMin = plotDf["Freq"].min() if 'plotDf' in locals() else 0
                xMax = plotDf["Freq"].max() if 'plotDf' in locals() else 0
                
                # Override with user-defined frequency range if provided
                if user_start_freq is not None:
                    xMin = user_start_freq
                if user_stop_freq is not None:
                    xMax = user_stop_freq
                
                # Build xaxis configuration with optional dtick
                xaxis_config = {
                    'tickformat': ".5s",
                    'tickangle': 45,
                    'range': [
                        min(fig.layout.xaxis.range[0], xMin) if fig.layout.xaxis.range else xMin,
                        max(fig.layout.xaxis.range[1], xMax) if fig.layout.xaxis.range else xMax
                    ]
                }
                
                # Add dtick if x_step is provided
                if x_step is not None:
                    xaxis_config['dtick'] = x_step
                
                # Build yaxis configuration with optional dtick
                yaxis_config = {}
                if y_step is not None:
                    yaxis_config['dtick'] = y_step
                
                fig.update_layout(
                    title=dict(
                        text=f"{Title}",
                        font=dict(size=20, color='black', family='Arial, bold')
                    ),
                    xaxis_title="Frequency",
                    xaxis=xaxis_config,
                    yaxis=yaxis_config if yaxis_config else None,
                    legend=dict(font=dict(color='black', family='Arial, bold')),
                    dragmode='zoom',
                    newshape=dict(line_color='black', line_width=2),
                    modebar_add=['drawline', 'eraseshape', 'toggleSpikeLines']
                )

            # --- Save Output Files ---
            sanitized_title = re.sub(r'[<>:"/\\|?*]', '', Title)
            image_path = os.path.join(self.imagePath, f"{sanitized_title}.png")
            html_path = os.path.join(self.htmlPath, f"{sanitized_title}.html")
            
            fig.write_image(image_path, width=1024, height=673)
            fig.write_html(html_path)

        except Exception as e:
            self.logger.error(f"Failed to process row '{row.get('Plot Title', 'Unknown')}': {e}")

    def process_data(self):
        """
        Main execution method: Sets up thread pool to process rows concurrently.
        """
        try:
            start_time = time.time()
            self.logger.info(f"Starting batch processing of {len(self.df)} plots...")
    
            # Increase max_workers for I/O-bound tasks (file reading/writing)
            # Optimal value is typically 2-5x CPU count for I/O operations
            max_workers = min(32, (os.cpu_count() or 1) * 4)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for take in range(len(self.df)):
                    row = self.df.iloc[take]
                    futures.append(executor.submit(self.process_row, row))

                for future in as_completed(futures):
                    # We check result to catch any exceptions raised within threads
                    # that weren't caught in process_row
                    try:
                        future.result()
                    except Exception as thread_e:
                        self.logger.error(f"Thread execution failed: {thread_e}")

            end_time = time.time()
            total_duration = end_time - start_time
            
            print(f"Total time taken: {total_duration:.2f} seconds")
            print("All images have been saved.")
            
            self.logger.info(f"Batch processing completed in {total_duration:.2f} seconds.")

        except Exception as e:
            self.logger.critical(f"Critical error in process_data: {e}", exc_info=True)
            print(e)

if __name__ == "__main__":
    # Example usage - Uses relative paths from current working directory
    # This will work on any Windows laptop as long as the script is run from the project root
    
    # Get the current working directory (should be project root)
    project_root = os.getcwd()
    
    # Build paths relative to project root
    refer = os.path.join(project_root, r"setting\CFG\Batch\Module_20250307_233428.csv")
    dataSrc = os.path.join(project_root, r"dataset\results")
    htmlPath = os.path.join(project_root, r"output\htmlAuto")
    imgPath = os.path.join(project_root, r"output\image")
    
    # Ensure directories exist (optional safety check)
    os.makedirs(htmlPath, exist_ok=True)
    os.makedirs(imgPath, exist_ok=True)

    processor = ModuleGenerator(refer, dataSrc, htmlPath, imgPath, False, False, False, "Lot")
    processor.process_data()