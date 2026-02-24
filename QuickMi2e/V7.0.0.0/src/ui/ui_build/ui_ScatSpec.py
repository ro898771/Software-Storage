# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ScatSpec.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QWidget)

class Ui_Scat(object):
    def setupUi(self, Scat):
        if not Scat.objectName():
            Scat.setObjectName(u"Scat")
        Scat.resize(440, 273)
        self.groupBox = QGroupBox(Scat)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 421, 261))
        font = QFont()
        font.setBold(True)
        self.groupBox.setFont(font)
        self.ScatlistWidget = QListWidget(self.groupBox)
        self.ScatlistWidget.setObjectName(u"ScatlistWidget")
        self.ScatlistWidget.setGeometry(QRect(10, 20, 401, 201))
        self.ScatConfirmedButton = QPushButton(self.groupBox)
        self.ScatConfirmedButton.setObjectName(u"ScatConfirmedButton")
        self.ScatConfirmedButton.setGeometry(QRect(10, 224, 401, 31))

        self.retranslateUi(Scat)

        QMetaObject.connectSlotsByName(Scat)
    # setupUi

    def retranslateUi(self, Scat):
        Scat.setWindowTitle(QCoreApplication.translate("Scat", u"Form", None))
        self.groupBox.setTitle(QCoreApplication.translate("Scat", u"Scat Spec Version", None))
        self.ScatConfirmedButton.setText(QCoreApplication.translate("Scat", u"Confirmed", None))
    # retranslateUi

