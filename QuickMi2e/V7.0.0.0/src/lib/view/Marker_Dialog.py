import os
import json
import re
from PySide6.QtWidgets import QDialog, QStyledItemDelegate, QStyle, QListWidgetItem
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QPainter
from PySide6.QtCore import Qt
from ui.ui_build.ui_Marker import Ui_marker
from lib.helper.Feature import Feature
from lib.setting.IconManager import IconManager


class ColorItemDelegate(QStyledItemDelegate):
    """Custom delegate to handle colored background with white text and spacing."""
    
    def paint(self, painter, option, index):
        """Paint the item with colored background, white text, and white padding."""
        # Get the color from item data
        color_hex = index.data(Qt.UserRole)
        
        if color_hex:
            # Fill entire item background with white (for padding effect)
            painter.fillRect(option.rect, QColor("white"))
            
            # Create inner rectangle with padding (2px top/bottom for spacing)
            padding = 2
            inner_rect = option.rect.adjusted(0, padding, 0, -padding)
            
            # Fill inner rectangle with the color
            painter.fillRect(inner_rect, QColor(color_hex))
            
            # Draw text in white
            painter.save()
            painter.setPen(QColor("#FFFFFF"))  # White text
            
            # Set font (normal size)
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            
            # Draw text centered vertically with left padding
            text = index.data(Qt.DisplayRole)
            painter.drawText(inner_rect.adjusted(5, 0, 0, 0), 
                           Qt.AlignVCenter, text)
            painter.restore()
        else:
            # Fall back to default painting
            super().paint(painter, option, index)


