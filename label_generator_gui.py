import sys
import os
import json
import matplotlib.pyplot as plt
import random
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QProgressBar, QSpinBox, QDoubleSpinBox, QLineEdit, QCheckBox,
    QComboBox, QGroupBox, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QSplitter,
    QDialog, QDialogButtonBox, QFormLayout, QScrollArea, QFrame, QTextEdit
)
from PyQt6.QtGui import QColor 

from label_generator_core import LabelGeneratorSettings, LabelGenerator 



class UnitSelectionDialog(QDialog):
    """Dialog for selecting allowed units from a list"""
    def __init__(self, parent=None, available_units=None, selected_units=None):
        super().__init__(parent)
        self.available_units = available_units or []
        self.selected_units = selected_units or []
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Select Allowed Units")
        self.setMinimumSize(500, 600)  # Increased size
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Select which units should be available for label generation.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Unit list - with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.unit_list = QListWidget()
        self.unit_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.unit_list.setMinimumHeight(400)  # Larger list
        
        # Populate with available units
        for unit in self.available_units:
            item = QListWidgetItem(unit if unit != "" else "[No unit - empty string]")
            self.unit_list.addItem(item)
            if unit in self.selected_units:
                item.setSelected(True)
        
        scroll_area.setWidget(self.unit_list)
        layout.addWidget(scroll_area)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all)
        
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(clear_all_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Warning label for empty selection
        self.warning_label = QLabel("At least one unit must be selected.")
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
        
    def select_all(self):
        """Select all units in the list"""
        for i in range(self.unit_list.count()):
            item = self.unit_list.item(i)
            item.setSelected(True)
            
    def clear_all(self):
        """Clear all selections in the list"""
        for i in range(self.unit_list.count()):
            item = self.unit_list.item(i)
            item.setSelected(False)
            
    def validate_and_accept(self):
        """Validate that at least one unit is selected before accepting"""
        selected_units = self.get_selected_units()
        if not selected_units:
            self.warning_label.setVisible(True)
            return  # Don't close the dialog
            
        self.warning_label.setVisible(False)
        self.accept()
            
    def get_selected_units(self):
        """Get the list of selected units (convert display text back to actual units)"""
        selected = []
        for item in self.unit_list.selectedItems():
            text = item.text()
            # Convert display text back to actual unit
            if text == "[No unit - empty string]":
                selected.append("")
            else:
                selected.append(text)
        return selected


# Create a stream that redirects console output to a QTextEdit
class OutputStream:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        
    def write(self, text):
        cursor = self.text_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.text_widget.setTextCursor(cursor)
        self.text_widget.ensureCursorVisible()
        
    def flush(self):
        pass


class SettingsTab(QWidget):
    """Base class for settings tabs with common functionality"""
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
    def add_section(self, title):
        """Add a section header to the layout"""
        section_label = QLabel(f"<b>{title}</b>")
        section_label.setStyleSheet("font-size: 14px; margin-top: 15px; margin-bottom: 5px;")
        self.layout.addWidget(section_label)
        
    def add_setting(self, label, widget):
        """Add a setting with label and widget"""
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel(label))
        hbox.addStretch()
        hbox.addWidget(widget)
        self.layout.addLayout(hbox)
        
    def add_row(self, widgets):
        """Add a row of widgets"""
        hbox = QHBoxLayout()
        for widget in widgets:
            hbox.addWidget(widget)
        self.layout.addLayout(hbox)
        
    def add_group(self, title, layout):
        """Add a group box with layout"""
        group = QGroupBox(title)
        group.setLayout(layout)
        self.layout.addWidget(group)


class UnitsOptionsSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Units section - occupies upper half
        self.add_section("Units Configuration")
        
        unit_group = QGroupBox("Units Management")
        unit_group_layout = QVBoxLayout()
        
        # Currently selected units display with scroll area
        selected_units_label = QLabel("Currently selected units:")
        unit_group_layout.addWidget(selected_units_label)
        
        scroll_area_units = QScrollArea()
        scroll_area_units.setWidgetResizable(True)
        scroll_area_units.setMinimumHeight(120)
        scroll_area_units.setMaximumHeight(180)
        
        self.selected_units_display = QListWidget()
        self.selected_units_display.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.update_selected_units_display()
        
        scroll_area_units.setWidget(self.selected_units_display)
        unit_group_layout.addWidget(scroll_area_units)
        
        # Display count of selected units
        ##self.units_count_label = QLabel(f"Selected: {len(self.settings.units)} units")
        ##self.units_count_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        ##unit_group_layout.addWidget(self.units_count_label)
        
        # Unit management buttons
        unit_button_layout = QHBoxLayout()
        
        self.select_units_btn = QPushButton("📋 Select Unit Options")
        self.select_units_btn.clicked.connect(self.open_unit_selection)
        self.select_units_btn.setMinimumHeight(40)
        
        unit_button_layout.addWidget(self.select_units_btn)
        unit_button_layout.addStretch()
        
        unit_group_layout.addLayout(unit_button_layout)
        
        # Add custom unit section
        custom_unit_layout = QHBoxLayout()
        
        self.new_unit_edit = QLineEdit()
        self.new_unit_edit.setPlaceholderText("Enter custom unit (e.g., '  km')")
        self.new_unit_edit.setMinimumHeight(30)
        
        self.add_unit_btn = QPushButton("➕ Add")
        self.add_unit_btn.clicked.connect(self.add_custom_unit)
        self.add_unit_btn.setMinimumHeight(30)
        
        self.remove_custom_btn = QPushButton("🗑 Remove Selected")
        self.remove_custom_btn.clicked.connect(self.remove_custom_unit)
        self.remove_custom_btn.setMinimumHeight(30)
        
        custom_unit_layout.addWidget(QLabel("Custom Unit:"))
        custom_unit_layout.addWidget(self.new_unit_edit)
        custom_unit_layout.addWidget(self.add_unit_btn)
        custom_unit_layout.addWidget(self.remove_custom_btn)
        
        unit_group_layout.addLayout(custom_unit_layout)
        unit_group.setLayout(unit_group_layout)
        self.layout.addWidget(unit_group)
        
        # Unit separators - occupies lower half
        self.add_section("Unit Separators")
        
        sep_group = QGroupBox("Unit Separators (select multiple)")
        sep_group_layout = QVBoxLayout()
        
        # Separator list with scroll area
        scroll_area_sep = QScrollArea()
        scroll_area_sep.setWidgetResizable(True)
        scroll_area_sep.setMinimumHeight(80)
        scroll_area_sep.setMaximumHeight(120)
        
        self.separator_list = QListWidget()
        self.separator_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for sep in self.settings.unit_separator:
            item = QListWidgetItem(sep)
            self.separator_list.addItem(item)
            item.setSelected(True)
        self.separator_list.itemChanged.connect(self.update_separators)
        
        scroll_area_sep.setWidget(self.separator_list)
        sep_group_layout.addWidget(scroll_area_sep)
        
        # Add/remove buttons for separator list
        sep_button_layout = QHBoxLayout()
        self.add_sep_btn = QPushButton("Add Separator")
        self.add_sep_btn.clicked.connect(self.add_separator_item)
        self.remove_sep_btn = QPushButton("Remove Selected")
        self.remove_sep_btn.clicked.connect(self.remove_separator_items)
        self.new_sep_edit = QLineEdit()
        self.new_sep_edit.setPlaceholderText("Enter new separator...")
        
        sep_button_layout.addWidget(self.new_sep_edit)
        sep_button_layout.addWidget(self.add_sep_btn)
        sep_button_layout.addWidget(self.remove_sep_btn)
        
        sep_group_layout.addLayout(sep_button_layout)
        sep_group.setLayout(sep_group_layout)
        self.layout.addWidget(sep_group)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def update_selected_units_display(self):
        """Update the display of selected units"""
        self.selected_units_display.clear()
        for unit in self.settings.units:
            display_text = unit if unit != "" else "[No unit - empty string]"
            self.selected_units_display.addItem(display_text)
        # Update count label
        if hasattr(self, 'units_count_label'):
            self.units_count_label.setText(f"Selected: {len(self.settings.units)} units")
            
    def open_unit_selection(self):
        """Open the unit selection dialog"""
        # Get current available units (including custom ones)
        available_units = [
            "", "  mg", "  mL", "  μg", "  μL", "  %", "  ppm", "  kelvin", "  M", 
            " mM", " nM", " seconds", "  minutes", " hours", "  days", " (s)", 
            "  (h)", " Celsius", "  Fahrenheit", "  Rankine", "meter", "liter", 
            "(kg/L)", " m", " cm"
        ]
        
        # Add any custom units that aren't already in the list
        for unit in self.settings.units:
            if unit not in available_units and unit != "":
                available_units.append(unit)
                
        dialog = UnitSelectionDialog(self, available_units, self.settings.units)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update the selected units
            selected_units = dialog.get_selected_units()
            self.settings.units = selected_units
            self.update_selected_units_display()
            
    def add_custom_unit(self):
        """Add a custom unit to the list"""
        custom_unit = self.new_unit_edit.text().strip()
        if custom_unit:
            # Add to settings if not already present
            if custom_unit not in self.settings.units:
                self.settings.units.append(custom_unit)
                self.update_selected_units_display()
                self.new_unit_edit.clear()
            else:
                QMessageBox.information(self, "Duplicate Unit", 
                                      f"Unit '{custom_unit}' is already in the list.")
        else:
            QMessageBox.warning(self, "Empty Unit", 
                              "Please enter a unit name.")
                
    def remove_custom_unit(self):
        """Remove selected custom unit from the list"""
        selected_items = self.selected_units_display.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", 
                              "Please select a unit to remove.")
            return
            
        # Confirm removal
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Remove {len(selected_items)} selected unit(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                display_text = item.text()
                # Convert display text back to actual unit
                if display_text == "[No unit - empty string]":
                    unit = ""
                else:
                    unit = display_text
                    
                if unit in self.settings.units:
                    self.settings.units.remove(unit)
                    
            self.update_selected_units_display()
            
    def update_separators(self):
        """Update selected separators in settings"""
        selected = []
        for i in range(self.separator_list.count()):
            item = self.separator_list.item(i)
            selected.append(item.text())
        self.settings.unit_separator = selected
        
    def add_separator_item(self):
        """Add new separator item to the list"""
        sep = self.new_sep_edit.text().strip()
        if sep:
            item = QListWidgetItem(sep)
            self.separator_list.addItem(item)
            self.new_sep_edit.clear()
            self.update_separators()
            
    def remove_separator_items(self):
        """Remove selected separator items from the list"""
        for item in self.separator_list.selectedItems():
            self.separator_list.takeItem(self.separator_list.row(item))
        self.update_separators()


class GeneralSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Only keep Output Configuration section
        self.add_section("Output Configuration")
        
        # Number of labels
        self.num_labels_spin = QSpinBox()
        self.num_labels_spin.setRange(1, 10000)
        self.num_labels_spin.setValue(self.settings.num_labels)
        self.num_labels_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'num_labels', v))
        self.add_setting("Number of labels:", self.num_labels_spin)
        
        # Output format
        self.format_combo = QComboBox()
        self.format_combo.addItems(['png', 'jpg', 'jpeg', 'tiff', 'bmp'])
        self.format_combo.setCurrentText(self.settings.output_format)
        self.format_combo.currentTextChanged.connect(
            lambda t: setattr(self.settings, 'output_format', t))
        self.add_setting("Output format:", self.format_combo)
        
        # Output directory
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit(self.settings.output_dir)
        self.output_dir_edit.textChanged.connect(
            lambda t: setattr(self.settings, 'output_dir', t))
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output_dir)
        
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(browse_btn)
        self.layout.addLayout(output_layout)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def browse_output_dir(self):
        """Open directory dialog for output path"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.settings.output_dir)
        if dir_path:
            self.output_dir_edit.setText(dir_path)


class TextContentSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Label text options - occupies upper half
        self.add_section("Label Text Options")
        
        text_group = QGroupBox("Text Options (select multiple)")
        text_group_layout = QVBoxLayout()
        
        # Text list with scroll area
        scroll_area_text = QScrollArea()
        scroll_area_text.setWidgetResizable(True)
        scroll_area_text.setMinimumHeight(200)  # Increased height
        scroll_area_text.setMaximumHeight(300)
        
        self.text_list = QListWidget()
        self.text_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for text in self.settings.label_text_options:
            item = QListWidgetItem(text)
            self.text_list.addItem(item)
            item.setSelected(True)
        self.text_list.itemChanged.connect(self.update_text_options)
        
        scroll_area_text.setWidget(self.text_list)
        text_group_layout.addWidget(scroll_area_text)
        
        # Add/remove buttons for text list
        text_button_layout = QHBoxLayout()
        self.add_text_btn = QPushButton("Add Text")
        self.add_text_btn.clicked.connect(self.add_text_item)
        self.remove_text_btn = QPushButton("Remove Selected")
        self.remove_text_btn.clicked.connect(self.remove_text_items)
        self.new_text_edit = QLineEdit()
        self.new_text_edit.setPlaceholderText("Enter new text...")
        
        text_button_layout.addWidget(self.new_text_edit)
        text_button_layout.addWidget(self.add_text_btn)
        text_button_layout.addWidget(self.remove_text_btn)
        
        text_group_layout.addLayout(text_button_layout)
        text_group.setLayout(text_group_layout)
        self.layout.addWidget(text_group)
        
        # Scientific notation - occupies lower half
        self.add_section("Scientific Notation")
        
        sci_group = QGroupBox("Scientific Notation Settings")
        sci_group_layout = QVBoxLayout()
        
        # Scientific notation probability
        sci_prob_layout = QHBoxLayout()
        sci_prob_layout.addWidget(QLabel("Probability of scientific notation (0.0-1.0):"))
        self.sci_prob_spin = QDoubleSpinBox()
        self.sci_prob_spin.setRange(0.0, 1.0)
        self.sci_prob_spin.setSingleStep(0.01)
        self.sci_prob_spin.setValue(self.settings.scientific_notation_prob)
        self.sci_prob_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'scientific_notation_prob', v))
        sci_prob_layout.addWidget(self.sci_prob_spin)
        sci_prob_layout.addStretch()
        
        sci_group_layout.addLayout(sci_prob_layout)
        
        # Note about scientific notation
        note_label = QLabel("Note: Scientific notation applies to numbers with commas (e.g., 10,000 → 1.0 × 10⁴)")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #666666; font-style: italic;")
        sci_group_layout.addWidget(note_label)
        
        sci_group.setLayout(sci_group_layout)
        self.layout.addWidget(sci_group)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def update_text_options(self):
        """Update selected text options in settings"""
        selected = []
        for i in range(self.text_list.count()):
            item = self.text_list.item(i)
            selected.append(item.text())
        self.settings.label_text_options = selected
            
    def add_text_item(self):
        """Add new text item to the list"""
        text = self.new_text_edit.text().strip()
        if text:
            item = QListWidgetItem(text)
            self.text_list.addItem(item)
            self.new_text_edit.clear()
            self.update_text_options()
            
    def remove_text_items(self):
        """Remove selected text items from the list"""
        for item in self.text_list.selectedItems():
            self.text_list.takeItem(self.text_list.row(item))
        self.update_text_options()

###################################################################################################
class FontStyleSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Font size settings - removed section title
        # Base font size
        base_font_layout = QHBoxLayout()
        base_font_layout.addWidget(QLabel("Base font size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 72)
        self.font_size_spin.setValue(self.settings.base_font_size)
        self.font_size_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'base_font_size', v))
        base_font_layout.addWidget(self.font_size_spin)
        base_font_layout.addStretch()
        self.layout.addLayout(base_font_layout)
        
        # Font size variation
        font_var_layout = QHBoxLayout()
        font_var_layout.addWidget(QLabel("Font size variation (±):"))
        self.font_var_spin = QSpinBox()
        self.font_var_spin.setRange(0, 20)
        self.font_var_spin.setValue(self.settings.font_size_variation)
        self.font_var_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'font_size_variation', v))
        font_var_layout.addWidget(self.font_var_spin)
        font_var_layout.addStretch()
        self.layout.addLayout(font_var_layout)
        
        # Add spacing
        self.layout.addSpacing(15)
        
        # Font families - properly contained group
        font_families_group = QGroupBox("Font Families (select multiple)")
        font_families_layout = QVBoxLayout()
        font_families_layout.setContentsMargins(5, 10, 5, 10)  # Tighter margins
        
        self.font_list = QListWidget()
        self.font_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Fixed height for font list - fits better in group
        self.font_list.setMinimumHeight(80)
        self.font_list.setMaximumHeight(120)
        
        font_families_layout.addWidget(self.font_list)
        font_families_group.setLayout(font_families_layout)
        self.layout.addWidget(font_families_group)
        
        # Add spacing
        self.layout.addSpacing(10)
        
        # Font weights - properly contained group
        font_weights_group = QGroupBox("Font Weights (select multiple)")
        font_weights_layout = QVBoxLayout()
        font_weights_layout.setContentsMargins(5, 10, 5, 10)  # Tighter margins
        
        self.weight_list = QListWidget()
        self.weight_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Fixed height for weight list - fits better in group
        self.weight_list.setMinimumHeight(80)
        self.weight_list.setMaximumHeight(120)
        
        for weight in self.settings.font_weights:
            item = QListWidgetItem(weight)
            self.weight_list.addItem(item)
            item.setSelected(True)
        self.weight_list.itemSelectionChanged.connect(self.update_weights)
        
        font_weights_layout.addWidget(self.weight_list)
        font_weights_group.setLayout(font_weights_layout)
        self.layout.addWidget(font_weights_group)
        
        # Add spacing
        self.layout.addSpacing(10)
        
        # Text colors - redesigned with new layout strategy
        color_group = QGroupBox("Text Colors (Double-Click to Pick)")
        color_group_layout = QHBoxLayout()  # Changed to horizontal layout
        color_group_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left side: Color list (occupies half the width)
        left_layout = QVBoxLayout()
        
        self.color_list = QListWidget()
        self.color_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.color_list.itemDoubleClicked.connect(self.pick_color)
        
        # Set height for color list - ensure it fits within frame
        self.color_list.setMinimumHeight(80)
        self.color_list.setMaximumHeight(120)
        
        # Enable scrolling
        self.color_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.color_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        left_layout.addWidget(self.color_list)
        
        # Right side: Controls and preset colors
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 0, 0, 0)  # Left margin to separate from list
        right_layout.setSpacing(5)  # Reduced spacing between elements
        
        # Remove button and preview in a horizontal layout
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 5)  # Reduced bottom margin
        
        # Add spacer to push to right
        controls_layout.addStretch()
        
        # Remove button
        self.remove_color_btn = QPushButton("🗑 Remove Selected")
        self.remove_color_btn.clicked.connect(self.remove_selected_color)
        self.remove_color_btn.setMinimumHeight(35)
        self.remove_color_btn.setMaximumWidth(150)  # Limit width
        
        # Preview of selected color
        self.color_preview = QLabel("")
        self.color_preview.setFixedSize(45, 35)  # Fixed size
        self.color_preview.setStyleSheet("background-color: #000000; border: 2px solid #666666;")
        
        controls_layout.addWidget(self.remove_color_btn)
        controls_layout.addWidget(self.color_preview)
        
        right_layout.addLayout(controls_layout)
        
        # Preset colors section - moved up and aligned to right
        preset_container = QVBoxLayout()
        preset_container.setContentsMargins(0, 0, 0, 0)
        preset_container.setSpacing(5)  # Space between label and buttons
        
        # Presets label
        preset_label = QLabel("Presets:")
        preset_label.setStyleSheet("font-weight: bold;")
        preset_container.addWidget(preset_label)
        
        # Preset colors in a grid (2 rows of 5) - right aligned
        preset_colors_grid = QGridLayout()
        preset_colors_grid.setContentsMargins(0, 0, 0, 0)
        preset_colors_grid.setHorizontalSpacing(8)  # Horizontal spacing between buttons
        preset_colors_grid.setVerticalSpacing(12)  # Vertical spacing between rows
        
        preset_colors = [
            ("Black", "#000000"),
            ("Dark Gray", "#333333"),
            ("Gray", "#666666"),
            ("White", "#FFFFFF"),
            ("Red", "#FF0000"),
            ("Green", "#00FF00"),
            ("Blue", "#0000FF"),
            ("Dark Red", "#8B0000"),
            ("Dark Green", "#006400"),
            ("Dark Blue", "#00008B")
        ]
        
        # Distribute 5 colors per row
        for i, (name, color) in enumerate(preset_colors):
            row = i // 5  # 0 for first 5, 1 for next 5
            col = i % 5   # 0-4 for columns
            
            btn = QPushButton("")
            btn.setToolTip(f"{name}: {color}")
            btn.setFixedSize(20, 20)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 1px solid #666666;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    border: 2px solid #333333;
                }}
            """)
            btn.clicked.connect(lambda checked, c=color: self.add_preset_color(c))
            preset_colors_grid.addWidget(btn, row, col)
        
        # Add the grid to a container for right alignment
        preset_grid_widget = QWidget()
        preset_grid_widget.setLayout(preset_colors_grid)
        
        # Container to align grid to right
        grid_container = QHBoxLayout()
        grid_container.setContentsMargins(0, 0, 0, 0)
        grid_container.addStretch()
        grid_container.addWidget(preset_grid_widget)
        
        preset_container.addLayout(grid_container)
        
        # Add preset container to right layout
        right_layout.addLayout(preset_container)
        
        # Add stretch to push everything up
        right_layout.addStretch()
        
        # Add left and right layouts to main layout with stretch factors
        color_group_layout.addLayout(left_layout, 1)  # Takes 1 part of space (left half)
        color_group_layout.addLayout(right_layout, 1)  # Takes 1 part of space (right half)
        
        color_group.setLayout(color_group_layout)
        
        # Populate with current colors using enhanced display
        self.update_color_display()
        
        self.layout.addWidget(color_group)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def is_dark_color(self, hex_color):
        """Check if a color is dark (for text contrast)"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Handle short hex format
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            
            # Convert to RGB
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            
            # Calculate luminance (perceived brightness)
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            
            return luminance < 0.5
        except:
            return True  # Default to dark if parsing fails
            
    def update_color_display(self):
        """Update the color list with visual swatches"""
        self.color_list.clear()
        for color in self.settings.text_colors:
            item = QListWidgetItem()
            
            # Create color swatch icon
            pixmap = QPixmap(24, 24)
            pixmap.fill(QColor(color))
            
            # Set icon
            item.setIcon(QIcon(pixmap))
            
            # Set text with color name if possible
            color_name = self.get_color_name(color)
            item.setText(f"{color_name} ({color})")
            
            # Set foreground color for contrast
            if self.is_dark_color(color):
                item.setForeground(Qt.GlobalColor.white)
            else:
                item.setForeground(Qt.GlobalColor.black)
                
            # Store the hex color in item data
            item.setData(Qt.ItemDataRole.UserRole, color)
            
            self.color_list.addItem(item)
            
    def get_color_name(self, hex_color):
        """Try to get a color name from hex value"""
        color_names = {
            "#000000": "Black",
            "#333333": "Dark Gray",
            "#555555": "Medium Gray",
            "#777777": "Light Gray",
            "#FFFFFF": "White",
            "#FF0000": "Red",
            "#00FF00": "Green",
            "#0000FF": "Blue",
            "#FFA500": "Orange",
            "#800080": "Purple",
            "#FFFF00": "Yellow",
            "#00FFFF": "Cyan",
            "#FF00FF": "Magenta",
            "#A52A2A": "Brown"
        }
        
        return color_names.get(hex_color.upper(), "Custom")
        
    def update_colors(self):
        """Update text colors in settings"""
        colors = []
        for i in range(self.color_list.count()):
            item = self.color_list.item(i)
            hex_color = item.data(Qt.ItemDataRole.UserRole)
            if hex_color:
                colors.append(hex_color)
        self.settings.text_colors = colors
        
    def pick_color(self, item):
        """Open color picker dialog when double-clicking a color"""
        current_color = item.data(Qt.ItemDataRole.UserRole)
        if not current_color:
            current_color = "#000000"
            
        # Create QColor from hex string
        try:
            qcolor = QColor(current_color)
            if not qcolor.isValid():
                qcolor = QColor("#000000")
        except:
            qcolor = QColor("#000000")
        
        color = QColorDialog.getColor(qcolor, self, "Pick Text Color")
        
        if color.isValid():
            hex_color = color.name()
            
            # Check if this color already exists (different from current)
            if hex_color != current_color and hex_color in self.settings.text_colors:
                QMessageBox.information(self, "Duplicate Color", 
                                      f"Color '{hex_color}' is already in the list.")
                return
            
            # Update the color in the list
            if hex_color != current_color:
                # Replace the old color with new one
                idx = self.settings.text_colors.index(current_color)
                self.settings.text_colors[idx] = hex_color
            else:
                # Just refresh display if same color
                pass
            
            # Refresh display
            self.update_color_display()
            
            # Update preview
            self.color_preview.setStyleSheet(f"background-color: {hex_color}; border: 2px solid #666666;")
            
    def add_preset_color(self, hex_color):
        """Add a preset color when clicked"""
        if hex_color not in self.settings.text_colors:
            self.settings.text_colors.append(hex_color)
            self.update_color_display()
            
            # Update preview with newly added color
            self.color_preview.setStyleSheet(f"background-color: {hex_color}; border: 2px solid #666666;")
        else:
            QMessageBox.information(self, "Duplicate Color", 
                                  f"Color '{hex_color}' is already in the list.")
                
    def remove_selected_color(self):
        """Remove selected color from the list"""
        selected_items = self.color_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", 
                              "Please select a color to remove.")
            return
            
        # Confirm removal
        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Remove {len(selected_items)} selected color(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                hex_color = item.data(Qt.ItemDataRole.UserRole)
                if hex_color and hex_color in self.settings.text_colors:
                    self.settings.text_colors.remove(hex_color)
                    
            self.update_color_display()
            # Reset preview to black
            self.color_preview.setStyleSheet("background-color: #000000; border: 2px solid #666666;")
            
    def update_font_families(self):
        """Update selected font families in settings"""
        selected = [item.text() for item in self.font_list.selectedItems()]
        self.settings.font_families = selected
        
    def update_weights(self):
        """Update selected font weights in settings"""
        selected = [item.text() for item in self.weight_list.selectedItems()]
        self.settings.font_weights = selected
        
    def showEvent(self, event):
        """Load font families when tab is shown"""
        super().showEvent(event)
        if self.font_list.count() == 0:
            self.load_font_families()
            
    def load_font_families(self):
        """Load system font families into the list"""
        self.font_list.clear()
        for font in self.settings.get_safe_fonts():
            item = QListWidgetItem(font)
            self.font_list.addItem(item)
            # Select common fonts by default
            if font in ['DejaVu Sans', 'Arial', 'Verdana', 'Times New Roman']:
                item.setSelected(True)
        self.font_list.itemSelectionChanged.connect(self.update_font_families)
##############################################################################################################
class VintageBackgroundSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Combined Vintage Effects section (merging both previous sections)
        vintage_group = QGroupBox("Vintage Effects")
        vintage_layout = QVBoxLayout()
        vintage_layout.setSpacing(1)  # Increased spacing between option groups
        
        # Vintage effect probability with comment
        vintage_prob_container = QVBoxLayout()
        vintage_prob_container.setSpacing(3)  # Slightly increased spacing between control and comment
        
        vintage_prob_layout = QHBoxLayout()
        vintage_prob_layout.addWidget(QLabel("Vintage effect probability (0.0-1.0):"))
        self.vintage_prob_spin = QDoubleSpinBox()
        self.vintage_prob_spin.setRange(0.0, 1.0)
        self.vintage_prob_spin.setSingleStep(0.05)
        self.vintage_prob_spin.setValue(self.settings.vintage_effect_prob)
        self.vintage_prob_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'vintage_effect_prob', v))
        self.vintage_prob_spin.setMaximumWidth(80)  # Limit width
        vintage_prob_layout.addWidget(self.vintage_prob_spin)
        vintage_prob_layout.addStretch()
        
        vintage_prob_container.addLayout(vintage_prob_layout)
        
        # Comment for vintage effect probability
        vintage_prob_comment = QLabel("Probability that ANY vintage effects will be applied to a given label")
        vintage_prob_comment.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
        vintage_prob_comment.setWordWrap(True)
        vintage_prob_container.addWidget(vintage_prob_comment)
        
        vintage_layout.addLayout(vintage_prob_container)
        
        # Add spacing between this option group and next
        vintage_layout.addSpacing(12)
        
        # Vintage intensity with comment
        vintage_intensity_container = QVBoxLayout()
        vintage_intensity_container.setSpacing(3)
        
        vintage_intensity_layout = QHBoxLayout()
        vintage_intensity_layout.addWidget(QLabel("Vintage intensity (0.0-1.0):"))
        self.vintage_intensity_spin = QDoubleSpinBox()
        self.vintage_intensity_spin.setRange(0.0, 1.0)
        self.vintage_intensity_spin.setSingleStep(0.1)
        self.vintage_intensity_spin.setValue(self.settings.vintage_intensity)
        self.vintage_intensity_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'vintage_intensity', v))
        self.vintage_intensity_spin.setMaximumWidth(80)
        vintage_intensity_layout.addWidget(self.vintage_intensity_spin)
        vintage_intensity_layout.addStretch()
        
        vintage_intensity_container.addLayout(vintage_intensity_layout)
        
        # Comment for vintage intensity
        vintage_intensity_comment = QLabel("Overall intensity multiplier for ALL vintage effects")
        vintage_intensity_comment.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
        vintage_intensity_comment.setWordWrap(True)
        vintage_intensity_container.addWidget(vintage_intensity_comment)
        
        vintage_layout.addLayout(vintage_intensity_container)
        
        # Add spacing
        vintage_layout.addSpacing(12)
        
        # Texture file with comment - fixed layout
        texture_container = QVBoxLayout()
        texture_container.setSpacing(3)
        
        # Create a horizontal layout for the texture file controls
        texture_controls_layout = QHBoxLayout()
        
        # Label on left
        texture_label = QLabel("Path to texture file:")
        texture_label.setMinimumWidth(40)  # Ensure label has enough space
        
        # Line edit for file path
        self.texture_edit = QLineEdit(self.settings.texture_file)
        self.texture_edit.textChanged.connect(
            lambda t: setattr(self.settings, 'texture_file', t))
        
        # Browse button with fixed width
        self.texture_browse_btn = QPushButton("Browse...")
        self.texture_browse_btn.clicked.connect(self.browse_texture_file)
        self.texture_browse_btn.setFixedWidth(80)  # Fixed width for button
        
        # Add widgets to layout with stretch factors
        texture_controls_layout.addWidget(texture_label)
        texture_controls_layout.addWidget(self.texture_edit, 1)  # Line edit gets stretch factor
        texture_controls_layout.addWidget(self.texture_browse_btn)
        
        texture_container.addLayout(texture_controls_layout)
        
        # Comment for texture file
        texture_comment = QLabel("The actual texture image used for the vintage effect")
        texture_comment.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
        texture_comment.setWordWrap(True)
        texture_container.addWidget(texture_comment)
        
        vintage_layout.addLayout(texture_container)
        
        # Add spacing
        vintage_layout.addSpacing(12)
        
        # Noise intensity with comment
        noise_container = QVBoxLayout()
        noise_container.setSpacing(3)
        
        noise_layout = QHBoxLayout()
        noise_layout.addWidget(QLabel("Noise intensity (0.0-1.0):"))
        self.noise_spin = QDoubleSpinBox()
        self.noise_spin.setRange(0.0, 1.0)
        self.noise_spin.setSingleStep(0.05)
        self.noise_spin.setValue(self.settings.noise_intensity)
        self.noise_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'noise_intensity', v))
        self.noise_spin.setMaximumWidth(80)
        noise_layout.addWidget(self.noise_spin)
        noise_layout.addStretch()
        
        noise_container.addLayout(noise_layout)
        
        # Comment for noise intensity
        noise_comment = QLabel("Fine-tune how much random noise/grain to add")
        noise_comment.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
        noise_comment.setWordWrap(True)
        noise_container.addWidget(noise_comment)
        
        vintage_layout.addLayout(noise_container)
        
        # Add spacing
        vintage_layout.addSpacing(12)
        
        # Blur intensity with comment
        blur_container = QVBoxLayout()
        blur_container.setSpacing(3)
        
        blur_layout = QHBoxLayout()
        blur_layout.addWidget(QLabel("Blur intensity (0.0-2.0):"))
        self.blur_spin = QDoubleSpinBox()
        self.blur_spin.setRange(0.0, 2.0)
        self.blur_spin.setSingleStep(0.1)
        self.blur_spin.setValue(self.settings.blur_intensity)
        self.blur_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'blur_intensity', v))
        self.blur_spin.setMaximumWidth(80)
        blur_layout.addWidget(self.blur_spin)
        blur_layout.addStretch()
        
        blur_container.addLayout(blur_layout)
        
        # Comment for blur intensity
        blur_comment = QLabel("Fine-tune how much Gaussian blur to apply")
        blur_comment.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
        blur_comment.setWordWrap(True)
        blur_container.addWidget(blur_comment)
        
        vintage_layout.addLayout(blur_container)
        
        vintage_group.setLayout(vintage_layout)
        self.layout.addWidget(vintage_group)
        
        # Reduced spacing between Vintage Effects and Realism Effects
        self.layout.addSpacing(10)
        
        # Realism Effects section - moved closer
        realism_group = QGroupBox("Realism Effects")
        realism_layout = QVBoxLayout()
        realism_layout.setSpacing(8)
        realism_layout.setContentsMargins(10, 12, 10, 12)  # Reduced vertical padding
        
        # Add realism checkbox
        self.realism_cb = QCheckBox("Add realism effects")
        self.realism_cb.setChecked(self.settings.add_realism)
        self.realism_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'add_realism', 
                             s == Qt.CheckState.Checked.value))
        self.realism_cb.stateChanged.connect(self.toggle_realism_options)
        realism_layout.addWidget(self.realism_cb)
        
        # Realism intensity with comment
        realism_intensity_container = QVBoxLayout()
        realism_intensity_container.setSpacing(3)
        
        realism_intensity_layout = QHBoxLayout()
        realism_intensity_layout.addWidget(QLabel("Realism intensity (0.0-1.0):"))
        self.realism_intensity_spin = QDoubleSpinBox()
        self.realism_intensity_spin.setRange(0.0, 1.0)
        self.realism_intensity_spin.setSingleStep(0.1)
        self.realism_intensity_spin.setValue(self.settings.realism_intensity)
        self.realism_intensity_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'realism_intensity', v))
        self.realism_intensity_spin.setMaximumWidth(80)
        realism_intensity_layout.addWidget(self.realism_intensity_spin)
        realism_intensity_layout.addStretch()
        
        realism_intensity_container.addLayout(realism_intensity_layout)
        
        # Comment for realism intensity
        realism_comment = QLabel("Controls the strength of all realism enhancement effects")
        realism_comment.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
        realism_comment.setWordWrap(True)
        realism_intensity_container.addWidget(realism_comment)
        
        realism_layout.addLayout(realism_intensity_container)
        realism_group.setLayout(realism_layout)
        self.layout.addWidget(realism_group)
        
        # Reduced spacing between Realism Effects and Background
        self.layout.addSpacing(10)
        
        # Background section - moved closer
        background_group = QGroupBox("Background Settings")
        background_layout = QVBoxLayout()
        background_layout.setSpacing(8)
        background_layout.setContentsMargins(10, 12, 10, 12)  # Reduced vertical padding
        
        # Background brightness with comment
        bg_brightness_container = QVBoxLayout()
        bg_brightness_container.setSpacing(3)
        
        bg_brightness_layout = QHBoxLayout()
        bg_brightness_layout.addWidget(QLabel("Minimum background brightness (0.0-1.0):"))
        self.bg_brightness_spin = QDoubleSpinBox()
        self.bg_brightness_spin.setRange(0.0, 1.0)
        self.bg_brightness_spin.setSingleStep(0.05)
        self.bg_brightness_spin.setValue(self.settings.min_background_brightness)
        self.bg_brightness_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'min_background_brightness', v))
        self.bg_brightness_spin.setMaximumWidth(80)
        bg_brightness_layout.addWidget(self.bg_brightness_spin)
        bg_brightness_layout.addStretch()
        
        bg_brightness_container.addLayout(bg_brightness_layout)
        
        # Comment for background brightness
        bg_brightness_comment = QLabel("How light the automatically generated backgrounds will be")
        bg_brightness_comment.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
        bg_brightness_comment.setWordWrap(True)
        bg_brightness_container.addWidget(bg_brightness_comment)
        
        background_layout.addLayout(bg_brightness_container)
        
        # Add spacing
        background_layout.addSpacing(12)
        
        # Transparent background probability with comment
        transparent_prob_container = QVBoxLayout()
        transparent_prob_container.setSpacing(3)
        
        transparent_prob_layout = QHBoxLayout()
        transparent_prob_layout.addWidget(QLabel("Transparent background probability (0.0-1.0):"))
        self.transparent_prob_spin = QDoubleSpinBox()
        self.transparent_prob_spin.setRange(0.0, 1.0)
        self.transparent_prob_spin.setSingleStep(0.05)
        self.transparent_prob_spin.setValue(self.settings.transparent_bg_prob)
        self.transparent_prob_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'transparent_bg_prob', v))
        self.transparent_prob_spin.setMaximumWidth(80)
        transparent_prob_layout.addWidget(self.transparent_prob_spin)
        transparent_prob_layout.addStretch()
        
        transparent_prob_container.addLayout(transparent_prob_layout)
        
        # Comment for transparent background probability
        transparent_prob_comment = QLabel("Chance that a label will have a transparent (no color) background")
        transparent_prob_comment.setStyleSheet("color: #666666; font-style: italic; font-size: 11px;")
        transparent_prob_comment.setWordWrap(True)
        transparent_prob_container.addWidget(transparent_prob_comment)
        
        background_layout.addLayout(transparent_prob_container)
        
        background_group.setLayout(background_layout)
        self.layout.addWidget(background_group)
        
        # Initially set enabled state for realism options
        self.toggle_realism_options(self.settings.add_realism)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def browse_texture_file(self):
        """Open file dialog for texture file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Texture File", 
            os.path.dirname(self.settings.texture_file) if self.settings.texture_file else "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.texture_edit.setText(file_path)
            
    def toggle_realism_options(self, state):
        """Enable/disable realism options based on checkbox state"""
        enabled = state == Qt.CheckState.Checked.value
        self.realism_intensity_spin.setEnabled(enabled)
