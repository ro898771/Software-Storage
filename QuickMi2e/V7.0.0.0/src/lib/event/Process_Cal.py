import os
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import re

# --- Custom Logger Import ---
from lib.helper.Logger import LoggerSetup 

class CalGen:
    def __init__(self, srcPath, htmlPath, imgPath, specValue, title):
        # --- Initialize Logger ---
        self.logger = LoggerSetup(
            log_name='Cal modulegenerator', 
            log_dir_relative_path=r"output\Log"
        ).get_logger()
        
        self.logger.info("Initializing CalGen class...")

        try:
            self.htmlPath  = htmlPath
            self.imagePath = imgPath
            self.srcPath   = srcPath
            self.tempDict  = dict()
            self.specValue = specValue
            
            if os.path.exists(srcPath):
                self.totalFile = sum(len(files) for _, _, files in os.walk(srcPath))
                self.logger.info(f"Total files found in source: {self.totalFile}")
            else:
                self.logger.warning(f"Source path does not exist: {srcPath}")
                self.totalFile = 0

            # Only load batch file if title is provided and not empty
            if title and str(title).strip():
                refdataPath = os.path.join(os.getcwd(), 'setting', 'CFG', 'Batch', title)
                if os.path.exists(refdataPath) and os.path.isfile(refdataPath):
                    self.refData = pd.read_csv(refdataPath)
                    self.logger.info(f"Loaded reference data from: {refdataPath}")
                else:
                    self.logger.warning(f"Reference data file not found or invalid: {refdataPath}")
                    self.refData = pd.DataFrame()
            else:
                # No batch file selected - use default CH_S-Parameter naming
                self.logger.info("No batch file selected. Using default CH_S-Parameter naming.")
                self.refData = pd.DataFrame()

        except Exception as e:
            self.logger.critical(f"Initialization failed: {e}")
            print(e)

    def getData(self):
        # logging excluded from inner loop for performance
        try:
            count = 0
            for root, dirs, files in os.walk(self.srcPath):
                for file in files:
                    if file.endswith('.csv'):
                        parent_dir = os.path.basename(root)
                        if parent_dir not in self.tempDict:
                            self.tempDict[parent_dir] = []
                        self.tempDict[parent_dir].append(os.path.join(root, file))
                        count += 1
            
            self.logger.info(f"Scanned {count} CSV files across {len(self.tempDict)} folders.")

        except Exception as e:
            self.logger.error(f"Error in getData: {e}")
            print(f"An error occurred: {e}")


    def group_files_by_ch_sparam(self, tempDict):
        grouped = defaultdict(list)
        for ch, files in tempDict.items():
            for f in files:
                sparam = os.path.basename(f).split('.')[0].split('_')[-1]
                key = (ch, sparam)
                grouped[key].append(f)
        return grouped


    def remove_s_param(self, filename):
        name = os.path.basename(filename).split('.')[0]
        cleaned = re.sub(r'_S\d+$', '', name)
        return cleaned
    
    def process_group(self, ch, sparam, file_list, specdf):
        try:
            fig = go.Figure()
            xMin, xMax = float('inf'), float('-inf')

            # [PERFORMANCE] Trace generation loop - Logging skipped
            for file in file_list:
                df = pd.read_csv(file)
                name = os.path.basename(file).split('.')[0]
                name = self.remove_s_param(name)

                x_values = df["Freq"] if "Freq" in df.columns else df["freq[HZ]"]
                y_values = df[f"{sparam}"]

                xMin = min(xMin, x_values.min())
                xMax = max(xMax, x_values.max())

                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='lines',
                    name=name,
                    showlegend=True,
                    hovertemplate=(
                        f"<b>{name}</b><br>" +
                        "Frequency: %{x}<br>" +
                        f"{sparam}: %{{y}}<extra></extra>"
                            )
                ))
            
            # Add Spec Limits if available
            if specdf is not None and "USL" in specdf.columns and "LSL" in specdf.columns:
                usl_valid = specdf["USL"].notnull() & (specdf["USL"] != 0)
                lsl_valid = specdf["LSL"].notnull() & (specdf["LSL"] != 0)

                fig.add_trace(go.Scatter(
                    x=x_values[usl_valid],
                    y=specdf["USL"][usl_valid],
                    mode='lines',
                    line=dict(color="Red", width=2),
                    showlegend=False
                ))
                fig.add_trace(go.Scatter(
                    x=x_values[lsl_valid],
                    y=specdf["LSL"][lsl_valid],
                    mode='lines',
                    line=dict(color="Black", width=2),
                    showlegend=False
                ))

            # Determine Title
            if not self.refData.empty:
                filtered_value = self.refData.loc[(self.refData ['S-Parameter'] == sparam) 
                                                & (self.refData ['Channel Number'] == ch), 'Plot Title']

                title = filtered_value.iloc[0] if not filtered_value.empty else f"{ch}_{sparam}"
            else:
                title = f"{ch}_{sparam}"

            fig.update_layout(
                title=dict(
                    # text=f"{ch}_{sparam}",
                    text=f"{title}",
                    font=dict(size=20, color='black', family='Arial, bold')
                ),
                xaxis_title="Frequency",
                xaxis=dict(
                    tickformat=".5s",
                    tickangle=90,
                    range=[xMin, xMax]
                ),
                legend=dict(font=dict(color='black', family='Arial, bold')),
                dragmode='zoom',
                newshape=dict(line_color='black',line_width=2),
                modebar_add=['drawline', 'eraseshape','toggleSpikeLines']
            )

            imgFilename = f"{title}.png"
            htmlFilename = f"{title}.html"

            # Create output directories if they don't exist
            os.makedirs(self.imagePath, exist_ok=True)
            os.makedirs(self.htmlPath, exist_ok=True)

            fig.write_image(os.path.join(self.imagePath, imgFilename), width=1024, height=673)
            fig.write_html(os.path.join(self.htmlPath, htmlFilename))

        except Exception as e:
            self.logger.error(f"Error processing group {ch}_{sparam}: {e}")
            # print(f"Error combining group {ch}_{sparam}: {e}")

    def savePlots(self):
        self.logger.info("Starting savePlots process...")
        try:
            self.getData()
            grouped = self.group_files_by_ch_sparam(self.tempDict)
            
            self.logger.info(f"Identified {len(grouped)} plot groups to generate.")

            # Increase max_workers for I/O-bound tasks (file reading/writing)
            # Optimal value is typically 2-5x CPU count for I/O operations
            max_workers = min(32, (os.cpu_count() or 1) * 4)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for (ch, sparam), files in grouped.items():
                    # Find spec file for this group
                    specdf = None
                    tfile = None
                    for file in files:
                        name = os.path.basename(file).split('.')[0]
                        name = self.remove_s_param(name)
                        if self.specValue and self.specValue in name:
                            tfile = file
                            specdf = pd.read_csv(tfile)
                            break
                    futures.append(executor.submit(self.process_group, ch, sparam, files, specdf))

                # Wait for completion with as_completed for better progress tracking
                for future in as_completed(futures):
                    # Retrieve result to catch any exceptions raised inside threads
                    try:
                        future.result()
                    except Exception as thread_e:
                        self.logger.error(f"Thread execution failed: {thread_e}")

            self.logger.info("All plots generated and saved successfully.")

        except Exception as e:
            self.logger.critical(f"Critical error in savePlots: {e}", exc_info=True)
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    htmlPath = r'C:\Users\ro898771\Documents\QuickMi2e\output\AutoHtml'
    imgPath = r'C:\Users\ro898771\Documents\QuickMi2e\output\AutoImage'
    srcPath = r'C:\Users\ro898771\Documents\QuickMi2e\dataset\results'
    
    # Spec value logic needs a valid string to match, passing None if not used
    # Title also needs a valid filename or None
    Test = CalGen(srcPath, htmlPath, imgPath, specValue="Golden", title=None)
    Test.savePlots()