class Marker_Dialog:
    """Dialog for marker configuration."""
    
    def __init__(self, error_handle):
        """
        Initialize Marker Dialog.
        
        Args:
            error_handle: Error handling callback function
        """
        self.markerDialog = QDialog()
        self.uiMarker = Ui_marker()
        self.uiMarker.setupUi(self.markerDialog)
        self.handle_error = error_handle
        self.feature = Feature()
        self.icon_manager = IconManager()
        
        # Set dialog title
        self.markerDialog.setWindowTitle("Marker Configuration")
        
        # Set button icons
        self._set_button_icons()
        
        # Initialize marker data storage
        self.marker_data = {}
        self.marker_json_path = os.path.join(os.getcwd(), "setting", "CFG", "Marker", "marker.json")
        self.markers_list = []  # Store all marker configurations
        self.plot_markers = False  # Flag to determine if markers should be plotted
        self.auto_name_counter = 1  # Counter for auto-generated names
        
        # Ensure marker directory exists
        os.makedirs(os.path.dirname(self.marker_json_path), exist_ok=True)
        
        # Populate comboboxes
        self._populate_marker_type()
        self._populate_marker_color()
        
        # Load existing markers from JSON
        self._load_markers_from_json()
        
        # Connect button signals
        self.uiMarker.MarkerAddButton.clicked.connect(self._add_marker)
        self.uiMarker.MarkerUndoButton.clicked.connect(self._undo_marker)
        self.uiMarker.MarkerClearButton.clicked.connect(self._clear_all_markers)
        self.uiMarker.MarkerPlotButton.clicked.connect(self._plot_markers)
        self.uiMarker.MarkerCancelButton.clicked.connect(self._cancel_markers)
        
        # Connect type change to update input validation
        self.uiMarker.MarkerType_comboBox.currentTextChanged.connect(self._on_type_changed)
        
        # Connect double-click on list widget to toggle all checkboxes
        self.uiMarker.AddLine_listWidget.doubleClicked.connect(self._toggle_all_checkboxes)
        self.all_checked = True  # Track the state for toggle
        
        # Apply scrollbar style to AddLine_listWidget
        self._apply_scrollbar_style()
    
    def _set_button_icons(self):
        """Set icons for marker dialog buttons."""
        try:
            # Add Button - Plus icon
            self.uiMarker.MarkerAddButton.setIcon(self.icon_manager.Plus)
            
            # Undo Button - Reverse icon
            self.uiMarker.MarkerUndoButton.setIcon(self.icon_manager.reverse)
            
            # Plot Button - Plotting icon
            self.uiMarker.MarkerPlotButton.setIcon(self.icon_manager.Plotting)
            
            # Clear All Button - Undo icon
            self.uiMarker.MarkerClearButton.setIcon(self.icon_manager.Undo)
        except Exception as e:
            # Silently fail if icons can't be loaded
            pass
    
    def _apply_scrollbar_style(self):
        """Apply custom scrollbar style to AddLine_listWidget."""
        scrollbar_style = """
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
        self.uiMarker.AddLine_listWidget.setStyleSheet(scrollbar_style)
    
    def _populate_marker_type(self):
        """Populate MarkerType_comboBox with marker types."""
        try:
            marker_types = ["Single", "Range", "OnePoint"]
            self.uiMarker.MarkerType_comboBox.addItems(marker_types)
        except Exception as e:
            self.handle_error(f"Error populating marker types: {str(e)}")
    
    def _populate_marker_color(self):
        """Populate MarkerColor_comboBox with colors from colorReference.json."""
        try:
            # Load color reference JSON
            color_json_path = os.path.join(os.getcwd(), "setting", "CFG", "DefineUnitColor", "colorReference.json")
            
            if not os.path.exists(color_json_path):
                self.handle_error(f"Color reference file not found: {color_json_path}")
                return
            
            with open(color_json_path, "r") as file:
                color_data = json.load(file)
            
            # Create a model for the combobox
            model = QStandardItemModel()
            
            # Add default black color as first option
            default_item = QStandardItem("Default (Black)")
            default_item.setData("#000000", Qt.UserRole)
            model.appendRow(default_item)
            
            # Add colors to combobox with colored backgrounds
            for key, color_hex in color_data.items():
                display_text = f"Color {key}"
                item = QStandardItem(display_text)
                
                # Store color hex as user data (delegate will use this for background)
                item.setData(color_hex, Qt.UserRole)
                
                model.appendRow(item)
            
            # Set the model to the combobox
            self.uiMarker.MarkerColor_comboBox.setModel(model)
            
            # Set custom delegate for magnified hover effect
            delegate = ColorItemDelegate(self.uiMarker.MarkerColor_comboBox)
            self.uiMarker.MarkerColor_comboBox.setItemDelegate(delegate)
            
            # Connect signal to update combobox button color
            self.uiMarker.MarkerColor_comboBox.currentIndexChanged.connect(self._update_combobox_color)
            
            # Set initial color
            self._update_combobox_color()
            
        except Exception as e:
            self.handle_error(f"Error populating marker colors: {str(e)}")
    
    def _update_combobox_color(self):
        """Update the combobox button to show the selected color."""
        try:
            current_index = self.uiMarker.MarkerColor_comboBox.currentIndex()
            if current_index >= 0:
                model = self.uiMarker.MarkerColor_comboBox.model()
                item = model.item(current_index)
                
                if item:
                    color_hex = item.data(Qt.UserRole)
                    
                    if color_hex:
                        # Update combobox button with colored background and white text
                        self.uiMarker.MarkerColor_comboBox.setStyleSheet(f"""
                            QComboBox {{
                                background-color: {color_hex};
                                color: white;
                            }}
                        """)
        except Exception as e:
            pass  # Silently fail to avoid disrupting UI
    
    def _on_type_changed(self, marker_type):
        """
        Handle marker type change to update placeholder text.
        
        Args:
            marker_type: Selected marker type ("Single", "Range", or "OnePoint")
        """
        if marker_type == "Single":
            self.uiMarker.frequencyEdit.setPlaceholderText("e.g., 2.5G (vertical line)")
            self.uiMarker.valueEdit.setPlaceholderText("e.g., -10 (horizontal line)")
        elif marker_type == "Range":
            self.uiMarker.frequencyEdit.setPlaceholderText("e.g., 1G-3G (2 vertical lines)")
            self.uiMarker.valueEdit.setPlaceholderText("e.g., 5-10 (2 horizontal lines)")
        elif marker_type == "OnePoint":
            self.uiMarker.frequencyEdit.setPlaceholderText("e.g., 2.5G (required)")
            self.uiMarker.valueEdit.setPlaceholderText("e.g., -10 (required)")
    
    def _parse_frequency(self, freq_str):
        """
        Parse frequency string using Feature.format_frequency logic.
        
        Args:
            freq_str: Frequency string (e.g., "2.5G", "100M")
            
        Returns:
            Float value in Hz, or None if invalid
        """
        try:
            return self.feature.IntergerValueConverter(freq_str.strip())
        except Exception as e:
            self.handle_error(f"Invalid frequency format: {freq_str}")
            return None
    
    def _validate_single_input(self, freq_str, value_str):
        """
        Validate single marker input.
        User can input either frequency OR value (or both).
        - Frequency: draws 1 vertical line
        - Value: draws 1 horizontal line
        
        Args:
            freq_str: Frequency string (can be empty)
            value_str: Value string (can be empty)
            
        Returns:
            Tuple of (frequency, value) or (None, None) if invalid
        """
        frequency = None
        value = None
        
        # Parse frequency if provided
        if freq_str:
            frequency = self._parse_frequency(freq_str)
            if frequency is None:
                return None, None
        
        # Parse value if provided
        if value_str:
            try:
                value = float(value_str.strip())
            except ValueError:
                self.handle_error(f"Invalid value format: {value_str}")
                return None, None
        
        # At least one must be provided
        if frequency is None and value is None:
            self.handle_error("Please enter at least frequency or value")
            return None, None
        
        return frequency, value
    
    def _validate_range_input(self, freq_str, value_str):
        """
        Validate range marker input.
        User can input either frequency range OR value range (or both).
        - Frequency range: draws 2 vertical lines
        - Value range: draws 2 horizontal lines
        
        Args:
            freq_str: Frequency range string (e.g., "1G-3G") (can be empty)
            value_str: Value range string (e.g., "-10--5" or "5-10") (can be empty)
            
        Returns:
            Tuple of ((freq_start, freq_end), (value_start, value_end)) or (None, None) if invalid
        """
        freq_range = None
        value_range = None
        
        # Parse frequency range if provided
        if freq_str:
            freq_parts = freq_str.split('-')
            if len(freq_parts) < 2:
                self.handle_error("Frequency range must be in format: START-END (e.g., 1G-3G)")
                return None, None
            
            # Handle cases like "300M-500M" (2 parts)
            if len(freq_parts) == 2:
                freq_start = self._parse_frequency(freq_parts[0])
                freq_end = self._parse_frequency(freq_parts[1])
            else:
                self.handle_error("Invalid frequency range format")
                return None, None
            
            if freq_start is None or freq_end is None:
                return None, None
            
            freq_range = (freq_start, freq_end)
        
        # Parse value range if provided
        if value_str:
            # Use regex to properly split range with negative numbers
            value_match = re.match(r'^(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)$', value_str.strip())
            if not value_match:
                self.handle_error("Value range must be in format: START-END (e.g., -10--5 or 5-10)")
                return None, None
            
            try:
                value_start = float(value_match.group(1))
                value_end = float(value_match.group(2))
                value_range = (value_start, value_end)
            except ValueError:
                self.handle_error(f"Invalid value range format: {value_str}")
                return None, None
        
        # At least one must be provided
        if freq_range is None and value_range is None:
            self.handle_error("Please enter at least frequency range or value range")
            return None, None
        
        return freq_range, value_range
    
    def _add_marker(self):
        """Add marker to list and save to JSON."""
        try:
            # Get input values
            marker_type = self.uiMarker.MarkerType_comboBox.currentText()
            name = self.uiMarker.NameEdit.text().strip()
            freq_str = self.uiMarker.frequencyEdit.text().strip()
            value_str = self.uiMarker.valueEdit.text().strip()
            
            # Get selected color
            current_index = self.uiMarker.MarkerColor_comboBox.currentIndex()
            model = self.uiMarker.MarkerColor_comboBox.model()
            item = model.item(current_index)
            color_hex = item.data(Qt.UserRole) if item else "#000000"
            color_name = item.text() if item else "Default (Black)"
            
            # Create marker configuration based on type (without Name yet)
            marker_config = {
                "Type": marker_type,
                "Color": color_hex,
                "ColorName": color_name
            }
            
            if marker_type == "Single":
                frequency, value = self._validate_single_input(freq_str, value_str)
                if frequency is None and value is None:
                    return
                
                # Store frequency if provided (for vertical line)
                if frequency is not None:
                    marker_config["Frequency"] = frequency
                    marker_config["FrequencyDisplay"] = self.feature.format_frequency(frequency)
                    marker_config["LineType"] = "Vertical"
                
                # Store value if provided (for horizontal line)
                if value is not None:
                    marker_config["Value"] = value
                    if "LineType" in marker_config:
                        marker_config["LineType"] = "Both"  # Both vertical and horizontal
                    else:
                        marker_config["LineType"] = "Horizontal"
                
                # Auto-generate name if empty
                auto_generated = False
                if not name:
                    freq_part = f"freq[{marker_config.get('FrequencyDisplay', '')}]" if frequency is not None else ""
                    value_part = f"value[{marker_config.get('Value', '')}]" if value is not None else ""
                    separator = "|" if freq_part and value_part else ""
                    name = f"line{self.auto_name_counter}"
                    self.auto_name_counter += 1
                    auto_generated = True
                
                marker_config["Name"] = name
                
                # Display format for list
                freq_display_part = f"freq[{marker_config.get('FrequencyDisplay', '')}]" if frequency is not None else ""
                value_display_part = f"value[{marker_config.get('Value', '')}]" if value is not None else ""
                info_separator = "|" if freq_display_part and value_display_part else ""
                
                # For auto-generated names, format: line1 - freq[...]|value[...] - color
                # For custom names, format: CustomName - freq[...]|value[...] - color
                if freq_display_part or value_display_part:
                    display_text = f"{name} - {freq_display_part}{info_separator}{value_display_part} - {color_name}"
                else:
                    display_text = f"{name} - {color_name}"
            
            elif marker_type == "OnePoint":
                # OnePoint requires both frequency and value
                if not freq_str or not value_str:
                    self.handle_error("OnePoint marker requires both frequency and value")
                    return
                
                frequency = self._parse_frequency(freq_str)
                if frequency is None:
                    return
                
                try:
                    value = float(value_str.strip())
                except ValueError:
                    self.handle_error(f"Invalid value format: {value_str}")
                    return
                
                marker_config["Frequency"] = frequency
                marker_config["FrequencyDisplay"] = self.feature.format_frequency(frequency)
                marker_config["Value"] = value
                marker_config["LineType"] = "Point"
                
                # Auto-generate name if empty
                if not name:
                    name = f"line{self.auto_name_counter}"
                    self.auto_name_counter += 1
                
                marker_config["Name"] = name
                
                # Display format for list (always show freq/value info)
                freq_display_text = marker_config["FrequencyDisplay"]
                value_display_text = marker_config["Value"]
                display_text = f"{name} - freq[{freq_display_text}]|value[{value_display_text}] - {color_name}"
                
            elif marker_type == "Range":
                freq_range, value_range = self._validate_range_input(freq_str, value_str)
                if freq_range is None and value_range is None:
                    return
                
                # Store frequency range if provided (for 2 vertical lines)
                if freq_range is not None:
                    marker_config["FrequencyStart"] = freq_range[0]
                    marker_config["FrequencyEnd"] = freq_range[1]
                    marker_config["FrequencyStartDisplay"] = self.feature.format_frequency(freq_range[0])
                    marker_config["FrequencyEndDisplay"] = self.feature.format_frequency(freq_range[1])
                    marker_config["LineType"] = "Vertical"
                
                # Store value range if provided (for 2 horizontal lines)
                if value_range is not None:
                    marker_config["ValueStart"] = value_range[0]
                    marker_config["ValueEnd"] = value_range[1]
                    if "LineType" in marker_config:
                        marker_config["LineType"] = "Both"  # Both vertical and horizontal
                    else:
                        marker_config["LineType"] = "Horizontal"
                
                # Auto-generate name if empty
                if not name:
                    name = f"line{self.auto_name_counter}"
                    self.auto_name_counter += 1
                
                marker_config["Name"] = name
                
                # Display format for list (always show freq/value info)
                freq_display_part = ""
                if freq_range is not None:
                    freq_start_display = marker_config["FrequencyStartDisplay"]
                    freq_end_display = marker_config["FrequencyEndDisplay"]
                    freq_display_part = f"freq[{freq_start_display}-{freq_end_display}]"
                
                value_display_part = ""
                if value_range is not None:
                    value_start = marker_config["ValueStart"]
                    value_end = marker_config["ValueEnd"]
                    value_display_part = f"value[{value_start}-{value_end}]"
                
                info_separator = "|" if freq_display_part and value_display_part else ""
                
                if freq_display_part or value_display_part:
                    display_text = f"{name} - {freq_display_part}{info_separator}{value_display_part} - {color_name}"
                else:
                    display_text = f"{name} - {color_name}"
            
            # Add to markers list
            self.markers_list.append(marker_config)
            
            # Add to list widget with color and make it checkable
            list_item = QListWidgetItem(display_text)
            list_item.setForeground(QColor(color_hex))
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Checked)  # Default to checked
            self.uiMarker.AddLine_listWidget.addItem(list_item)
            
            # Save to JSON
            self._save_markers_to_json()
            
            # Clear input fields
            self.uiMarker.NameEdit.clear()
            self.uiMarker.frequencyEdit.clear()
            self.uiMarker.valueEdit.clear()
            
        except Exception as e:
            self.handle_error(f"Error adding marker: {str(e)}")
    
    def _undo_marker(self):
        """Remove the latest marker from list."""
        try:
            if len(self.markers_list) > 0:
                # Remove last marker from list
                self.markers_list.pop()
                
                # Remove last item from list widget
                count = self.uiMarker.AddLine_listWidget.count()
                if count > 0:
                    self.uiMarker.AddLine_listWidget.takeItem(count - 1)
                
                # Save updated list to JSON
                self._save_markers_to_json()
            else:
                self.handle_error("No markers to undo")
        except Exception as e:
            self.handle_error(f"Error undoing marker: {str(e)}")
    
    def _clear_all_markers(self):
        """Clear all markers from list and JSON."""
        try:
            # Clear markers list
            self.markers_list.clear()
            
            # Clear list widget
            self.uiMarker.AddLine_listWidget.clear()
            
            # Save empty list to JSON
            self._save_markers_to_json()
            
        except Exception as e:
            self.handle_error(f"Error clearing markers: {str(e)}")
    
    def _plot_markers(self):
        """Set flag to plot markers and close dialog."""
        try:
            self.plot_markers = True
            self.markerDialog.accept()
        except Exception as e:
            self.handle_error(f"Error plotting markers: {str(e)}")
    
    def _cancel_markers(self):
        """Cancel marker plotting and close dialog."""
        try:
            self.plot_markers = False
            self.markerDialog.reject()
        except Exception as e:
            self.handle_error(f"Error canceling markers: {str(e)}")
    
    def _save_markers_to_json(self):
        """Save markers list to JSON file."""
        try:
            with open(self.marker_json_path, 'w') as f:
                json.dump(self.markers_list, f, indent=2)
        except Exception as e:
            self.handle_error(f"Error saving markers to JSON: {str(e)}")
    
    def _load_markers_from_json(self):
        """Load markers from JSON file and populate list widget."""
        try:
            if os.path.exists(self.marker_json_path):
                with open(self.marker_json_path, 'r') as f:
                    self.markers_list = json.load(f)
                
                # Populate list widget with full display format
                for marker in self.markers_list:
                    marker_type = marker.get('Type', 'Single')
                    name = marker['Name']
                    color_name = marker.get('ColorName', 'Default (Black)')
                    
                    # Reconstruct display text based on marker type
                    if marker_type == 'Single':
                        freq_display_part = ""
                        value_display_part = ""
                        
                        if 'FrequencyDisplay' in marker:
                            freq_display_part = f"freq[{marker['FrequencyDisplay']}]"
                        
                        if 'Value' in marker:
                            value_display_part = f"value[{marker['Value']}]"
                        
                        info_separator = "|" if freq_display_part and value_display_part else ""
                        
                        if freq_display_part or value_display_part:
                            display_text = f"{name} - {freq_display_part}{info_separator}{value_display_part} - {color_name}"
                        else:
                            display_text = f"{name} - {color_name}"
                    
                    elif marker_type == 'OnePoint':
                        freq_display_text = marker.get('FrequencyDisplay', '')
                        value_display_text = marker.get('Value', '')
                        display_text = f"{name} - freq[{freq_display_text}]|value[{value_display_text}] - {color_name}"
                    
                    elif marker_type == 'Range':
                        freq_display_part = ""
                        value_display_part = ""
                        
                        if 'FrequencyStartDisplay' in marker and 'FrequencyEndDisplay' in marker:
                            freq_start_display = marker['FrequencyStartDisplay']
                            freq_end_display = marker['FrequencyEndDisplay']
                            freq_display_part = f"freq[{freq_start_display}-{freq_end_display}]"
                        
                        if 'ValueStart' in marker and 'ValueEnd' in marker:
                            value_start = marker['ValueStart']
                            value_end = marker['ValueEnd']
                            value_display_part = f"value[{value_start}-{value_end}]"
                        
                        info_separator = "|" if freq_display_part and value_display_part else ""
                        
                        if freq_display_part or value_display_part:
                            display_text = f"{name} - {freq_display_part}{info_separator}{value_display_part} - {color_name}"
                        else:
                            display_text = f"{name} - {color_name}"
                    else:
                        # Fallback for unknown types
                        display_text = f"{name} - {color_name}"
                    
                    list_item = QListWidgetItem(display_text)
                    list_item.setForeground(QColor(marker['Color']))
                    list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
                    list_item.setCheckState(Qt.Checked)  # Default to checked
                    self.uiMarker.AddLine_listWidget.addItem(list_item)
            else:
                # Create empty JSON file
                self.markers_list = []
                self._save_markers_to_json()
        except Exception as e:
            self.handle_error(f"Error loading markers from JSON: {str(e)}")
            self.markers_list = []
    
    def marker_dialog(self):
        """
        Open the marker dialog.
        
        Returns:
            bool: True if user clicked Plot, False if canceled
        """
        try:
            result = self.markerDialog.exec()
            return self.plot_markers and result == QDialog.Accepted
        except Exception as e:
            self.handle_error(f"{str(e)}")
            return False
    
    def get_markers(self):
        """
        Get list of all markers for plotting.
        
        Returns:
            List of marker configurations
        """
        return self.markers_list
    
    def should_plot_markers(self):
        """
        Check if markers should be plotted.
        
        Returns:
            bool: True if markers should be plotted
        """
        return self.plot_markers and len(self.markers_list) > 0
    
    def get_selected_markers(self):
        """
        Get list of checked marker names from AddLine_listWidget.
        Only markers that are checked will be returned.
        
        Returns:
            List of checked marker display names
        """
        selected_markers = []
        try:
            for i in range(self.uiMarker.AddLine_listWidget.count()):
                item = self.uiMarker.AddLine_listWidget.item(i)
                # Only include items that are checked
                if item and item.checkState() == Qt.Checked:
                    selected_markers.append(item.text())
            return selected_markers
        except Exception as e:
            self.handle_error(f"Error getting selected markers: {str(e)}")
            return []
    
    def _toggle_all_checkboxes(self):
        """
        Toggle all checkboxes in AddLine_listWidget.
        Double-click once: Check all
        Double-click again: Uncheck all
        """
        try:
            # Toggle the state
            self.all_checked = not self.all_checked
            
            # Apply to all items
            for i in range(self.uiMarker.AddLine_listWidget.count()):
                item = self.uiMarker.AddLine_listWidget.item(i)
                if item:
                    if self.all_checked:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
        except Exception as e:
            self.handle_error(f"Error toggling checkboxes: {str(e)}")



