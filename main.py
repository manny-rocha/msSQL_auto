import pyodbc
import os
import csv
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget, QLabel, QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QCheckBox
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
import sys
import logging
import dotenv

from logger import setup_logging

# Set up logging config
setup_logging()

# Init logger
logger = logging.getLogger(__name__)

dotenv.load_dotenv()


class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)
        self.rules = []

        # SQL keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("blue"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "\\bSELECT\\b", "\\bFROM\\b", "\\bWHERE\\b", "\\bAND\\b", "\\bOR\\b",
            "\\bNOT\\b", "\\bNULL\\b", "\\bIS\\b", "\\bLIKE\\b", "\\bIN\\b",
            "\\bEXISTS\\b", "\\bALL\\b", "\\bANY\\b", "\\bDISTINCT\\b", "\\bGROUP\\b",
            "\\bBY\\b", "\\bORDER\\b", "\\bHAVING\\b", "\\bUNION\\b", "\\bJOIN\\b",
            "\\bINNER\\b", "\\bLEFT\\b", "\\bRIGHT\\b", "\\bON\\b", "\\bINSERT\\b",
            "\\bINTO\\b", "\\bVALUES\\b", "\\bUPDATE\\b", "\\bSET\\b", "\\bDELETE\\b",
            "\\bCREATE\\b", "\\bALTER\\b", "\\bTABLE\\b", "\\bDROP\\b", "\\bPRIMARY\\b",
            "\\bKEY\\b", "\\bFOREIGN\\b", "\\bCHECK\\b", "\\bDEFAULT\\b", "\\bINDEX\\b",
            "\\bVIEW\\b", "\\bCONSTRAINT\\b", "\\bTRIGGER\\b", "\\bCASCADE\\b"
        ]

        for keyword in keywords:
            pattern = QRegExp(keyword)
            self.rules.append((pattern, keyword_format))

        # Single line comments
        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(QColor("green"))
        single_line_comment_pattern = QRegExp("--[^\n]*")
        self.rules.append((single_line_comment_pattern,
                          single_line_comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
        self.setCurrentBlockState(0)


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Custom MS SQL Query App")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.server_input = QLineEdit()
        layout.addWidget(QLabel("Enter server:"))
        layout.addWidget(self.server_input)

        self.database_input = QLineEdit()
        layout.addWidget(QLabel("Enter database:"))
        layout.addWidget(self.database_input)

        self.driver_input = QLineEdit()
        layout.addWidget(
            QLabel("Enter driver (default: ODBC Driver 17 for SQL Server):"))
        layout.addWidget(self.driver_input)

        self.collation_input = QLineEdit()
        layout.addWidget(
            QLabel("Enter collation (default: SQL_Latin1_General_CP1_CI_AS):"))
        layout.addWidget(self.collation_input)

        # Add Trusted Connection checkbox and related input fields
        self.trusted_connection_checkbox = QCheckBox(
            "Use Windows Authentication")
        self.trusted_connection_checkbox.setChecked(True)
        self.trusted_connection_checkbox.stateChanged.connect(
            self.toggle_credentials_input)
        layout.addWidget(self.trusted_connection_checkbox)

        self.credentials_layout = QHBoxLayout()

        self.uid_input = QLineEdit()
        self.uid_input.setPlaceholderText("UID")
        self.uid_input.setEnabled(False)
        self.credentials_layout.addWidget(self.uid_input)

        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("PWD")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setEnabled(False)
        self.credentials_layout.addWidget(self.pwd_input)

        layout.addLayout(self.credentials_layout)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_db)
        layout.addWidget(self.connect_button)

        self.query_input = QTextEdit()
        layout.addWidget(QLabel("Enter your custom query:"))
        layout.addWidget(self.query_input)
        # Apply the SQL syntax highlighter to the QTextEdit
        self.sql_highlighter = SqlHighlighter(self.query_input.document())

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_query)
        layout.addWidget(self.submit_button)

        self.result_label = QLabel("Result:")
        layout.addWidget(self.result_label)

        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def toggle_credentials_input(self, state):
        is_enabled = not bool(state)
        self.uid_input.setEnabled(is_enabled)
        self.pwd_input.setEnabled(is_enabled)

    def connect_to_db(self):
        server = self.server_input.text()
        database = self.database_input.text()
        driver = self.driver_input.text() or "ODBC Driver 17 for SQL Server"
        collation = self.collation_input.text() or "SQL_Latin1_General_CP1_CI_AS"

        if self.trusted_connection_checkbox.isChecked():
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};COLLATION={collation};Trusted_Connection=yes;"
        else:
            uid = self.uid_input.text()
            pwd = self.pwd_input.text()
            conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};COLLATION={collation};UID={uid};PWD={pwd};"

        self.handler = MyHandler(conn_str)

        # Test the connection and show a message box
        try:
            with pyodbc.connect(self.handler.conn_str):
                QMessageBox.information(
                    self, "Success", "Connection successful!")
        except pyodbc.Error as e:
            QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")

    def submit_query(self):
        query = self.query_input.text()

        try:
            # Process the query using the handler object
            result = self.handler.process_custom_query(query)

            # Set the result_table data with the query result
            self.set_result_table_data(result)
        except pyodbc.Error as e:
            QMessageBox.critical(self, "Error", f"Query failed: {str(e)}")

    def set_result_table_data(self, data):
        if data:
            row_count = len(data)
            col_count = len(data[0])

            self.result_table.setRowCount(row_count)
            self.result_table.setColumnCount(col_count)

            for row, rowData in enumerate(data):
                for col, value in enumerate(rowData):
                    item = QTableWidgetItem(str(value))
                    self.result_table.setItem(row, col, item)

            self.result_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeToContents)
            self.result_table.verticalHeader().setSectionResizeMode(
                QHeaderView.ResizeToContents)
        else:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)


class MyHandler:
    def __init__(self, conn_str):
        self.conn_str = conn_str

    def process_custom_query(self, query):
        with pyodbc.connect(self.conn_str) as conn:
            c = conn.cursor()
            c.execute(query)
            result = c.fetchall()

            return result


def main():
    # start the GUI application
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())

    logger.info("Program exited successfully")


if __name__ == "__main__":
    main()
