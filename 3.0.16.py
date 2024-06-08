import sys
import random
import json
import sqlite3
import win32com.client
import re
from PyQt5 import QtWidgets, QtCore, QtGui, QtPrintSupport


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USCAD")
        self.resize(1000, 800)  # Increased width to accommodate new columns
        self.settings = self.load_settings()
        self.custom_domains = self.settings.get('custom_domains', [])
        self.predefined_domains = self.settings.get('predefined_domains', ["npt-c.ru", "wheil.com", "albacore.ru"])

        self.init_db()  # Initialize the SQLite database

        main_layout = QtWidgets.QVBoxLayout()
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.tab_widget = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.setup_generator_tab()
        self.setup_database_tab()
        self.setup_settings_tab()

        if self.settings.get("dark_theme", False):
            self.apply_dark_theme()

        self.update_database_view()  # Ensure DB is populated at startup
        self.toggle_dark_theme()  # Применение темы на основе сохраненных настроек

    def init_db(self):
        self.conn = sqlite3.connect("uscad.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                pc_login TEXT,
                pc_password TEXT,
                domain TEXT,
                email TEXT,
                password TEXT
            )
        ''')
        self.conn.commit()

    def update_checkboxes(self):
        # Clear existing checkboxes
        for i in reversed(range(self.checkbox_layout.count())):
            self.checkbox_layout.itemAt(i).widget().setParent(None)

        # Add new checkboxes for each domain
        for domain in self.predefined_domains + self.custom_domains:
            checkbox = QtWidgets.QCheckBox(domain)
            checkbox.setChecked(False)
            self.checkbox_layout.addWidget(checkbox)

    def setup_generator_tab(self):
        generator_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(generator_tab, "Генератор")
        generator_layout = QtWidgets.QVBoxLayout()
        generator_tab.setLayout(generator_layout)

        title_label = QtWidgets.QLabel("Генератор информации пользователя")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        generator_layout.addWidget(title_label)

        form_layout = QtWidgets.QFormLayout()
        generator_layout.addLayout(form_layout)

        self.full_name_field = QtWidgets.QLineEdit()
        self.full_name_field.setMinimumHeight(40)  # Increase the height of the field
        self.full_name_field.setStyleSheet("font-size: 16px;")  # Adjust the font size
        full_name_label = QtWidgets.QLabel("Фамилия и Имя:")
        full_name_label.setStyleSheet("font-size: 14px; font-weight: bold;")  # Increase the font size of the label
        form_layout.addRow(full_name_label, self.full_name_field)
    
        self.checkbox_layout = QtWidgets.QVBoxLayout()
        generator_layout.addLayout(self.checkbox_layout)
        self.update_checkboxes()

        self.output_field = QtWidgets.QTextEdit()
        self.output_field.setReadOnly(True)
        generator_layout.addWidget(self.output_field)

        buttons_layout = QtWidgets.QHBoxLayout()
        generate_button = QtWidgets.QPushButton("Сгенерировать")
        copy_button = QtWidgets.QPushButton("Копировать")
        add_to_db_button = QtWidgets.QPushButton("Добавить в базу")
        print_button = QtWidgets.QPushButton("Печатать")
        send_mail_button = QtWidgets.QPushButton("Отправить по почте")

        for btn in [generate_button, copy_button, add_to_db_button, print_button, send_mail_button]:
            btn.setStyleSheet("font-size: 14px; padding: 10px;")
            buttons_layout.addWidget(btn)

        generator_layout.addLayout(buttons_layout)

        generate_button.clicked.connect(self.generate_info)
        copy_button.clicked.connect(self.copy_info)
        add_to_db_button.clicked.connect(self.add_to_db)
        print_button.clicked.connect(self.print_info)
        send_mail_button.clicked.connect(self.send_email)

    def setup_database_tab(self):
        database_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(database_tab, "База данных")
        database_layout = QtWidgets.QVBoxLayout()
        database_tab.setLayout(database_layout)

        search_layout = QtWidgets.QHBoxLayout()
        search_label = QtWidgets.QLabel("Поиск:")
        self.search_field = QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Введите имя для поиска...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_field)
        database_layout.addLayout(search_layout)

        self.database_view = QtWidgets.QTableView()
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["ID", "ФИ", "Логин ПК", "Пароль ПК", "Домен", "Email", "Пароль"])
        self.database_view.setModel(self.model)
        self.database_view.verticalHeader().setVisible(False)
        self.database_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.database_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.database_view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.database_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.database_view.customContextMenuRequested.connect(self.show_context_menu)
        database_layout.addWidget(self.database_view)

        self.database_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.search_field.textChanged.connect(self.update_database_view)

        self.deleted_rows = []  # Keep track of deleted rows for undo operation

    def setup_settings_tab(self):
        settings_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(settings_tab, "Настройки")
        settings_layout = QtWidgets.QVBoxLayout()
        settings_tab.setLayout(settings_layout)

        # Theme settings
        theme_group = QtWidgets.QGroupBox("Тема")
        theme_layout = QtWidgets.QVBoxLayout()
        theme_group.setLayout(theme_layout)
        self.dark_theme_checkbox = QtWidgets.QCheckBox("Темная тема")
        self.dark_theme_checkbox.setChecked(self.settings.get("dark_theme", False))
        self.dark_theme_checkbox.stateChanged.connect(self.toggle_dark_theme)
        theme_layout.addWidget(self.dark_theme_checkbox)
        settings_layout.addWidget(theme_group)

        # Password complexity settings
        password_group = QtWidgets.QGroupBox("Сложность пароля")
        password_layout = QtWidgets.QVBoxLayout()
        password_group.setLayout(password_layout)
        self.complexity_combo = QtWidgets.QComboBox()
        self.complexity_combo.addItems(["Низкая", "Средняя", "Высокая"])
        self.complexity_combo.setCurrentIndex(self.settings.get("password_complexity", 1))
        password_layout.addWidget(self.complexity_combo)
        settings_layout.addWidget(password_group)

        # Domain settings
        domain_group = QtWidgets.QGroupBox("Домены")
        domain_layout = QtWidgets.QVBoxLayout()
        domain_group.setLayout(domain_layout)
        edit_domains_button = QtWidgets.QPushButton("Редактировать домены")
        edit_domains_button.clicked.connect(self.show_domain_dialog)
        domain_layout.addWidget(edit_domains_button)
        settings_layout.addWidget(domain_group)

        # Apply theme styles
        if self.settings.get("dark_theme", False):
            self.apply_dark_theme()
        else:
            self.apply_light_theme()




    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_settings(self):
        with open("settings.json", "w") as f:
            settings = {
                "dark_theme": self.dark_theme_checkbox.isChecked(),
                "custom_domains": self.custom_domains,
                "predefined_domains": self.predefined_domains,
                "password_complexity": self.complexity_combo.currentIndex()
            }
            json.dump(settings, f)

    def apply_light_theme(self):
        light_theme = """
        QWidget {
            background-color: #f0f0f0;
            color: #000000;
            border-radius: 5px;
        }
        QLineEdit, QTextEdit, QComboBox, QTableView {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton {
            background-color: #cccccc;
            color: #000000;
            border: 1px solid #999999;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #999999;
        }
        QPushButton:pressed {
            background-color: #666666;
        }
        QCheckBox {
            color: #000000;
            padding: 5px;
        }
        QComboBox {
        background-color: #cccccc;
        color: #000000;
        border: 1px solid #999999;
        border-radius: 5px;
        padding: 5px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: url(path_to_down_arrow_image.png);
            width: 16px;
            height: 16px;
        }
        QComboBox:hover {
            background-color: #cccccc;
        }
        QComboBox QAbstractItemView {
            background-color: #cccccc;
            border: 1px solid #666666;
            selection-background-color: #666666;
        }
        QDialog {
            background-color: #f0f0f0;
            color: #000000;
            border-radius: 5px;
        }
        QTabWidget::pane {
            border: 1px solid #999999;
            border-radius: 5px;
        }
        QTabBar::tab {
            background-color: #cccccc;
            color: #000000;
            padding: 10px;
            border: 1px solid #999999;
            font-size: 12px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QTabBar::tab:selected {
            background-color: #999999;
        }
        QHeaderView::section {
            background-color: #cccccc;
            color: #000000;
            border: 1px solid #999999;
            padding: 4px;
            font-size: 12px;
            border-radius: 5px;
        }
        QMenu {
            background-color: #cccccc;
            color: #000000;
            border: 1px solid #999999;
            border-radius: 5px;
        }
        QMenu::item {
            padding: 8px 16px;
        }
        QMenu::item:selected {
            background-color: #999999;
        }
        QMainWindow::separator {
            background-color: #f0f0f0;
            width: 1px;
        }
        """
        self.setStyleSheet(light_theme)
        self.database_view.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #cccccc; border-radius: 5px; }")
        self.database_view.verticalHeader().setStyleSheet("QHeaderView::section { background-color: #cccccc; border-radius: 5px; }")


    def apply_dark_theme(self):
        dark_theme = """
        QWidget {
            background-color: #2e2e2e;
            color: #f0f0f0;
            border-radius: 5px;
        }
        QLineEdit, QTextEdit, QComboBox, QTableView {
            background-color: #3c3c3c;
            color: #f0f0f0;
            border: 1px solid #4a4a4a;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton {
            background-color: #4a4a4a;
            color: #f0f0f0;
            border: 1px solid #5a5a5a;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #5a5a5a;
        }
        QPushButton:pressed {
            background-color: #6a6a6a;
        }
        QCheckBox {
            color: #f0f0f0;
            padding: 5px;
        }
        QComboBox {
        background-color: #3c3c3c;
        color: #f0f0f0;
        border: 1px solid #4a4a4a;
        border-radius: 5px;
        padding: 5px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: url(path_to_dark_arrow_image.png);
            width: 16px;
            height: 16px;
        }
        QComboBox:hover {
            background-color: #5a5a5a;
        }
        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            border: 1px solid #4a4a4a;
            selection-background-color: #4a4a4a;
        }
        QDialog {
            background-color: #2e2e2e;
            color: #f0f0f0;
            border-radius: 5px;
        }
        QTabWidget::pane {
            border: 1px solid #5a5a5a;
            border-radius: 5px;
        }
        QTabBar::tab {
            background-color: #4a4a4a;
            color: #f0f0f0;
            padding: 10px;
            border: 1px solid #5a5a5a;
            font-size: 12px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QTabBar::tab:selected {
            background-color: #5a5a5a;
        }
        QHeaderView::section {
            background-color: #3c3c3c;
            color: #f0f0f0;
            border: 1px solid #4a4a4a;
            padding: 4px;
            font-size: 12px;
            border-radius: 5px;
        }
        QMenu {
            background-color: #3c3c3c;
            color: #f0f0f0;
            border: 1px solid #4a4a4a;
            border-radius: 5px;
        }
        QMenu::item {
            padding: 8px 16px;
        }
        QMenu::item:selected {
            background-color: #5a5a5a;
        }
        QMainWindow::separator {
            background-color: #2e2e2e;
            width: 1px;
        }
        """
        self.setStyleSheet(dark_theme)
        self.database_view.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #3c3c3c; }")
        self.database_view.verticalHeader().setStyleSheet("QHeaderView::section { background-color: #3c3c3c; }")





    def toggle_dark_theme(self):
        if self.dark_theme_checkbox.isChecked():
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
        self.save_settings()

    def show_domain_dialog(self):
        dialog = DomainDialog(self.predefined_domains + self.custom_domains, self.dark_theme_checkbox.isChecked())
        if dialog.exec_():
            domains = dialog.get_domains()
            predefined_set = set(self.predefined_domains)
            self.custom_domains = [domain for domain in domains if domain not in predefined_set]
            self.predefined_domains = [domain for domain in domains if domain in predefined_set]
            self.update_checkboxes()
            self.save_settings()

    def generate_info(self):
        full_name = self.full_name_field.text().strip()
        name_parts = full_name.split(" ")

        if len(name_parts) < 2:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите имя и фамилию через пробел.")
            return

        last_name, first_name = name_parts[0].capitalize(), name_parts[1].capitalize()
        password = self.generate_password()

        # Email format: first letter of first name + last name
        email_firstpart = f"{self.transliterate(first_name[0].lower())}.{self.transliterate(last_name.lower())}"

        self.generated_info = {
            "name": f"{last_name} {first_name}",
            "emails": [],
            "password": password,
            "pc_login": email_firstpart
        }

        output_text = f"{self.generated_info['name']}\n{email_firstpart}\n{password}\n\n"

        # Add emails with selected domains
        for i in range(self.checkbox_layout.count()):
            checkbox = self.checkbox_layout.itemAt(i).widget()
            if checkbox.isChecked():
                email = f"{email_firstpart}@{checkbox.text()}"
                self.generated_info["emails"].append(email)
                output_text += f"{email}\n{password}\n\n"

        self.output_field.setText(output_text)

    def add_to_db(self):
        if not hasattr(self, 'generated_info') or not self.generated_info.get("emails"):
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте информацию!")
            return

        name = self.generated_info["name"]
        pc_login = self.generated_info["pc_login"]
        pc_password = self.generated_info["password"]

        # Insert the main user information into the database
        self.cursor.execute("INSERT INTO users (name, pc_login, pc_password) VALUES (?, ?, ?)", (name, pc_login, pc_password))
        user_id = self.cursor.lastrowid

        # Insert email and password for each domain
        for email in self.generated_info["emails"]:
            domain = email.split('@')[1]
            self.cursor.execute("INSERT INTO users (name, pc_login, pc_password, domain, email, password) VALUES (?, ?, ?, ?, ?, ?)", (name, pc_login, pc_password, domain, email, pc_password))

        self.conn.commit()
        QtWidgets.QMessageBox.information(self, "Успешно", "Информация добавлена в базу данных.")
        self.update_database_view()
        
        

    def print_info(self):
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
        dialog = QtPrintSupport.QPrintDialog(printer, self)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            painter = QtGui.QPainter(printer)
            rect = painter.viewport()
            size = self.output_field.document().size()
            size.scale(rect.size(), QtCore.Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.output_field.document().documentLayout().frameBoundingRect())
            self.output_field.document().print_(painter)
            painter.end()

    def send_email(self):
        if not hasattr(self, 'generated_info') or self.generated_info.get("emails"):
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте информацию!")
            return

        # Prepare email body
        subject = "User Information"
        body = f"Name: {self.generated_info['name']}\nPassword: {self.generated_info['password']}\n"
        body += "\n".join(self.generated_info["emails"])

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        mail.Body = body
        mail.Display(True)

    def update_database_view(self):
        search_term = self.search_field.text().strip()
        query = "SELECT id, name, pc_login, pc_password, domain, email, password FROM users"
        if search_term:
            if search_term[0].islower():
                name_search_term = search_term[0].upper() + search_term[1:]
            else:
                name_search_term = search_term
            query += f" WHERE name LIKE ? OR pc_login LIKE ? OR pc_password LIKE ? OR domain LIKE ? OR email LIKE ? OR password LIKE ?"
            self.cursor.execute(query, (
                f"%{name_search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%",
                f"%{search_term}%"))
        else:
            self.cursor.execute(query)
        self.model.setRowCount(0)
        for row_id, row_data in enumerate(self.cursor.fetchall()):
            for column_id, data in enumerate(row_data):
                item = QtGui.QStandardItem(str(data))
                self.model.setItem(row_id, column_id, item)
                    
    def generate_password(self):
        complexity = self.complexity_combo.currentIndex()
        length = [8, 12, 16][complexity]
        letters = "abcdefghijklmnopqrstuvwxyz"
        numbers = "0123456789"
        symbols = "!@#$%^&*()-_=+"
        password_characters = []

        if complexity == 0:  # Low complexity
            password_characters = random.sample(letters + numbers, length)
        elif complexity == 1:  # Medium complexity
            password_characters = random.sample(letters + letters.upper() + numbers, length)
        elif complexity == 2:  # High complexity
            password_characters = random.sample(letters + letters.upper() + numbers + symbols, length)

        return ''.join(password_characters)

    def transliterate(self, text):
        exceptions = {"ъ": "", "ь": ""}
        translit_table = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch","ы": "y", "э": "e", "ю": "yu", "я": "ia"}
        for char in text:
            if char in exceptions:
                text = text.replace(char, exceptions[char])
            elif char in translit_table:
                text = text.replace(char, translit_table[char])
        return text

    def copy_info(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.output_field.toPlainText())
        QtWidgets.QMessageBox.information(self, "Скопировано", "Информация скопирована в буфер обмена!")

    def show_context_menu(self, position):
        menu = QtWidgets.QMenu()
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")
        undo_action = menu.addAction("Отменить удаление")
        print_action = menu.addAction("Печатать")
        send_mail_action = menu.addAction("Отправить по почте")

        action = menu.exec_(self.database_view.viewport().mapToGlobal(position))

        if action == edit_action:
            self.edit_user()
        elif action == delete_action:
            self.delete_user_from_db()
        elif action == undo_action:
            self.undo_delete_user_from_db()
        elif action == print_action:
            self.print_selected_user()
        elif action == send_mail_action:
            self.send_selected_user()

    def edit_user(self):
        selected_indexes = self.database_view.selectionModel().selectedRows()
        if not selected_indexes:
            return

        row_id = selected_indexes[0].row()
        user_id = int(self.model.item(row_id, 0).text())
        user_data = [self.model.item(row_id, col).text() for col in range(self.model.columnCount())]

        dialog = EditUserDialog(user_data, self.dark_theme_checkbox.isChecked())
        if dialog.exec_():
            updated_data = dialog.get_user_data()
            self.cursor.execute("UPDATE users SET name = ?, pc_login = ?, pc_password = ?, domain = ?, email = ?, password = ? WHERE id = ?",
                            (*updated_data[1:], user_id))
            self.conn.commit()
            self.update_database_view()

    def delete_user_from_db(self):
        selected_indexes = self.database_view.selectionModel().selectedRows()
        for index in sorted(selected_indexes, reverse=True):
            row_id = index.row()
            user_id = self.model.item(row_id, 0).text()
            # Store deleted row for undo
            deleted_row = [self.model.item(row_id, col).text() for col in range(self.model.columnCount())]
            self.deleted_rows.append((user_id, deleted_row))
            self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()
        self.update_database_view()

    def undo_delete_user_from_db(self):
        if not self.deleted_rows:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Нет удаленных записей для восстановления.")
            return

        last_deleted = self.deleted_rows.pop()
        user_id, row_data = last_deleted
        try:
            self.cursor.execute(
                "INSERT INTO users (id, name, pc_login, pc_password, domain, email, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, *row_data[1:]))
            self.conn.commit()
        except sqlite3.IntegrityError:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Запись с ID {user_id} уже существует.")
        self.update_database_view()

    def print_selected_user(self):
        selected_indexes = self.database_view.selectionModel().selectedRows()
        if not selected_indexes:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите запись для печати.")
            return

        row_id = selected_indexes[0].row()
        user_data = [self.model.item(row_id, col).text() for col in range(self.model.columnCount())]
        output_text = f"ID: {user_data[0]}\nФИ: {user_data[1]}\nЛогин ПК: {user_data[2]}\nПароль ПК: {user_data[3]}\nДомен: {user_data[4]}\nEmail: {user_data[5]}\nПароль: {user_data[6]}"

        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
        dialog = QtPrintSupport.QPrintDialog(printer, self)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            painter = QtGui.QPainter(printer)
            rect = painter.viewport()
            painter.setViewport(rect.x(), rect.y(), 600, 800)
            painter.setWindow(0, 0, 600, 800)
            painter.drawText(QtCore.QRectF(0, 0, 600, 800), QtCore.Qt.AlignLeft | QtCore.Qt.TextWordWrap, output_text)
            painter.end()

    def send_selected_user(self):
        selected_indexes = self.database_view.selectionModel().selectedRows()
        if not selected_indexes:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите запись для отправки по почте.")
            return

        row_id = selected_indexes[0].row()
        user_data = [self.model.item(row_id, col).text() for col in range(self.model.columnCount())]
        output_text = f"ID: {user_data[0]}\nФИ: {user_data[1]}\nЛогин ПК: {user_data[2]}\нПароль ПК: {user_data[3]}\нДомен: {user_data[4]}\нEmail: {user_data[5]}\нПароль: {user_data[6]}"

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.Subject = "User Information"
        mail.Body = output_text
        mail.Display(True)        
        


class DomainDialog(QtWidgets.QDialog):
    def __init__(self, domains, dark_theme=False):
        super().__init__()
        self.setWindowTitle("Редактирование доменов")
        self.setFixedSize(400, 300)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.domains_list = QtWidgets.QListWidget()
        for domain in sorted(set(domains)):
            self.domains_list.addItem(domain)
        layout.addWidget(self.domains_list)

        add_layout = QtWidgets.QHBoxLayout()
        self.new_domain_line_edit = QtWidgets.QLineEdit()
        self.new_domain_line_edit.setPlaceholderText("Новый домен")
        add_button = QtWidgets.QPushButton("Добавить")
        add_button.setStyleSheet("font-size: 10px; padding: 8px;")
        add_layout.addWidget(self.new_domain_line_edit)
        add_layout.addWidget(add_button)
        layout.addLayout(add_layout)

        remove_button = QtWidgets.QPushButton("Удалить")
        remove_button.setStyleSheet("font-size: 10px; padding: 8px;")
        layout.addWidget(remove_button)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        add_button.clicked.connect(self.add_domain)
        remove_button.clicked.connect(self.remove_domain)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        if dark_theme:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
            

    def apply_dark_theme(self):
        dark_theme_stylesheet = """
        QDialog {
            background-color: #2e2e2e;
            color: #f0f0f0;
            border-radius: 5px;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #3c3c3c;
            color: #f0f0f0;
            border: 1px solid #4a4a4a;
            border-radius: 5px;
            padding: 5px;
        }
        QListWidget, QLineEdit {
            background-color: #3c3c3c;
            color: #f0f0f0;
            border: 1px solid #4a4a4a;
        }
        QPushButton {
            background-color: #4a4a4a;
            color: #f0f0f0;
            border: 1px solid #5a5a5a;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #5a5a5a;
        }
        QPushButton:pressed {
            background-color: #6a6a6a;
        }
        QDialogButtonBox {
            background-color: #4a4a4a;
            border: 1px solid #5a5a5a;
            color: #f0f0f0;
        }
        """
        self.setStyleSheet(dark_theme_stylesheet)

    def apply_light_theme(self):
        light_theme_stylesheet = """
                QWidget {
            background-color: #ffffff;
            color: #000000;
            border-radius: 5px;
        }
        QLineEdit, QTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
        }
        QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton {
            background-color: #cccccc;
            color: #000000;
            border: 1px solid #999999;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        }
        QPushButton#edit_domains_button {
            background-color: #cccccc;
            color: #000000;
            border: 1px solid #999999;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        }
        QDialog {
            background-color: #f0f0f0;
            color: #000000;
            border-radius: 5px;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton {
            background-color: #cccccc;
            color: #000000;
            border: 1px solid #999999;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #999999;
        }
        QPushButton:pressed {
            background-color: #666666;
        }
        """
        self.setStyleSheet(light_theme_stylesheet)




    def add_domain(self):
        new_domain = self.new_domain_line_edit.text().strip()
        if new_domain and not any(self.domains_list.item(i).text() == new_domain for i in range(self.domains_list.count())):
            self.domains_list.addItem(new_domain)
            self.new_domain_line_edit.clear()

    def remove_domain(self):
        selected_items = self.domains_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.domains_list.takeItem(self.domains_list.row(item))

    def get_domains(self):
        return [self.domains_list.item(i).text() for i in range(self.domains_list.count())]


class EditUserDialog(QtWidgets.QDialog):
    def __init__(self, user_data, dark_theme=False):
        super().__init__()
        self.setWindowTitle("Редактировать пользователя")
        self.setFixedSize(400, 300)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        form_layout = QtWidgets.QFormLayout()
        self.id_edit = QtWidgets.QLineEdit(user_data[0])
        self.id_edit.setReadOnly(True)
        self.name_edit = QtWidgets.QLineEdit(user_data[1])
        self.pc_login_edit = QtWidgets.QLineEdit(user_data[2])
        self.pc_password_edit = QtWidgets.QLineEdit(user_data[3])
        self.domain_edit = QtWidgets.QLineEdit(user_data[4])
        self.email_edit = QtWidgets.QLineEdit(user_data[5])
        self.password_edit = QtWidgets.QLineEdit(user_data[6])

        # Create separate label widgets and apply stylesheet
        label_style = "color: #f0f0f0;" if dark_theme else ""
        id_label = QtWidgets.QLabel("ID:")
        id_label.setStyleSheet(label_style)
        name_label = QtWidgets.QLabel("ФИ:")
        name_label.setStyleSheet(label_style)
        pc_login_label = QtWidgets.QLabel("Логин ПК:")
        pc_login_label.setStyleSheet(label_style)
        pc_password_label = QtWidgets.QLabel("Пароль ПК:")
        pc_password_label.setStyleSheet(label_style)
        domain_label = QtWidgets.QLabel("Домен:")
        domain_label.setStyleSheet(label_style)
        email_label = QtWidgets.QLabel("Email:")
        email_label.setStyleSheet(label_style)
        password_label = QtWidgets.QLabel("Пароль:")
        password_label.setStyleSheet(label_style)

        form_layout.addRow(id_label, self.id_edit)
        form_layout.addRow(name_label, self.name_edit)
        form_layout.addRow(pc_login_label, self.pc_login_edit)
        form_layout.addRow(pc_password_label, self.pc_password_edit)
        form_layout.addRow(domain_label, self.domain_edit)
        form_layout.addRow(email_label, self.email_edit)
        form_layout.addRow(password_label, self.password_edit)

        layout.addLayout(form_layout)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        if dark_theme:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def apply_dark_theme(self):
        dark_theme_stylesheet = """
        QDialog {
            background-color: #2e2e2e;
            color: #f0f0f0;
            border-radius: 5px;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #3c3c3c;
            color: #f0f0f0;
            border: 1px solid #4a4a4a;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton {
            background-color: #4a4a4a;
            color: #f0f0f0;
            border: 1px solid #5a5a5a;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #5a5a5a;
        }
        QPushButton:pressed {
            background-color: #6a6a6a;
        }
        """
        self.setStyleSheet(dark_theme_stylesheet)

    def apply_light_theme(self):
        light_theme_stylesheet = """
        QDialog {
            background-color: #f0f0f0;
            color: #000000;
            border-radius: 5px;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton {
            background-color: #cccccc;
            color: #000000;
            border: 1px solid #999999;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #999999;
        }
        QPushButton:pressed {
            background-color: #666666;
        }
        """
        self.setStyleSheet(light_theme_stylesheet)



    def get_user_data(self):
        return [
            self.id_edit.text(),
            self.name_edit.text(),
            self.pc_login_edit.text(),
            self.pc_password_edit.text(),
            self.domain_edit.text(),
            self.email_edit.text(),
            self.password_edit.text()
        ]


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
