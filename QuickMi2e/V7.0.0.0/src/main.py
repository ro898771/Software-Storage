'''
Author: Ong Roey Yee
Description: For Quick Trace use case, it still a prototype. Don give high expectation on this
'''
import sys
from PySide6 import QtWidgets
from lib.controller.Main_Widget import Main_Widget
from lib.helper.Customize_UI import Style
# -----------------------------------------------------------------------------
# MAIN APPLICATION EXECUTION
# -----------------------------------------------------------------------------

style = Style()

app = QtWidgets.QApplication(sys.argv)

app.setStyle("Window")

app.setStyleSheet(style.MainFrameStyle)

window = Main_Widget()

window.show()

app.exec()