######################################################################################################################################################

class RotationEffectsSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Rotation settings
        self.add_section("Rotation Settings")
        
        # Enable rotation checkbox
        self.rotation_cb = QCheckBox("Enable rotation")
        self.rotation_cb.setChecked(self.settings.rotation_allowed)
        self.rotation_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'rotation_allowed', 
                             s == Qt.CheckState.Checked.value))
        self.rotation_cb.stateChanged.connect(self.toggle_rotation_options)
        self.layout.addWidget(self.rotation_cb)
        
        # Rotation angles
        self.angle_list = QListWidget()
        self.angle_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for angle in self.settings.rotation_angle_allowed:
            item = QListWidgetItem(angle)
            self.angle_list.addItem(item)
            if angle != 'customize':  # Select all except 'customize' by default
                item.setSelected(True)
        self.angle_list.itemSelectionChanged.connect(self.update_angles)
        
        angle_group = QGroupBox("Allowed Rotation Angles (select multiple)")
        angle_group_layout = QVBoxLayout()
        angle_group_layout.addWidget(self.angle_list)
        angle_group.setLayout(angle_group_layout)
        self.layout.addWidget(angle_group)
        
        # Custom angle step
        self.angle_step_label = QLabel("Custom angle step (degrees):")
        self.angle_step_spin = QSpinBox()
        self.angle_step_spin.setRange(1, 30)
        self.angle_step_spin.setValue(self.settings.custom_angle_step)
        self.angle_step_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'custom_angle_step', v))
        
        angle_step_layout = QHBoxLayout()
        angle_step_layout.addWidget(self.angle_step_label)
        angle_step_layout.addWidget(self.angle_step_spin)
        angle_step_layout.addStretch()
        self.layout.addLayout(angle_step_layout)
        
        # Initially set enabled state
        self.toggle_rotation_options(self.settings.rotation_allowed)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def toggle_rotation_options(self, state):
        """Enable/disable rotation options based on checkbox state"""
        enabled = state == Qt.CheckState.Checked.value
        self.angle_list.setEnabled(enabled)
        self.angle_step_label.setEnabled(enabled)
        self.angle_step_spin.setEnabled(enabled)
        
    def update_angles(self):
        """Update selected rotation angles in settings"""
        selected = [item.text() for item in self.angle_list.selectedItems()]
        self.settings.rotation_angle_allowed = selected


