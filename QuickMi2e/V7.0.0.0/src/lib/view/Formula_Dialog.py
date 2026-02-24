import os
import threading
from PySide6.QtWidgets import QDialog, QFileDialog

# Local Imports
from ui.ui_build.ui_formula import Ui_Formula
from lib.event.F_Formula import FormulaProcessor
from lib.setting.IconManager import IconManager

class Formula_Dialog:
    def __init__(self, error_handle, formulaComboBox, Manual_lineEdit, update_progress, update_text_edit_color, update_progress_text, progressing_progress_text, complete_progress_text):
        # ---------------------------------------------------------
        # 1. Assign External Callbacks & Widgets
        # ---------------------------------------------------------
        self.handle_error = error_handle
        self.Formula_comboBox = formulaComboBox
        self.Manual_lineEdit = Manual_lineEdit
        self.update_progress = update_progress
        self.update_text_edit_color = update_text_edit_color
        self.update_progress_text = update_progress_text
        self.progressing_progress_text = progressing_progress_text
        self.complete_progress_text = complete_progress_text

        # ---------------------------------------------------------
        # 2. Initialize Logic (Formula Processor)
        # ---------------------------------------------------------
        # Used os.path.join for safer path handling across operating systems
        db_path = os.path.join(os.getcwd(), "setting", "CFG", "Formula", "formula_database.txt")
        self.Formula = FormulaProcessor(procedure_db_path=db_path)

        # ---------------------------------------------------------
        # 3. Initialize UI Components
        # ---------------------------------------------------------
        self.formulaDialog = QDialog()
        self.uiformula = Ui_Formula()
        self.uiformula.setupUi(self.formulaDialog)
        
        self.formulaDialog.setWindowTitle("Formula Configuration")
        self.uiformula.FormulalistEdit.setText(self.Formula.get_sympy_operator_help())

        # ---------------------------------------------------------
        # 4. Initialize Icons
        # ---------------------------------------------------------
        self.Icon = IconManager()
        self.uiformula.FormulaAddButton.setIcon(self.Icon.Plus)
        self.uiformula.FormulaSaveButton.setIcon(self.Icon.Gen)
        self.uiformula.FormulaCleanButton.setIcon(self.Icon.Undo)
        self.uiformula.FormulaLoadButton.setIcon(self.Icon.Param)
        self.uiformula.FormulaShowButton.setIcon(self.Icon.Tick)

    def formula_dialog(self):
        """Sets up connections and opens the dialog."""
        try:
            # Signal Connections
            self.uiformula.FormulaShowButton.clicked.connect(self.AppendEditor)
            self.uiformula.FormulaCancelButton.clicked.connect(self.formulaDialog.close)
            self.uiformula.FormulaAddButton.clicked.connect(self.AddFormula)
            self.uiformula.FormulaSaveButton.clicked.connect(self.save_formula_procedure)
            self.uiformula.FormulaLoadButton.clicked.connect(self.checkFormulaHeader)
            
            # Inline lambda for simple UI clearing
            self.uiformula.FormulaCleanButton.clicked.connect(
                lambda: self.uiformula.FormulaEditortextEdit.setPlainText("")
            )
            
            # Fixed: Removed 'lambda:' so the function actually executes when clicked
            self.uiformula.FormulaTracktoolButton.clicked.connect(self.Extract_directory)

            self.formulaDialog.exec()

        except Exception as e:
            self.handle_error(f"{str(e)}")

    # =========================================================================
    # UI INTERACTION METHODS
    # =========================================================================

    def checkFormulaHeader(self):
        """Loads formula list into the Header text edit."""
        self.Formula.set_csv_path(f"{self.uiformula.FormulaTrackPathEdit.text()}")
        sorted_string = "\n".join(f">> {item}" for item in sorted(map(str, self.Formula.getList())))
        self.uiformula.FormulaHeadertextEdit.setText(sorted_string)

    def AppendEditor(self):
        """Loads the current database content into the main Editor."""
        try:
            formulaText = self.Formula.get_procedure_db_as_string()
            self.uiformula.FormulaEditortextEdit.setText(formulaText)
        except Exception as e:
            self.handle_error(f"{str(e)}")

    def AddFormula(self):
        """Creates a new empty formula template in the database with the specified name."""
        try:
            FormulaNewName = self.uiformula.FormulaAddEdit.text()
            
            # Validate that a name was provided
            if not FormulaNewName or not FormulaNewName.strip():
                self.handle_error("Please enter a formula name in the 'Add' field")
                return
            
            # Create an empty formula template (just START and END tags with no content)
            empty_formula = ""  # Empty string means no formula steps
            
            # Append the new empty formula to the database
            self.Formula.append_procedure_to_db(FormulaNewName.strip(), empty_formula)
            
            # Refresh the editor to show the updated database
            self.uiformula.FormulaEditortextEdit.setText(self.Formula.get_procedure_db_as_string())
            
            # Clear the Add field after successful addition
            self.uiformula.FormulaAddEdit.clear()
            
        except Exception as e:
            self.handle_error(f"{str(e)}")

    def save_formula_procedure(self):
        """Saves the current editor text to the physical file."""
        try:
            formulaText = self.uiformula.FormulaEditortextEdit.toPlainText()
            self.Formula.save_text_to_file(formulaText)
        except Exception as e:
            self.handle_error(f"{str(e)}")

    def refresh_formula(self):
        """Refreshes the ComboBox with available procedures."""
        try:
            self.Formula_comboBox.clear()
            text = self.Formula.get_available_procedures()
            self.Formula_comboBox.addItems(text)
        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    # =========================================================================
    # FILE SYSTEM & EXECUTION METHODS
    # =========================================================================

    def Extract_directory(self):
        """Opens File Dialog to select directory."""
        try:
            current_path = self.uiformula.FormulaTrackPathEdit.text()
            
            if current_path:
                formula_directory = f"{current_path}"
            else:
                formula_directory = os.path.join(os.getcwd(), "dataset", "results")

            if not os.path.exists(formula_directory):
                self.handle_error(f"The directory '{formula_directory}' does not exist!")
                return

            # QFileDialog returns a tuple (filename, filter), we only need [0]
            directory = QFileDialog.getOpenFileName(self.formulaDialog, "Select File", formula_directory)
            
            if directory[0]:  # Only update if user didn't cancel
                self.uiformula.FormulaTrackPathEdit.clear()
                self.uiformula.FormulaTrackPathEdit.setText(directory[0])

        except Exception as e:
            self.handle_error(f"Error in Extract_directory: {str(e)}")

    def formulaExecute(self):
        """Threaded wrapper for formula execution to prevent UI freezing."""
        try:
            thread = threading.Thread(target=self._formulaExecuteTask)
            thread.start()
        except Exception as e:
            self.handle_error(f"\n{str(e)}")
    
    def _formulaExecuteTask(self):
        """Executes the formula processing logic in a separate thread."""
        # 1. Get and Normalize Path
        base_path_str = self.Manual_lineEdit.text()
        base_path = os.path.normpath(base_path_str)

        try:
            # 2. Validate directory
            if not os.path.isdir(base_path):
                raise NotADirectoryError(f"{base_path} is not a directory")

            # Initialize progress
            self.update_progress(0)
            self.progressing_progress_text("\nStarting Formula Execution...")
            
            # 3. Get procedure name
            procedure_name = self.Formula_comboBox.currentText()
            if not procedure_name:
                raise ValueError("Please select a formula from the dropdown")
            
            self.progressing_progress_text(f"\nSelected Formula: {procedure_name}")
            
            # 4. Get list of files
            DirectoryItem = os.listdir(base_path)
            csv_files = [item for item in DirectoryItem if item.endswith('.csv')]
            
            if not csv_files:
                raise ValueError(f"No CSV files found in {base_path}")
            
            full_paths = [os.path.join(base_path, item) for item in csv_files]
            total_files = len(full_paths)
            
            self.progressing_progress_text(f"\nFound {total_files} CSV files to process")
            self.update_progress(5)
            
            # 5. Process each file
            for idx, file in enumerate(full_paths, start=1):
                try:
                    # Update progress text for current file
                    filename = os.path.basename(file)
                    self.progressing_progress_text(f"\nProcessing [{idx}/{total_files}]: {filename}")
                    
                    # Load CSV
                    self.Formula.set_csv_path(file)
                    
                    # Load and Run Procedure
                    self.Formula.load_procedure_from_db(procedure_name)
                    self.Formula.run()
                    
                    # Save Result
                    output_file = f"{file}"
                    self.Formula.save_result_to_csv(output_file)
                    
                    # Update UI Progress (5% to 95% range for file processing)
                    progress_value = 5 + int((idx / total_files) * 90)
                    self.update_progress(progress_value)
                    self.progressing_progress_text(f"Saved: {filename}")
                    
                except Exception as file_error:
                    self.progressing_progress_text(f"\nError processing {filename}: {str(file_error)}")
                    print(f"Error processing {file}: {str(file_error)}")
                    continue

            # 6. Complete
            self.update_progress(100)
            self.update_text_edit_color(100)
            self.complete_progress_text(f"\nFormula Execution Completed! Processed {total_files} files")

        except ValueError as ve:
            print(f"\n{str(ve)}")
            self.handle_error(f"\n{str(ve)}")

        except FileNotFoundError:
            print(f"Error: Path not found at {base_path}")
            self.handle_error(f"\nPath not found: {base_path}")

        except NotADirectoryError as nde:
            print(f"Error: {str(nde)}")
            self.handle_error(f"\n{str(nde)}")
        
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            self.handle_error(f"\nUnexpected error: {str(e)}")