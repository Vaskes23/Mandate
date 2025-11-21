"""
Main application window with glass-morphic effect.

This module provides a demo window that showcases the glass-morphic (translucent blur)
effect on macOS. Users can interactively adjust the material type and transparency.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSlider, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.core.window import GlassMorphicWindow
from app.config import GlassConfig, MaterialType, DEFAULT_WINDOW_SIZE, DEFAULT_WINDOW_TITLE


class MainWindow(GlassMorphicWindow):
    """
    Main application window demonstrating glass-morphic effect.

    This window extends GlassMorphicWindow to provide a demo interface with:
    - Title and description text
    - Interactive controls for changing material type and transparency
    - Close button

    All UI elements have semi-transparent backgrounds for visibility against the glass effect.
    """

    def __init__(self, config: GlassConfig = None):
        """
        Initialize the main window.

        Args:
            config: Optional GlassConfig for customizing the glass effect.
                   If None, uses DEFAULT_CONFIG from app.config.
        """
        super().__init__(config)
        self.setWindowTitle(DEFAULT_WINDOW_TITLE)
        self.resize(*DEFAULT_WINDOW_SIZE)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface layout and widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        self._add_header(layout)
        self._add_content(layout)
        self._add_controls(layout)
        layout.addStretch()
        self._add_footer(layout)

    def _add_header(self, layout):
        """
        Add title label to the layout.

        Args:
            layout: QVBoxLayout to add the header to
        """
        title_label = QLabel("Glass-Morphic Demo")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 32, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 0.3);
                padding: 15px;
                border-radius: 10px;
            }
        """)
        layout.addWidget(title_label)

    def _add_content(self, layout):
        """
        Add description text to the layout.

        Args:
            layout: QVBoxLayout to add the content to
        """
        content_label = QLabel(
            "This window demonstrates a glass-morphic effect\n"
            "using NSVisualEffectView on macOS.\n\n"
            "Try moving this window over different backgrounds\n"
            "to see the blur and transparency in action!"
        )
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setWordWrap(True)
        content_label.setFont(QFont("Arial", 14))
        content_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 0.25);
                padding: 20px;
                border-radius: 10px;
            }
        """)
        layout.addWidget(content_label)

    def _add_controls(self, layout):
        """
        Add interactive controls (material selector and transparency slider) to the layout.

        The controls are contained in a semi-transparent panel for visibility.

        Args:
            layout: QVBoxLayout to add the controls to
        """
        # Container widget with dark background for visibility
        controls_widget = QWidget()
        controls_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.4);
                border-radius: 10px;
            }
        """)

        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(15)

        # Material type selector
        material_layout = QHBoxLayout()
        material_label = QLabel("Material:")
        material_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")

        self.material_combo = QComboBox()
        self.material_combo.addItems(["sidebar", "titlebar", "menu", "popover", "hudWindow", "contentBackground"])
        self.material_combo.setCurrentText(self.glass_config.material.value)
        self.material_combo.currentTextChanged.connect(self._on_material_changed)
        self.material_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(30, 30, 30, 0.98);
                color: white;
                selection-background-color: rgba(100, 100, 100, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """)

        material_layout.addWidget(material_label)
        material_layout.addWidget(self.material_combo)
        material_layout.addStretch()
        controls_layout.addLayout(material_layout)

        # Transparency slider
        alpha_layout = QVBoxLayout()
        alpha_label = QLabel("Transparency:")
        alpha_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")

        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setMinimum(0)  # 0% = fully transparent
        self.alpha_slider.setMaximum(100)  # 100% = fully opaque
        self.alpha_slider.setValue(int(self.glass_config.window_alpha * 100))
        # Use sliderReleased instead of valueChanged to reduce update frequency
        self.alpha_slider.sliderReleased.connect(self._on_alpha_changed)
        self.alpha_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.2);
                height: 10px;
                border-radius: 5px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QSlider::handle:horizontal {
                background: white;
                border: 2px solid rgba(255, 255, 255, 0.8);
                width: 20px;
                height: 20px;
                margin: -7px 0;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid white;
            }
        """)

        alpha_layout.addWidget(alpha_label)
        alpha_layout.addWidget(self.alpha_slider)
        controls_layout.addLayout(alpha_layout)

        layout.addWidget(controls_widget)

    def _add_footer(self, layout):
        """
        Add fullscreen and close buttons to the layout.

        Args:
            layout: QVBoxLayout to add the footer to
        """
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        # Button style (shared)
        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """

        # Fullscreen button
        self.fullscreen_button = QPushButton("Fullscreen")
        self.fullscreen_button.setFixedSize(120, 40)
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        self.fullscreen_button.setStyleSheet(button_style)
        footer_layout.addWidget(self.fullscreen_button)

        footer_layout.addSpacing(10)

        # Close button
        close_button = QPushButton("Close")
        close_button.setFixedSize(100, 40)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet(button_style)
        footer_layout.addWidget(close_button)

        footer_layout.addStretch()
        layout.addLayout(footer_layout)

    def _on_material_changed(self, material_name: str):
        """
        Handle material type change from the dropdown.

        Creates a new GlassConfig with the selected material and updates the window.

        Args:
            material_name: Name of the material type (e.g., "sidebar", "menu")
        """
        try:
            material = MaterialType(material_name)
            new_config = GlassConfig(
                material=material,
                blending_mode=self.glass_config.blending_mode,
                state=self.glass_config.state,
                appearance=self.glass_config.appearance,
                window_alpha=self.glass_config.window_alpha,
                emphasized=self.glass_config.emphasized,
            )
            self.update_glass_config(new_config)
        except ValueError:
            # Invalid material name, ignore
            pass

    def _on_alpha_changed(self):
        """
        Handle transparency slider release.

        Creates a new GlassConfig with the updated alpha value and updates the window.
        Uses sliderReleased signal to avoid updating on every pixel movement.
        """
        alpha = self.alpha_slider.value() / 100.0
        new_config = GlassConfig(
            material=self.glass_config.material,
            blending_mode=self.glass_config.blending_mode,
            state=self.glass_config.state,
            appearance=self.glass_config.appearance,
            window_alpha=alpha,
            emphasized=self.glass_config.emphasized,
        )
        self.update_glass_config(new_config)

    def _toggle_fullscreen(self):
        """
        Toggle between fullscreen and windowed mode.
        """
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_button.setText("Fullscreen")
        else:
            self.showFullScreen()
            self.fullscreen_button.setText("Exit Fullscreen")
