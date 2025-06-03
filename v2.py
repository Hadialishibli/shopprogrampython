import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QMessageBox, QDialog, QFormLayout, QFileDialog, QDoubleSpinBox,
    QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal

# --- Data Model ---
class ShopItem:
    def __init__(self, name, description, price, quantity, buy_multiplier=1.0):
        self.name = name
        self.description = description
        self.price = float(price)
        self.quantity = int(quantity)
        self.buy_multiplier = float(buy_multiplier) # New attribute for buy quantity

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "quantity": self.quantity,
            "buy_multiplier": self.buy_multiplier # Include in JSON export
        }

    @staticmethod
    def from_dict(data):
        # Provide default values for new attributes for backward compatibility
        return ShopItem(
            data.get("name", "Unknown Item"),
            data.get("description", ""),
            data.get("price", 0.0),
            data.get("quantity", 0),
            data.get("buy_multiplier", 1.0) # Default to 1.0 if not found in JSON
        )

    def __str__(self):
        return f"{self.name} - ${self.price:.2f} (x{self.quantity})"

# --- Dialog for Adding/Editing Items ---
class ItemDialog(QDialog):
    def __init__(self, item=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Item")
        self.setGeometry(200, 200, 350, 250) # Slightly larger to accommodate new field

        self.item = item
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.name_input = QLineEdit()
        self.description_input = QLineEdit()
        self.price_input = QDoubleSpinBox()
        self.price_input.setPrefix("$")
        self.price_input.setMinimum(0.0)
        self.price_input.setMaximum(999999.99)
        self.price_input.setDecimals(2)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(0)
        self.quantity_input.setMaximum(99999)
        self.buy_multiplier_input = QDoubleSpinBox() # New input for multiplier
        self.buy_multiplier_input.setMinimum(0.1) # Cannot buy less than 0.1
        self.buy_multiplier_input.setMaximum(999.0)
        self.buy_multiplier_input.setDecimals(1) # Allow one decimal place
        self.buy_multiplier_input.setSingleStep(0.1) # Step by 0.1

        layout.addRow("Name:", self.name_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Price:", self.price_input)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Buy Multiplier:", self.buy_multiplier_input) # Add to form

        if self.item:
            self.name_input.setText(self.item.name)
            self.description_input.setText(self.item.description)
            self.price_input.setValue(self.item.price)
            self.quantity_input.setValue(self.item.quantity)
            self.buy_multiplier_input.setValue(self.item.buy_multiplier) # Set existing value
        else:
            self.buy_multiplier_input.setValue(1.0) # Default for new items

        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def get_item_data(self):
        name = self.name_input.text().strip()
        description = self.description_input.text().strip()
        price = self.price_input.value()
        quantity = self.quantity_input.value()
        buy_multiplier = self.buy_multiplier_input.value() # Get multiplier value

        if not name:
            QMessageBox.warning(self, "Input Error", "Item name cannot be empty.")
            return None
        if buy_multiplier <= 0:
            QMessageBox.warning(self, "Input Error", "Buy multiplier must be greater than 0.")
            return None

        return ShopItem(name, description, price, quantity, buy_multiplier)

# --- Shop View Page ---
class ShopView(QWidget):
    item_purchased = pyqtSignal() # Signal to notify main app of purchase

    def __init__(self, shop_items, parent=None):
        super().__init__(parent)
        self.shop_items = shop_items # Reference to the shared item list
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.shop_list_widget = QListWidget()
        self.shop_list_widget.itemClicked.connect(self.display_item_details)
        self.shop_list_widget.itemSelectionChanged.connect(self.update_buy_button_state) # Connect for button state
        layout.addWidget(self.shop_list_widget)

        self.details_label = QLabel("Select an item to see its details.")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label)

        self.buy_button = QPushButton("Buy Selected Item")
        self.buy_button.clicked.connect(self.buy_item)
        self.buy_button.setEnabled(False) # Initially disabled
        layout.addWidget(self.buy_button)

        self.setLayout(layout)
        self.update_shop_list()

    def update_shop_list(self):
        self.shop_list_widget.clear()
        for item in self.shop_items:
            # Display current quantity and the buy multiplier
            item_text = f"<html><b>{item.name}</b> - ${item.price:.2f} (x{item.quantity}) - Buy x{item.buy_multiplier:.1f}</html>"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item) # Store the actual item object
            self.shop_list_widget.addItem(list_item)
        self.details_label.setText("Select an item to see its details.") # Reset details
        self.update_buy_button_state() # Ensure button state is correct after list update

    def display_item_details(self, item_widget):
        item = item_widget.data(Qt.ItemDataRole.UserRole)
        if item:
            details_text = (
                f"<html>"
                f"<b>Name:</b> {item.name}<br>"
                f"<b>Description:</b> {item.description}<br>"
                f"<b>Price:</b> ${item.price:.2f}<br>"
                f"<b>Quantity:</b> {item.quantity}<br>"
                f"<b>Buy Multiplier:</b> {item.buy_multiplier:.1f}"
                f"</html>"
            )
            self.details_label.setText(details_text)

    def update_buy_button_state(self):
        selected_item_widget = self.shop_list_widget.currentItem()
        if selected_item_widget:
            item = selected_item_widget.data(Qt.ItemDataRole.UserRole)
            # Enable buy button only if an item is selected AND its quantity is greater than 0
            self.buy_button.setEnabled(item.quantity > 0)
        else:
            self.buy_button.setEnabled(False)

    def buy_item(self):
        selected_item_widget = self.shop_list_widget.currentItem()
        if not selected_item_widget:
            QMessageBox.warning(self, "No Item Selected", "Please select an item to buy.")
            return

        item_to_buy = selected_item_widget.data(Qt.ItemDataRole.UserRole)

    def buy_item(self):
        selected_item_widget = self.shop_list_widget.currentItem()
        if not selected_item_widget:
            QMessageBox.warning(self, "No Item Selected", "Please select an item to buy.")
            return

        item_to_buy = selected_item_widget.data(Qt.ItemDataRole.UserRole)

        if item_to_buy.quantity <= 0:
            QMessageBox.information(self, "Out of Stock", f"'{item_to_buy.name}' is out of stock.")
            return

        # Calculate new quantity (this will likely be a float)
        new_quantity_float = item_to_buy.quantity - item_to_buy.buy_multiplier

        if new_quantity_float < 0:
            # If buying the multiplier would result in negative, set to 0 and inform
            QMessageBox.information(self, "Partial Purchase",
                                    f"Not enough '{item_to_buy.name}' to buy {item_to_buy.buy_multiplier:.1f}. "
                                    f"Buying remaining {item_to_buy.quantity:.1f} units.")
            item_to_buy.quantity = 0 # Ensure it's an integer 0
        else:
            # Cast the new quantity back to an integer before assigning it.
            # You might want to round or floor depending on desired behavior.
            # For simplicity, let's floor it (take the whole number part).
            item_to_buy.quantity = int(new_quantity_float)
            QMessageBox.information(self, "Purchase Successful",
                                    f"Bought {item_to_buy.buy_multiplier:.1f} units of '{item_to_buy.name}'. "
                                    f"Remaining: {item_to_buy.quantity}") # Note: Displaying int quantity

        # Emit signal to trigger update in both views
        self.item_purchased.emit()


