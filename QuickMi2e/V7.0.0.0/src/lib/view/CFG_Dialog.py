from ui.ui_build.ui_cfg import Ui_CFG
from PySide6.QtCore import  QMetaObject, Q_ARG
from PySide6.QtWidgets import  QColorDialog, QDialog, QAbstractItemView
import os

# ... inside your class ...
class CFG_Dialog:
    def __init__(self,colordata,error_handle,ProgressBar_textEdit,byLotCheckbox,byUiCheckbox,byCfgFileCheckbox):
        self.dialog = QDialog()
        self.ui = Ui_CFG()
        self.ui.setupUi(self.dialog)
        self.handle_error = error_handle
        self.__Dialog_colorDict = dict()
        self.__Dialog_compileDict =dict()
        self.colordata = colordata
        self.ProgressBar_textEdit = ProgressBar_textEdit
        self.ByLot_checkBox = byLotCheckbox
        self.cfgUI_checkBox = byUiCheckbox
        self.cfgFile_checkBox = byCfgFileCheckbox

        # --- Add this line below ---
        self.dialog.setWindowTitle("CFG Arrangement Dialog")

    def setcolorDict(self, colordata):
        self.__Dialog_colorDict = colordata

    def setcompileDict(self, compileDict):
        self.__Dialog_compileDict = compileDict

    @property
    def getcolorDict(self):
        return self.__Dialog_colorDict

    @property
    def getcompileDict(self):
        return self.__Dialog_compileDict

    def open_dialog(self,args):
            try:
                if args[1]:  # Check if the checkbox is checked
                    self.__Dialog_compileDict= {}
                    self.__Dialog_colorDict= {}
                    self.ui.listWidget_UnitList.clear()
                    self.ui.listWidget_G1.clear()
                    self.ui.listWidget_G2.clear()
                    self.ui.listWidget_G3.clear()
                    self.ui.listWidget_G4.clear()
                    if self.ByLot_checkBox.isChecked():
                        self.cfgUI_checkBox.setChecked(False)

                    if self.cfgUI_checkBox.isChecked():
                        self.cfgFile_checkBox.setChecked(False)
                        if args[0]=="":
                            self.handle_error(f"\n Please Check Manual Plot path, it is empty!")
                        
                        components  = [sample.split(".")[0] for sample in os.listdir(args[0])]

                        self.ui.listWidget_UnitList.addItems(components)
                        self.ui.listWidget_UnitList.setDragEnabled(True)
                        self.ui.listWidget_UnitList.setAcceptDrops(True)
                        self.ui.listWidget_UnitList.setSelectionMode(QAbstractItemView.MultiSelection)
                        self.ui.listWidget_UnitList.dropEvent = self.drop_event_wrapper(self.ui.listWidget_UnitList.dropEvent, 
                                                                                        [self.ui.listWidget_G1, self.ui.listWidget_UnitList])
                        self.ui.listWidget_UnitList.dropEvent = self.drop_event_wrapper(self.ui.listWidget_UnitList.dropEvent, 
                                                                                        [self.ui.listWidget_G2, self.ui.listWidget_UnitList])
                        self.ui.listWidget_UnitList.dropEvent = self.drop_event_wrapper(self.ui.listWidget_UnitList.dropEvent, 
                                                                                        [self.ui.listWidget_G3, self.ui.listWidget_UnitList])
                        self.ui.listWidget_UnitList.dropEvent = self.drop_event_wrapper(self.ui.listWidget_UnitList.dropEvent, 
                                                                                        [self.ui.listWidget_G4, self.ui.listWidget_UnitList])

                        self.ui.listWidget_G1.setDragEnabled(True)
                        self.ui.listWidget_G1.setAcceptDrops(True)
                        self.ui.listWidget_G1.setSelectionMode(QAbstractItemView.MultiSelection)
                        self.ui.listWidget_G1.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G1.dropEvent, 
                                                                                [self.ui.listWidget_UnitList, self.ui.listWidget_G1])
                        self.ui.listWidget_G2.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G2.dropEvent, 
                                                                                [self.ui.listWidget_G1, self.ui.listWidget_G2])
                        self.ui.listWidget_G3.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G3.dropEvent, 
                                                                                [self.ui.listWidget_G1, self.ui.listWidget_G3])
                        self.ui.listWidget_G4.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G4.dropEvent, 
                                                                                [self.ui.listWidget_G1, self.ui.listWidget_G4])
                        
                        self.ui.listWidget_G2.setDragEnabled(True)
                        self.ui.listWidget_G2.setAcceptDrops(True)
                        self.ui.listWidget_G2.setSelectionMode(QAbstractItemView.MultiSelection)
                        self.ui.listWidget_G2.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G2.dropEvent, 
                                                                                [self.ui.listWidget_UnitList, self.ui.listWidget_G2])
                        
                        self.ui.listWidget_G1.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G1.dropEvent, 
                                                                                [self.ui.listWidget_G2, self.ui.listWidget_G1])
                        self.ui.listWidget_G3.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G3.dropEvent, 
                                                                                [self.ui.listWidget_G2, self.ui.listWidget_G3])
                        self.ui.listWidget_G4.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G4.dropEvent, 
                                                                                [self.ui.listWidget_G2, self.ui.listWidget_G4])

                        self.ui.listWidget_G3.setDragEnabled(True)
                        self.ui.listWidget_G3.setAcceptDrops(True)
                        self.ui.listWidget_G3.setSelectionMode(QAbstractItemView.MultiSelection)
                        self.ui.listWidget_G3.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G3.dropEvent, 
                                                                                [self.ui.listWidget_UnitList, self.ui.listWidget_G3])
                        
                        self.ui.listWidget_G1.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G1.dropEvent, 
                                                                                [self.ui.listWidget_G3, self.ui.listWidget_G1])
                        self.ui.listWidget_G2.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G2.dropEvent, 
                                                                                [self.ui.listWidget_G3, self.ui.listWidget_G2])
                        self.ui.listWidget_G4.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G4.dropEvent, 
                                                                                [self.ui.listWidget_G3, self.ui.listWidget_G4])

                        self.ui.listWidget_G4.setDragEnabled(True)
                        self.ui.listWidget_G4.setAcceptDrops(True)
                        self.ui.listWidget_G4.setSelectionMode(QAbstractItemView.MultiSelection)
                        self.ui.listWidget_G4.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G4.dropEvent, 
                                                                                [self.ui.listWidget_UnitList, self.ui.listWidget_G4])
                        
                        self.ui.listWidget_G1.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G1.dropEvent, 
                                                                                [self.ui.listWidget_G4, self.ui.listWidget_G1])
                        self.ui.listWidget_G2.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G2.dropEvent, 
                                                                                [self.ui.listWidget_G4, self.ui.listWidget_G2])
                        self.ui.listWidget_G3.dropEvent = self.drop_event_wrapper(self.ui.listWidget_G3.dropEvent, 
                                                                                [self.ui.listWidget_G4, self.ui.listWidget_G3])
                        
                        # Set Default Color
                        self.__Dialog_colorDict["G1"]=self.colordata["1"]
                        self.__Dialog_colorDict["G2"]=self.colordata["2"]
                        self.__Dialog_colorDict["G3"]=self.colordata["3"]
                        self.__Dialog_colorDict["G4"]=self.colordata["4"]

                        self.ui.selectButton_1.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {self.colordata["1"]}; /* Default  background color */
                        }}
                        """)

                        self.ui.selectButton_2.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {self.colordata["2"]}; /* Default  background color */

                        }}
                        """)

                        self.ui.selectButton_3.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {self.colordata["3"]}; /* Dyefault background color */
                
                        }}
                        """)

                        self.ui.selectButton_4.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {self.colordata["4"]}; /* Default  background color */
                        }}
                        """)

                        self.ui.selectButton_1.clicked.connect(lambda: self.color('G1'))
                        self.ui.selectButton_2.clicked.connect(lambda: self.color('G2'))
                        self.ui.selectButton_3.clicked.connect(lambda: self.color('G3'))
                        self.ui.selectButton_4.clicked.connect(lambda: self.color('G4'))

                        self.ui.cancelButton.clicked.connect(self.dialog.close)  # This ensures the dialog closes
                        self.ui.doneButton.clicked.connect(self.unitCompile)
                        self.dialog.exec()
                    else:
                        self.__Dialog_colorDict={}
                        self.__Dialog_compileDict= {}

            except Exception as e:
                self.Dialog_handle_error(f"\n{e}")

    def drop_event_wrapper(self, original_drop_event, list_widgets):
        def new_drop_event(event):
                # Call the original dropEvent method
            original_drop_event(event)
                
            source_list_widget = event.source()
            selected_items = source_list_widget.selectedItems()
                
                # Remove the dragged items from the source list widget
            for item in selected_items:
                source_list_widget.takeItem(source_list_widget.row(item))
                del item  # Delete the item to avoid memory leak

        return new_drop_event

    def unitCompile(self):
            try:
                colorText =""
                arrangeText=""
                itemsG1 = [self.ui.listWidget_G1.item(i).text() for i in range(self.ui.listWidget_G1.count())]
                itemsG2 = [self.ui.listWidget_G2.item(i).text() for i in range(self.ui.listWidget_G2.count())]
                itemsG3 = [self.ui.listWidget_G3.item(i).text() for i in range(self.ui.listWidget_G3.count())]
                itemsG4 = [self.ui.listWidget_G4.item(i).text() for i in range(self.ui.listWidget_G4.count())]
                if itemsG1:
                    self.__Dialog_compileDict["G1"]= itemsG1
                if itemsG2:
                    self.__Dialog_compileDict["G2"]= itemsG2
                if itemsG3:
                    self.__Dialog_compileDict["G3"]= itemsG3
                if itemsG4:
                    self.__Dialog_compileDict["G4"]= itemsG4

                self.dialog.close()

                if self.__Dialog_compileDict:
                    colorText="Color is Set"
                else:
                    colorText="Color not Set"

                if self.__Dialog_compileDict:
                    arrangeText="Unit Arrangement is set"
                else:
                    arrangeText="Unit Arrangement not set"

                self.ProgressBar_textEdit.setText(f"\n{colorText} and {arrangeText}")

            except Exception as e:
                self.Dialog_handle_error(f"\n{str(e)}")
                self.handle_error(f"\n{str(e)}")


    def color(self, argument):
        color = QColorDialog.getColor()
        if color.isValid():
            if argument =="G1":
                self.ui.selectButton_1.setStyleSheet(f"QPushButton {{ background-color: {color.name()}; }}")
            elif argument =="G2":
                self.ui.selectButton_2.setStyleSheet(f"QPushButton {{ background-color: {color.name()}; }}")
            elif argument =="G3":
                self.ui.selectButton_3.setStyleSheet(f"QPushButton {{ background-color: {color.name()}; }}")
            elif argument =="G4":
                self.ui.selectButton_4.setStyleSheet(f"QPushButton {{ background-color: {color.name()}; }}")

            self.__Dialog_colorDict[argument]=color.name()

    def Dialog_handle_error(self, error_message):
        error_style = """
        background-color: #ff3d5a;
        """
        QMetaObject.invokeMethod(self.ui.MessageBox, "setStyleSheet", Q_ARG(str, error_style))
        # self.update_progress_text(error_message)
        print(f"Error: {error_message}")