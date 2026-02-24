from PySide6.QtCore import QMetaObject, Q_ARG, Slot, Qt


class ProgressBarHandler:
    """
    Centralized progress bar handling class for UI components.
    Manages progress bar updates, text updates, and styling.
    """
    
    def __init__(self, progress_bar=None, progress_text_widget=None, message_box2_widget=None):
        """
        Initialize ProgressBarHandler with UI widgets.
        
        Args:
            progress_bar: Progress bar widget (progressBar)
            progress_text_widget: Primary progress text widget (ProgressBar_textEdit)
            message_box2_widget: Secondary message box widget (MessageBox2text)
        """
        self.progress_bar = progress_bar
        self.progress_text_widget = progress_text_widget
        self.message_box2_widget = message_box2_widget
        
        # Style constants
        self.progress_bar_style = """
            QProgressBar {
                background-color: transparent;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #99c2ff; 
                border-radius: 2px;
            }
        """
        
        self.complete_style = """
        background-color: #c8ffc8;
        """
        
        self.progressing_style = """
        background-color: #ffd699;
        """
    
    @Slot(int)
    def update_progress(self, value):
        """
        Update progress bar value.
        
        Args:
            value: Progress value (0-100)
        """
        if self.progress_bar:
            QMetaObject.invokeMethod(
                self.progress_bar, 
                "setStyleSheet", 
                Qt.QueuedConnection,
                Q_ARG(str, self.progress_bar_style)
            )
            QMetaObject.invokeMethod(
                self.progress_bar, 
                "setValue", 
                Qt.QueuedConnection,
                Q_ARG(int, value)
            )
    
    @Slot(str)
    def update_progress_text(self, text):
        """
        Update primary progress text widget.
        
        Args:
            text: Text to display
        """
        if self.progress_text_widget:
            QMetaObject.invokeMethod(
                self.progress_text_widget, 
                "setText", 
                Qt.QueuedConnection,
                Q_ARG(str, text)
            )
    
    @Slot(str)
    def update_progress_text2(self, text):
        """
        Update secondary message box widget.
        
        Args:
            text: Text to display
        """
        if self.message_box2_widget:
            QMetaObject.invokeMethod(
                self.message_box2_widget, 
                "setText", 
                Qt.QueuedConnection,
                Q_ARG(str, text)
            )
    
    @Slot(str)
    def complete_progress_text(self, message):
        """
        Set progress text with completion style (green background).
        
        Args:
            message: Completion message to display
        """
        if self.progress_text_widget:
            QMetaObject.invokeMethod(
                self.progress_text_widget, 
                "setStyleSheet", 
                Qt.QueuedConnection,
                Q_ARG(str, self.complete_style)
            )
            self.update_progress_text(message)
    
    @Slot(str)
    def progressing_progress_text(self, message):
        """
        Set progress text with in-progress style (orange background).
        
        Args:
            message: Progress message to display
        """
        if self.progress_text_widget:
            QMetaObject.invokeMethod(
                self.progress_text_widget, 
                "setStyleSheet", 
                Qt.QueuedConnection,
                Q_ARG(str, self.progressing_style)
            )
            self.update_progress_text(message)
    
    @Slot(int)
    def update_text_edit_color(self, value):
        """
        Update primary text widget with gradient effect based on progress.
        Shows gradient during progress (0-99%), fully light green when complete (100%).
        
        Args:
            value: Progress value (0-100)
        """
        try:
            if self.progress_text_widget:
                # Ensure value is within valid range and format properly
                value = max(0, min(100, value))
                
                # If progress is 100%, show fully light green background instead of gradient
                if value >= 100:
                    complete_style = """
                    background-color: #c8ffc8;
                    """
                    QMetaObject.invokeMethod(
                        self.progress_text_widget, 
                        "setStyleSheet", 
                        Qt.QueuedConnection,
                        Q_ARG(str, complete_style)
                    )
                else:
                    # Use gradient for progress < 100%
                    gradient_value = value / 100.0
                    
                    # Format gradient value to avoid scientific notation or invalid values
                    gradient_str = f"{gradient_value:.6f}"
                    
                    gradient_style = f"""
                    background: qlineargradient(
                        spread:pad, x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(144, 238, 144, 255),
                        stop:{gradient_str} rgba(144, 238, 144, 255),
                        stop:{gradient_str} rgba(255, 255, 255, 255),
                        stop:1 rgba(255, 255, 255, 255)
                    );
                    """
                    QMetaObject.invokeMethod(
                        self.progress_text_widget, 
                        "setStyleSheet", 
                        Qt.QueuedConnection,
                        Q_ARG(str, gradient_style)
                    )
        except Exception as e:
            raise ValueError(f"{e}")
    
    @Slot(int)
    def update_text_edit_color2(self, value):
        """
        Update secondary text widget with gradient effect based on progress.
        
        Args:
            value: Progress value (0-100)
        """
        try:
            if self.message_box2_widget:
                # Ensure value is within valid range and format properly
                value = max(0, min(100, value))
                gradient_value = value / 100.0
                
                # Format gradient value to avoid scientific notation or invalid values
                gradient_str = f"{gradient_value:.6f}"
                
                gradient_style = f"""
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(144, 238, 144, 255),
                    stop:{gradient_str} rgba(144, 238, 144, 255),
                    stop:{gradient_str} rgba(255, 255, 255, 255),
                    stop:1 rgba(255, 255, 255, 255)
                );
                """
                QMetaObject.invokeMethod(
                    self.message_box2_widget, 
                    "setStyleSheet", 
                    Qt.QueuedConnection,
                    Q_ARG(str, gradient_style)
                )
        except Exception as e:
            raise ValueError(f"{e}")
    
    @Slot(str)
    def run_progress_bar_manual(self, message):
        """
        Complete progress bar (100%) with completion message.
        
        Args:
            message: Completion message
        """
        try:
            self.update_progress(100)
            self.complete_progress_text(f"\n{message}")
        except Exception as e:
            raise ValueError(f"{str(e)}")
    
    @Slot(str)
    def loading_progress_bar_manual(self, message):
        """
        Set progress bar to loading state (50%) with progress message.
        
        Args:
            message: Loading message
        """
        try:
            self.progressing_progress_text(f"\n{message}")
            self.update_progress(50)
        except Exception as e:
            raise ValueError(f"{str(e)}")
    
    @Slot(str)
    def loading_configuration_manual(self, message, num):
        """
        Update secondary message box with custom progress value.
        Shows gradient during progress, fully green when complete (100%).
        
        Args:
            message: Configuration message
            num: Progress value (0-100)
        """
        try:
            self.update_progress_text2(f"{message}")
            
            # If progress is 100%, show fully green background instead of gradient
            if num >= 100:
                complete_style = """
                background-color: #c8ffc8;
                """
                if self.message_box2_widget:
                    QMetaObject.invokeMethod(
                        self.message_box2_widget, 
                        "setStyleSheet", 
                        Qt.QueuedConnection,
                        Q_ARG(str, complete_style)
                    )
            else:
                # Use gradient for progress < 100%
                self.update_text_edit_color2(num)
        except Exception as e:
            raise ValueError(f"{str(e)}")
    
    def set_progress_bar(self, widget):
        """Set or update the progress bar widget."""
        self.progress_bar = widget
    
    def set_progress_text_widget(self, widget):
        """Set or update the primary progress text widget."""
        self.progress_text_widget = widget
    
    def set_message_box2_widget(self, widget):
        """Set or update the secondary message box widget."""
        self.message_box2_widget = widget