class SizeResolutionSettingsTab(SettingsTab):
    def __init__(self, settings):
        super().__init__(settings)
        self.init_ui()
        
    def init_ui(self):
        # Size configuration checkbox at the top
        self.add_section("Size Configuration")
        
        self.size_res_cb = QCheckBox("Customize size resolution")
        self.size_res_cb.setChecked(self.settings.customized_size_resolution)
        self.size_res_cb.stateChanged.connect(
            lambda s: setattr(self.settings, 'customized_size_resolution', 
                             s == Qt.CheckState.Checked.value))
        self.size_res_cb.stateChanged.connect(self.toggle_size_options)
        self.layout.addWidget(self.size_res_cb)
        
        # Dimensions section (enabled when custom size is checked)
        self.add_section("Dimensions")
        
        # Width range
        width_layout = QHBoxLayout()
        self.min_width_spin = QSpinBox()
        self.min_width_spin.setRange(50, 2000)
        self.min_width_spin.setValue(self.settings.min_width)
        self.min_width_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'min_width', v))
        
        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(50, 2000)
        self.max_width_spin.setValue(self.settings.max_width)
        self.max_width_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'max_width', v))
        
        width_layout.addWidget(QLabel("Width range:"))
        width_layout.addWidget(QLabel("Min:"))
        width_layout.addWidget(self.min_width_spin)
        width_layout.addWidget(QLabel("Max:"))
        width_layout.addWidget(self.max_width_spin)
        width_layout.addStretch()
        self.layout.addLayout(width_layout)
        
        # Height range
        height_layout = QHBoxLayout()
        self.min_height_spin = QSpinBox()
        self.min_height_spin.setRange(50, 2000)
        self.min_height_spin.setValue(self.settings.min_height)
        self.min_height_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'min_height', v))
        
        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(50, 2000)
        self.max_height_spin.setValue(self.settings.max_height)
        self.max_height_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'max_height', v))
        
        height_layout.addWidget(QLabel("Height range:"))
        height_layout.addWidget(QLabel("Min:"))
        height_layout.addWidget(self.min_height_spin)
        height_layout.addWidget(QLabel("Max:"))
        height_layout.addWidget(self.max_height_spin)
        height_layout.addStretch()
        self.layout.addLayout(height_layout)
        
        # DPI settings
        self.add_section("DPI Settings")
        
        # DPI range (for custom size)
        dpi_range_layout = QHBoxLayout()
        self.min_dpi_spin = QSpinBox()
        self.min_dpi_spin.setRange(10, 600)
        self.min_dpi_spin.setValue(self.settings.min_dpi)
        self.min_dpi_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'min_dpi', v))
        
        self.max_dpi_spin = QSpinBox()
        self.max_dpi_spin.setRange(10, 600)
        self.max_dpi_spin.setValue(self.settings.max_dpi)
        self.max_dpi_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'max_dpi', v))
        
        dpi_range_layout.addWidget(QLabel("DPI range (custom size):"))
        dpi_range_layout.addWidget(QLabel("Min:"))
        dpi_range_layout.addWidget(self.min_dpi_spin)
        dpi_range_layout.addWidget(QLabel("Max:"))
        dpi_range_layout.addWidget(self.max_dpi_spin)
        dpi_range_layout.addStretch()
        self.layout.addLayout(dpi_range_layout)
        
        # Fixed DPI (for non-custom size)
        self.fixed_dpi_label = QLabel("Fixed DPI (non-custom size):")
        self.fixed_dpi_spin = QSpinBox()
        self.fixed_dpi_spin.setRange(10, 600)
        self.fixed_dpi_spin.setValue(self.settings.fixed_dpi)
        self.fixed_dpi_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'fixed_dpi', v))
        
        fixed_dpi_layout = QHBoxLayout()
        fixed_dpi_layout.addWidget(self.fixed_dpi_label)
        fixed_dpi_layout.addWidget(self.fixed_dpi_spin)
        fixed_dpi_layout.addStretch()
        self.layout.addLayout(fixed_dpi_layout)
        
        # Layout settings
        self.add_section("Layout Settings")
        
        # Text padding
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 100)
        self.padding_spin.setValue(self.settings.min_text_padding)
        self.padding_spin.valueChanged.connect(
            lambda v: setattr(self.settings, 'min_text_padding', v))
        self.add_setting("Minimum text padding (pixels):", self.padding_spin)
        
        # Note about the clipping option (removed as requested)
        ##note_label = QLabel("Note: Clipping functionality has been removed from this version.")
        ##note_label.setStyleSheet("color: gray; font-style: italic;")
        ##self.layout.addWidget(note_label)
        
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def toggle_size_options(self, state):
        """Enable/disable size options based on checkbox state"""
        enabled = state == Qt.CheckState.Checked.value
        self.min_width_spin.setEnabled(enabled)
        self.max_width_spin.setEnabled(enabled)
        self.min_height_spin.setEnabled(enabled)
        self.max_height_spin.setEnabled(enabled)
        self.min_dpi_spin.setEnabled(enabled)
        self.max_dpi_spin.setEnabled(enabled)
        self.fixed_dpi_spin.setEnabled(not enabled)  # Fixed DPI enabled when custom is off


