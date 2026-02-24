import pandas as pd
import numpy as np
from sympy import sympify, Symbol, lambdify
from typing import List, Dict, Any, Optional
import logging
import os

# --- Custom Logger Import ---
from lib.helper.Logger import LoggerSetup 

class FormulaProcessor:
    """
    A class to manage, save, load, and apply multi-step
    symbolic formulas to pandas DataFrames.
    
    Uses a .txt file for the procedure database instead of JSON.
    """
    
    def __init__(self, procedure_db_path: str = 'procedures_database.txt'):
        """
        Initializes the processor.
        
        Args:
            procedure_db_path (str): Default path to the procedures .txt database.
        """
        # --- Initialize Logger ---
        self.logger = LoggerSetup(
            log_name='FormulaProcessor', 
            log_dir_relative_path=r"output\Log"
        ).get_logger()

        self.procedure_db_path = procedure_db_path
        
        # --- Internal State ---
        self.current_procedure_steps = []
        self.user_constants = {}
        self.original_df = None
        self.result_df = None

    # --- 1. CSV Path Setting (Req 1) ---
    def set_csv_path(self, csv_path: str):
        """
        (Req 1) Sets the file path for the input CSV.
        """
        self.logger.info(f"Setting input CSV path: {csv_path}")
        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
                
            self.original_df = pd.read_csv(csv_path)
            self.logger.info(f"CSV loaded successfully. Shape: {self.original_df.shape}")
        except Exception as e:
            self.logger.critical(f"Failed to load CSV: {e}", exc_info=True)
            raise

    # --- 2. Procedure DB Path Setting ---
    def set_procedure_db_path(self, db_path: str):
        """
        Sets the file path for the .txt procedure database.
        """
        self.logger.info(f"Procedure database path updated to: {db_path}")
        self.procedure_db_path = db_path

    # --- 3. Formula String Input (Req 2) ---
    def set_procedure_from_string(self, procedure_string: str):
        """
        (Req 2) Parses a multi-line string and sets it as the active procedure.
        """
        try:
            self.current_procedure_steps = self._parse_procedure_from_string(procedure_string)
            self.logger.info(f"Active procedure set from string ({len(self.current_procedure_steps)} steps).")
        except Exception as e:
            self.logger.error(f"Error parsing procedure string: {e}")

    # --- 4. Save Procedure ---
    def save_procedure_to_db(self, title: str):
        """
        Saves the *currently active* procedure to the .txt file.
        """
        if not self.current_procedure_steps:
            self.logger.warning("Attempted to save empty procedure. Use set_procedure_from_string() first.")
            return
            
        try:
            db_data = self._load_equation_db(self.procedure_db_path)
            db_data[title] = self.current_procedure_steps
            self._save_equation_db(self.procedure_db_path, db_data)
            self.logger.info(f"Procedure '{title}' saved to {self.procedure_db_path}.")
        except Exception as e:
            self.logger.error(f"Error saving procedure '{title}': {e}")

    # --- 5. Load Procedure ---
    def load_procedure_from_db(self, title: str) -> bool:
        """
        Loads a procedure from the .txt file by key and sets it as active.
        """
        try:
            db_data = self._load_equation_db(self.procedure_db_path)
            
            if title not in db_data:
                self.logger.error(f"Procedure '{title}' not found in {self.procedure_db_path}.")
                self.current_procedure_steps = []
                return False
                
            self.current_procedure_steps = db_data[title]
            self.logger.info(f"Successfully loaded procedure '{title}' ({len(self.current_procedure_steps)} steps).")
            return True
        except Exception as e:
            self.logger.error(f"Error loading procedure from DB: {e}")
            return False
        
    # --- 6. (NEW) Get Procedure List ---
    def get_available_procedures(self) -> List[str]:
        """
        (NEW) Loads the procedure database and returns a list of all
        available procedure titles (keys).
        """
        try:
            db_data = self._load_equation_db(self.procedure_db_path)
            return list(db_data.keys())
        except Exception as e:
            self.logger.error(f"Error retrieving available procedures: {e}")
            return []
    
    def getList(self):
        if self.original_df is not None:
            return self.original_df.loc[:, (self.original_df != 0).any()].columns.tolist()
        return []

    # --- 7. Run Program ---
    def run(self) -> Optional[pd.DataFrame]:
        self.logger.info("Starting calculation run...")
        
        if self.original_df is None:
            self.logger.error("No CSV data loaded. Cannot run.")
            return None

        if not self.current_procedure_steps:
            self.logger.error("No procedure steps defined. Cannot run.")
            return None

        # 2. Apply Procedure
        try:
            self.user_constants = {} 
            self.result_df = self._apply_procedure(self.original_df, self.current_procedure_steps)
            
            # 3. Store and return result
            if self.result_df is not None:
                self.logger.info("Procedure applied successfully.")
            
            return self.result_df
        except Exception as e:
            self.logger.critical(f"Run failed during procedure application: {e}", exc_info=True)
            return None

    # --- 8. Export Result ---
    def save_result_to_csv(self, output_path: str) -> Optional[pd.DataFrame]:
        """
        Exports the most recent result DataFrame to a CSV file
        and returns the result DataFrame.
        """
        if self.result_df is None:
            self.logger.error("No result DataFrame to save. Call run() first.")
            return None 

        try:
            self.result_df.to_csv(output_path, index=False)
            self.logger.info(f"Successfully saved results to {output_path}")
            return self.result_df 
        except Exception as e:
            self.logger.error(f"Error saving result CSV: {e}")
            return None 

    # --- 9. (NEWLY ADDED) Get DB as String ---
    def get_procedure_db_as_string(self) -> str:
        try:
            with open(self.procedure_db_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.warning(f"'{self.procedure_db_path}' not found. Returning empty string.")
            return ""
        except Exception as e:
            self.logger.error(f"Error reading DB file: {e}")
            return ""

    # --- 10. (NEWLY ADDED) Append Procedure to DB ---
    def append_procedure_to_db(self, title: str, procedure_string: str):
        self.logger.info(f"Appending new procedure '{title}' to DB...")
        
        # 1. Parse the string into steps (can be empty for new templates)
        steps_list = FormulaProcessor._parse_procedure_from_string(procedure_string)
        
        if not steps_list:
            self.logger.info(f"Creating empty formula template for '{title}'.")

        try:
            # 2. Open in append mode ('a')
            with open(self.procedure_db_path, 'a') as f:
                f.write(f"\n[START:{title}]\n")
                # Write steps if any exist
                for target, formula in steps_list:
                    f.write(f"    {target} = {formula}\n")
                # If no steps, just write a comment placeholder
                if not steps_list:
                    f.write(f"    # Add your formula steps here\n")
                    f.write(f"    # Example: Result = ColumnA + ColumnB\n")
                f.write(f"[END:{title}]\n\n")
            
            if steps_list:
                self.logger.info(f"Appended '{title}' with {len(steps_list)} steps to database.")
            else:
                self.logger.info(f"Created empty template '{title}' in database.")
        except Exception as e:
            self.logger.error(f"Error appending to file: {e}")


    # --- Internal Helper Methods ---

    def _apply_procedure(self, df: pd.DataFrame, procedure_steps: List[tuple]) -> Optional[pd.DataFrame]:
        """
        Applies a sequential list of symbolic formulas to a DataFrame.
        MODIFIED: Automatically prefixes generated columns with 'F|'
        """
        current_df = df.copy()
        
        self.logger.info(f"Processing {len(procedure_steps)} formulas...")
        
        for i, (target_dirty, formula_dirty) in enumerate(procedure_steps):
            
            # Define the final column name with F| prefix
            final_target_name = f"F|{target_dirty}" if not target_dirty.startswith("F|") else target_dirty
            
            self.logger.info(f"Applying Step {i+1}: {final_target_name} = {formula_dirty}")

            try:
                available_cols_dirty = list(current_df.columns)
                
                # Create mappings for safe variable naming
                dirty_to_clean_map = {col: f"__v{j}__" for j, col in enumerate(available_cols_dirty)}
                clean_to_dirty_map = {f"__v{j}__": col for j, col in enumerate(available_cols_dirty)}
                clean_symbols = {clean: Symbol(clean) for clean in clean_to_dirty_map}

                # Replace Dirty column names in formula with Clean keys (e.g. 'Mag(dB)' -> '__v0__')
                formula_clean = formula_dirty
                sorted_dirty_names = sorted(dirty_to_clean_map.keys(), key=len, reverse=True)
                for dirty_name in sorted_dirty_names:
                    formula_clean = formula_clean.replace(dirty_name, dirty_to_clean_map[dirty_name])

                try:
                    formula_expr = sympify(formula_clean, locals=clean_symbols)
                except Exception as e:
                    self.logger.error(f"Error parsing formula '{formula_clean}': {e}. Skipping step.")
                    continue
                    
                step_input_vars_clean = list(formula_expr.free_symbols)
                
                # Check for missing variables
                # Note: We do this check during lambda arg generation for flexibility with F| prefixes
                
                # [HEAVY PROCESSING START]
                lambda_func = lambdify(step_input_vars_clean, formula_expr, 'numpy')
                
                args_for_lambda = []
                for var_clean in step_input_vars_clean:
                    var_clean_str = str(var_clean)
                    
                    # 1. Check User Constants
                    if var_clean_str in self.user_constants:
                        args_for_lambda.append(self.user_constants[var_clean_str])
                        continue

                    # 2. Identify the original variable name
                    # If it was sanitized (e.g. __v0__), get the original name.
                    # If it wasn't sanitized (e.g. "Result" from a previous formula), keep as is.
                    if var_clean_str in clean_to_dirty_map:
                        dirty_name = clean_to_dirty_map[var_clean_str]
                    else:
                        dirty_name = var_clean_str

                    # 3. Fetch Data (with logic to find 'F|' prefix if needed)
                    if dirty_name in current_df.columns:
                        args_for_lambda.append(current_df[dirty_name])
                    elif f"F|{dirty_name}" in current_df.columns:
                        # If formula asks for 'Result' but we saved it as 'F|Result' previously
                        args_for_lambda.append(current_df[f"F|{dirty_name}"])
                    else:
                        raise ValueError(f"Variable '{dirty_name}' (or 'F|{dirty_name}') not found in DataFrame or constants.")
                
                # Save result with the F| prefix
                current_df[final_target_name] = lambda_func(*args_for_lambda)
                # [HEAVY PROCESSING END]

            except Exception as e:
                self.logger.error(f"Failed at step {i+1} ({target_dirty}): {e}")
                raise e

        return current_df

    # --- Static Helpers ---

    @staticmethod
    def _get_constants_from_user(missing_vars: List[Symbol]) -> Dict[str, float]:
        print("\n--- Formula requires constants not in DataFrame ---")
        constants_dict = {}
        for var_symbol in missing_vars:
            var_str = str(var_symbol)
            while True:
                try:
                    value_str = input(f"Enter constant value for '{var_str}': ")
                    constants_dict[var_str] = float(value_str)
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")
        return constants_dict

    @staticmethod
    def _load_equation_db(filename: str) -> Dict[str, List[tuple]]:
        db_data = {}
        try:
            with open(filename, 'r') as f:
                current_title = None
                current_steps_str = []
                for line in f:
                    line = line.strip()
                    if line.startswith('[START:') and ']' in line:
                        current_title = line[7:-1].strip()
                        current_steps_str = []
                    elif line.startswith('[END:') and ']' in line:
                        if current_title:
                            proc_string = "\n".join(current_steps_str)
                            steps_list = FormulaProcessor._parse_procedure_from_string(proc_string)
                            db_data[current_title] = steps_list
                        current_title = None
                        current_steps_str = []
                    elif current_title and line:
                        current_steps_str.append(line)
        except FileNotFoundError:
            return {} 
        return db_data

    @staticmethod
    def _save_equation_db(filename: str, data: Dict[str, List[tuple]]):
        with open(filename, 'w') as f:
            for title, steps_list in data.items():
                f.write(f"[START:{title}]\n")
                for target, formula in steps_list:
                    f.write(f"    {target} = {formula}\n")
                f.write(f"[END:{title}]\n\n")

    @staticmethod
    def _parse_procedure_from_string(input_string: str) -> List[tuple]:
        steps = []
        for line in input_string.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('=', 1)
            if len(parts) != 2:
                continue
                
            target = parts[0].strip()
            formula = parts[1].strip()
            steps.append((target, formula))
            
        return steps
    
    def save_text_to_file(self, content: str) -> bool:
        filepath = self.procedure_db_path
        self.logger.info(f"Saving content to {filepath}...")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info("Content saved successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Error saving file to {filepath}: {e}")
            return False
        
    def get_sympy_operator_help(self):
        return """<b>+</b> : Addition of two expressions
        <br><br>
        <b>-</b> : Subtraction of one expression from another
        <br><br>
        <b>*</b> : Multiplication of two expressions
        <br><br>
        <b>/</b> : Division of one expression by another
        <br><br>
        <b>**</b> : Exponentiation (e.g., x**2 means x squared)
        <br><br>
        <b>abs</b> : Magnitude of a number or complex value
        <br><br>
        <b>log</b> : Natural logarithm (base e)
        <br><br>
        <b>log(x, 10)</b> : Base-10 logarithm, useful for dB calculations
        <br><br>
        <b>exp</b> : Exponential function, e^x
        <br><br>
        <b>sqrt</b> : Square root of a value
        <br><br>
        <b>sin</b> : Sine of an angle (in radians)
        <br><br>
        <b>cos</b> : Cosine of an angle (in radians)
        <br><br>
        <b>tan</b> : Tangent of an angle (in radians)
        <br><br>
        <b>asin</b> : Inverse sine (arcsin)
        <br><br>
        <b>acos</b> : Inverse cosine (arccos)
        <br><br>
        <b>atan</b> : Inverse tangent (arctan)
        <br><br>
        <b>atan2</b> : Arctangent of y/x considering quadrant
        <br><br>
        <b>pi</b> : Mathematical constant &pi;
        <br><br>
        <b>I</b> : Imaginary unit (&radic;-1)
        <br><br>
        <b>re</b> : Extracts the real part of a complex expression
        <br><br>
        <b>im</b> : Extracts the imaginary part of a complex expression
        <br><br>
        <b>conjugate</b> : Returns the complex conjugate
        <br><br>
        <b>simplify</b> : Simplifies a symbolic expression
        <br><br>
        <b>expand</b> : Expands a symbolic expression
        <br><br>
        <b>factor</b> : Factors a symbolic expression
        <br><br>
        <b>collect</b> : Collects like terms in an expression
        <br><br>
        <b>subs</b> : Substitutes values into an expression
        <br><br>
        <b>solve</b> : Solves equations symbolically
        <br><br>
        <b>Eq</b> : Defines symbolic equality for solving equations
        <br><br>
        <b>symbols</b> : Creates symbolic variables
        <br><br>
        <b>Symbol</b> : Defines a single symbolic variable
        <br><br>
        <b>Function</b> : Defines a symbolic function
        <br><br>
        <b>Matrix</b> : Creates a symbolic matrix
        <br><br>
        <b>det</b> : Computes the determinant of a matrix
        <br><br>
        <b>inv</b> : Computes the inverse of a matrix
        <br><br>
        <b>transpose</b> : Transposes a matrix
        <br><br>
        <b>Piecewise</b> : Defines conditional expressions
        <br><br>
        <b>Max</b> : Returns the maximum of given values
        <br><br>
        <b>Min</b> : Returns the minimum of given values"""

if __name__ == "__main__":
    # Example Usage with Logging
    db_file = r'formula_database.txt'
    
    # Ensure output directory exists for logger
    os.makedirs(r"output\Log", exist_ok=True)

    processor = FormulaProcessor(procedure_db_path=db_file)
    
    # Notice: In the string below, you write "Result", but it will generate "F|Result"
    second_string = """
    A = 10
    B = 20
    Result = A + B
    Final = Result * 2
    """
    
    processor.set_procedure_from_string(second_string)

    procedure_name = "Prefix Test Calculation"
    processor.save_procedure_to_db(procedure_name)
    
    # Create a dummy CSV for testing
    dummy_csv = "dummy.csv"
    pd.DataFrame({'Input': [1, 2, 3]}).to_csv(dummy_csv, index=False)

    try:
        processor.set_csv_path(dummy_csv)
        df_new = processor.run()
        
        if df_new is not None:
            print("\n--- Result DataFrame Columns ---")
            print(df_new.columns)
            # You should see: Input, F|A, F|B, F|Result, F|Final
            output_file = "output_demo_prefix.csv"
            processor.save_result_to_csv(output_file)
    except Exception as e:
        print(f"Execution stopped due to error: {e}")