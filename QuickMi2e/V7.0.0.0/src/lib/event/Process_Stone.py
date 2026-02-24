import os
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import json
import threading

# --- Custom Logger Import ---
from lib.helper.Logger import LoggerSetup 

class stoneGen:
    def __init__(self, srcPath, htmlPath, imgPath, flag, x_step=None, y_step=None):
        # --- Initialize Logger ---
        self.logger = LoggerSetup(
            log_name='stoneGen modulegenerator', 
            log_dir_relative_path=r"output\Log"
        ).get_logger()
        
        self.logger.info("Initializing stoneGen class...")

        try:
            self.srcPath = srcPath
            self.htmlPath = htmlPath
            self.imgPath = imgPath
            self.overlapFlag = flag
            self.x_step = x_step
            self.y_step = y_step
            self.extractList = dict()
            
            # Create output directories if they don't exist
            os.makedirs(self.htmlPath, exist_ok=True)
            os.makedirs(self.imgPath, exist_ok=True)
            
            # Load color reference from colorReference.json
            color_ref_path = os.path.join(os.getcwd(), 'setting', 'CFG', 'DefineUnitColor', 'colorReference.json')
            if os.path.exists(color_ref_path):
                with open(color_ref_path, 'r') as f:
                    self.colordata = json.load(f)
                self.logger.info(f"Loaded {len(self.colordata)} colors from colorReference.json")
            else:
                # Fallback to default colors if file not found
                self.colordata = {str(i): f"#{i:06x}" for i in range(1, 24)}
                self.logger.warning("colorReference.json not found, using default colors")
            
            self.logger.info(f"X-step: {x_step}, Y-step: {y_step}")

        except Exception as e:
            self.logger.critical(f"Error initializing stoneGen: {e}")
            raise

    def extract_channel_csv_files(self):
        self.logger.info(f"Scanning source directory: {self.srcPath}")
        try:       
            channel_regex = re.compile(r'CH(\d+)')
            
            if not os.path.exists(self.srcPath):
                raise FileNotFoundError(f"Source path not found: {self.srcPath}")

            extracted_dirs = os.listdir(self.srcPath)
            channel_groups = dict()

            for dir_name in extracted_dirs:
                # Skip "All files" folder
                if dir_name == "All files":
                    self.logger.info(f"Skipping 'All files' folder")
                    continue
                
                dir_path = os.path.join(self.srcPath, dir_name)
                if not os.path.isdir(dir_path):
                    continue

                csv_files = [f for f in os.listdir(dir_path) if f.endswith('.csv')]

                for f in csv_files:
                    match = channel_regex.search(f)
                    if match:
                        ch_number = int(match.group(1))
                        file_path = os.path.join(dir_path, f)

                        if ch_number not in channel_groups:
                            channel_groups[ch_number] = []
                        channel_groups[ch_number].append(file_path)

            self.extractList = channel_groups
            self.logger.info(f"Scan complete. Found {len(self.extractList)} channel groups.")
            return self.extractList
        
        except Exception as e:
            self.logger.error(f"Error extracting channel CSV files: {e}", exc_info=True)
            raise

    def filterDbSparams(self, dataframe):
        if not dataframe.empty:
            header = list(dataframe.columns)
            return [col for col in header if "dB:" in col]
        else:
            # Low-level warning, kept silent to avoid log spam in loops
            return None

    def process(self, ch_number, file_path):
        # [PERFORMANCE CRITICAL] 
        # No INFO/DEBUG logs here to prevent thread locking/IO slowdowns during parallel execution.
        try:
            name = os.path.basename(file_path).split('.')[0]
            df = pd.read_csv(file_path)
            sParamHeader = self.filterDbSparams(df)

            if not sParamHeader:
                return

            if self.overlapFlag:
                fig = go.Figure()
                xMin, xMax = float('inf'), float('-inf')

                # Color counter for this chart only (resets for each chart)
                trace_color_index = 1

                for sparam in sParamHeader:
                    x_values = df["freq[HZ]"]
                    y_values = df[sparam]
                    xMin = min(xMin, x_values.min())
                    xMax = max(xMax, x_values.max())

                    # Get color for this trace from colorReference.json
                    color_key = str(trace_color_index)
                    trace_color = self.colordata.get(color_key, self.colordata.get("1", "#CC092F"))
                    
                    # Increment and wrap around for next trace in this chart
                    trace_color_index += 1
                    if trace_color_index > len(self.colordata):
                        trace_color_index = 1

                    fig.add_trace(go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode='lines',
                        line=dict(color=trace_color),
                        name=f"CH{ch_number}_{sparam}",
                        showlegend=True,
                        hovertemplate=(
                        f"<b>CH{ch_number}_{sparam}</b><br>" +
                        "Frequency: %{x}<br>" +
                        f"{sparam}: %{{y}}<extra></extra>"
                            )
                    ))

                fig = self.figSetting(fig, ch_number, xMin, xMax, name)
                imgFilename = f"{name}.png"
                htmlFilename = f"{name}.html"
                fig.write_image(os.path.join(self.imgPath, imgFilename), width=1024, height=673)
                fig.write_html(os.path.join(self.htmlPath, htmlFilename))

            else:
                # Non-overlap mode: Each S-parameter gets its own chart
                # Color counter resets for each individual chart
                for sparam_index, sparam in enumerate(sParamHeader):
                    fig = go.Figure()
                    x_values = df["freq[HZ]"]
                    y_values = df[sparam]
                    xMin = x_values.min()
                    xMax = x_values.max()

                    # For non-overlap mode, each chart has only 1 trace
                    # Use color 1 for single trace, or cycle through if needed
                    # Since there's only 1 trace per chart, always use color 1
                    trace_color = self.colordata.get("1", "#CC092F")

                    fig.add_trace(go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode='lines',
                        line=dict(color=trace_color),
                        name=f"CH{ch_number}_{sparam}",
                        showlegend=True,
                        hovertemplate=(
                        f"<b>CH{ch_number}_{sparam}</b><br>" +
                        "Frequency: %{x}<br>" +
                        f"{sparam}: %{{y}}<extra></extra>"
                            )
                    ))

                    fig = self.figSetting(fig, ch_number, xMin, xMax, name)

                    sparam_clean = re.search(r"S\d+", sparam)
                    suffix = sparam_clean.group() if sparam_clean else sparam

                    imgFilename = f"{name}_{suffix}.png"
                    htmlFilename = f"{name}_{suffix}.html"
                    fig.write_image(os.path.join(self.imgPath, imgFilename), width=1024, height=673)
                    fig.write_html(os.path.join(self.htmlPath, htmlFilename))

        except Exception as e:
            # Only log actual errors
            self.logger.error(f"Error processing file {file_path}: {e}")

    def savePlots(self):
        self.logger.info("Starting parallel plot generation...")
        try:
            # Increase max_workers for I/O-bound tasks (file reading/writing)
            # Optimal value is typically 2-5x CPU count for I/O operations
            max_workers = min(32, (os.cpu_count() or 1) * 4)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for ch_number, file_list in self.extractList.items():
                    for file_path in file_list:
                        futures.append(executor.submit(self.process, ch_number, file_path))

                # Wait for completion with as_completed for better progress tracking
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"Error in processing task: {e}")
            
            self.logger.info("All plots generated and saved successfully.")

        except Exception as e:
            self.logger.error(f"Error saving plots: {e}", exc_info=True)

    def figSetting(self, fig, ch_number, xMin, xMax, name):
        try:
            # Build xaxis configuration with optional dtick
            xaxis_config = dict(
                tickformat=".5s",
                tickangle=90,
                range=[xMin, xMax]
            )
            if self.x_step is not None:
                xaxis_config['dtick'] = self.x_step
            
            # Build yaxis configuration with optional dtick
            yaxis_config = dict(
                title="Amplitude"
            )
            if self.y_step is not None:
                yaxis_config['dtick'] = self.y_step
            
            fig.update_layout(
                title=dict(
                    text=f"{name}",
                    font=dict(size=20, color='black', family='Arial, bold')
                ),
                xaxis_title="Frequency",
                xaxis=xaxis_config,
                yaxis=yaxis_config,
                legend=dict(font=dict(color='black', family='Arial, bold')),
                dragmode='zoom',
                newshape=dict(line_color='black',line_width=2),
                modebar_add=['drawline', 'eraseshape','toggleSpikeLines']

            )
            return fig
        
        except Exception as e:
            self.logger.error(f"Error setting figure properties: {e}")
            raise # Re-raise to be caught by process()
      
    @property
    def count_plots_to_generate(self):
        self.logger.info("Counting potential plots...")
        try:
            total_plots = 0

            for ch_number, file_list in self.extractList.items():
                for file_path in file_list:
                    try:
                        # Reading CSV here just to count is expensive, but keeping logic as requested.
                        # No logging inside loop.
                        df = pd.read_csv(file_path)
                        sParamHeader = self.filterDbSparams(df)

                        if not sParamHeader:
                            continue

                        if self.overlapFlag:
                            # One plot per file
                            total_plots += 1
                        else:
                            # One plot per s-parameter
                            total_plots += len(sParamHeader)

                    except Exception as e:
                        self.logger.warning(f"Skipping file in count due to error: {file_path} - {e}")

            self.logger.info(f"Total estimated plots: {total_plots}")
            return total_plots
        except Exception as e:
            self.logger.error(f"Error counting plots to generate: {e}")
            return 0


if __name__ == "__main__":
    htmlPath = r'C:\Users\ro898771\Documents\QuickMi2e\output\AutoHtml'
    imgPath = r'C:\Users\ro898771\Documents\QuickMi2e\output\AutoImage'
    srcPath = r'C:\Users\ro898771\Documents\QuickMi2e\dataset\results'

    try:
        Test = stoneGen(srcPath, htmlPath, imgPath, True)
        Test.extract_channel_csv_files()
        print(Test.count_plots_to_generate, "plots will be generated.")
        Test.savePlots()
    except Exception as main_e:
        print(f"Execution failed: {main_e}")