class GenerationThread(QThread):
    """Thread for running the label generation"""
    progress_updated = pyqtSignal(int, str)
    image_generated = pyqtSignal(str)
    log_message = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.stopped = False
        
    def run(self):
        """Run the generation process"""
        generator = LabelGenerator(self.settings)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.settings.output_dir, exist_ok=True)
        
        for i in range(self.settings.num_labels):
            if self.stopped:
                break
                
            label_idx = i + 1
            self.progress_updated.emit(
                int((i+1)/self.settings.num_labels*100), 
                f"Generating label {label_idx}/{self.settings.num_labels}"
            )
            
            # Create label image
            image, metadata = generator.create_label_image(label_idx)
            
            # Determine DPI based on settings
            if self.settings.customized_size_resolution:
                dpi = random.randint(self.settings.min_dpi, self.settings.max_dpi)
            else:
                dpi = self.settings.fixed_dpi
            
            # Save image
            img_filename = f"label_{label_idx:03d}.{self.settings.output_format}"
            img_path = os.path.join(self.settings.output_dir, img_filename)
            
            # Set save parameters
            save_params = {}
            
            # Add DPI information for supported formats
            if self.settings.output_format.lower() in ['png', 'jpg', 'jpeg', 'tiff']:
                save_params['dpi'] = (dpi, dpi)
            
            # Convert to RGB if saving as JPG
            if self.settings.output_format.lower() in ['jpg', 'jpeg']:
                if image.mode in ['RGBA', 'LA']:
                    # Use specified background color for JPG conversion
                    bg_color = metadata['background']
                    if bg_color == "transparent":
                        bg_color = "#FFFFFF"  # Default to white for transparent
                    background = Image.new('RGB', image.size, bg_color)
                    background.paste(image, mask=image.split()[3] if image.mode == 'RGBA' else None)
                    image = background
                save_params['quality'] = 95
            
            # Save the image
            image.save(img_path, **save_params)
            
            # Add filename to metadata
            metadata["image_filename"] = img_filename
            generator.metadata.append(metadata)
            
            # Emit log message
            self.log_message.emit(f"Generated label: {img_filename}")
            
            # Emit signal with the generated image path for preview
            self.image_generated.emit(img_path)
            
        # Save metadata after all labels are generated
        csv_path, txt_path = generator.save_metadata()
        self.log_message.emit(f"Metadata saved to: {csv_path} and {txt_path}")
        self.log_message.emit(f"Successfully generated {self.settings.num_labels} labels in '{self.settings.output_dir}'")
        
        self.finished.emit()
        
    def stop(self):
        """Stop the generation process"""
        self.stopped = True


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = LabelGeneratorSettings()
        self.settings.update_calculated_properties()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Automated Generator of Customized Labels")
        #self.setWindowIcon(QIcon("LOGO-1.png"))
        self.setMinimumSize(1000, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for settings and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Settings panel (left)
        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)
        
        # Create tab widget for settings with 7 tabs (added new tab)
        self.tabs = QTabWidget()
        self.tabs.addTab(GeneralSettingsTab(self.settings), "General Settings")
        self.tabs.addTab(TextContentSettingsTab(self.settings), "Text & Content")
        self.tabs.addTab(UnitsOptionsSettingsTab(self.settings), "Options for Units")
        self.tabs.addTab(FontStyleSettingsTab(self.settings), "Font & Style")
        self.tabs.addTab(VintageBackgroundSettingsTab(self.settings), "Vintage & Background Effects")  # New tab
        self.tabs.addTab(RotationEffectsSettingsTab(self.settings), "Rotation Effects")
        self.tabs.addTab(SizeResolutionSettingsTab(self.settings), "Size & Resolution")
        
        settings_layout.addWidget(self.tabs)
        
        # Preview panel (right)
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        
        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc;")
        self.preview_label.setText("Preview will appear here")
        
        # Scroll area for preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.preview_label)
        
        preview_layout.addWidget(QLabel("<b>Generated Label Preview</b>"))
        preview_layout.addWidget(scroll_area)
        
        # Add panels to splitter
        splitter.addWidget(settings_panel)
        splitter.addWidget(preview_panel)
        splitter.setSizes([400, 600])
       
        # Create a horizontal layout for the bottom part (status and outputs)
        bottom_layout = QHBoxLayout()
        
        # Left: Status and Progression
        status_group = QGroupBox("Status and Progression of the Generation")
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("<b>Current Status: </b>"))
        self.status_label = QLabel("Ready to proceed.")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(QLabel("<b>Progression: </b>"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        status_layout.addWidget(self.progress_bar)
        status_group.setLayout(status_layout)
        
        # Right: Prompt Outputs
        output_group = QGroupBox("Prompt Outputs")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("font-family: monospace;")
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        
        # Add the two group boxes to the bottom layout
        bottom_layout.addWidget(status_group)
        bottom_layout.addWidget(output_group)
        
        # Add the bottom layout to the main layout
        main_layout.addLayout(bottom_layout)
        
        # Redirect stdout and stderr to the output text widget
        sys.stdout = OutputStream(self.output_text)
        sys.stderr = OutputStream(self.output_text)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton(QIcon("control-power.png"),"   Start Label Generation")
        self.start_btn.clicked.connect(self.start_generation)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton(QIcon("control-stop-square.png"),"   Stop Label Generation")
        self.stop_btn.clicked.connect(self.stop_generation)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        save_btn = QPushButton(QIcon("control-skip-090.png"),"   Save Settings")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        load_btn = QPushButton(QIcon("control-skip-270.png"),"   Load Settings")
        load_btn.clicked.connect(self.load_settings)
        button_layout.addWidget(load_btn)
        
        main_layout.addLayout(button_layout)
        
        # Initialize generation thread
        self.generation_thread = None
        
    def start_generation(self):
        """Start the label generation process"""
        # Clear the output text widget
        self.output_text.clear()
        
        # Validate settings
        if not self.validate_settings():
            return
            
        # Confirm with user
        reply = QMessageBox.question(
            self, 
            "Confirm Action",
            f"Begin to generate {self.settings.num_labels} labels?\n",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # Create and start generation thread
        self.generation_thread = GenerationThread(self.settings)
        self.generation_thread.progress_updated.connect(self.update_progress)
        self.generation_thread.image_generated.connect(self.update_preview)
        self.generation_thread.log_message.connect(self.output_text.append)
        self.generation_thread.finished.connect(self.generation_finished)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.tabs.setEnabled(False)
        
        self.generation_thread.start()
        
    def stop_generation(self):
        """Stop the generation process"""
        if self.generation_thread and self.generation_thread.isRunning():
            self.generation_thread.stop()
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Stopping generation...")
            
    def generation_finished(self):
        """Clean up after generation completes"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.tabs.setEnabled(True)
        self.status_label.setText("Generation completed")
        
    def update_progress(self, value, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def update_preview(self, image_path):
        """Update the preview with the generated image"""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale pixmap to fit label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.preview_label.width(), 
                self.preview_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
        
    def validate_settings(self):
        """Validate settings before starting generation"""
        # Check output directory
        if not os.path.exists(self.settings.output_dir):
            try:
                os.makedirs(self.settings.output_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Invalid Directory",
                    f"Cannot create output directory:\n{self.settings.output_dir}\n\n{str(e)}"
                )
                return False
        
        # Check texture file if specified
        if self.settings.texture_file and not os.path.exists(self.settings.texture_file):
            reply = QMessageBox.question(
                self,
                "Texture File Not Found",
                f"Texture file '{self.settings.texture_file}' not found.\nContinue without texture?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return False
        
        # Check min/max values
        if self.settings.min_width > self.settings.max_width:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "Minimum width cannot be greater than maximum width"
            )
            return False
            
        if self.settings.min_height > self.settings.max_height:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "Minimum height cannot be greater than maximum height"
            )
            return False
            
        if self.settings.min_dpi > self.settings.max_dpi:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "Minimum DPI cannot be greater than maximum DPI"
            )
            return False
        
        # Check that at least one text option is selected
        if not self.settings.label_text_options:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "At least one label text option must be specified"
            )
            return False
        
        # Check that at least one font family is selected
        if not self.settings.font_families:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "At least one font family must be selected"
            )
            return False
        
        # Check that at least one font weight is selected
        if not self.settings.font_weights:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "At least one font weight must be selected"
            )
            return False
        
        # Check that at least one text color is specified
        if not self.settings.text_colors:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "At least one text color must be specified"
            )
            return False
            
        return True
        
    def save_settings(self):
        """Save current settings to a JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Settings", 
            "", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            # Extract settings to save
            settings_dict = {}
            for attr in dir(self.settings):
                if not attr.startswith("__") and not callable(getattr(self.settings, attr)):
                    value = getattr(self.settings, attr)
                    # Convert lists and other types to JSON-serializable format
                    if isinstance(value, (list, tuple, dict, str, int, float, bool, type(None))):
                        settings_dict[attr] = value
                    elif hasattr(value, '__dict__'):
                        settings_dict[attr] = value.__dict__
            
            # Save to file
            try:
                with open(file_path, 'w') as f:
                    json.dump(settings_dict, f, indent=2)
                QMessageBox.information(
                    self,
                    "Settings Saved",
                    f"Settings saved to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save settings:\n{str(e)}"
                )
                

    def load_settings(self):
        """Load settings from a JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Load Settings", 
            "", 
            "JSON Files (*.json)"
        )
    
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    settings_dict = json.load(f)
            
                # Handle backward compatibility for units
                if 'available_units' not in settings_dict and 'units' in settings_dict:
                    # Old format: only has 'units' list
                    settings_dict['available_units'] = settings_dict['units']
            
                # Apply loaded settings
                for key, value in settings_dict.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
            
                # Update calculated properties
                self.settings.update_calculated_properties()
            
                # Refresh UI by recreating tabs
                self.refresh_tabs()
            
                QMessageBox.information(
                    self,
                    "Settings Loaded",
                    f"Settings loaded from:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Load Error",
                    f"Failed to load settings:\n{str(e)}"
                )
    
    def refresh_tabs(self):
        """Refresh all tabs with current settings"""
        # Store current tab index
        current_index = self.tabs.currentIndex()
        
        # Remove old tabs
        for i in range(self.tabs.count()):
            self.tabs.removeTab(0)
        
        # Add new tabs with updated settings in correct order
        self.tabs.addTab(GeneralSettingsTab(self.settings), "General Settings")
        self.tabs.addTab(TextContentSettingsTab(self.settings), "Text & Content")
        self.tabs.addTab(UnitsOptionsSettingsTab(self.settings), "Options for Units")
        self.tabs.addTab(FontStyleSettingsTab(self.settings), "Font & Style")
        self.tabs.addTab(VintageBackgroundSettingsTab(self.settings), "Vintage & Background Effects")  # New tab
        self.tabs.addTab(RotationEffectsSettingsTab(self.settings), "Rotation Effects")
        self.tabs.addTab(SizeResolutionSettingsTab(self.settings), "Size & Resolution")
        
        # Restore previous tab
        if 0 <= current_index < self.tabs.count():
            self.tabs.setCurrentIndex(current_index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
  

