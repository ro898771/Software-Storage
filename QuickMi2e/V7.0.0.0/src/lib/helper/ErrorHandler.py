from PySide6.QtCore import QMetaObject, Q_ARG


class ErrorHandler:
    """
    Centralized error handling class for UI components.
    Handles error display and styling for different UI elements.
    """
    
    def __init__(self, progress_text_widget=None, message_box2_widget=None, dialog_message_box=None):
        """
        Initialize ErrorHandler with UI widgets.
        
        Args:
            progress_text_widget: Primary progress text widget (ProgressBar_textEdit)
            message_box2_widget: Secondary message box widget (MessageBox2text)
            dialog_message_box: Dialog message box widget (for dialogs)
        """
        self.progress_text_widget = progress_text_widget
        self.message_box2_widget = message_box2_widget
        self.dialog_message_box = dialog_message_box
        
        # Error style constant
        self.error_style = """
        background-color: #ff3d5a;
        """
    
    def handle_error(self, error_message):
        """
        Handle error for primary progress text widget.
        
        Args:
            error_message: Error message to display
        """
        if self.progress_text_widget:
            QMetaObject.invokeMethod(
                self.progress_text_widget, 
                "setStyleSheet", 
                Q_ARG(str, self.error_style)
            )
            QMetaObject.invokeMethod(
                self.progress_text_widget, 
                "setText", 
                Q_ARG(str, error_message)
            )
        print(f"Error: {error_message}")
    
    def handle_error2(self, error_message):
        """
        Handle error for secondary message box widget.
        
        Args:
            error_message: Error message to display
        """
        if self.message_box2_widget:
            QMetaObject.invokeMethod(
                self.message_box2_widget, 
                "setStyleSheet", 
                Q_ARG(str, self.error_style)
            )
            QMetaObject.invokeMethod(
                self.message_box2_widget, 
                "setText", 
                Q_ARG(str, error_message)
            )
        print(f"Error: {error_message}")
    
    def dialog_handle_error(self, error_message):
        """
        Handle error for dialog message box widget.
        
        Args:
            error_message: Error message to display
        """
        if self.dialog_message_box:
            QMetaObject.invokeMethod(
                self.dialog_message_box, 
                "setStyleSheet", 
                Q_ARG(str, self.error_style)
            )
        print(f"Error: {error_message}")
    
    def set_progress_text_widget(self, widget):
        """Set or update the primary progress text widget."""
        self.progress_text_widget = widget
    
    def set_message_box2_widget(self, widget):
        """Set or update the secondary message box widget."""
        self.message_box2_widget = widget
    
    def set_dialog_message_box(self, widget):
        """Set or update the dialog message box widget."""
        self.dialog_message_box = widget



