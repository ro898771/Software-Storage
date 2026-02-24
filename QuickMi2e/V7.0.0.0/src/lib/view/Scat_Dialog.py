from PySide6.QtWidgets import QDialog,QListWidget
from ui.ui_build.ui_ScatSpec import Ui_Scat
import os

class Scat_Dialog:
    def __init__(self):
        self.scatLog = QDialog()
        self.uiscat  = Ui_Scat()
        self.uiscat.setupUi(self.scatLog)
        self.__scatValue=None

    @property
    def getSpecHeader(self):
        self.__specPath = r"{path}\dataset\cntrace\zip".format(path=os.getcwd())
        if not self.__specPath:
            return []
        return [
            os.path.splitext(filename)[0]
            for filename in os.listdir(self.__specPath)
            if filename.lower().endswith('.zip')
        ]
    
    @property
    def getscatValue(self):
        return self.__scatValue
    
    def apply(self):
        self.uiscat.ScatlistWidget.clear()
        self.uiscat.ScatlistWidget.addItems(self.getSpecHeader)
        self.uiscat.ScatlistWidget.setSelectionMode(QListWidget.SingleSelection)  
        self.uiscat.ScatConfirmedButton.clicked.connect(self.get_selected_item)                                 
        self.scatLog.exec()
    
    def get_selected_item(self):
        selected_items = self.uiscat.ScatlistWidget.selectedItems()
        if selected_items:
            self.__scatValue=selected_items[0].text()           
        else:
            None
        self.scatLog.close()