# --- Management View Page ---
class ManagementView(QWidget):
    items_changed = pyqtSignal() # Signal to notify ShopView of changes

    def __init__(self, shop_items, parent=None):
        super().__init__(parent)
        self.shop_items = shop_items # Reference to the shared item list
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Item List
        self.management_list_widget = QListWidget()
        layout.addWidget(self.management_list_widget)

        # Buttons for Add, Edit, Delete
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Add Item")
        edit_button = QPushButton("Edit Item")
        delete_button = QPushButton("Delete Item")
        export_button = QPushButton("Export to JSON")
        import_button = QPushButton("Import from JSON")

        add_button.clicked.connect(self.add_item)
        edit_button.clicked.connect(self.edit_item)
        delete_button.clicked.connect(self.delete_item)
        export_button.clicked.connect(self.export_items)
        import_button.clicked.connect(self.import_items)

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch() # Push buttons to the left
        buttons_layout.addWidget(import_button)
        buttons_layout.addWidget(export_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.update_management_list()

    def update_management_list(self):
        self.management_list_widget.clear()
        for item in self.shop_items:
            item_text = str(item)
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item) # Store the actual item object
            self.management_list_widget.addItem(list_item)
        self.items_changed.emit() # Notify ShopView

    def add_item(self):
        dialog = ItemDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_item = dialog.get_item_data()
            if new_item:
                self.shop_items.append(new_item)
                self.update_management_list()
                QMessageBox.information(self, "Success", f"Item '{new_item.name}' added.")

    def edit_item(self):
        selected_item_widget = self.management_list_widget.currentItem()
        if not selected_item_widget:
            QMessageBox.warning(self, "No Item Selected", "Please select an item to edit.")
            return

        original_item = selected_item_widget.data(Qt.ItemDataRole.UserRole)
        dialog = ItemDialog(item=original_item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_item_data = dialog.get_item_data()
            if updated_item_data:
                # Find the index of the original item and replace it
                try:
                    index = self.shop_items.index(original_item)
                    self.shop_items[index] = updated_item_data
                    self.update_management_list()
                    QMessageBox.information(self, "Success", f"Item '{updated_item_data.name}' updated.")
                except ValueError:
                    QMessageBox.critical(self, "Error", "Could not find original item for update.")

    def delete_item(self):
        selected_item_widget = self.management_list_widget.currentItem()
        if not selected_item_widget:
            QMessageBox.warning(self, "No Item Selected", "Please select an item to delete.")
            return

        item_to_delete = selected_item_widget.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, 'Delete Item',
                                     f"Are you sure you want to delete '{item_to_delete.name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.shop_items.remove(item_to_delete)
            self.update_management_list()
            QMessageBox.information(self, "Success", f"Item '{item_to_delete.name}' deleted.")

    def export_items(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Shop Data", "shop_items.json",
                                                    "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                data_to_export = [item.to_dict() for item in self.shop_items]
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(data_to_export, f, indent=4, ensure_ascii=False)
                QMessageBox.information(self, "Export Successful", f"Shop data exported to:\n{file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {e}")

    def import_items(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Shop Data", "",
                                                    "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)

                if not isinstance(imported_data, list):
                    raise ValueError("JSON file does not contain a list of items.")

                new_items = []
                for item_data in imported_data:
                    new_items.append(ShopItem.from_dict(item_data))

                # Clear existing items and add new ones
                self.shop_items.clear()
                self.shop_items.extend(new_items)
                self.update_management_list()
                QMessageBox.information(self, "Import Successful", f"Shop data imported from:\n{file_name}")
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Import Error", "Invalid JSON file format.")
            except ValueError as ve:
                QMessageBox.critical(self, "Import Error", f"Data format error: {ve}")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import data: {e}")

# --- Main Application Window ---
class ShopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shop Management System")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height

        self.shop_items = [] # Central list to hold ShopItem objects

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Shop View
        self.shop_view = ShopView(self.shop_items)
        main_layout.addWidget(self.shop_view)

        # Management View
        self.management_view = ManagementView(self.shop_items)
        main_layout.addWidget(self.management_view)

        # Connect signals for updates
        self.management_view.items_changed.connect(self.shop_view.update_shop_list)
        # New: Connect shop view's purchase signal to refresh all views
        self.shop_view.item_purchased.connect(self.refresh_all_views)

        # Tabs or buttons to switch views
        switch_layout = QHBoxLayout()
        self.shop_button = QPushButton("Shop View")
        self.manage_button = QPushButton("Management View")

        self.shop_button.clicked.connect(self.show_shop_view)
        self.manage_button.clicked.connect(self.show_management_view)

        switch_layout.addWidget(self.shop_button)
        switch_layout.addWidget(self.manage_button)
        main_layout.addLayout(switch_layout)

        # Initially show Shop View
        self.show_shop_view()

    def show_shop_view(self):
        self.shop_view.show()
        self.management_view.hide()
        self.shop_button.setEnabled(False)
        self.manage_button.setEnabled(True)
        self.shop_view.update_shop_list() # Ensure shop list is updated when switching

    def show_management_view(self):
        self.shop_view.hide()
        self.management_view.show()
        self.shop_button.setEnabled(True)
        self.manage_button.setEnabled(False)
        self.management_view.update_management_list() # Ensure management list is updated when switching

    def refresh_all_views(self):
        """Refreshes both the shop and management views."""
        self.shop_view.update_shop_list()
        self.management_view.update_management_list()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShopApp()
    window.show()
    sys.exit(app.exec())