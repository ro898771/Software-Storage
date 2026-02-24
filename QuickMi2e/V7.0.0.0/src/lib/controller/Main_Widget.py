import os
import time
import threading
import pandas as pd
import re
import json
import numpy as np
import plotly.graph_objects as go
from PySide6.QtCore import Qt, QMetaObject, Q_ARG,QObject,QSize, QEvent
from PySide6.QtWidgets import QWidget, QFileDialog, QMessageBox, QListWidgetItem, QStyledItemDelegate, QColorDialog
from PySide6.QtGui import QColor, QPalette
from datetime import datetime
from resources import resource_rc
from ui.ui_build.ui_main import Ui_Main
from lib.event.Ppt_tiger import PresentationCreator
from lib.event.Ppt_cal import PresentationCreatorWithDetails
from lib.event.Ppt_stone import PresentationCreatorWithStone
from lib.event.Compile_Tiger import TigerOrCntrace
from lib.event.Compile_Scat import Scat
from lib.event.Compile_TouchStone import TouchStone
from lib.event.Process_Cal import CalGen
from lib.event.Process_Stone import stoneGen
from lib.event.Process_Tiger import ModuleGenerator
from lib.event.Process_Regen import RegenProcessor
from lib.event.Gen_TSF import TSFGen
from lib.event.Gen_TCF import Genbatch
from lib.event.F_Rename import DynamicRenamer
from lib.event.F_extractAutoLot import extractLotData
from lib.helper.Feature import Feature
from lib.helper.Directory import Directory
from lib.helper.Group import CsvFileProcessor
from lib.helper.CheckBox import CheckBoxFeature
from lib.helper.Customize_UI import Style
from lib.helper.Worker import ProgressBarWorker
from lib.helper.ErrorHandler import ErrorHandler
from lib.helper.ProgressBarHandler import ProgressBarHandler
from lib.view.CFG_Dialog import CFG_Dialog
from lib.view.Formula_Dialog import Formula_Dialog    
from lib.view.Scat_Dialog import Scat_Dialog
from lib.view.Header_Dialog import Header_Dialog
from lib.view.Marker_Dialog import Marker_Dialog
from lib.setting.IconManager import IconManager
from PySide6.QtCore import Slot

class ColorComboBoxDelegate(QStyledItemDelegate):
    """Custom delegate to paint combobox items with colored background"""
    
    def paint(self, painter, option, index):
        """Paint each item with colored background only covering text height"""
        from PySide6.QtWidgets import QStyle
        from PySide6.QtCore import QRect
        
        # Get the color hex from the item data
        color_hex = index.data(Qt.UserRole)
        color_text = index.data(Qt.DisplayRole)  # Hex code like "#4682B4"
        
        if color_hex and color_text:
            # Fill entire background with white first
            painter.fillRect(option.rect, QColor("white"))
            
            # Set font to match combobox font (8pt, bold)
            font = painter.font()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            
            # Calculate text height
            metrics = painter.fontMetrics()
            text_height = metrics.height()
            
            # Create a rectangle that only covers the text height (centered vertically)
            color_rect = QRect(
                option.rect.left(),
                option.rect.top() + (option.rect.height() - text_height) // 2,
                option.rect.width(),
                text_height
            )
            
            # Fill only the text height area with the color
            painter.fillRect(color_rect, QColor(color_hex))
            
            # Draw text in black for readability, centered
            painter.setPen(QColor("black"))
            painter.drawText(option.rect, Qt.AlignCenter, color_text)
        else:
            # Fallback to default painting
            super().paint(painter, option, index)

