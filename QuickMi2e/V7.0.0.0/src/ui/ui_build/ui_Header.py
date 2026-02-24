# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'header.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGroupBox,
    QLabel, QPushButton, QSizePolicy, QWidget)

class Ui_Header(object):
    def setupUi(self, Header):
        if not Header.objectName():
            Header.setObjectName(u"Header")
        Header.resize(1150, 293)
        self.groupBox = QGroupBox(Header)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 20, 201, 261))
        font = QFont()
        font.setBold(True)
        self.groupBox.setFont(font)
        self.SubLot_checkBox = QCheckBox(self.groupBox)
        self.SubLot_checkBox.setObjectName(u"SubLot_checkBox")
        self.SubLot_checkBox.setGeometry(QRect(10, 70, 61, 20))
        self.TesterName_checkBox = QCheckBox(self.groupBox)
        self.TesterName_checkBox.setObjectName(u"TesterName_checkBox")
        self.TesterName_checkBox.setGeometry(QRect(90, 70, 91, 20))
        self.MFGID_checkBox = QCheckBox(self.groupBox)
        self.MFGID_checkBox.setObjectName(u"MFGID_checkBox")
        self.MFGID_checkBox.setGeometry(QRect(10, 110, 61, 20))
        self.ModuleID_checkBox = QCheckBox(self.groupBox)
        self.ModuleID_checkBox.setObjectName(u"ModuleID_checkBox")
        self.ModuleID_checkBox.setGeometry(QRect(90, 110, 81, 20))
        self.AssemblyLotcheckBox = QCheckBox(self.groupBox)
        self.AssemblyLotcheckBox.setObjectName(u"AssemblyLotcheckBox")
        self.AssemblyLotcheckBox.setGeometry(QRect(90, 150, 101, 20))
        self.Default_checkBox = QCheckBox(self.groupBox)
        self.Default_checkBox.setObjectName(u"Default_checkBox")
        self.Default_checkBox.setGeometry(QRect(10, 30, 71, 20))
        self.headerUpdateButton = QPushButton(self.groupBox)
        self.headerUpdateButton.setObjectName(u"headerUpdateButton")
        self.headerUpdateButton.setGeometry(QRect(10, 220, 171, 31))
        self.WaferID_checkBox = QCheckBox(self.groupBox)
        self.WaferID_checkBox.setObjectName(u"WaferID_checkBox")
        self.WaferID_checkBox.setGeometry(QRect(10, 150, 71, 20))
        self.PcbLot_checkBox = QCheckBox(self.groupBox)
        self.PcbLot_checkBox.setObjectName(u"PcbLot_checkBox")
        self.PcbLot_checkBox.setGeometry(QRect(90, 30, 71, 20))
        self.Samplelabel = QLabel(Header)
        self.Samplelabel.setObjectName(u"Samplelabel")
        self.Samplelabel.setGeometry(QRect(230, 120, 901, 41))
        font1 = QFont()
        font1.setPointSize(9)
        font1.setBold(False)
        self.Samplelabel.setFont(font1)

        self.retranslateUi(Header)

        QMetaObject.connectSlotsByName(Header)
    # setupUi

    def retranslateUi(self, Header):
        Header.setWindowTitle(QCoreApplication.translate("Header", u"Dialog", None))
        self.groupBox.setTitle(QCoreApplication.translate("Header", u"Header Arrangement", None))
        self.SubLot_checkBox.setText(QCoreApplication.translate("Header", u"SubLot", None))
        self.TesterName_checkBox.setText(QCoreApplication.translate("Header", u"TesterName", None))
        self.MFGID_checkBox.setText(QCoreApplication.translate("Header", u"MFGID", None))
        self.ModuleID_checkBox.setText(QCoreApplication.translate("Header", u"ModuleID", None))
        self.AssemblyLotcheckBox.setText(QCoreApplication.translate("Header", u"AssemblyLot", None))
        self.Default_checkBox.setText(QCoreApplication.translate("Header", u"Default", None))
        self.headerUpdateButton.setText(QCoreApplication.translate("Header", u"Update", None))
        self.WaferID_checkBox.setText(QCoreApplication.translate("Header", u"WaferID", None))
        self.PcbLot_checkBox.setText(QCoreApplication.translate("Header", u"PcbLot", None))
        self.Samplelabel.setText(QCoreApplication.translate("Header", u"TextLabel", None))
    # retranslateUi

