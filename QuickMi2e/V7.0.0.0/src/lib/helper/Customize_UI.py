"""Custom UI styles and utilities."""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QMovie


class Style:
    """Provides custom styling and UI utilities."""

    def __init__(self):
        """Initialize Style."""
        pass

    @property
    def MainFrameStyle(self):
        """
        Get the main frame stylesheet.

        Returns:
            CSS stylesheet string for the main application frame
        """
        return """

            /* --- GLOBAL SETTINGS --- */
            QWidget {
                background-color: white;
            }
            QFrame {
                background-color: white;
            }
            QLabel {
                color: black;
            }

            /* --- BUTTONS --- */
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e6f5ff;
            }

            QToolButton {
                background-color: white;
                color: black;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 1px 1px;
            }

            /* --- CHECKBOXES --- */
            QCheckBox {
                color: black;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border-radius: 4px;
                border: 1px solid #a9a9a9;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                background-color: #e6f5ff;
            }
            QCheckBox::indicator:checked {
                background-color: #cce6ff;
                border: 1px solid #b3d9ff;
                image: url(":/newPrefix/images/blackTicker.png");
            }

            /* --- COMBOBOXES --- */
            QComboBox {
                background-color: #ffffff;
                color: black;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 5px;
            }
            QComboBox:hover {
                background-color: #e6f5ff;
            }
            QComboBox QAbstractItemView {
                color: black;
                background-color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border: none;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 3px solid #000000;
                margin-right: 5px;
            }
            QComboBox::down-arrow:hover {
                border-top: 6px solid #004578;
            }

            /* --- TEXT INPUTS --- */
            QLineEdit {
                background-color: white;
                color: #333333;
                border: 1px solid #dcdcdc;
                border-radius: 1px;
                padding: 1px;
            }
            QTextEdit {
                background-color: white;
                color: #333333;
                border: 1px solid #dcdcdc;
                border-radius: 1px;
                padding: 5px;
            }

            /* --- LIST WIDGETS --- */
            QListWidget {
                background-color: white;
                color: #333333;
                border: 1px solid #dcdcdc;
                border-radius: 1px;
                padding: 1px;
            }
            QListWidget::item {
                margin-bottom: 4px;
            }
            QListWidget::item:hover {
                background-color: #e5e5e5;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #e5e5e5;
                color: black;
            }
            QListWidget::indicator {
                width: 15px;
                height: 15px;
                border-radius: 4px;
                border: 1px solid #a9a9a9;
                background-color: white;
            }
            QListWidget::indicator:hover {
                background-color: #cce6ff;
            }
            QListWidget::indicator:checked {
                background-color: #cce6ff;
                border: 2px solid #b3d9ff;
                image: url(":/newPrefix/images/blackTicker.png");
            }

            /* --- TABS --- */
            QTabWidget::pane {
                border: 1px solid #dcdcdc;
            }
            QTabBar::tab {
                background: white;
                color: black;
                border: 1px solid #dcdcdc;
                padding: 5px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #e6f5ff;
                font-weight: bold;
            }

            /* --- GROUP BOXES --- */
            QGroupBox {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                font-weight: bold;
                font-family: 'Segoe UI';
                font-size: 104px;
                color: black;
            }

            /* --- PROGRESS BARS --- */
            QProgressBar {
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                text-align: center;
                color: black;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: black;
                width: 1px;
                margin: 0px;
            }

            /* --- SCROLL BARS --- */
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """

    def _setup_file_link(self, label_widget, file_path, display_text):
        """
        Configure a QLabel to act as a clickable file link.

        Args:
            label_widget: QLabel widget to configure
            file_path: Path to the file
            display_text: Text to display for the link
        """
        if not file_path:
            return  # Handle cases where path might be empty

        # Standard Label Settings
        label_widget.setTextFormat(Qt.RichText)
        label_widget.setTextInteractionFlags(Qt.TextBrowserInteraction)
        label_widget.setOpenExternalLinks(True)

        # Format the URL (Handle backslashes for Windows paths)
        clean_url = f"file:///{file_path.replace('\\', '/')}"

        # Set the HTML Text
        html_content = (
            f"<a href='{clean_url}' target='_blank' "
            f"style='color:#0000EE;'>{display_text}</a>"
        )
        label_widget.setText(html_content)

    def apply_color_combobox_style(self, combobox, current_color):
        """
        Apply custom styling to a color combobox.
        
        Args:
            combobox: QComboBox widget to style
            current_color: Hex color code for the background
        """
        if current_color:
            combobox.setStyleSheet(f"""
                QComboBox {{
                    background-color: {current_color};
                    color: black;
                    font-weight: bold;
                    padding: 2px;
                    border: 1px solid #ccc;
                    text-align: left;
                }}
                QComboBox::drop-down {{
                    border: none;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid black;
                    margin-right: 5px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: white;
                    border: 1px solid #ccc;
                    selection-background-color: #e0e0e0;
                }}
                QComboBox QAbstractItemView::item {{
                    padding: 0.5px;
                    min-height: 20px;
                    border: none;
                }}
            """)

    def deployGif(self, movie_label):
        """
        Deploy animated GIF to a QLabel widget.

        Args:
            movie_label: QLabel widget to display the GIF
        """
        gif_path = os.path.join(os.getcwd(), 'configSetting', 'mice.gif')
        movie = QMovie(gif_path)
        movie_label.setFixedSize(160, 140)
        movie.setScaledSize(movie_label.size())
        movie_label.setMovie(movie)
        movie.start()