class Main_Widget(QWidget,Ui_Main,QObject):
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            
            # Initialize Error Handler and Progress Bar Handler FIRST
            # (before any UI operations that might use them)
            self.error_handler = ErrorHandler(
                progress_text_widget=self.ProgressBar_textEdit,
                message_box2_widget=self.MessageBox2text
            )
            self.progress_handler = ProgressBarHandler(
                progress_bar=self.progressBar,
                progress_text_widget=self.ProgressBar_textEdit,
                message_box2_widget=self.MessageBox2text
            )
            
            self.versionName = "QuickMi2e | v7.0.0.0 |"
            if not Feature().get_default_value():
                raise ValueError("Missing 'Development' value in environment configuration.")

            self.setWindowTitle(f"{self.versionName} {Feature().get_default_value()}")      
            self.update_progress(0)
            self.ProgressBar_textEdit.setText("\nWelcome to QuickMi2e, Wish you Enjoy your Day!^^")

            #TEMP CLOSE FOR TSF GEN
            self.groupBox_9.setEnabled(False)
            self.SpecLine_checkBox.setEnabled(False)
            self.AutoSpecLine_checkBox.setEnabled(False)
            
            # Object Init
            self.tpList= Feature().get_development_list()
            self.stopEvent=threading.Event()
            self.extract = extractLotData()
            self.Icon = IconManager()
            self.Custom = Style()

            # Boolean Flag
            self.SelectAll_Flag=False
            self.pptFlag=False
            self.specFlag=False
            self.FilterLotList_comboBox.addItems(["LOT","SL","MFG","MOD","PID","WF","PCB","TT","ASM"])
            self.GeneratorGroup_comboBox.addItems(["LOT","SL","MFG","MOD","PID","WF","PCB","TT","ASM"])

            # Param INIT
            self.Dialog_colorDict= dict()
            self.Dialog_compileDict= dict()
            self.selected = dict()
            self.colorNonAssignCounting=1
            self.TSFNote_label.setStyleSheet("color: red")

            # Mice Movie
            self.Custom.deployGif(self.movieLabel)

            self.fileType_comboBox.currentTextChanged.connect(self.check_filetype_and_toggle_button)

            # Output HTML File Path
            self.tracePath = r"{path}/dataset/cntrace/trace".format(path=os.getcwd())
            self.zipPath = r"{path}/dataset/cntrace/zip".format(path=os.getcwd())
            self.resultPath = r"{path}/dataset/results".format(path=os.getcwd())
            self.htmlPath = r"{path}/output/html".format(path=os.getcwd())
            self.imagePath = r"{path}/output/image".format(path=os.getcwd())
            self.AutoImagePath = r"{path}/output/AutoImage".format(path=os.getcwd())
            self.AutoHtmlPath = r"{path}/output/AutoHtml".format(path=os.getcwd())
            self.logPath = r"{path}/output/Log".format(path=os.getcwd())
            self.specPath = r"{path}/setting/CFG/SpecLine".format(path=os.getcwd())
            self.batchPath = r"{path}/setting/CFG/Batch".format(path=os.getcwd())
            self.pptxPath = r"{path}/output/pptx".format(path=os.getcwd())
            self.savepath = r'{path}\dataset\results'.format(path=os.getcwd())
            self.copysrc = r'{path}\dataset\cntrace\zip'.format(path=os.getcwd())    
            self.dest = r'{path}\dataset\cntrace\trace'.format(path=os.getcwd())
            self.tcfPath = r"{path}/setting/CFG/TCF".format(path=os.getcwd())
            self.tsfPath = r"{path}/setting/CFG/TSF".format(path=os.getcwd())
            self.byUnitPath = r"{path}/setting/CFG/DefineUnitColor".format(path=os.getcwd())
            self.byLotPath = r"{path}/setting/CFG/LotArrangementAuto".format(path=os.getcwd())
            self.overwritePath = r"{path}/setting/CFG/ReplaceLot".format(path=os.getcwd())
            self.colorurl= r"{path}\setting\CFG\DefineUnitColor\colorReference.json".format(path=os.getcwd())
            self.formulaPath = r"{path}/setting/CFG/Formula".format(path=os.getcwd())
            self.regenPath = r"{path}/setting/CFG/Regen".format(path=os.getcwd())
            self.regenOutputPath = r"{path}/output/Regen".format(path=os.getcwd())
            self.recordPath = r"{path}/configSetting/Record.json".format(path=os.getcwd())

            
            # Label Link
            self.w3_Link.setOpenExternalLinks(True)
            self.w3_Link.setText("<a href='https://www.w3schools.com/colors/colors_picker.asp' style='color:#0000EE;'>Color Ref Link</a>")

            self.UserFeedback_Link.setOpenExternalLinks(True)
            self.UserFeedback_Link.setText(
                # 1. The '>>>' part (Bold, Segoe UI)
                "<span style='font-size: 11pt; font-weight: bold; font-family: \'Segoe UI\';'>"
                "--> </span>"
                
                # 2. The link part (Underlined, Segoe UI)
                "<a href='https://docs.google.com/spreadsheets/d/1XdhEeNbzXawwOFhAW4NZ7qpMmRvBccd_9cd9_0RhdYU/edit?gid=0#gid=0' "
                "style='color:#0000EE; font-size: 10pt; font-family: \'Segoe UI\';'>" # <-- Added here
                "UserFeedBack/TodoList</a>"
            )

            # Color Json Link
            self.ColorJason_label.setTextFormat(Qt.RichText)
            self.ColorJason_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
            self.ColorJason_label.setOpenExternalLinks(True)
            JsonColorUrl = f"file:///{self.colorurl.replace('\\', '/')}"
            self.ColorJason_label.setText(f"<a href='{JsonColorUrl}' target='_blank' style='color:#0000EE;'>Color Json Path</a>")


            # Color Json Link
            self.Custom._setup_file_link(self.ColorJason_label, self.colorurl, "Color Json Path")
            self.Custom._setup_file_link(self.PPT_Link, self.pptxPath, "Pptx Path")
            self.Custom._setup_file_link(self.Batch_Link, self.batchPath, "Batch Path")
            self.Custom._setup_file_link(self.TCF_Link, self.tcfPath, "TCF Path")
            self.Custom._setup_file_link(self.TSF_Link, self.tsfPath, "TSF Path")
            self.Custom._setup_file_link(self.ByUnit_Link, self.byUnitPath, "Unit List Path")
            self.Custom._setup_file_link(self.ByLot_Link, self.byLotPath, "Grp List Path")
            self.Custom._setup_file_link(self.Overwrite_Link, self.overwritePath, "Overwrite Path")
            self.Custom._setup_file_link(self.Spec_Link, self.specPath, "Spec Path")
            self.Custom._setup_file_link(self.dataset_Link, self.resultPath, "Results Path")
            self.Custom._setup_file_link(self.RegenPath_label, self.regenPath, "Configuration")
            self.Custom._setup_file_link(self.Regenoutput_label, self.regenOutputPath, "Output")

            # Window & Tab Icon
            self.setWindowIcon(self.Icon.Window)
            self.tabWidget.setTabIcon(0,self.Icon.Line)
            self.tabWidget.setTabIcon(1,self.Icon.Setting)
            self.tabWidget.setTabIcon(2,self.Icon.Update)
        
            # Set Icon
            self.LoadButton.setIcon(self.Icon.Param)
            self.compileButton.setIcon(self.Icon.Load)
            self.plotButton.setIcon(self.Icon.Plotting)
            self.PopulatedUnitList_button.setIcon(self.Icon.List)
            self.button_ReplaceCFG.setIcon(self.Icon.Replace)
            self.PPTButton.setIcon(self.Icon.PPT)
            self.CapturedButton.setIcon(self.Icon.Capture)
            self.ServiceButton.setIconSize(QSize(22, 20)) 
            self.ServiceButton.setIcon(self.Icon.Service)
            self.RefreshFirstButton.setIcon(self.Icon.Undo)
            self.RefreshButton.setIcon(self.Icon.Undo)
            self.genModuleButton.setIcon(self.Icon.Gen)
            self.SpecLineButton.setIcon(self.Icon.Gen)
            self.LotModuleButton.setIcon(self.Icon.LotList)
            self.EditFormulaButton.setIcon(self.Icon.Edit)
            self.Formula_RefreshButton.setIcon(self.Icon.Undo)
            self.FormulaExecuteButton.setIcon(self.Icon.Execute)
            self.LOTApplyButton.setIcon(self.Icon.RegexList)
            self.button_HeaderEdit.setIcon(self.Icon.Select)
            self.Regen_Button.setIcon(self.Icon.Gen)
            self.RefreshMemory_Button.setIcon(self.Icon.Undo)

            # Init FileType Setting
            self.SI = ["Tiger/Cntrace", "Scat","TouchStone"]

            # CheckBox Init
            self.ManualHover_checkBox.setChecked(True)
            self.Legend_checkBox.setChecked(True)
            self.ByUnit_checkBox.setChecked(True)
            self.SOnly_checkBox.setChecked(True)

            # Combo Box
            self.TPType_comboBox.addItems(self.tpList)
            self.TPType_comboBox.setCurrentText(Feature().get_default_value())
            self.fileType_comboBox.addItems(self.SI)
            self.Generator_comboBox.addItems(os.listdir(r'{path}/setting/CFG/Batch'.format(path=os.getcwd())))
            self.comboBoxTSF.addItems(os.listdir(r'{path}/setting/CFG/TSF'.format(path=os.getcwd())))
            self.comboBoxTcf.addItems(os.listdir(r'{path}/setting/CFG/TCF'.format(path=os.getcwd())))
            self.Generator_comboBox.currentTextChanged.connect(self.updateBatchLabel)
            self.fileType_comboBox.currentTextChanged.connect(self.updateFileType)
            self.ModuleBatchLabel.setText(f"Batch Ref: {self.Generator_comboBox.currentText()}")
            self.ManualPloting_groupBox.setTitle(f"Manual Plotting -{self.fileType_comboBox.currentText()}")
            self.RegenFiles_comboBox.addItems(os.listdir(r'{path}/setting/CFG/Regen'.format(path=os.getcwd())))

            # Tool Button
            self.Extract_toolButton.clicked.connect(lambda: self.Extract_directory('1'))
            self.Plot_toolButton.clicked.connect(lambda: self.Extract_directory('2'))
            
            # Button
            self.compileButton.clicked.connect(self.start_compile)
            self.LoadButton.clicked.connect(self.start_listParam)
            self.plotButton.clicked.connect(self.start_tracePlot)
            self.PopulatedUnitList_button.clicked.connect(self.start_populateList)
            self.button_ReplaceCFG.clicked.connect(self.start_cfgOverwrite)
            self.CapturedButton.clicked.connect(lambda: self.capture('1'))
            self.ServiceButton.clicked.connect(lambda: self.capture('2'))
            self.genModuleButton.clicked.connect(self.batchHandle)
            self.PPTButton.clicked.connect(self.pptClick)
            self.RefreshFirstButton.clicked.connect(self.refreshPage1Combo)
            self.RefreshButton.clicked.connect(self.refreshtcf)
            self.SpecLineButton.clicked.connect(self.tsfhandle)
            self.deleteAllButton.clicked.connect(self.deleteAll)
            self.deletePartButton.clicked.connect(self.deletePart)
            self.LotModuleButton.clicked.connect(self.start_extractDatalot)
            self.Regen_Button.clicked.connect(self.start_regen_process)
            
            # Memory feature - check if button exists
            if hasattr(self, 'RefreshMemory_Button'):
                self.RefreshMemory_Button.clicked.connect(self.load_memory)
           
           
            # Check Box
            self.ByUnit_checkBox.clicked.connect(lambda: CheckBoxFeature().chbox_unit_logic(self.ByUnit_checkBox,self.ByLot_checkBox,
                                                                                           self.SearchRegex_lineEdit,self.ColorCode_lineEdit))
            self.ByLot_checkBox.clicked.connect(lambda: CheckBoxFeature().chbox_lot_logic(self.ByLot_checkBox,self.ByUnit_checkBox,self.cfgFile_checkBox,self.cfgUI_checkBox,
                                                                                         self.SearchRegex_lineEdit,self.ColorCode_lineEdit))
            self.cfgFile_checkBox.clicked.connect(lambda: CheckBoxFeature().chbox_cfg_file_logic(self.cfgFile_checkBox,self.cfgUI_checkBox,self.ByLot_checkBox))
            self.AutoByUnit_checkBox.clicked.connect(lambda: CheckBoxFeature().auto_chbox_unit_logic(self.AutoByUnit_checkBox,self.AutoByLot_checkBox))
            self.AutoByLot_checkBox.clicked.connect(lambda: CheckBoxFeature().auto_chbox_lot_logic(self.AutoByLot_checkBox,self.AutoByUnit_checkBox))
            
            # Widget
            self.listWidget.doubleClicked.connect(self.select_all_items)

            # Color Assignment List - Now using ComboBoxes
            colorListCFGList = Feature().ColorReference
            with open(r"{path}\setting\CFG\DefineUnitColor\colorReference.json".format(path=os.getcwd()),"r") as file:
                self.colordata =json.load(file)
    
            # Create custom delegate for colored dropdown items
            self.color_delegate = ColorComboBoxDelegate()
    
            # Initialize comboboxes with colors from colorReference.json
            # Each combobox will contain all available colors as options
            for i in range(1, 24):  # CFGF1 to CFGF23
                combobox = getattr(self, f"CFGF{i}_comboBox")
                
                # Set the custom delegate to paint colored items
                combobox.setItemDelegate(self.color_delegate)
                
                # Populate combobox with all available colors
                for color_key in sorted(self.colordata.keys(), key=lambda x: int(x)):
                    color_hex = self.colordata[color_key]
                    # Display hex code directly (e.g., "#4682B4")
                    combobox.addItem(color_hex, color_hex)  # Display text and user data (Qt.UserRole)
                
                # Set the current selection to match the index (Group1 -> Color1, etc.)
                if i <= len(self.colordata):
                    current_color = colorListCFGList.get(str(i), list(self.colordata.values())[0])
                    index = combobox.findData(current_color)
                    if index >= 0:
                        combobox.setCurrentIndex(index)
                
                # Apply custom styling to show colored background
                self._apply_combobox_color_style(combobox)
                
                # Connect combobox change to update styling and save
                combobox.currentIndexChanged.connect(lambda idx, cb=combobox: self._on_color_changed(cb))
                combobox.currentIndexChanged.connect(self.save_color_reference)

            self.cfgUI = CFG_Dialog(self.colordata,self.handle_error,self.ProgressBar_textEdit,self.ByLot_checkBox,self.ByUnit_checkBox,self.cfgFile_checkBox)
            self.cfgUI_checkBox.clicked.connect(lambda: self.cfgUI.open_dialog([self.Manual_lineEdit.text(),self.cfgUI_checkBox.isChecked()]))

            self.formulaUI = Formula_Dialog(self.handle_error,self.Formula_comboBox,self.Manual_lineEdit,self.update_progress,self.update_text_edit_color,self.update_progress_text,self.progressing_progress_text,self.complete_progress_text)
            self.scatUI = Scat_Dialog()                                           
            self.EditFormulaButton.clicked.connect(self.formulaUI.formula_dialog)
            self.Formula_RefreshButton.clicked.connect(self.formulaUI.refresh_formula)
            self.FormulaExecuteButton.clicked.connect(self.formulaUI.formulaExecute)
            self.headerUI = Header_Dialog(self.handle_error)
            self.button_HeaderEdit.clicked.connect(self.headerUI.header_dialog)
            self.markerUI = Marker_Dialog(self.handle_error)
            self.LOTApplyButton.clicked.connect(self.start_apply_lot_to_dialog)
            self.CFGDefaultButton.clicked.connect(self.reset_colors_to_default)
            
            # Install event filters on color labels for double-click color picker
            for i in range(1, 24):
                label = getattr(self, f"colorLabel{i}")
                label.installEventFilter(self)
                # Store the label index as a property for easy access in eventFilter
                label.setProperty("labelIndex", i)

        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def save_compile_memory(self):
        """
        Save compile-related settings to Record.json when compileButton is pressed.
        Saves: ZipDir_lineEdit, TPType_comboBox, fileType_comboBox
        """
        try:
            # Load existing record or create new one
            if os.path.exists(self.recordPath):
                with open(self.recordPath, 'r') as f:
                    record = json.load(f)
            else:
                record = {}
            
            # Update compile settings
            record['compile'] = {
                'ZipDir': self.ZipDir_lineEdit.text(),
                'TPType': self.TPType_comboBox.currentText(),
                'fileType': self.fileType_comboBox.currentText()
            }
            
            # Save to file
            os.makedirs(os.path.dirname(self.recordPath), exist_ok=True)
            with open(self.recordPath, 'w') as f:
                json.dump(record, f, indent=4)
            
            print(f"[MEMORY] Saved compile settings to {self.recordPath}")
            
        except Exception as e:
            print(f"[MEMORY] Error saving compile memory: {e}")

    def save_plot_memory(self):
        """
        Save plot-related settings to Record.json when plotButton is pressed.
        Saves: Manual_lineEdit, XsteplineEdit, YsteplineEdit, SearchRegex_lineEdit, 
               ColorCode_lineEdit, FilterLotList_comboBox, Startfreq_lineEdit, Startfreq_lineEdit_2
        """
        try:
            # Load existing record or create new one
            if os.path.exists(self.recordPath):
                with open(self.recordPath, 'r') as f:
                    record = json.load(f)
            else:
                record = {}
            
            # Update plot settings
            record['plot'] = {
                'Manual_lineEdit': self.Manual_lineEdit.text(),
                'XsteplineEdit': self.XsteplineEdit.text(),
                'YsteplineEdit': self.YsteplineEdit.text(),
                'SearchRegex_lineEdit': self.SearchRegex_lineEdit.text(),
                'ColorCode_lineEdit': self.ColorCode_lineEdit.text(),
                'FilterLotList_comboBox': self.FilterLotList_comboBox.currentText(),
                'Startfreq_lineEdit': self.Startfreq_lineEdit.text(),
                'Startfreq_lineEdit_2': self.Startfreq_lineEdit_2.text()
            }
            
            # Save to file
            os.makedirs(os.path.dirname(self.recordPath), exist_ok=True)
            with open(self.recordPath, 'w') as f:
                json.dump(record, f, indent=4)
            
            print(f"[MEMORY] Saved plot settings to {self.recordPath}")
            
        except Exception as e:
            print(f"[MEMORY] Error saving plot memory: {e}")

    def load_memory(self):
        """
        Load saved settings from Record.json and restore them to UI elements.
        Called when RefreshMemory_Button is clicked.
        """
        try:
            if not os.path.exists(self.recordPath):
                self.RunProgressBarManual("No memory record found. Please compile or plot first.")
                return
            
            with open(self.recordPath, 'r') as f:
                record = json.load(f)
            
            # Restore compile settings if available
            if 'compile' in record:
                compile_data = record['compile']
                
                if 'ZipDir' in compile_data:
                    self.ZipDir_lineEdit.setText(compile_data['ZipDir'])
                
                if 'TPType' in compile_data:
                    index = self.TPType_comboBox.findText(compile_data['TPType'])
                    if index >= 0:
                        self.TPType_comboBox.setCurrentIndex(index)
                
                if 'fileType' in compile_data:
                    index = self.fileType_comboBox.findText(compile_data['fileType'])
                    if index >= 0:
                        self.fileType_comboBox.setCurrentIndex(index)
            
            # Restore plot settings if available
            if 'plot' in record:
                plot_data = record['plot']
                
                if 'Manual_lineEdit' in plot_data:
                    self.Manual_lineEdit.setText(plot_data['Manual_lineEdit'])
                
                if 'XsteplineEdit' in plot_data:
                    self.XsteplineEdit.setText(plot_data['XsteplineEdit'])
                
                if 'YsteplineEdit' in plot_data:
                    self.YsteplineEdit.setText(plot_data['YsteplineEdit'])
                
                if 'SearchRegex_lineEdit' in plot_data:
                    self.SearchRegex_lineEdit.setText(plot_data['SearchRegex_lineEdit'])
                
                if 'ColorCode_lineEdit' in plot_data:
                    self.ColorCode_lineEdit.setText(plot_data['ColorCode_lineEdit'])
                
                if 'FilterLotList_comboBox' in plot_data:
                    index = self.FilterLotList_comboBox.findText(plot_data['FilterLotList_comboBox'])
                    if index >= 0:
                        self.FilterLotList_comboBox.setCurrentIndex(index)
                
                if 'Startfreq_lineEdit' in plot_data:
                    self.Startfreq_lineEdit.setText(plot_data['Startfreq_lineEdit'])
                
                if 'Startfreq_lineEdit_2' in plot_data:
                    self.Startfreq_lineEdit_2.setText(plot_data['Startfreq_lineEdit_2'])
            
            self.RunProgressBarManual("Memory restored successfully!")
            print(f"[MEMORY] Loaded settings from {self.recordPath}")
            
        except Exception as e:
            self.handle_error(f"\nError loading memory: {str(e)}")

    def eventFilter(self, obj, event):
        """
        Event filter to handle double-clicks on color labels.
        Opens QColorDialog to let user pick a custom color.
        """
        try:
            # Check if the event is a double-click on a color label
            if event.type() == QEvent.MouseButtonDblClick:
                # Get the label index
                label_index = obj.property("labelIndex")
                if label_index is not None:
                    self._open_color_picker(label_index)
                    return True  # Event handled
        except Exception as e:
            print(f"Error in eventFilter: {e}")
        
        # Pass the event to the parent class
        return super().eventFilter(obj, event)
    
    def _open_color_picker(self, label_index):
        """
        Open color picker dialog and update the corresponding combobox and colorReference.json.
        
        Args:
            label_index: Index of the color label (1-23)
        """
        try:
            # Get the corresponding combobox
            combobox = getattr(self, f"CFGF{label_index}_comboBox")
            
            # Get current color
            current_color_hex = combobox.currentData()
            current_color = QColor(current_color_hex) if current_color_hex else QColor("#FFFFFF")
            
            # Open color picker dialog
            color = QColorDialog.getColor(current_color, self, f"Select Color for Group {label_index}")
            
            # If user selected a color (didn't cancel)
            if color.isValid():
                new_color_hex = color.name().upper()  # Get hex color like "#FF0000"
                
                # Update colorReference.json
                self.colordata[str(label_index)] = new_color_hex
                color_json_path = r"{path}\setting\CFG\DefineUnitColor\colorReference.json".format(path=os.getcwd())
                with open(color_json_path, 'w') as file:
                    json.dump(self.colordata, file, indent=4)
                
                # Check if this color already exists in the combobox
                index = combobox.findData(new_color_hex)
                
                if index >= 0:
                    # Color exists, just select it
                    combobox.blockSignals(True)
                    combobox.setCurrentIndex(index)
                    combobox.blockSignals(False)
                else:
                    # Color doesn't exist, add it and select it
                    combobox.blockSignals(True)
                    combobox.addItem(new_color_hex, new_color_hex)
                    new_index = combobox.count() - 1
                    combobox.setCurrentIndex(new_index)
                    combobox.blockSignals(False)
                
                # Update the combobox styling to show the new color
                self._apply_combobox_color_style(combobox)
                
                print(f"Color for Group {label_index} updated to {new_color_hex}")
                
        except Exception as e:
            self.handle_error(f"\nError opening color picker: {str(e)}")
    
    def _on_color_changed(self, combobox):
        """
        Handle color combobox selection change to update styling in real-time.
        
        Args:
            combobox: The QComboBox that changed
        """
        try:
            # Update the combobox styling immediately
            self._apply_combobox_color_style(combobox)
        except Exception as e:
            print(f"Error updating color: {e}")
    
    def _apply_combobox_color_style(self, combobox):
        """
        Apply custom styling to a color combobox to show colored background with black text.
        Uses the styling method from Customize_UI.
        
        Args:
            combobox: QComboBox widget to style
        """
        try:
            # Get current selected color
            current_color = combobox.currentData()
            # Use the styling method from Customize_UI
            self.Custom.apply_color_combobox_style(combobox, current_color)
        except Exception as e:
            print(f"Error applying combobox style: {e}")

    def save_color_reference(self, update_ui=True):
        """
        Save the current state of color comboboxes to colorReference.json.
        Each combobox selection is saved to its corresponding position (1-23).
        This method is called whenever any combobox selection changes.
        
        Args:
            update_ui: If True, update combobox styling. Set to False when calling from worker threads.
        """
        try:
            # Build new color reference dictionary from combobox selections
            new_color_ref = {}
            
            for i in range(1, 24):  # CFGF1 to CFGF23
                combobox = getattr(self, f"CFGF{i}_comboBox")
                # Get selected color hex from combobox
                color_hex = combobox.currentData()
                if color_hex:
                    new_color_ref[str(i)] = color_hex
                    # Update combobox styling to reflect new selection (only if update_ui is True)
                    if update_ui:
                        self._apply_combobox_color_style(combobox)
            
            # Save to colorReference.json
            color_json_path = r"{path}\setting\CFG\DefineUnitColor\colorReference.json".format(path=os.getcwd())
            with open(color_json_path, 'w') as file:
                json.dump(new_color_ref, file, indent=4)
            
            # Update self.colordata to reflect changes
            self.colordata = new_color_ref
            
            print(f"Color reference updated: {len(new_color_ref)} colors saved")
            
        except Exception as e:
            self.handle_error(f"\nError saving color reference: {str(e)}")

    def reset_colors_to_default(self):
        """
        Reset all color comboboxes to their default color sequence from colorDefault.json.
        Also updates colorReference.json and repopulates all comboboxes with the new colors.
        """
        try:
            # Load default colors from colorDefault.json
            default_json_path = r"{path}\setting\CFG\DefineUnitColor\colorDefault.json".format(path=os.getcwd())
            with open(default_json_path, 'r') as file:
                default_colors = json.load(file)
            
            # Update colorReference.json with default colors first
            color_json_path = r"{path}\setting\CFG\DefineUnitColor\colorReference.json".format(path=os.getcwd())
            with open(color_json_path, 'w') as file:
                json.dump(default_colors, file, indent=4)
            
            # Update self.colordata
            self.colordata = default_colors
            
            # Repopulate and update each combobox with new colors
            for i in range(1, 24):  # CFGF1 to CFGF23
                combobox = getattr(self, f"CFGF{i}_comboBox")
                
                # Block signals during repopulation
                combobox.blockSignals(True)
                
                # Clear existing items
                combobox.clear()
                
                # Repopulate with updated colors from colorDefault.json
                for color_key in sorted(default_colors.keys(), key=lambda x: int(x)):
                    color_hex = default_colors[color_key]
                    combobox.addItem(color_hex, color_hex)
                
                # Set the current selection to match the position (CFGF1 -> Color1, etc.)
                default_color = default_colors.get(str(i))
                if default_color:
                    index = combobox.findData(default_color)
                    if index >= 0:
                        combobox.setCurrentIndex(index)
                
                # Unblock signals
                combobox.blockSignals(False)
                
                # Update styling immediately to show the color
                self._apply_combobox_color_style(combobox)
            
            print("Colors reset to default sequence")
            self.RunProgressBarManual("CFG Colors reset to default.")
            
        except Exception as e:
            self.handle_error(f"\nError resetting colors: {str(e)}")

    def check_filetype_and_toggle_button(self):
        selected = self.fileType_comboBox.currentText()
        allowed = ["Tiger/Cntrace"]

        if selected in allowed:
            self.button_HeaderEdit.setEnabled(True)
        else:
            self.button_HeaderEdit.setEnabled(False)

    def start_apply_lot_to_dialog(self):
        """Threaded wrapper for apply_lot_to_dialog to prevent UI freezing"""
        try:
            thread = threading.Thread(target=self.apply_lot_to_dialog)
            thread.start()
        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def apply_lot_to_dialog(self):
        try:
            text = self.FilterLotList_comboBox.currentText()
            path = self.Manual_lineEdit.text()
            if path:  
                processor = CsvFileProcessor(path)
                check = processor.check_key_availability(text)
                self.lot_values_string, lot_indices_string = processor.get_key_values_string(text)
                self.SearchRegex_lineEdit.setText(self.lot_values_string)
                self.ColorCode_lineEdit.setText(lot_indices_string)
                
            if check:
                self.RunProgressBarManual(f"Passed: {text} is found")
            
            else:
                raise ValueError("Please provide a valid directory path.")

        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def start_extractDatalot(self):
        """Threaded wrapper for extractDatalot to prevent UI freezing"""
        try:
            thread = threading.Thread(target=self.extractDatalot)
            thread.start()
        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def extractDatalot(self):
        try:
            self.extract.extract_lot_dataframe()
            self.RunProgressBarManual("Completed Populated Lot List Event")

        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def start_regen_process(self):
        """Threaded wrapper for regen_process to prevent UI freezing"""
        try:
            thread = threading.Thread(target=self.regen_process)
            thread.start()
        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def regen_process(self):
        """Process Regen file with interpolation"""
        try:
            # Get selected Regen file
            regen_file = self.RegenFiles_comboBox.currentText()
            if not regen_file:
                raise ValueError("Please select a Regen file from the dropdown")
            
            # Build paths
            regen_csv_path = os.path.join(os.getcwd(), 'setting', 'CFG', 'Regen', regen_file)
            dataset_results_path = os.path.join(os.getcwd(), 'dataset', 'results')
            output_dir = os.path.join(os.getcwd(), 'output', 'Regen')
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"Regen_Output_{timestamp}.csv"
            output_path = os.path.join(output_dir, output_filename)
            
            # Create progress callback
            def regen_progress_callback(message, progress):
                self.progress_handler.loading_configuration_manual(message, progress)
            
            # Initialize processor and run
            processor = RegenProcessor(progress_callback=regen_progress_callback)
            success = processor.process_regen_file(regen_csv_path, dataset_results_path, output_path)
            
            if success:
                self.LoadingConfigurationManual(f"Regen completed successfully!\nOutput: {output_filename}", 100)
            else:
                raise ValueError("Regen processing failed")
                
        except Exception as e:
            self.handle_error2(f"Regen Error: {str(e)}")

    def deleteAll(self):
        try:
            threadDeleteAll = threading.Thread(target=self._deleteAllTask)
            threadDeleteAll.start()

        except Exception as e:
            self.handle_error2(f"{str(e)}")

    def _deleteAllTask(self):
        try:
            # Initialize progress
            self.LoadingConfigurationManual("Starting deletion of all generated files...", 0)
            obj = Directory()
            
            # Total folders to delete: 11
            total_folders = 11
            current = 0
            
            # Delete HTML folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting HTML folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.htmlPath)
            
            # Delete Image folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting Image folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.imagePath)
            
            # Delete AutoHtml folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting AutoHtml folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.AutoHtmlPath)
            
            # Delete AutoImage folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting AutoImage folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.AutoImagePath)
            
            # Delete SpecLine folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting SpecLine folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.specPath)
            
            # Delete Batch folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting Batch folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.batchPath)
            
            # Delete PPTX folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting PPTX folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.pptxPath)
            
            # Delete Trace folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting Trace folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.tracePath)
            
            # Delete Zip folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting Zip folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.zipPath)
            
            # Delete Results folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting Results folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.resultPath)
            
            # Delete Log folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting Log folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.logPath)
            
            # Complete
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.LoadingConfigurationManual(f"Delete All Completed_{now}", 100)

        except Exception as e:
            self.handle_error2(f"{str(e)}")

    def deletePart(self):
        try:
            # Create a new thread to execute the delete operation
            threadDeleteAll = threading.Thread(target=self._deletepartTask)

            # Start the thread
            threadDeleteAll.start()

        except Exception as e:
            # Handle any exceptions that occur
            self.handle_error2(f"{str(e)}")

    def _deletepartTask(self):
        try:
            # Initialize progress
            self.LoadingConfigurationManual("Starting deletion of Batch & SpecLine files...", 0)
            obj = Directory()
            
            # Total folders to delete: 2
            total_folders = 2
            current = 0
            
            # Delete SpecLine folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting SpecLine folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.specPath)
            
            # Delete Batch folder
            current += 1
            self.LoadingConfigurationManual(f"Deleting Batch folder... [{current}/{total_folders}]", int((current / total_folders) * 100))
            obj.delete_all_files_and_subfolders(self.batchPath)
            
            # Complete
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.LoadingConfigurationManual(f"Delete Part Completed_{now}", 100)

        except Exception as e:
            self.handle_error2(f"{str(e)}")

    def updateBatchLabel(self):
        try:
            self.ModuleBatchLabel.setText(f"Batch Ref: {self.Generator_comboBox.currentText()}")

        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def updateFileType(self):
        try:
            self.ManualPloting_groupBox.setTitle(f"Manual Ploting -{self.fileType_comboBox.currentText()}")

            if self.fileType_comboBox.currentText() == "TouchStone":               
                self.cfgUI_checkBox.setEnabled(False)
                self.cfgFile_checkBox.setEnabled(False)
                self.ByLot_checkBox.setEnabled(False)
                self.SpecLine_checkBox.setEnabled(False) 
                self.AutoByLot_checkBox.setEnabled(False)
                self.AutoByUnit_checkBox.setEnabled(False)
                self.AutoSpecLine_checkBox.setEnabled(False)
                self.Generator_comboBox.setEnabled(False)

                self.cfgUI_checkBox.setChecked(False)
                self.cfgFile_checkBox.setChecked(False)
                self.ByLot_checkBox.setChecked(False)
                self.SpecLine_checkBox.setChecked(False)
                self.AutoByLot_checkBox.setChecked(False)
                self.AutoByUnit_checkBox.setChecked(False)
                self.AutoSpecLine_checkBox.setChecked(False)

                self.SpecLine_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }")  
                self.cfgUI_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }") 
                self.cfgFile_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }")
                self.ByLot_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }")
                self.Batch_groupBox.setStyleSheet("QGroupBox:disabled { color: gray; }")
                self.AutoByLot_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }")
                self.AutoByUnit_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }")
                self.AutoSpecLine_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }")
                self.Generator_comboBox.setStyleSheet("QComboBox:disabled { color: gray; }")

            if self.fileType_comboBox.currentText() == "Scat":
                self.Batch_groupBox.setEnabled(True) 
                self.AutoSpecLine_checkBox.setEnabled(False)
                self.AutoByLot_checkBox.setEnabled(False)
                self.cfgUI_checkBox.setEnabled(False)
                self.cfgFile_checkBox.setEnabled(False)
                self.ByLot_checkBox.setEnabled(False)
                self.AutoByLot_checkBox.setEnabled(False)
                self.SpecLine_checkBox.setEnabled(False)
                self.AutoByUnit_checkBox.setEnabled(False)

                self.ByLot_checkBox.setChecked(False)
                self.SpecLine_checkBox.setChecked(False)             
                self.AutoByUnit_checkBox.setChecked(False)
                self.AutoByLot_checkBox.setChecked(False)
                self.cfgUI_checkBox.setChecked(False)
                self.cfgFile_checkBox.setChecked(False)

                self.AutoSpecLine_checkBox.setStyleSheet("QCheckBox:disabled { color:  gray; }")
                self.AutoByLot_checkBox.setStyleSheet("QCheckBox:disabled { color:  gray; }")
                self.AutoByUnit_checkBox.setStyleSheet("QCheckBox:disabled { color:  gray; }")
                self.SpecLine_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }") 
                self.cfgUI_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }") 
                self.cfgFile_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }")
                self.ByLot_checkBox.setStyleSheet("QCheckBox:disabled { color: gray; }") 
                
            if self.fileType_comboBox.currentText() == "Tiger/Cntrace":
                self.cfgUI_checkBox.setEnabled(True)
                self.cfgFile_checkBox.setEnabled(True)
                self.ByLot_checkBox.setEnabled(True)
                self.SpecLine_checkBox.setEnabled(True) 
                self.Batch_groupBox.setEnabled(True) 
                self.Generator_comboBox.setEnabled(True)
                self.AutoSpecLine_checkBox.setEnabled(True)
                self.AutoByLot_checkBox.setEnabled(True)
                self.AutoByUnit_checkBox.setEnabled(True)

        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def refreshtcf(self):
        try:
            self.comboBoxTcf.clear()
            self.comboBoxTSF.clear()
            self.RegenFiles_comboBox.clear()
            self.comboBoxTcf.addItems(os.listdir(r'{path}/setting/CFG/TCF'.format(path=os.getcwd())))
            self.comboBoxTSF.addItems(os.listdir(r'{path}/setting/CFG/TSF'.format(path=os.getcwd())))
            self.RegenFiles_comboBox.addItems(os.listdir(r'{path}/setting/CFG/Regen'.format(path=os.getcwd())))
        except Exception as e:
            self.handle_error2(f"{str(e)}")
            raise ValueError(f"{str(e)}")
        
    def tsfhandle(self):
        try:
            threadTsf=threading.Thread(target=self.tsfGenerate)
            threadTsf.start()

        except Exception as e:
            self.handle_error(f"{str(e)}")
     
    def tsfGenerate(self):
        try:
            self.LoadingConfigurationManual("Handling TSF...",50)
            tsf_path = r'{path}\setting\CFG\TSF\{dataFrame}'.format(path=os.getcwd(),dataFrame=self.comboBoxTSF.currentText())
            trace_path = r'{path}\setting\CFG\Batch\{dataFrame}'.format(path=os.getcwd(),dataFrame=self.Generator_comboBox.currentText())
            self.update_progress_text2("Please Wait....")
            
            # Check if triggerSwapFlagcheckBox exists, otherwise default to False
            swap_flag = self.triggerSwapFlagcheckBox.isChecked() if hasattr(self, 'triggerSwapFlagcheckBox') else False
            
            # Create progress callback for TSFGen
            def tsf_progress_callback(message, value):
                self.progress_handler.loading_configuration_manual(message, value)
            
            processor = TSFGen(tsf_path, trace_path, progress_callback=tsf_progress_callback)
            processor.process_and_save_results(triggerSwapFlag=swap_flag)
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Read with encoding fallback
            specline_path = r"{path}\setting\CFG\SpecLine\SpecLine.csv".format(path=os.getcwd())
            
            # Check if file exists before trying to read it
            if not os.path.exists(specline_path):
                self.LoadingConfigurationManual(f"Spec File Generated_{now}\nSpecLine.csv created successfully!",100)
                return
            
            try:
                spec_df_temp = pd.read_csv(specline_path, encoding='utf-8', on_bad_lines='skip')
            except UnicodeDecodeError:
                try:
                    spec_df_temp = pd.read_csv(specline_path, encoding='latin-1', on_bad_lines='skip')
                except UnicodeDecodeError:
                    spec_df_temp = pd.read_csv(specline_path, encoding='cp1252', on_bad_lines='skip')
            except Exception as e:
                self.handle_error2(f"Error reading SpecLine.csv: {str(e)}")
                return

            # Check if Channel Group column exists
            if 'Channel Group' not in spec_df_temp.columns:
                self.handle_error2(f"SpecLine.csv is missing 'Channel Group' column!\nFound columns: {list(spec_df_temp.columns)}\nPlease check the file format.")
            else:
                df = spec_df_temp["Channel Group"]
                if df.isna().all():
                    self.handle_error2(f"Please Check Again! \n1.It could be not syncrhonize with batch or\n2. No SpecLine.csv file found")
                else:
                    self.LoadingConfigurationManual(f"Spec File Generated_{now}\nPlease Check Spec follow TSF correctly before use!",100)

        except Exception as e:
            self.handle_error2(f"{str(e)}")

    def refreshPage1Combo(self):
        try:
            self.Generator_comboBox.clear()
            self.Generator_comboBox.addItems(os.listdir(r'{path}/setting/CFG/Batch'.format(path=os.getcwd())))

        except Exception as e:
            self.handle_error(f"{str(e)}")
            raise ValueError(f"{str(e)}")
        
    def pptClick(self):
        try:
            threadppt=threading.Thread(target=self.ppt)
            threadppt.start()

        except Exception as e:
            self.handle_error(f"{str(e)}")
            
    def ppt(self):
        try:
            self.complete_progress_text("\nCapturing in Power Point.....")
            print("Arrange in Power Point.....")
            self.update_progress(int(0))
            self.update_text_edit_color(0)
            image_folder = r"{path}\output\AutoImage".format(path=os.getcwd())
            html_folder = r"{path}\output\AutoHtml".format(path=os.getcwd())
            template_path = r'{path}\setting\CFG\pptTemplate\Template.pptx'.format(path=os.getcwd())
            
            author_name = self.AuthorlineEdit.text()
            title = self.TitlelineEdit.text()
            name = self.NameineEdit.text()
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = r'{path}\output\pptx\{name}_{time}.pptx'.format(name=name,time=now,path=os.getcwd())
            author_pos = (0.5, 5.4)  # Position of the author name (left, top) in inches
            title_pos = (0.5, 4)   # Position of the title (left, top) in inches

            if self.fileType_comboBox.currentText() == "Tiger/Cntrace":
                # Only load batch file if Generator_comboBox has a selection
                if not self.Generator_comboBox.currentText().strip():
                    raise ValueError("Please select a batch file from Generator dropdown for Tiger/Cntrace PPT generation.")
                
                # Read batch file with encoding fallback
                batch_path = r"{path}/setting/CFG/Batch/{module}".format(path=os.getcwd(),module=self.Generator_comboBox.currentText())
                try:
                    batch_df = pd.read_csv(batch_path, encoding='utf-8', on_bad_lines='skip')
                except UnicodeDecodeError:
                    try:
                        batch_df = pd.read_csv(batch_path, encoding='latin-1', on_bad_lines='skip')
                    except UnicodeDecodeError:
                        batch_df = pd.read_csv(batch_path, encoding='cp1252', on_bad_lines='skip')
                
                presentation_creator = PresentationCreator(
                image_folder=image_folder,
                template_path=template_path,
                output_path=output_path,
                author_name=author_name,
                title=title,
                author_pos=author_pos,
                title_pos=title_pos,
                df=batch_df,  # Pass the DataFrame to the class
                progress_callback=lambda progress: (self.update_progress(progress), self.update_text_edit_color(progress))
            )
                presentation_creator.create_image_slides()

            elif self.fileType_comboBox.currentText() == "Scat": 
                ppt_creator = PresentationCreatorWithDetails(
                    template_path, output_path, author_name, title, author_pos, title_pos,
                    progress_callback=lambda progress: (self.update_progress(progress), self.update_text_edit_color(progress))
                )
                # Only load batch file if Generator_comboBox has a selection
                batch_df = None
                if self.Generator_comboBox.currentText().strip():
                    batch_file_path = r"{path}/setting/CFG/Batch/{module}".format(path=os.getcwd(),module=self.Generator_comboBox.currentText())
                    if os.path.exists(batch_file_path):
                        # Read with encoding fallback
                        try:
                            batch_df = pd.read_csv(batch_file_path, encoding='utf-8', on_bad_lines='skip')
                        except UnicodeDecodeError:
                            try:
                                batch_df = pd.read_csv(batch_file_path, encoding='latin-1', on_bad_lines='skip')
                            except UnicodeDecodeError:
                                batch_df = pd.read_csv(batch_file_path, encoding='cp1252', on_bad_lines='skip')
                ppt_creator.create_subplot_slides(image_folder, html_folder, batch_df)

            elif self.fileType_comboBox.currentText() == "TouchStone": 
                ppt_creator = PresentationCreatorWithStone(
                    template_path, output_path, author_name, title, author_pos, title_pos,
                    progress_callback=lambda progress: (self.update_progress(progress), self.update_text_edit_color(progress))
                )
                ppt_creator.create_subplot_slides(image_folder, html_folder)

            self.update_progress(int(100))
            self.update_text_edit_color(100)
            self.complete_progress_text("\nCaptured in Power Point.....")
            print("Finish Captured in Power Point.....")

        except Exception as e:
            self.handle_error(f"\n{str(e)}")
            raise ValueError(f"{str(e)}")

    def batchHandle(self):
        try:
            threadbatch=threading.Thread(target=self.batch)
            threadbatch.start()

        except Exception as e:
            self.handle_error2(f"{str(e)}")

    def batch(self):
        try:
            self.LoadingConfigurationManual("Handling TCF...",0)
            path = r"{path}/setting/CFG/TCF/{TCF}".format(path=os.getcwd(), TCF=self.comboBoxTcf.currentText())
            
            # Create progress callback for Genbatch
            def tcf_progress_callback(message, value):
                self.progress_handler.loading_configuration_manual(message, value)
            
            Genbatch(path, progress_callback=tcf_progress_callback).processing(self.TCF_GRPBY_checkBox.isChecked())
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.LoadingConfigurationManual(f"Batch File Generated_{now}",100)

        except ValueError as e:
            self.handle_error2(f"{str(e)}")

    def capture(self,args):
        try:
            # Save color reference before capturing/plotting to ensure it's up-to-date (without UI updates from worker thread)
            self.save_color_reference(update_ui=False)
            
            self.TotalFile=0
            self.update_progress(0)
            self.update_text_edit_color(int(0))          
            self.pptFlag=False
            path = os.getcwd()
            refer = r"{path}\setting\CFG\Batch\{item}".format(path=path,item=self.Generator_comboBox.currentText())
            dataSrc = r"{path}\dataset\results".format(path=path)
            htmlPath = r"{path}\output\AutoHtml".format(path=path)
            imgPath = r"{path}\output\AutoImage".format(path=path)

            variable = len(os.listdir(r"{path}\output\AutoImage".format(path=os.getcwd())))
            if variable>0:
                obj =Directory()
                obj.delete_all_files_and_subfolders(imgPath)
                obj.delete_all_files_and_subfolders(htmlPath)

            self.update_progress_text("\nDeleted Image/HTMLAuto information....")
            
            if self.fileType_comboBox.currentText()=="Tiger/Cntrace":

                self.processor = ModuleGenerator(refer, dataSrc, htmlPath, imgPath,self.AutoSpecLine_checkBox.isChecked(),self.AutoByLot_checkBox.isChecked(),self.AutoByUnit_checkBox.isChecked(),self.GeneratorGroup_comboBox.currentText())
                
                self.TotalFile = len(self.processor.df)
                if self.processor:
                    self.capture_thread = threading.Thread(target=self.processor.process_data)
                    self.capture_thread.start()
                
                    self.progress_thread = threading.Thread(target=self.monitor_progress,args=args)
                    self.progress_thread.start()

            elif  self.fileType_comboBox.currentText()=="Scat":
                self.scatValue=self.scatUI.getSpecHeader[0]
                self.scatUI.apply()
                self.scatValue = self.scatUI.getscatValue

                # Pass None if Generator_comboBox is empty, otherwise pass the selected batch file
                batch_file = self.Generator_comboBox.currentText() if self.Generator_comboBox.currentText().strip() else None
                self.CalProcessor = CalGen(dataSrc,htmlPath, imgPath,self.scatValue,batch_file)

                self.TotalFile = self.CalProcessor.totalFile
                if self.CalProcessor:
                    self.capture_thread = threading.Thread(target=self.CalProcessor.savePlots)
                    self.capture_thread.start() 

                    self.progress_thread = threading.Thread(target=self.monitor_progress,args=args)
                    self.progress_thread.start()

            elif  self.fileType_comboBox.currentText()=="TouchStone":
                
                flag = self.TouchStoneOverlayAlert(self,"Option")
                
                # Get X-step and Y-step values from UI
                x_step = Feature().IntergerValueConverter(self.XsteplineEdit.text()) if self.XsteplineEdit.text() else None
                y_step = Feature().IntergerValueConverter(self.YsteplineEdit.text()) if self.YsteplineEdit.text() else None
               
                self.StoneProcessor = stoneGen(dataSrc, htmlPath, imgPath, flag, x_step, y_step)
                self.StoneProcessor.extract_channel_csv_files()
                self.TotalFile = self.StoneProcessor.count_plots_to_generate
                if self.StoneProcessor:
                    self.capture_thread = threading.Thread(target=self.StoneProcessor.savePlots)
                    self.capture_thread.start() 

                    self.progress_thread = threading.Thread(target=self.monitor_progress,args=args)
                    self.progress_thread.start()
            else:
                print("Processor not initialized. Please call capture() first.")

        except Exception as e:
            self.handle_error(f"{str(e)}")

    def monitor_progress(self, args):
        try:
            save = 0
            NormalizeCount = 0
            self.update_progress_text("\nRunning Excel Script to generate All Images")

            last_update_time = time.time()

            while self.capture_thread.is_alive():
                variable = len(os.listdir(os.path.join(os.getcwd(), "output", "AutoImage")))
                NormalizeCount = (variable / self.TotalFile) * 100

                current_time = time.time()
                if NormalizeCount > save and int(NormalizeCount) != int(save):
                    if current_time - last_update_time >= 0.5:  # 500ms to prevent too frequent updates
                        print(f"Debug ProgressBar Counter: {NormalizeCount:.2f}")
                        self.update_progress(int(NormalizeCount))
                        self.update_text_edit_color(int(NormalizeCount))
                        last_update_time = current_time

                save = NormalizeCount

            if args == "2":
                if self.AutoImagePath and self.AutoHtmlPath:
                    # Check both directories exist and are not empty
                    if (os.path.isdir(self.AutoImagePath) and os.listdir(self.AutoImagePath)) and \
                    (os.path.isdir(self.AutoHtmlPath) and os.listdir(self.AutoHtmlPath)):
                        self.pptClick()
                    else:
                        self.handle_error("Both directories for HTML and Image are empty or do not exist!\nPlease Check your Batch File Setting & Also Pupulated List")

        except Exception as e:
            self.handle_error(f"{str(e)}")

    def start_cfgOverwrite(self):
        """Threaded wrapper for cfgOverwrite to prevent UI freezing"""
        try:
            thread = threading.Thread(target=self.cfgOverwrite)
            thread.start()
        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def cfgOverwrite(self):
        try:
            self.LoadingProgressBarManual("Progressing...")
            DynamicRenamer().execute()
            self.RunProgressBarManual("Completed OverWrite file's Name")

        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def start_populateList(self):
        """Threaded wrapper for populateList to prevent UI freezing"""
        try:
            thread = threading.Thread(target=self.populateList)
            thread.start()
        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def populateList(self):
        try:
            text = self.Manual_lineEdit.text()
            text = r"{path}".format(path=text)
            if text:
                ResultPath = text
            else:
                ResultPath = r"{path}\dataset\results".format(path=os.getcwd())
            if len(os.listdir(ResultPath))>0:
                allList= Feature().get_unique_csv_basenames(ResultPath)
                path = r"{ori}\setting\CFG\DefineUnitColor\unit_color.csv".format(ori=os.getcwd())
                df =pd.DataFrame(columns=["Unit","ColorSelect"])
                df["Unit"] = allList
                df["ColorSelect"] = np.random.choice(np.arange(1, 24), size=len(allList), replace=True)

                df.to_csv(path,index=False)
                self.RunProgressBarManual("Completed Populated List Event")

        except Exception as e:
            self.handle_error(f"\n{str(e)}")
       
    def start_tracePlot(self):
        """Threaded wrapper for tracePlot to prevent UI freezing"""
        try:
            # If marker checkbox is checked, open Marker dialog BEFORE threading
            if self.marker_checkBox.isChecked():
                self.markerUI.marker_dialog()
            
            # If Scat file type is selected and not using CFG options, open dialog BEFORE threading
            if (self.fileType_comboBox.currentText() == "Scat" and 
                self.ByUnit_checkBox.isChecked() and 
                not self.cfgUI_checkBox.isChecked() and 
                not self.cfgFile_checkBox.isChecked()):
                self.scatUI.apply()
                self.scatValue = self.scatUI.getscatValue
                if not self.scatValue:
                    raise ValueError("Please select a Scat spec file from the dialog")
            
            thread = threading.Thread(target=self.tracePlot)
            thread.start()
        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def tracePlot(self):
        try:
            # Save plot settings to memory
            self.save_plot_memory()
            
            # Save color reference before plotting to ensure it's up-to-date (without UI updates from worker thread)
            self.save_color_reference(update_ui=False)
            
            # Initialize progress with orange color for processing
            self.update_progress(0)
            self.progressing_progress_text("\nStarting Manual Plot Process...")
            
            # Parse frequency range from user input
            self.freq_start = None
            self.freq_stop = None
            
            if self.Startfreq_lineEdit.text().strip():
                try:
                    self.freq_start = Feature().IntergerValueConverter(self.Startfreq_lineEdit.text())
                    self.progressing_progress_text(f"\nStart Frequency: {Feature().format_frequency(self.freq_start)}")
                except:
                    self.progressing_progress_text("\nWarning: Invalid Start Frequency format, ignoring...")
                    self.freq_start = None
            
            if self.Startfreq_lineEdit_2.text().strip():
                try:
                    self.freq_stop = Feature().IntergerValueConverter(self.Startfreq_lineEdit_2.text())
                    self.progressing_progress_text(f"\nStop Frequency: {Feature().format_frequency(self.freq_stop)}")
                except:
                    self.progressing_progress_text("\nWarning: Invalid Stop Frequency format, ignoring...")
                    self.freq_stop = None
            
            if self.freq_start is not None and self.freq_stop is not None:
                self.progressing_progress_text(f"\nFrequency Range: {Feature().format_frequency(self.freq_start)} - {Feature().format_frequency(self.freq_stop)}")
            elif self.freq_start is not None:
                self.progressing_progress_text(f"\nFrequency Range: From {Feature().format_frequency(self.freq_start)} onwards")
            elif self.freq_stop is not None:
                self.progressing_progress_text(f"\nFrequency Range: Up to {Feature().format_frequency(self.freq_stop)}")
            
            # Check if markers should be plotted
            self.marker_list = []
            if self.marker_checkBox.isChecked() and self.markerUI.should_plot_markers():
                self.marker_list = self.markerUI.get_markers()
                self.progressing_progress_text(f"\nMarker Configuration Loaded: {len(self.marker_list)} marker(s)")
            
            # Load spec lines if available
            self.progressing_progress_text("\nChecking Spec Line Configuration...")
            specline_csv = r'{path}\setting\CFG\SpecLine\SpecLine.csv'.format(path=os.getcwd())
            
            # Check if SpecLine.csv file exists
            if os.path.exists(specline_csv) and os.path.isfile(specline_csv):
                # Read with encoding fallback
                try:
                    self.spec_df = pd.read_csv(specline_csv, encoding='utf-8', on_bad_lines='skip')
                except UnicodeDecodeError:
                    try:
                        self.spec_df = pd.read_csv(specline_csv, encoding='latin-1', on_bad_lines='skip')
                    except UnicodeDecodeError:
                        self.spec_df = pd.read_csv(specline_csv, encoding='cp1252', on_bad_lines='skip')
                except Exception as e:
                    self.progressing_progress_text(f"\nWarning: Error reading SpecLine.csv: {str(e)}")
                    self.specFlag = False
                    return
                
                # Validate that required columns exist
                if 'Channel Group' not in self.spec_df.columns or 'S-Parameter' not in self.spec_df.columns:
                    self.progressing_progress_text(f"\nWarning: SpecLine.csv missing required columns. Found: {list(self.spec_df.columns)}")
                    self.specFlag = False
                else:
                    self.specFlag = True
                    self.progressing_progress_text("Spec Line Loaded Successfully")
            else:
                self.specFlag=False
                self.progressing_progress_text("No Spec Line Configuration Found (File doesn't exist)")
   
            ori = self.Manual_lineEdit.text()
            
            # Validate file type matches the directory contents
            self.update_progress(10)
            self.progressing_progress_text("\nValidating Directory and File Type...")
            
            if not os.path.exists(ori) or not os.path.isdir(ori):
                raise ValueError(f"Invalid directory path: {ori}")
            
            files_in_dir = os.listdir(ori)
            if not files_in_dir:
                raise ValueError(f"No files found in directory: {ori}")
            
            # Check if files match the selected file type
            selected_filetype = self.fileType_comboBox.currentText()
            if selected_filetype == "Tiger/Cntrace":
                # Tiger files should have _DateTime pattern
                has_tiger_files = any("_DateTime" in f for f in files_in_dir if f.endswith('.csv'))
                if not has_tiger_files:
                    raise ValueError("Selected file type is 'Tiger/Cntrace' but the directory contains Scat files.\nPlease select the correct file type.")
            elif selected_filetype == "Scat":
                # Scat files should NOT have _DateTime pattern
                has_scat_files = any(f.endswith('.csv') and "_DateTime" not in f for f in files_in_dir)
                if not has_scat_files:
                    raise ValueError("Selected file type is 'Scat' but the directory contains Tiger/Cntrace files.\nPlease select the correct file type.")
            
            self.progressing_progress_text(f"File Type Validation Passed: {selected_filetype}")
            self.update_progress(20)
            
            fig = go.Figure()
            smitchfig =go.Figure()
            selected_items = [item.text() for item in self.listWidget.findItems("*", Qt.MatchWildcard) if item.checkState() == Qt.Checked]
            if len(selected_items)==0:
                raise ValueError("Please Select the S parameter")
            
            self.progressing_progress_text(f"\nSelected S-Parameters: {', '.join(selected_items)}")
            self.update_progress(30)

            if self.ByUnit_checkBox.isChecked():
                self.progressing_progress_text("\nProcessing By Unit Mode...")
                if self.cfgUI_checkBox.isChecked():
                    self.progressing_progress_text("\nUsing CFG UI Configuration...")
                    self.update_progress(40)
                    self.cfgUI_plot(ori,selected_items,self.cfgUI.getcompileDict,self.cfgUI.getcolorDict)

                elif self.cfgFile_checkBox.isChecked():
                    self.progressing_progress_text("\nUsing CFG File Configuration...")
                    self.update_progress(40)
                    self.cfgFile_Plot(ori,selected_items,fig)               
                else:
                    self.progressing_progress_text("Processing Without CFG Configuration...")
                    self.update_progress(40)
                    # Scat dialog is now opened in start_tracePlot before threading
                    # scatValue should already be set if fileType is Scat
                    self.nonColorAssign(ori,selected_items,fig,smitchfig)

            elif self.ByLot_checkBox.isChecked():
                self.progressing_progress_text("\nProcessing By Lot Mode...")
                self.update_progress(40)
                self.cfgLot_Plot(ori,selected_items,fig)
            else:
                raise ValueError("Please Tick Either By Unit or By Lot")
            
            # Complete - Change to green
            self.update_progress(100)
            self.complete_progress_text("\nManual Plot Completed Successfully!")

        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def cfgLot_Plot(self, oriPath, selected_items, fig):
        try:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.basename(oriPath)
            groupSelect = self.FilterLotList_comboBox.currentText()
            checkPatternString = re.compile(r"^([^|]+(\|[^|]+)*)\|?$")
            checkPatternInteger = re.compile(r"^(\d+(\|\d+)*)\|?$")
            # Create pattern that matches groupSelect followed by [...] 
            # The pattern looks for groupSelect at word boundary or after underscore/space
            # This handles: LOT, MFG, MFG-A, LOT_123, TEST*01, ABC123, 999, XYZ, etc.
            LotPattern = re.compile(r'(?:^|_)' + re.escape(str(groupSelect)) + r'\[([^\]]+)\]')
            sample = os.listdir(oriPath)
            runPlot = dict()

            if checkPatternString.match(self.SearchRegex_lineEdit.text()) and "|" in self.SearchRegex_lineEdit.text():
                pattern_list = [clean for clean in self.SearchRegex_lineEdit.text().split("|") if clean]
            else:
                raise ValueError("Wrong lot regex name pattern! Please Check")
            
            if checkPatternInteger.match(self.ColorCode_lineEdit.text()) and "|" in self.ColorCode_lineEdit.text():
                color_list = [clean for clean in self.ColorCode_lineEdit.text().split("|") if clean]
            else:
                raise ValueError("Wrong color regex pattern! Please Check")

            if len(pattern_list) == 0 or len(pattern_list) != len(color_list):
                pairFlag = False
                raise ValueError("Wrong Length between color regex vs lot name regex!")
            else:
                pairFlag = True
                pairLot = dict(zip(pattern_list, color_list))

            # Start
            if pairFlag:
                print(f"\n=== Pattern Matching Debug ===")
                for data in sample:
                    match = LotPattern.search(data)
                    if match:
                        extracted_value = match.group(1)  # e.g., "1", "50199", "MFG-A", etc.
                        print(f"File: {data}")
                        print(f"  Extracted value: '{extracted_value}'")
                        matched = False
                        for pattern in pattern_list:  # Use pattern_list to maintain order
                            # Use exact match OR substring match for complex patterns
                            # Exact match: pattern == extracted_value (e.g., "1" == "1", "50199" == "50199")
                            # Substring match: pattern in extracted_value (e.g., "MFG-A" in "MFG-A-001")
                            is_exact_match = (pattern == extracted_value)
                            is_substring_match = (pattern in extracted_value) and len(pattern) > 3  # Only use substring for longer patterns
                            
                            print(f"  Checking pattern '{pattern}': exact={is_exact_match}, substring={is_substring_match}")
                            
                            if is_exact_match or is_substring_match:
                                color_code = pairLot[pattern]  # Get the corresponding color code
                                print(f"  ✓ MATCHED! Assigned color code: {color_code}")
                                if color_code in runPlot:
                                    runPlot[color_code].append(data)
                                else:
                                    runPlot[color_code] = [data]
                                matched = True
                                break
                        
                        # If no pattern matched, add to unmatched group (color code 0)
                        if not matched:
                            print(f"  ✗ NO MATCH - Assigned to color code 0 (black)")
                            if 0 in runPlot:
                                runPlot[0].append(data)
                            else:
                                runPlot[0] = [data]
                print(f"==============================\n")

            src = Feature().ColorReference
            threads = []
            
            # Debug: Print the runPlot structure to verify color code assignments
            print(f"\n=== cfgLot_Plot Debug Info ===")
            print(f"GroupSelect: {groupSelect}")
            print(f"Pattern List: {pattern_list}")
            print(f"Color List: {color_list}")
            print(f"PairLot Mapping: {pairLot}")
            print(f"RunPlot Structure:")
            for color_code, files in runPlot.items():
                print(f"  Color Code '{color_code}': {len(files)} files")
            print(f"==============================\n")
            
            # Shared list to collect traces with their sort order
            # Structure: [(sort_index, trace_object, xMin, xMax), ...]
            traces_with_order = []
            traces_lock = threading.Lock()
            
            # Shared dictionary to track which legend groups have been shown
            # Key: legend_group_name, Value: True if already shown
            legend_tracker = {}
            tracker_lock = threading.Lock()

            def process_file(sort_index, input, color_code, value):
                # color_code is the value from ColorCode_lineEdit (e.g., "1", "2", "3")
                # Convert it to actual color from colorReference.json
                if color_code == 0 or color_code == "0":
                    actual_color = "#000000"  # Black for unmatched items
                else:
                    actual_color = src.get(str(color_code), "#000000")  # Get color from reference
                for z in value:
                    # Read with encoding fallback
                    try:
                        df = pd.read_csv(os.path.join(oriPath, z), encoding='utf-8', on_bad_lines='skip')
                    except UnicodeDecodeError:
                        try:
                            df = pd.read_csv(os.path.join(oriPath, z), encoding='latin-1', on_bad_lines='skip')
                        except UnicodeDecodeError:
                            df = pd.read_csv(os.path.join(oriPath, z), encoding='cp1252', on_bad_lines='skip')
                    x_values = df["Freq"] if "Freq" in df.columns else df["freq[HZ]"]
                    y_values = df[f"{input}"]
                    
                    # Apply frequency range filter
                    x_values, y_values = self.filter_frequency_range(x_values, y_values)
                    
                    if len(x_values) == 0:
                        return  # Skip if no data in range

                    xMin=x_values.min()
                    xMax=x_values.max()
    
                    # Extract the group value (LOT, MFG, etc.) from filename
                    # Pattern matches groupSelect at start or after underscore, followed by [value]
                    lot_match = re.search(r'(?:^|_)' + re.escape(groupSelect) + r'\[([^\]]+)\]', z)
                    lot = lot_match.group(1) if lot_match else None

                    lot = f"Group-[{lot}]"
                    Sparam = input.split("_")[0]
                    legend_group_name = f"{Sparam}-{lot}"
                    
                    # Thread-safe check for legend flag
                    with tracker_lock:
                        legendFlag = legend_group_name not in legend_tracker
                        if legendFlag:
                            legend_tracker[legend_group_name] = True
                    
                    # Create trace object but DON'T add to fig yet
                    trace = go.Line(x=x_values, y=y_values, 
                                          line=dict(color=actual_color), 
                                          mode='lines',
                                          showlegend=legendFlag,  
                                          legendgroup=legend_group_name,  # Group all traces with same lot
                                          name=legend_group_name,                    
                                          hovertemplate=(
                                        f"<b>{Sparam}-{lot}</b><br>" +
                                        "Frequency: %{x}<br>" +
                                        f"{input}: %{{y}}<extra></extra>"
                                ))
                    
                    # Store trace with its sort order
                    with traces_lock:
                        traces_with_order.append((sort_index, trace, xMin, xMax))

            # Process files in the order defined by pattern_list (from SearchRegex_lineEdit)
            # This ensures the plot sequence and legend order match the user's specification
            sort_index = 0
            for input in selected_items:
                # Iterate through color_list (which corresponds to pattern_list order)
                for color_code in color_list:
                    if color_code in runPlot:
                        value = runPlot[color_code]
                        thread = threading.Thread(target=process_file, args=(sort_index, input, color_code, value))
                        threads.append(thread)
                        thread.start()
                        sort_index += 1
                
                # Also process any unmatched items (color_code 0) at the end
                if 0 in runPlot:
                    thread = threading.Thread(target=process_file, args=(sort_index, input, 0, runPlot[0]))
                    threads.append(thread)
                    thread.start()
                    sort_index += 1

            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Sort traces by sort_index and add them to the figure in the correct order
            traces_with_order.sort(key=lambda x: x[0])
            for sort_idx, trace, xMin, xMax in traces_with_order:
                fig.add_trace(trace)
                self.apply_layout(fig, base_name, xMin, xMax, show_legend=self.Legend_checkBox.isChecked(), 
                                  manual_hover=self.ManualHover_checkBox.isChecked())

            if self.specFlag:
                # Check if required columns exist in spec_df
                if 'Channel Group' in self.spec_df.columns and 'S-Parameter' in self.spec_df.columns:
                    for sItem in selected_items:
                        filtered_spec_df = self.spec_df[
                        (self.spec_df['Channel Group'] == base_name) &
                        (self.spec_df['S-Parameter'] == sItem)
                                    ]
                        self.specFig(fig, self.SpecLine_checkBox.isChecked(), filtered_spec_df, sItem)
                else:
                    print(f"Warning: SpecLine.csv is missing required columns. Found columns: {list(self.spec_df.columns)}")

            # Legend sorting is now handled by processing order above
            # No need for post-processing sort since threads are started in pattern_list order

            # Apply markers if configured
            self.apply_markers(fig)

            fig.write_html(r"{path}/{name}_{time}.html".format(path=self.htmlPath, name=base_name,time=now),auto_open=True)
            fig.write_image(r"{path}/{name}_{time}.png".format(path=self.imagePath, name=base_name,time=now),width=1920, height=1080)

        except Exception as e:
            self.handle_error(f"{str(e)}")
        
    def cfgFile_Plot(self, oriPath, selected_items, fig):
            try:
                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.basename(oriPath)
                src = Feature().ExtractUnitColorData
                
                # 1. Sort the file list first to ensure the base sequence is correct
                sample = sorted(os.listdir(oriPath)) 

                # Shared list to store results from threads
                # Structure: (sort_index, trace_object)
                results = []
                results_lock = threading.Lock()

                def process_file(sort_index, filename, input_param, colorGroup):
                    try:
                        # Read with encoding fallback
                        try:
                            df = pd.read_csv(r"{path}/{key}".format(path=oriPath, key=filename), encoding='utf-8', on_bad_lines='skip')
                        except UnicodeDecodeError:
                            try:
                                df = pd.read_csv(r"{path}/{key}".format(path=oriPath, key=filename), encoding='latin-1', on_bad_lines='skip')
                            except UnicodeDecodeError:
                                df = pd.read_csv(r"{path}/{key}".format(path=oriPath, key=filename), encoding='cp1252', on_bad_lines='skip')
                        
                        if input_param in df.columns:
                            Sparam = re.search(r'S\d+', input_param).group()
                            x_values = df["Freq"] if "Freq" in df.columns else df["freq[HZ]"]
                            y_values = df[f"{input_param}"]
                            
                            # Apply frequency range filter
                            x_values, y_values = self.filter_frequency_range(x_values, y_values)
                            
                            if len(x_values) == 0:
                                return  # Skip if no data in range

                            if self.fileType_comboBox.currentText() == "Tiger/Cntrace":
                                result = re.search(r"^(.*)_DateTime", filename).group(1)
                            else:
                                result = filename.split(".")[0]    

                            # Create the trace object BUT DO NOT add to fig yet
                            trace = go.Line(
                                x=x_values, 
                                y=y_values, 
                                line=dict(color=colorGroup), 
                                mode='lines', 
                                name=f"{Sparam}_{result}",
                                hovertemplate=(
                                    f"<b>{Sparam}-{result}</b><br>" +
                                    "Frequency: %{x}<br>" +
                                    f"{input_param}: %{{y}}<extra></extra>"
                                )
                            )
                            
                            # Calculate Min/Max for layout (optional, can be done here or in main thread)
                            xMin = x_values.min()
                            xMax = x_values.max()

                            # Store the result with the index to sort later
                            with results_lock:
                                results.append({
                                    "index": sort_index,
                                    "trace": trace,
                                    "xMin": xMin,
                                    "xMax": xMax
                                })
                    except Exception as e:
                        print(f"Error processing {filename}: {e}")

                threads = []
                global_index = 0

                # 2. Launch Threads
                for input_param in selected_items:
                    for x in sample:
                        colorGroup = src.get(x.split(".")[0], "#000000")
                        
                        # Pass 'global_index' so we know the order later
                        thread = threading.Thread(
                            target=process_file, 
                            args=(global_index, x, input_param, colorGroup)
                        )
                        threads.append(thread)
                        thread.start()
                        global_index += 1

                # 3. Wait for all threads to finish
                for thread in threads:
                    thread.join()

                # 4. Sort results by the index we assigned
                results.sort(key=lambda x: x["index"])

                # 5. Add traces to Figure sequentially (Strict Order)
                final_xMin = float('inf')
                final_xMax = float('-inf')

                for item in results:
                    fig.add_trace(item["trace"])
                    # Aggregate min/max
                    if item["xMin"] < final_xMin: final_xMin = item["xMin"]
                    if item["xMax"] > final_xMax: final_xMax = item["xMax"]

                # 6. Apply Layout once at the end
                if results:
                    self.apply_layout(fig, base_name, final_xMin, final_xMax, 
                                    show_legend=self.Legend_checkBox.isChecked(), 
                                    manual_hover=self.ManualHover_checkBox.isChecked()) 

                # 7. Add Spec Lines
                if self.specFlag:
                    # Check if required columns exist in spec_df
                    if 'Channel Group' in self.spec_df.columns and 'S-Parameter' in self.spec_df.columns:
                        for sItem in selected_items:
                            filtered_spec_df = self.spec_df[
                                (self.spec_df['Channel Group'] == base_name) &
                                (self.spec_df['S-Parameter'] == sItem)
                            ]
                            self.specFig(fig, self.SpecLine_checkBox.isChecked(), filtered_spec_df, sItem)
                    else:
                        print(f"Warning: SpecLine.csv is missing required columns. Found columns: {list(self.spec_df.columns)}")

                # 8. Apply markers if configured
                self.apply_markers(fig)

                fig.write_html(r"{path}/{name}_{time}.html".format(path=self.htmlPath, name=base_name, time=now), auto_open=True)
                fig.write_image(r"{path}/{name}_{time}.png".format(path=self.imagePath, name=base_name, time=now), width=1920, height=1080)

            except Exception as e:
                self.handle_error(f"{str(e)}")

    def cfgUI_plot(self, ori, selected_items, Dialog_compileDict, Dialog_colorDict):
        try:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.basename(ori)
            
            # 1. Create a thread-safe list to store results and a Lock
            plot_results = []
            results_lock = threading.Lock()

            # Modified process function: Doesn't add to fig, but stores to list
            def process_file(filename, input_param, color, sort_index):
                try:
                    path = os.path.join(ori, filename)
                    # Read with encoding fallback
                    try:
                        df = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
                    except UnicodeDecodeError:
                        try:
                            df = pd.read_csv(path, encoding='latin-1', on_bad_lines='skip')
                        except UnicodeDecodeError:
                            df = pd.read_csv(path, encoding='cp1252', on_bad_lines='skip')
                    
                    if input_param in df.columns:
                        Sparam = input_param.split("_")[0]
                        x_values = df["Freq"] if "Freq" in df.columns else df["freq[HZ]"]
                        y_values = df[f"{input_param}"]
                        
                        # Apply frequency range filter
                        x_values, y_values = self.filter_frequency_range(x_values, y_values)
                        
                        if len(x_values) == 0:
                            return  # Skip if no data in range

                        if self.fileType_comboBox.currentText() == "Tiger/Cntrace":
                            result = re.search(r"^(.*)_DateTime", filename).group(1)
                        else:
                            result = filename.split(".")[0]
                        
                        xMin = x_values.min()
                        xMax = x_values.max()

                        # Create the trace object but DO NOT add to fig yet
                        # Note: go.Line is deprecated, using go.Scatter(mode='lines') is standard
                        trace = go.Scatter(
                            x=x_values, 
                            y=y_values, 
                            line=dict(color=color), 
                            mode='lines', 
                            name=f"{Sparam}-{result}",                               
                            hovertemplate=(
                                f"<b>{Sparam}-{result}</b><br>" +
                                "Frequency: %{x}<br>" +
                                f"{input_param}: %{{y}}<extra></extra>"
                            )
                        )

                        # Store result with the sort_index to restore order later
                        with results_lock:
                            plot_results.append({
                                "index": sort_index,
                                "trace": trace,
                                "xMin": xMin,
                                "xMax": xMax
                            })
                except Exception as err:
                    print(f"Error processing {filename}: {err}")

            fig = go.Figure()
            threads = []
            
            # 2. Assign a global index to ensure order is tracked
            global_sort_index = 0

            # Iterate in the specific order you want (G1 -> G2 -> G3)
            for input_param in selected_items:
                # Assuming Dialog_compileDict keys are in order, or you can sort them explicitly:
                # for key in sorted(Dialog_compileDict.keys()): 
                for key, value in Dialog_compileDict.items():
                    color = Dialog_colorDict[key]
                    for x in value:
                        # Pass the global_sort_index to the thread
                        thread = threading.Thread(target=process_file, args=(f"{x}.csv", input_param, color, global_sort_index))
                        threads.append(thread)
                        thread.start()
                        
                        global_sort_index += 1 # Increment for the next file

            # Wait for all threads to finish
            for thread in threads:
                thread.join()

            # 3. Sort the results based on the index we assigned
            plot_results.sort(key=lambda x: x["index"])

            # 4. Add traces to figure in order and calculate global Min/Max
            overall_xMin = float('inf')
            overall_xMax = float('-inf')

            for item in plot_results:
                fig.add_trace(item["trace"])
                
                # Track min/max for the layout
                if item["xMin"] < overall_xMin: overall_xMin = item["xMin"]
                if item["xMax"] > overall_xMax: overall_xMax = item["xMax"]

            # Apply layout ONCE after all traces are added
            if plot_results:
                self.apply_layout(fig, base_name, overall_xMin, overall_xMax, 
                                show_legend=self.Legend_checkBox.isChecked(), 
                                manual_hover=self.ManualHover_checkBox.isChecked())

            # Handle Spec Lines (Outside threading loop)
            if self.specFlag:
                # Check if required columns exist in spec_df
                if 'Channel Group' in self.spec_df.columns and 'S-Parameter' in self.spec_df.columns:
                    for sItem in selected_items:
                        filtered_spec_df = self.spec_df[
                            (self.spec_df['Channel Group'] == base_name) &
                            (self.spec_df['S-Parameter'] == sItem)
                        ]
                        self.specFig(fig, self.SpecLine_checkBox.isChecked(), filtered_spec_df, sItem)
                else:
                    print(f"Warning: SpecLine.csv is missing required columns. Found columns: {list(self.spec_df.columns)}")

            # Apply markers if configured
            self.apply_markers(fig)

            fig.write_html(r"{path}/{name}_{time}.html".format(path=self.htmlPath, name=base_name, time=now), auto_open=True)
            fig.write_image(r"{path}/{name}_{time}.png".format(path=self.imagePath, name=base_name, time=now), width=1920, height=1080)

        except Exception as e:
            self.handle_error(f"{str(e)}")

    def nonColorAssign(self, ori, selected_items, fig, smitchfig=None):
        try:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            sample = sorted(os.listdir(r'{path}'.format(path=ori)))  # Sort files to ensure consistent order
            threads = []
            base_name = os.path.basename(ori)
            data_lock = threading.Lock()  
            self.tempSpec = pd.DataFrame()
            overall_xMin = float('inf')
            overall_xMax = float('-inf')
            
            # Progress tracking
            total_files = len(sample)
            processed_files = 0
            
            self.update_progress_text(f"\nFound {total_files} files to process...")
            
            # Check if we're in "All files" folder for TouchStone
            is_all_files_folder = (self.fileType_comboBox.currentText() == "TouchStone" and 
                                   base_name == "All files")
            
            # For TouchStone "All files": Extract SN numbers and map to colors
            # Files with same SN get same color
            sn_color_map = {}
            sn_sort_map = {}  # Map filename to SN number for sorting
            
            if is_all_files_folder:
                sn_pattern = re.compile(r'SN(\d+)')
                for filename in sample:
                    sn_match = sn_pattern.search(filename)
                    if sn_match:
                        sn_number = sn_match.group(1)  # Extract the SN number (e.g., "11", "16")
                        # Map SN number directly to color key in colorReference.json
                        # If SN is beyond available colors, wrap around
                        color_key = str(int(sn_number) % len(self.colordata))
                        if color_key == "0":
                            color_key = str(len(self.colordata))  # Use last color instead of 0
                        sn_color_map[filename] = color_key
                        sn_sort_map[filename] = int(sn_number)  # For sorting
                        print(f"[DEBUG] All files - File: {filename} -> SN{sn_number} -> Color {color_key}")
                    else:
                        # If no SN found, assign color 1 and sort to end
                        sn_color_map[filename] = "1"
                        sn_sort_map[filename] = 9999  # Sort to end
                        print(f"[DEBUG] All files - File: {filename} -> No SN found -> Color 1")
                
                # Sort files by SN number for "All files" folder
                sample = sorted(sample, key=lambda x: sn_sort_map.get(x, 9999))
                # print(f"[DEBUG] Sorted files by SN: {sample}")
            
            # Shared color counter for traces (per chart for non-All files TouchStone, sequential for others)
            trace_color_counter = {"current": 1}
            trace_color_lock = threading.Lock()
            
            # Load batch file reference data if available (for Scat file type)
            batch_ref_data = pd.DataFrame()
            if self.fileType_comboBox.currentText() == "Scat":
                if self.Generator_comboBox.currentText().strip():
                    batch_file_path = os.path.join(os.getcwd(), 'setting', 'CFG', 'Batch', self.Generator_comboBox.currentText())
                    if os.path.exists(batch_file_path) and os.path.isfile(batch_file_path):
                        # Read with encoding fallback
                        try:
                            batch_ref_data = pd.read_csv(batch_file_path, encoding='utf-8', on_bad_lines='skip')
                        except UnicodeDecodeError:
                            try:
                                batch_ref_data = pd.read_csv(batch_file_path, encoding='latin-1', on_bad_lines='skip')
                            except UnicodeDecodeError:
                                batch_ref_data = pd.read_csv(batch_file_path, encoding='cp1252', on_bad_lines='skip')
                        self.update_progress_text(f"Loaded Batch Reference: {self.Generator_comboBox.currentText()}")
                        print(f"Loaded batch reference data for manual plotting: {batch_file_path}")
                else:
                    self.update_progress_text("No Batch File Selected - Using Default Naming")
           
            def process_file(filename):
                nonlocal overall_xMin, overall_xMax, processed_files
                try:
                    path = os.path.join(ori, filename)
                    # Read with encoding fallback
                    try:
                        df = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
                    except UnicodeDecodeError:
                        try:
                            df = pd.read_csv(path, encoding='latin-1', on_bad_lines='skip')
                        except UnicodeDecodeError:
                            df = pd.read_csv(path, encoding='cp1252', on_bad_lines='skip')
                    if self.fileType_comboBox.currentText() == "Scat":
                        if self.scatValue in filename:
                            path = r"{path}".format(path=os.path.join(ori,filename))
                            # Read with encoding fallback
                            try:
                                specdf=pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
                            except UnicodeDecodeError:
                                try:
                                    specdf=pd.read_csv(path, encoding='latin-1', on_bad_lines='skip')
                                except UnicodeDecodeError:
                                    specdf=pd.read_csv(path, encoding='cp1252', on_bad_lines='skip')
                            self.tempSpec = specdf
                        else:
                            specdf = self.tempSpec

                    for input in selected_items:
                       
                        self.input = input
                        if input in df.columns:
                            x_values = df["Freq"] if "Freq" in df.columns else df["freq[HZ]"]
                            y_values = df[f"{input}"]
                            
                            # Apply frequency range filter
                            x_values_filtered, y_values_filtered = self.filter_frequency_range(x_values, y_values)
                            
                            if len(x_values_filtered) == 0:
                                continue  # Skip if no data in range
                            
                            if self.fileType_comboBox.currentText() == "Tiger/Cntrace":
                                match = re.search(r"^(.*)_DateTime", filename)
                                result = match.group(1) if match else filename.split(".")[0]
                            else:
                                result=filename.split(".csv")[0]

                            Sparam = input.split("_")[0]

                            xMin=x_values_filtered.min()
                            xMax=x_values_filtered.max()
                          
                            # Assign color based on file type and folder
                            if is_all_files_folder:
                                # For TouchStone "All files": Use SN-based color mapping
                                color_key = sn_color_map.get(filename, "1")
                                assigned_color = self.colordata.get(color_key, self.colordata["1"])
                            else:
                                # For non-"All files" (including TouchStone non-All files): 
                                # Use sequential color assignment per chart (trace count)
                                with trace_color_lock:
                                    color_key = str(trace_color_counter["current"])
                                    assigned_color = self.colordata.get(color_key, self.colordata["1"])
                                    trace_color_counter["current"] += 1
                                    if trace_color_counter["current"] > len(self.colordata):
                                        trace_color_counter["current"] = 1  # Loop back to color 1
                            
                            with data_lock:
                                # Track overall min/max for layout
                                if xMin < overall_xMin:
                                    overall_xMin = xMin
                                if xMax > overall_xMax:
                                    overall_xMax = xMax
                                
                                fig.add_trace(go.Scatter(
                                    x=x_values_filtered,
                                    y=y_values_filtered,
                                    line=dict(color=assigned_color),
                                    mode='lines',
                                    name=f"{Sparam}-{result}",
                                    hovertemplate=(
                                        f"<b>{Sparam}-{result}</b><br>" +
                                        "Frequency: %{x}<br>" +
                                        f"{input}: %{{y}}<extra></extra>"
                                    )
                                ))
                                
                                if self.fileType_comboBox.currentText() == "Scat":
                                    if "USL" in specdf.columns and "LSL" in specdf.columns:
                                        # Filter out rows where "USL" or "LSL" are 0 or None
                                        usl_valid = specdf["USL"].notnull() & (specdf["USL"] != 0)
                                        lsl_valid = specdf["LSL"].notnull() & (specdf["LSL"] != 0)
                                        
                                        # Apply frequency range filter to spec lines as well
                                        x_spec_usl, y_spec_usl = self.filter_frequency_range(x_values[usl_valid], specdf["USL"][usl_valid])
                                        x_spec_lsl, y_spec_lsl = self.filter_frequency_range(x_values[lsl_valid], specdf["LSL"][lsl_valid])

                                        # Add traces with valid values
                                        if len(x_spec_usl) > 0:
                                            fig.add_trace(go.Scatter(
                                                x=x_spec_usl,
                                                y=y_spec_usl,
                                                mode='lines',
                                                line=dict(color="Red", width=2),
                                                showlegend=False
                                            ))
                                        if len(x_spec_lsl) > 0:
                                            fig.add_trace(go.Scatter(
                                                x=x_spec_lsl,
                                                y=y_spec_lsl,
                                                mode='lines',
                                                line=dict(color="Black", width=2),
                                                showlegend= False
                                            ))
                    
                    # Update progress after processing each file
                    with data_lock:
                        processed_files += 1
                        # Progress from 40% to 90% during file processing
                        progress = 40 + int((processed_files / total_files) * 50)
                        self.update_progress(progress)
                        self.progressing_progress_text(f"\nProcessing: {filename}")

                except Exception as e:
                    print(f"Error processing file {filename}: {e}")

            # Multi-threaded processing for input files
            self.progressing_progress_text("\nProcessing Files in Parallel...")
            for x in sample:
                thread = threading.Thread(target=process_file, args=(x,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()
            
            self.progressing_progress_text(f"\nCompleted Processing {processed_files} Files")
            self.update_progress(90)

            # Apply layout AFTER all threads complete (not from within threads)
            # Determine the plot title based on batch file reference (for Scat)
            plot_title = base_name
            if self.fileType_comboBox.currentText() == "Scat" and not batch_ref_data.empty:
                # Try to get title from batch file using Channel Number and S-Parameter
                # Use the first selected S-parameter for the title lookup
                if selected_items:
                    first_sparam = selected_items[0]
                    filtered_value = batch_ref_data.loc[
                        (batch_ref_data['S-Parameter'] == first_sparam) & 
                        (batch_ref_data['Channel Number'] == base_name), 
                        'Plot Title'
                    ]
                    if not filtered_value.empty:
                        plot_title = filtered_value.iloc[0]
                        print(f"Using batch file title: {plot_title}")
                    else:
                        # Fallback to CH_S format if not found in batch
                        plot_title = f"{base_name}_{first_sparam}"
                        print(f"Batch reference not found, using default: {plot_title}")
            
            if overall_xMin != float('inf') and overall_xMax != float('-inf'):
                self.progressing_progress_text("\nApplying Layout Configuration...")
                self.apply_layout(fig, plot_title, overall_xMin, overall_xMax,
                                show_legend=self.Legend_checkBox.isChecked(), 
                                manual_hover=self.ManualHover_checkBox.isChecked())

            self.update_progress(92)
            
            if self.specFlag:
                self.progressing_progress_text("\nAdding Spec Lines to Plot...")
                # Check if required columns exist in spec_df
                if 'Channel Group' in self.spec_df.columns and 'S-Parameter' in self.spec_df.columns:
                    for sItem in selected_items:
                        filtered_spec_df = self.spec_df[
                        (self.spec_df['Channel Group'] == base_name) &
                        (self.spec_df['S-Parameter'] == sItem)
                                    ]
                        self.specFig(fig, self.SpecLine_checkBox.isChecked(), filtered_spec_df, sItem)
                else:
                    print(f"Warning: SpecLine.csv is missing required columns. Found columns: {list(self.spec_df.columns)}")
                    self.progressing_progress_text("\nWarning: SpecLine.csv missing required columns")

            # Apply markers if configured
            self.progressing_progress_text("\nApplying Marker Lines...")
            self.apply_markers(fig)

            self.update_progress(95)
            self.progressing_progress_text("\nGenerating HTML and Image Files...")
            
            # Use plot_title for filename as well
            fig.write_html(r"{path}/{name}_{time}.html".format(path=self.htmlPath, name=plot_title,time=now),auto_open=True)
            fig.write_image(r"{path}/{name}_{time}.png".format(path=self.imagePath, name=plot_title,time=now),width=1920, height=1080)
            
            self.progressing_progress_text(f"\nPlot Saved: {plot_title}_{now}")

        except Exception as e:
            print(f"Error in nonColorAssign: {e}")

    def filter_frequency_range(self, x_values, y_values):
        """
        Filter data based on user-specified frequency range.
        
        Args:
            x_values: Frequency values (pandas Series or array)
            y_values: Amplitude values (pandas Series or array)
            
        Returns:
            tuple: (filtered_x_values, filtered_y_values)
        """
        try:
            # If no frequency filter is set, return original data
            if self.freq_start is None and self.freq_stop is None:
                return x_values, y_values
            
            # Create boolean mask for filtering
            mask = pd.Series([True] * len(x_values), index=x_values.index if hasattr(x_values, 'index') else None)
            
            if self.freq_start is not None:
                mask = mask & (x_values >= self.freq_start)
            
            if self.freq_stop is not None:
                mask = mask & (x_values <= self.freq_stop)
            
            # Apply mask to both x and y values
            filtered_x = x_values[mask]
            filtered_y = y_values[mask]
            
            return filtered_x, filtered_y
            
        except Exception as e:
            print(f"Error filtering frequency range: {e}")
            # Return original data if filtering fails
            return x_values, y_values
    
    def apply_markers(self, fig):
        """
        Apply marker lines to the figure based on selected markers in AddLine_listWidget.
        Only markers that are selected (checked) in the list will be plotted.
        
        Args:
            fig: Plotly figure object to add markers to
        """
        try:
            if hasattr(self, 'marker_list') and self.marker_list:
                # Get selected marker names from the Marker Dialog's list widget
                selected_markers = self.markerUI.get_selected_markers()
                
                if not selected_markers:
                    print("No markers selected in AddLine_listWidget")
                    return
                
                # Track annotation positions to prevent overlap
                marker_index = 0
                
                for marker in self.marker_list:
                    # Check if this marker is selected in the list widget
                    marker_display_name = self._get_marker_display_name(marker)
                    if marker_display_name not in selected_markers:
                        continue  # Skip unselected markers
                    
                    line_type = marker.get('LineType', 'Vertical')
                    color = marker['Color']
                    name = marker['Name']
                    marker_type = marker['Type']
                    
                    # Calculate offset for this marker to prevent label overlap
                    # Cycle through offsets to space out labels
                    y_offset = (marker_index % 3) * 0.15  # 0, 0.15, 0.30 in relative units
                    x_offset = (marker_index % 3) * 0.15
                    marker_index += 1
                    
                    if marker_type == 'OnePoint':
                        # OnePoint - Draw a single dot at the coordinate
                        freq = marker['Frequency']
                        value = marker['Value']
                        freq_display = marker.get('FrequencyDisplay', f"{freq}")
                        
                        fig.add_trace(go.Scatter(
                            x=[freq],
                            y=[value],
                            mode='markers',
                            marker=dict(
                                color=color,
                                size=12,
                                symbol='circle',
                                line=dict(color='white', width=2)  # White border for visibility
                            ),
                            name=name,
                            showlegend=True,
                            hovertemplate=(
                                f"<b>{name}</b><br>" +
                                f"Frequency: {freq_display}<br>" +
                                f"Value: {value}<extra></extra>"
                            )
                        ))
                    
                    elif marker_type == 'Single':
                        # Single line(s) - No legend since annotations are shown
                        if line_type in ['Vertical', 'Both']:
                            # Draw 1 vertical line at frequency
                            freq = marker['Frequency']
                            freq_display = marker.get('FrequencyDisplay', f"{freq}")
                            
                            fig.add_vline(
                                x=freq,
                                line_dash="dash",
                                line_color=color,
                                line_width=2,
                                annotation_text=f"{name}",
                                annotation_position="top",
                                annotation_textangle=45,
                                annotation=dict(yshift=y_offset * 20)  # Shift in pixels for staggering
                            )
                        
                        if line_type in ['Horizontal', 'Both']:
                            # Draw 1 horizontal line at value
                            value = marker['Value']
                            
                            fig.add_hline(
                                y=value,
                                line_dash="dash",
                                line_color=color,
                                line_width=2,
                                annotation_text=f"{name}",
                                annotation_position="bottom right",
                                annotation_textangle=0,
                                annotation=dict(xshift=0 * 100)  # Shift in pixels
                            )
                    
                    elif marker_type == 'Range':
                        # Two lines - No legend since annotations are shown
                        if line_type in ['Vertical', 'Both']:
                            # Draw 2 vertical lines at frequency range
                            freq_start = marker['FrequencyStart']
                            freq_end = marker['FrequencyEnd']
                            freq_start_display = marker.get('FrequencyStartDisplay', f"{freq_start}")
                            freq_end_display = marker.get('FrequencyEndDisplay', f"{freq_end}")
                            
                            fig.add_vline(
                                x=freq_start,
                                line_dash="dash",
                                line_color=color,
                                line_width=2,
                                annotation_text=f"{name}^",
                                annotation_position="top",
                                annotation_textangle=-45,
                                annotation=dict(yshift=y_offset * 20)  # Shift in pixels for staggering
                            )
                            fig.add_vline(
                                x=freq_end,
                                line_dash="dash",
                                line_color=color,
                                line_width=2,
                                annotation_text=f"{name}*",
                                annotation_position="top",
                                annotation_textangle=-45,
                                annotation=dict(yshift=y_offset * 20)  # Shift in pixels for staggering
                            )
                        
                        if line_type in ['Horizontal', 'Both']:
                            # Draw 2 horizontal lines at value range
                            value_start = marker['ValueStart']
                            value_end = marker['ValueEnd']
                            
                            fig.add_hline(
                                y=value_start,
                                line_dash="dash",
                                line_color=color,
                                line_width=2,
                                annotation_text=f"{name}^",
                                annotation_position="bottom right",
                                annotation_textangle=0,
                                annotation=dict(xshift=x_offset * 100)  # Shift in pixels
                            )
                            fig.add_hline(
                                y=value_end,
                                line_dash="dash",
                                line_color=color,
                                line_width=2,
                                annotation_text=f"{name}*",
                                annotation_position="bottom right",
                                annotation_textangle=0,
                                annotation=dict(xshift=x_offset * 100)  # Shift in pixels
                            )
        except Exception as e:
            print(f"Error applying markers: {e}")
    
    def _get_marker_display_name(self, marker):
        """
        Helper to construct the display name for a marker based on its type and data.
        This must match the format used in Marker_Dialog.py's AddLine_listWidget.
        
        Args:
            marker: Marker dictionary with Type, Name, Frequency, Value, etc.
            
        Returns:
            str: Display name in format "Name - freq[...]|value[...] - ColorName"
        """
        name = marker['Name']
        color_name = marker.get('ColorName', 'Default (Black)')
        marker_type = marker['Type']
        
        freq_info = ""
        value_info = ""
        
        if marker_type == "Single":
            if marker.get("Frequency") is not None:
                freq_info = f"freq[{marker.get('FrequencyDisplay', '')}]"
            if marker.get("Value") is not None:
                value_info = f"value[{marker.get('Value', '')}]"
        elif marker_type == "OnePoint":
            if marker.get("Frequency") is not None:
                freq_info = f"freq[{marker.get('FrequencyDisplay', '')}]"
            if marker.get("Value") is not None:
                value_info = f"value[{marker.get('Value', '')}]"
        elif marker_type == "Range":
            if marker.get("FrequencyStart") is not None and marker.get("FrequencyEnd") is not None:
                freq_info = f"freq[{marker.get('FrequencyStartDisplay', '')}-{marker.get('FrequencyEndDisplay', '')}]"
            if marker.get("ValueStart") is not None and marker.get("ValueEnd") is not None:
                value_info = f"value[{marker.get('ValueStart', '')}-{marker.get('ValueEnd', '')}]"
        
        # Build display text
        parts = [name]
        if freq_info and value_info:
            parts.append(f"{freq_info}|{value_info}")
        elif freq_info:
            parts.append(freq_info)
        elif value_info:
            parts.append(value_info)
        
        # Join parts with " - " and add color_name at the end
        return f"{' - '.join(parts)} - {color_name}"

    def apply_layout(self,fig, base_name, xMin, xMax,show_legend=True, manual_hover=False):

        x_dtick = Feature().IntergerValueConverter(self.XsteplineEdit.text()) if self.XsteplineEdit.text() else None
        y_dtick = Feature().IntergerValueConverter(self.YsteplineEdit.text()) if self.YsteplineEdit.text() else None

        fig.update_layout(
            title=base_name,
            xaxis_title="Frequency",
            yaxis_title="Amplitude",
            xaxis=dict(
                tickformat=".5s",
                dtick=x_dtick,
                tickangle=45,
                range=[
                    min(fig.layout.xaxis.range[0], xMin) if fig.layout.xaxis.range else xMin,
                    max(fig.layout.xaxis.range[1], xMax) if fig.layout.xaxis.range else xMax
                ]
            ),
            yaxis=dict(
                dtick=y_dtick,
                tickangle=0

            ),
            showlegend=show_legend,
            hovermode="closest" if manual_hover else False,
            legend=dict(
                font=dict(
                    color='black',
                    family='Arial, bold'
                )
            ),
            dragmode='zoom',
            newshape=dict(line_color='black',line_width=2),
            modebar_add=['toggleSpikeLines','drawline', 'eraseshape']
        )

    def specFig(self, fig, show_spec_lines, spec_df, current_s_parameter):
        try:
            if show_spec_lines:
                if not spec_df.empty:
                    # Filter by Enable column - only plot rows with "v"
                    if 'Enable' in spec_df.columns:
                        spec_df = spec_df[spec_df['Enable'] == 'v']
                    
                    if spec_df.empty:
                        print(f"No enabled spec lines to plot for {current_s_parameter}")
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
                                    text=f"Min Spec ({current_s_parameter})<br>TestParameter: {test_param}<br>Value: {min_val} dB<br>Freq: {Feature().format_frequency(start_freq)}",
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
                                    text=f"Min Spec ({current_s_parameter})<br>TestParameter: {test_param}<br>Value: {min_val} dB<br>Start: {Feature().format_frequency(start_freq)}<br>Stop: {Feature().format_frequency(stop_freq)}",
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
                                    text=f"Max Spec ({current_s_parameter})<br>TestParameter: {test_param}<br>Value: {max_val} dB<br>Freq: {Feature().format_frequency(start_freq)}",
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
                                    text=f"Max Spec ({current_s_parameter})<br>TestParameter: {test_param}<br>Value: {max_val} dB<br>Start: {Feature().format_frequency(start_freq)}<br>Stop: {Feature().format_frequency(stop_freq)}",
                                    showlegend=show_max_legend
                                ))
                            
                            # Mark MAX legend as shown
                            spec_legends_shown.add(max_legend_name)

                else:
                    if 'Channel Group' in spec_df.columns:
                        print(f"No spec lines to plot for {current_s_parameter} in {spec_df['Channel Group'].unique()}")
                    else:
                        print(f"No spec lines to plot for {current_s_parameter}")

        except Exception as e:
            print(f"Error in specFig: {e}")   

    def select_all_items(self):
        try:
            self.SelectAll_Flag = not self.SelectAll_Flag
            if self.SelectAll_Flag:
                for index in range(self.listWidget.count()):
                    item = self.listWidget.item(index)
                    item.setCheckState(Qt.Checked)
            else:
                for index in range(self.listWidget.count()):
                    item = self.listWidget.item(index)
                    item.setCheckState(Qt.Unchecked)
                    
        except Exception as e:
            print(f"Error in nonColorAssign: {e}")
            self.handle_error(f"Error in nonColorAssign: {e}")

    def filterItems(self):
        try:
            self.listWidget.clear()
            itemsList=Feature().get_unique_headers(self.SOnly_checkBox.isChecked(),self.FOnly_checkBox.isChecked(),r'{path}'.format(path=self.Manual_lineEdit.text()))
            # itemsList = Feature().get_unique_headers(r'{path}'.format(path=self.Manual_lineEdit.text()))

            if self.SFilter_lineEdit.text():               
                self.filterList=[item for item in itemsList if str(self.SFilter_lineEdit.text()).lower() in item.lower()]
            else:
                self.filterList=itemsList

            for i in (self.filterList):
                temp_item = QListWidgetItem(f'{i}')
                temp_item.setFlags(temp_item.flags() | Qt.ItemIsUserCheckable)  # Make the item checkable
                temp_item.setCheckState(Qt.Unchecked)  # Set initial check state to unchecked
                self.listWidget.addItem(temp_item)

        except Exception as e:
            self.handle_error(f"Error in nonColorAssign: {e}")
   
    def start_listParam(self):
        """Threaded wrapper for listParam to prevent UI freezing"""
        try:
            thread = threading.Thread(target=self.listParam)
            thread.start()
        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    @Slot()
    def listParam(self):
        try:
            self.LoadingProgressBarManual("Processing...")
            self.listWidget.clear()

            item = Feature().get_unique_headers(self.SOnly_checkBox.isChecked(),self.FOnly_checkBox.isChecked(),r'{path}'.format(path=self.Manual_lineEdit.text()))
            for i in item:
                temp_item = QListWidgetItem(f'{i}')
                temp_item.setFlags(temp_item.flags() | Qt.ItemIsUserCheckable)
                temp_item.setCheckState(Qt.Unchecked)
                self.listWidget.addItem(temp_item)

            self.RunProgressBarManual("Sparam Header Filtered...")

        except Exception as e:
            print(e)
            self.handle_error(f"\n{str(e)}")

    def Extract_directory(self, args):
        try:
            # For "1", open a dialog to select a random directory
            if args == "1":
                if self.ZipDir_lineEdit.text():
                    module_directory = r"{path}".format(path=self.ZipDir_lineEdit.text())
                else:
                    module_directory = r"{path}".format(path=os.getcwd())

                directory = QFileDialog.getExistingDirectory(self, "Select Directory",module_directory)

            # For "2", open a dialog starting in the specified directory
            elif args == "2":
                # Define the starting directory
                if self.Manual_lineEdit.text():
                    start_directory = r"{path}".format(path=self.Manual_lineEdit.text())
                else:
                    start_directory = r"{path}/dataset/results".format(path=os.getcwd())
                if not os.path.exists(start_directory):
                    # Handle case where the directory doesn't exist
                    self.handle_error(f"The directory '{start_directory}' does not exist!")
                    return
                # Open the dialog starting from the defined directory
                directory = QFileDialog.getExistingDirectory(self, "Select Directory", start_directory)


            # Set the selected directory path to the appropriate QLineEdit
            if directory:
                if args == "1":
                    self.ZipDir_lineEdit.clear()
                    self.ZipDir_lineEdit.setText(directory)
                elif args == "2":
                    self.Manual_lineEdit.clear()
                    self.Manual_lineEdit.setText(directory)

        except Exception as e:
            # Handle any errors
            self.handle_error(f"Error in Extract_directory: {str(e)}")

    def start_compile(self):
        self.Manual_lineEdit.clear()
        # Save compile settings to memory
        self.save_compile_memory()
        
        Feature().set_default_value(self.TPType_comboBox.currentText())
        self.setWindowTitle(f"{self.versionName} {self.TPType_comboBox.currentText()}")
        self.compile_thread = threading.Thread(target=self.Compile)      
        self.compile_thread.start()

    def Compile(self):
        try:
            self.update_progress(10)
            self.deleteFiles()

            if self.fileType_comboBox.currentText() == "Tiger/Cntrace":
                start_time = time.time()
                obj= TigerOrCntrace()
                self.update_progress_text("\nConvert to Data Frame ----> Data Processing")
                obj.set_path(self.dest, self.savepath)
                obj.Convert2DataFrame()
                self.update_text_edit_color(10)
                self.update_progress(10)
                obj.MetaHeaderPos()
                self.update_text_edit_color(25)
                self.update_progress(25)
                self.update_progress_text("\nData Processing --------> Convert to csv")
                obj.Dataprocessing()
                self.update_text_edit_color(70)
                self.update_progress(70)
                self.update_progress_text("\nConverting to csv ------> Save Files")
                obj.saveFile()
                end_time = time.time()
                elapsed_time = end_time - start_time
                self.update_progress_text(f"\nCompilation Completed in {Feature().convert_seconds(elapsed_time)}")
                self.update_text_edit_color(100)
                self.update_progress(100)
               

            elif self.fileType_comboBox.currentText() == "Scat":
                start_time = time.time()
                obj = Scat()
                self.update_progress_text("\nConvert to Data Frame ----> Data Processing")
                obj.setPath(self.dest, self.savepath)
                obj.convert2DataFrame()
                self.update_text_edit_color(50)
                self.update_progress(50)   
                self.update_progress_text("\nData Processing --------> Merging according to Channel")
                obj.extractData()
                self.update_text_edit_color(100)
                self.update_progress(100)      
                end_time = time.time()
                elapsed_time = end_time - start_time
                self.update_progress_text(f"\nCompilation Completed in {elapsed_time:.2f} Seconds")

            elif self.fileType_comboBox.currentText() == "TouchStone":
                start_time = time.time()
                datasrc = r'{path}'.format(path=self.ZipDir_lineEdit.text())
                obj = TouchStone()
                self.update_progress_text("\nConvert to Data Frame ----> Data Processing")
                obj.setpath(datasrc,self.savepath)
                self.update_text_edit_color(50)
                self.update_progress(50)
                self.update_progress_text("\nData Processing --------> Merging according to Channel")
                obj.DataProcessing()
                obj.saveData()
                self.update_text_edit_color(90)
                self.update_progress(90)
                
                # Consolidate all CSV files into "All files" folder
                self.update_progress_text("\nConsolidating files --------> Creating 'All files' folder")
                self.consolidate_touchstone_files()
                
                self.update_text_edit_color(100)
                self.update_progress(100)
                end_time = time.time()
                elapsed_time = end_time - start_time
                self.update_progress_text(f"\nCompilation Completed in {elapsed_time:.2f} Seconds")

        except Exception as e:
            self.handle_error(f"\n{str(e)}")

    def deleteFiles(self):
        try:
            datasrc = r'{path}'.format(path=self.ZipDir_lineEdit.text())
            self.update_progress_text("\nRemoving previous storage ----> Convert to Data Frame")
            dir = Directory()
            dir.delete_all_files_and_subfolders(self.copysrc)
            dir.delete_all_files_and_subfolders(self.dest)
            dir.delete_all_files_and_subfolders(self.savepath)
            
            # Clean up all folders inside results directory before compilation
            if os.path.exists(self.resultPath):
                import shutil
                for item in os.listdir(self.resultPath):
                    item_path = os.path.join(self.resultPath, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        print(f"Deleted results folder: {item}")
            
            dir.copy_file(datasrc)
            dir.rename_and_unzip_scat(self.copysrc, self.dest)

            if self.fileType_comboBox.currentText() == "Scat":
                dir.rename_and_unzip_scat(self.copysrc, self.dest)
            else:
                dir.rename_and_unzip(self.copysrc, self.dest)

            del dir
        except Exception as e:
            self.handle_error(str(e))

    def consolidate_touchstone_files(self):
        """
        Consolidate all CSV files from TouchStone result folders into a single 'All files' folder.
        This copies all CSV files from subdirectories in dataset/results into one consolidated folder.
        """
        try:
            import shutil
            
            # Define paths
            results_path = self.resultPath  # dataset/results
            all_files_folder = os.path.join(results_path, "All files")
            
            print(f"[DEBUG] Results path: {results_path}")
            print(f"[DEBUG] All files folder target: {all_files_folder}")
            
            # Check if results path exists
            if not os.path.exists(results_path):
                print(f"[ERROR] Results path does not exist: {results_path}")
                self.update_progress_text(f"\nError: Results folder not found at {results_path}")
                return
            
            # Create "All files" folder (delete if exists to start fresh)
            if os.path.exists(all_files_folder):
                shutil.rmtree(all_files_folder)
                print(f"[DEBUG] Removed existing 'All files' folder")
            
            os.makedirs(all_files_folder, exist_ok=True)
            print(f"[DEBUG] Created consolidated folder: {all_files_folder}")
            
            # Counter for tracking
            total_files_copied = 0
            folders_processed = 0
            
            # List all items in results directory
            items_in_results = os.listdir(results_path)
            print(f"[DEBUG] Items in results directory: {items_in_results}")
            
            # Iterate through all subdirectories in results
            for item in items_in_results:
                item_path = os.path.join(results_path, item)
                
                # Skip if it's not a directory or if it's the "All files" folder itself
                if not os.path.isdir(item_path):
                    print(f"[DEBUG] Skipping non-directory: {item}")
                    continue
                    
                if item == "All files":
                    print(f"[DEBUG] Skipping 'All files' folder itself")
                    continue
                
                print(f"[DEBUG] Processing folder: {item}")
                folders_processed += 1
                
                # Find all CSV files in this subdirectory
                files_in_folder = os.listdir(item_path)
                csv_files = [f for f in files_in_folder if f.endswith('.csv')]
                print(f"[DEBUG] Found {len(csv_files)} CSV files in {item}")
                
                for file in csv_files:
                    source_file = os.path.join(item_path, file)
                    dest_file = os.path.join(all_files_folder, file)
                    
                    # Handle duplicate filenames by adding folder prefix
                    if os.path.exists(dest_file):
                        # Add folder name as prefix to avoid overwriting
                        base_name, ext = os.path.splitext(file)
                        dest_file = os.path.join(all_files_folder, f"{item}_{base_name}{ext}")
                        print(f"[DEBUG] Duplicate detected, renaming to: {item}_{base_name}{ext}")
                    
                    # Copy the file
                    shutil.copy2(source_file, dest_file)
                    total_files_copied += 1
                    print(f"[DEBUG] Copied: {file}")
            
            print(
                f"[SUCCESS] Consolidation complete: Copied {total_files_copied} CSV files "
                f"from {folders_processed} folders into 'All files'"
            )
            self.update_progress_text(
                f"\nConsolidated {total_files_copied} CSV files from {folders_processed} folders"
            )
            
        except Exception as e:
            import traceback
            print(f"[ERROR] Error consolidating TouchStone files: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            self.update_progress_text(f"\nWarning: File consolidation failed - {str(e)}")

    ## Button Event 
    def keyReleaseEvent(self, event):
        try:
            # Check if the Enter key is released
            if event.key() == 16777220:  # Enter key
                current_tab_index = self.tabWidget.currentIndex()
                focused_widget = self.focusWidget()

                if current_tab_index == 0:
                    if focused_widget == self.SFilter_lineEdit:
                        # print(f"Enter pressed in: {focused_widget.objectName()}")
                        self.filterItems()
                    elif focused_widget == self.Manual_lineEdit:
                        self.listParam()
            else:
                # Call the base class method for other keys
                super(Main_Widget, self).keyReleaseEvent(event)

        except Exception as e:
            self.handle_error(f"Error: {e}")

    def start_loading_process(self, message):
        """
        Initializes and starts the worker thread.
        """
        # 1. Instantiate the worker
        self.thread = ProgressBarWorker(message)
        
        # 2. Connect signals to slots
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.finished_message.connect(self.progressing_progress_text)
        self.thread.finished_message.connect(self.complete_progress_text)
        self.thread.normal_updated.connect(self.listParam)

        # Connect to a cleanup slot when the thread finishes
        self.thread.finished.connect(self.thread_finished)
        self.thread.progress_updated.connect(self.thread_finished)

        # 3. Start the thread
        self.thread.start()

    def thread_finished(self):
        """
        Cleanup logic after the thread completes.
        """
        print("Progress bar thread finished.")
        # Optional: Delete the worker object when it's done
        self.thread.deleteLater()

    # ============================================
    # Delegated Methods to Helper Classes
    # ============================================
    
    # Progress Bar Methods - Delegated to ProgressBarHandler
    @Slot(int)
    def update_progress(self, value):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.update_progress(value)

    @Slot(str)
    def update_progress_text(self, text):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.update_progress_text(text)

    @Slot(str)
    def update_progress_text2(self, text):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.update_progress_text2(text)

    @Slot(str)
    def complete_progress_text(self, message):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.complete_progress_text(message)

    @Slot(str)
    def progressing_progress_text(self, message):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.progressing_progress_text(message)

    @Slot(int)
    def update_text_edit_color(self, value):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.update_text_edit_color(value)
        
    @Slot(int)
    def update_text_edit_color2(self, value):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.update_text_edit_color2(value)

    @Slot(str)
    def RunProgressBarManual(self, message):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.run_progress_bar_manual(message)
        
    @Slot(str)
    def LoadingProgressBarManual(self, message):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.loading_progress_bar_manual(message)
        
    @Slot(str)
    def LoadingConfigurationManual(self, message, num):
        """Delegate to ProgressBarHandler"""
        self.progress_handler.loading_configuration_manual(message, num)

    # Error Handling Methods - Delegated to ErrorHandler
    def handle_error(self, error_message):
        """Delegate to ErrorHandler"""
        self.error_handler.handle_error(error_message)

    def handle_error2(self, error_message):
        """Delegate to ErrorHandler"""
        self.error_handler.handle_error2(error_message)

    def Dialog_handle_error(self, error_message):
        """Delegate to ErrorHandler"""
        self.error_handler.dialog_handle_error(error_message)
        
    def TouchStoneOverlayAlert(self,parent=None, title="Confirm", message="Do you want to overlay the existing TouchStone plots?"):
        alert = QMessageBox(parent)
        alert.setWindowTitle(title)
        alert.setText(message)
        alert.setIcon(QMessageBox.Question)
        alert.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        alert.setDefaultButton(QMessageBox.No)

        result = alert.exec_()
        return result == QMessageBox.Yes