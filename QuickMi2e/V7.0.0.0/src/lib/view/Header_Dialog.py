from PySide6.QtWidgets import QDialog
from ui.ui_build.ui_Header import Ui_Header
from lib.event.F_HeaderGenerate import HeaderBuilder

class Header_Dialog:
    def __init__(self, errorHandle):
        self.headerDialog = QDialog()
        self.uiHeader = Ui_Header()
        self.uiHeader.setupUi(self.headerDialog)
        self.HeaderExtractor = HeaderBuilder()
        self.handle_error = errorHandle

        # --- FIX: Use lambda to pass the specific checkbox object ---
        # We use 'clicked' instead of 'stateChanged' to trigger only on user interaction
        self.uiHeader.Default_checkBox.clicked.connect(lambda: self.enforce_checkbox_logic(self.uiHeader.Default_checkBox))
        self.uiHeader.SubLot_checkBox.clicked.connect(lambda: self.enforce_checkbox_logic(self.uiHeader.SubLot_checkBox))
        self.uiHeader.MFGID_checkBox.clicked.connect(lambda: self.enforce_checkbox_logic(self.uiHeader.MFGID_checkBox))
        self.uiHeader.ModuleID_checkBox.clicked.connect(lambda: self.enforce_checkbox_logic(self.uiHeader.ModuleID_checkBox))
        self.uiHeader.WaferID_checkBox.clicked.connect(lambda: self.enforce_checkbox_logic(self.uiHeader.WaferID_checkBox))
        self.uiHeader.TesterName_checkBox.clicked.connect(lambda: self.enforce_checkbox_logic(self.uiHeader.TesterName_checkBox))
        self.uiHeader.AssemblyLotcheckBox.clicked.connect(lambda: self.enforce_checkbox_logic(self.uiHeader.AssemblyLotcheckBox))
        self.uiHeader.PcbLot_checkBox.clicked.connect(lambda: self.enforce_checkbox_logic(self.uiHeader.PcbLot_checkBox))
        
        self.uiHeader.headerUpdateButton.clicked.connect(self.save_header_config)

        # Initialize the 'selected' dictionary
        self.selected = {}

    def enforce_checkbox_logic(self, sender_checkbox):
        """
        Logic:
        1. If 'Default' is checked -> Uncheck all others.
        2. If any 'Other' is checked -> Uncheck Default.
        """
        default_cb = self.uiHeader.Default_checkBox
        other_checkboxes = [
            self.uiHeader.SubLot_checkBox,
            self.uiHeader.MFGID_checkBox,
            self.uiHeader.ModuleID_checkBox,
            self.uiHeader.WaferID_checkBox,
            self.uiHeader.TesterName_checkBox,
            self.uiHeader.AssemblyLotcheckBox,
            self.uiHeader.PcbLot_checkBox
        ]

        # Case 1: The clicked box was 'Default'
        if sender_checkbox == default_cb:
            if default_cb.isChecked():
                for cb in other_checkboxes:
                    cb.blockSignals(True)  # Prevent triggering logic again
                    cb.setChecked(False)
                    cb.blockSignals(False)

        # Case 2: The clicked box was one of the others
        elif sender_checkbox in other_checkboxes:
            if sender_checkbox.isChecked():
                default_cb.blockSignals(True)
                default_cb.setChecked(False)
                default_cb.blockSignals(False)

        self.update_header_config()  # Live update

    def save_header_config(self):
        try:
            self.HeaderExtractor.save_config(self.selected)
        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def update_header_config(self):
        try:
            # Build config
            self.selected = {
                'Default': self.uiHeader.Default_checkBox.isChecked(),
                'LOT': True,
                'SL': self.uiHeader.SubLot_checkBox.isChecked(),
                'MFG': self.uiHeader.MFGID_checkBox.isChecked(),
                'MOD': self.uiHeader.ModuleID_checkBox.isChecked(),
                'WF': self.uiHeader.WaferID_checkBox.isChecked(),
                'PID': True,
                'TT': self.uiHeader.TesterName_checkBox.isChecked(),
                'ASM': self.uiHeader.AssemblyLotcheckBox.isChecked(),
                'PCB': self.uiHeader.PcbLot_checkBox.isChecked(),
                'DateTime': True
            }

            # Preview
            dummy_header = self.HeaderExtractor.DummyHeader(self.selected)
            self.uiHeader.Samplelabel.setText(f"<b>New Header:</b><br>{dummy_header}.csv")

        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def CheckHeaderState(self):
        loaded_config = self.HeaderExtractor.load_config()
        
        # Safely map loaded config to UI
        self.uiHeader.Default_checkBox.setChecked(loaded_config.get('Default', False))
        self.uiHeader.SubLot_checkBox.setChecked(loaded_config.get('SL', False))
        self.uiHeader.MFGID_checkBox.setChecked(loaded_config.get('MFG', False))
        self.uiHeader.ModuleID_checkBox.setChecked(loaded_config.get('MOD', False))
        self.uiHeader.WaferID_checkBox.setChecked(loaded_config.get('WF', False))
        self.uiHeader.PcbLot_checkBox.setChecked(loaded_config.get('PCB', False))
        self.uiHeader.TesterName_checkBox.setChecked(loaded_config.get('TT', False))
        self.uiHeader.AssemblyLotcheckBox.setChecked(loaded_config.get('ASM', False))
        
        # Return the full config structure
        return {
            'Default': loaded_config.get('Default', False),
            'LOT': True,
            'SL': loaded_config.get('SL', False),
            'MFG': loaded_config.get('MFG', False),
            'MOD': loaded_config.get('MOD', False),
            'WF': loaded_config.get('WF', False),
            'PID': True,
            'PCB': loaded_config.get('PCB', False),
            'TT': loaded_config.get('TT', False),
            'ASM': loaded_config.get('ASM', False),
            'DateTime': True
        }

    def header_dialog(self):
        try:
            # Load state and show preview before opening
            current_state = self.CheckHeaderState()
            self.selected = current_state # Sync internal state
            
            dummy_header = self.HeaderExtractor.DummyHeader(current_state)
            self.uiHeader.Samplelabel.setText(f"<b>New Header:</b><br>{dummy_header}.csv")

            self.headerDialog.exec()

        except Exception as e:
            self.handle_error(f"\n{str(e)}")