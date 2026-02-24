# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'marker.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QGroupBox,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QWidget)

class Ui_marker(object):
    def setupUi(self, marker):
        if not marker.objectName():
            marker.setObjectName(u"marker")
        marker.resize(734, 436)
        self.MarkerEdit_groupBox = QGroupBox(marker)
        self.MarkerEdit_groupBox.setObjectName(u"MarkerEdit_groupBox")
        self.MarkerEdit_groupBox.setGeometry(QRect(10, 0, 721, 421))
        font = QFont()
        font.setBold(True)
        self.MarkerEdit_groupBox.setFont(font)
        self.frequencyEdit = QLineEdit(self.MarkerEdit_groupBox)
        self.frequencyEdit.setObjectName(u"frequencyEdit")
        self.frequencyEdit.setGeometry(QRect(90, 153, 211, 21))
        self.TestCode = QLabel(self.MarkerEdit_groupBox)
        self.TestCode.setObjectName(u"TestCode")
        self.TestCode.setGeometry(QRect(20, 153, 61, 21))
        font1 = QFont()
        font1.setBold(True)
        font1.setKerning(False)
        self.TestCode.setFont(font1)
        self.MarkerType_comboBox = QComboBox(self.MarkerEdit_groupBox)
        self.MarkerType_comboBox.setObjectName(u"MarkerType_comboBox")
        self.MarkerType_comboBox.setGeometry(QRect(90, 26, 211, 31))
        font2 = QFont()
        font2.setBold(False)
        font2.setKerning(False)
        self.MarkerType_comboBox.setFont(font2)
        self.TestCode_2 = QLabel(self.MarkerEdit_groupBox)
        self.TestCode_2.setObjectName(u"TestCode_2")
        self.TestCode_2.setGeometry(QRect(20, 30, 61, 21))
        self.TestCode_2.setFont(font1)
        self.valueEdit = QLineEdit(self.MarkerEdit_groupBox)
        self.valueEdit.setObjectName(u"valueEdit")
        self.valueEdit.setGeometry(QRect(90, 190, 211, 21))
        self.TestCode_3 = QLabel(self.MarkerEdit_groupBox)
        self.TestCode_3.setObjectName(u"TestCode_3")
        self.TestCode_3.setGeometry(QRect(20, 190, 61, 21))
        self.TestCode_3.setFont(font1)
        self.MarkerAddLine_groupBox = QGroupBox(self.MarkerEdit_groupBox)
        self.MarkerAddLine_groupBox.setObjectName(u"MarkerAddLine_groupBox")
        self.MarkerAddLine_groupBox.setGeometry(QRect(310, 10, 391, 401))
        self.MarkerAddLine_groupBox.setFont(font)
        self.AddLine_listWidget = QListWidget(self.MarkerAddLine_groupBox)
        self.AddLine_listWidget.setObjectName(u"AddLine_listWidget")
        self.AddLine_listWidget.setGeometry(QRect(10, 20, 371, 371))
        font3 = QFont()
        font3.setBold(True)
        font3.setKerning(True)
        self.AddLine_listWidget.setFont(font3)
        self.MarkerColor_comboBox = QComboBox(self.MarkerEdit_groupBox)
        self.MarkerColor_comboBox.setObjectName(u"MarkerColor_comboBox")
        self.MarkerColor_comboBox.setGeometry(QRect(90, 76, 211, 31))
        self.MarkerColor_comboBox.setFont(font2)
        self.TestCode_4 = QLabel(self.MarkerEdit_groupBox)
        self.TestCode_4.setObjectName(u"TestCode_4")
        self.TestCode_4.setGeometry(QRect(20, 80, 41, 21))
        self.TestCode_4.setFont(font1)
        self.MarkerAddButton = QPushButton(self.MarkerEdit_groupBox)
        self.MarkerAddButton.setObjectName(u"MarkerAddButton")
        self.MarkerAddButton.setGeometry(QRect(10, 230, 181, 31))
        font4 = QFont()
        font4.setBold(False)
        font4.setItalic(True)
        font4.setKerning(False)
        self.MarkerAddButton.setFont(font4)
        self.MarkerUndoButton = QPushButton(self.MarkerEdit_groupBox)
        self.MarkerUndoButton.setObjectName(u"MarkerUndoButton")
        self.MarkerUndoButton.setGeometry(QRect(200, 230, 101, 31))
        self.MarkerUndoButton.setFont(font4)
        self.MarkerPlotButton = QPushButton(self.MarkerEdit_groupBox)
        self.MarkerPlotButton.setObjectName(u"MarkerPlotButton")
        self.MarkerPlotButton.setGeometry(QRect(10, 320, 291, 51))
        self.MarkerPlotButton.setFont(font4)
        self.MarkerCancelButton = QPushButton(self.MarkerEdit_groupBox)
        self.MarkerCancelButton.setObjectName(u"MarkerCancelButton")
        self.MarkerCancelButton.setGeometry(QRect(10, 380, 291, 31))
        self.MarkerCancelButton.setFont(font4)
        self.MarkerClearButton = QPushButton(self.MarkerEdit_groupBox)
        self.MarkerClearButton.setObjectName(u"MarkerClearButton")
        self.MarkerClearButton.setGeometry(QRect(10, 280, 291, 31))
        self.MarkerClearButton.setFont(font4)
        self.NameEdit = QLineEdit(self.MarkerEdit_groupBox)
        self.NameEdit.setObjectName(u"NameEdit")
        self.NameEdit.setGeometry(QRect(90, 120, 211, 21))
        self.MarkerName = QLabel(self.MarkerEdit_groupBox)
        self.MarkerName.setObjectName(u"MarkerName")
        self.MarkerName.setGeometry(QRect(20, 120, 61, 21))
        self.MarkerName.setFont(font1)

        self.retranslateUi(marker)

        QMetaObject.connectSlotsByName(marker)
    # setupUi

    def retranslateUi(self, marker):
        marker.setWindowTitle(QCoreApplication.translate("marker", u"Dialog", None))
        self.MarkerEdit_groupBox.setTitle(QCoreApplication.translate("marker", u"Editor", None))
        self.TestCode.setText(QCoreApplication.translate("marker", u"Frequency:", None))
        self.TestCode_2.setText(QCoreApplication.translate("marker", u"Type:", None))
        self.TestCode_3.setText(QCoreApplication.translate("marker", u"Value:", None))
        self.MarkerAddLine_groupBox.setTitle(QCoreApplication.translate("marker", u"AddLine", None))
        self.TestCode_4.setText(QCoreApplication.translate("marker", u"Color:", None))
        self.MarkerAddButton.setText(QCoreApplication.translate("marker", u"Add", None))
        self.MarkerUndoButton.setText(QCoreApplication.translate("marker", u"Undo", None))
        self.MarkerPlotButton.setText(QCoreApplication.translate("marker", u"Plot", None))
        self.MarkerCancelButton.setText(QCoreApplication.translate("marker", u"Cancel", None))
        self.MarkerClearButton.setText(QCoreApplication.translate("marker", u"Clear All", None))
        self.MarkerName.setText(QCoreApplication.translate("marker", u"Name:", None))
    # retranslateUi

