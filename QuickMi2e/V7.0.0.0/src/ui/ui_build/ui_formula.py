# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'formula.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QTextEdit,
    QToolButton, QWidget)

class Ui_Formula(object):
    def setupUi(self, Formula):
        if not Formula.objectName():
            Formula.setObjectName(u"Formula")
        Formula.resize(1051, 743)
        self.FormulaEditor_GroupBox = QGroupBox(Formula)
        self.FormulaEditor_GroupBox.setObjectName(u"FormulaEditor_GroupBox")
        self.FormulaEditor_GroupBox.setGeometry(QRect(20, 10, 571, 721))
        font = QFont()
        font.setBold(True)
        self.FormulaEditor_GroupBox.setFont(font)
        self.FormulaEditortextEdit = QTextEdit(self.FormulaEditor_GroupBox)
        self.FormulaEditortextEdit.setObjectName(u"FormulaEditortextEdit")
        self.FormulaEditortextEdit.setGeometry(QRect(10, 60, 551, 651))
        self.FormulaAddButton = QPushButton(self.FormulaEditor_GroupBox)
        self.FormulaAddButton.setObjectName(u"FormulaAddButton")
        self.FormulaAddButton.setGeometry(QRect(330, 20, 131, 31))
        self.FormulaCleanButton = QPushButton(self.FormulaEditor_GroupBox)
        self.FormulaCleanButton.setObjectName(u"FormulaCleanButton")
        self.FormulaCleanButton.setGeometry(QRect(470, 20, 91, 31))
        self.FormulaAddEdit = QLineEdit(self.FormulaEditor_GroupBox)
        self.FormulaAddEdit.setObjectName(u"FormulaAddEdit")
        self.FormulaAddEdit.setGeometry(QRect(140, 26, 181, 21))
        self.FormulaNewNamelabel = QLabel(self.FormulaEditor_GroupBox)
        self.FormulaNewNamelabel.setObjectName(u"FormulaNewNamelabel")
        self.FormulaNewNamelabel.setGeometry(QRect(18, 28, 121, 16))
        self.FormulaNewNamelabel.setFont(font)
        self.FormulaController_groupBox = QGroupBox(Formula)
        self.FormulaController_groupBox.setObjectName(u"FormulaController_groupBox")
        self.FormulaController_groupBox.setGeometry(QRect(610, 670, 421, 61))
        self.FormulaController_groupBox.setFont(font)
        self.FormulaSaveButton = QPushButton(self.FormulaController_groupBox)
        self.FormulaSaveButton.setObjectName(u"FormulaSaveButton")
        self.FormulaSaveButton.setGeometry(QRect(180, 20, 131, 31))
        self.FormulaCancelButton = QPushButton(self.FormulaController_groupBox)
        self.FormulaCancelButton.setObjectName(u"FormulaCancelButton")
        self.FormulaCancelButton.setGeometry(QRect(320, 20, 91, 31))
        self.FormulaShowButton = QPushButton(self.FormulaController_groupBox)
        self.FormulaShowButton.setObjectName(u"FormulaShowButton")
        self.FormulaShowButton.setGeometry(QRect(10, 20, 161, 31))
        self.Formula_List_groupBox = QGroupBox(Formula)
        self.Formula_List_groupBox.setObjectName(u"Formula_List_groupBox")
        self.Formula_List_groupBox.setGeometry(QRect(610, 10, 421, 311))
        self.Formula_List_groupBox.setFont(font)
        self.FormulalistEdit = QTextEdit(self.Formula_List_groupBox)
        self.FormulalistEdit.setObjectName(u"FormulalistEdit")
        self.FormulalistEdit.setGeometry(QRect(10, 20, 401, 281))
        self.FormulaHeader_groupBox = QGroupBox(Formula)
        self.FormulaHeader_groupBox.setObjectName(u"FormulaHeader_groupBox")
        self.FormulaHeader_groupBox.setGeometry(QRect(610, 330, 421, 331))
        self.FormulaHeader_groupBox.setFont(font)
        self.FormulaLoadButton = QPushButton(self.FormulaHeader_groupBox)
        self.FormulaLoadButton.setObjectName(u"FormulaLoadButton")
        self.FormulaLoadButton.setGeometry(QRect(340, 20, 71, 31))
        self.label = QLabel(self.FormulaHeader_groupBox)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(6, 25, 61, 16))
        font1 = QFont()
        font1.setBold(False)
        self.label.setFont(font1)
        self.FormulaTrackPathEdit = QLineEdit(self.FormulaHeader_groupBox)
        self.FormulaTrackPathEdit.setObjectName(u"FormulaTrackPathEdit")
        self.FormulaTrackPathEdit.setGeometry(QRect(70, 23, 231, 21))
        self.FormulaTracktoolButton = QToolButton(self.FormulaHeader_groupBox)
        self.FormulaTracktoolButton.setObjectName(u"FormulaTracktoolButton")
        self.FormulaTracktoolButton.setGeometry(QRect(310, 30, 21, 22))
        self.FormulaHeadertextEdit = QTextEdit(self.FormulaHeader_groupBox)
        self.FormulaHeadertextEdit.setObjectName(u"FormulaHeadertextEdit")
        self.FormulaHeadertextEdit.setGeometry(QRect(10, 60, 401, 261))
        font2 = QFont()
        font2.setBold(False)
        font2.setStrikeOut(False)
        self.FormulaHeadertextEdit.setFont(font2)

        self.retranslateUi(Formula)

        QMetaObject.connectSlotsByName(Formula)
    # setupUi

    def retranslateUi(self, Formula):
        Formula.setWindowTitle(QCoreApplication.translate("Formula", u"Dialog", None))
        self.FormulaEditor_GroupBox.setTitle(QCoreApplication.translate("Formula", u"Formula Editor", None))
        self.FormulaAddButton.setText(QCoreApplication.translate("Formula", u"Add", None))
        self.FormulaCleanButton.setText(QCoreApplication.translate("Formula", u"Clean All", None))
        self.FormulaNewNamelabel.setText(QCoreApplication.translate("Formula", u"Formula New Name:", None))
        self.FormulaController_groupBox.setTitle(QCoreApplication.translate("Formula", u"Controller", None))
        self.FormulaSaveButton.setText(QCoreApplication.translate("Formula", u"Save", None))
        self.FormulaCancelButton.setText(QCoreApplication.translate("Formula", u"Cancel", None))
        self.FormulaShowButton.setText(QCoreApplication.translate("Formula", u"Show", None))
        self.Formula_List_groupBox.setTitle(QCoreApplication.translate("Formula", u"List of Formula", None))
        self.FormulaHeader_groupBox.setTitle(QCoreApplication.translate("Formula", u"Check Header Can Use", None))
        self.FormulaLoadButton.setText(QCoreApplication.translate("Formula", u"Load", None))
        self.label.setText(QCoreApplication.translate("Formula", u"TrackPath:", None))
        self.FormulaTracktoolButton.setText(QCoreApplication.translate("Formula", u"...", None))
    # retranslateUi

