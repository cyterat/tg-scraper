# Import necessary modules
from datetime import datetime
import time
import random
import os
import sys
import snscrape.modules.telegram as tg
from pyarrow import Table
from pyarrow.parquet import write_table
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QFormLayout, QRadioButton,
    QButtonGroup, QWidgetItem, QSpacerItem
)
from PyQt5.QtCore import QThread, pyqtSignal


# Define color constants
BG_COLOR = "#333333"
HL_COLOR = "#02a8c3"
FONT_COLOR = "#fefefe"
BG_COLOR_ENTRY = "#DEDEDE"


# Define thread for scraping
class ScrapeThread(QThread):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)


    def __init__(self, channel_name, start_date, finish_date, max_sleep, verbose):
        super().__init__()
        self.channel_name = channel_name
        self.start_date = start_date
        self.finish_date = finish_date
        self.max_sleep = max_sleep
        self.verbose = verbose
        self.scraping = True


    def run(self):
        scraped_data = self.scrape_channel(self.channel_name, self.start_date, self.finish_date, self.max_sleep, self.verbose)
        self.finished.emit(scraped_data)


    def scrape_channel(self, channel_name, start_date, finish_date, max_sleep, verbose):

        channel = tg.TelegramChannelScraper(channel_name)
        raw = []

        start_datetime_object = datetime.strptime(start_date, '%Y-%m-%d')
        finish_datetime_object = datetime.strptime(finish_date, '%Y-%m-%d')

        post_count = 0

        for i, post in enumerate(channel.get_items()):
            if not self.scraping:
                break

            if start_datetime_object.date() <= post.date.date() <= finish_datetime_object.date():
                if i == 0:
                    print(f"Sample Post: {post.content[:50]}...")

                content = post.content if verbose else '#####'
                raw.append({
                    'post_id': post.url.split('/')[-1],
                    'post_url': post.url,
                    'date': post.date,
                    'content': content
                })

                post_count += 1
                self.progress.emit(post_count)
                time.sleep(random.uniform(0, max_sleep))
            else:
                break

        return raw


    def stop(self):
        self.scraping = False


# Define the main application widget
class TelegramScraperApp(QWidget):


    def __init__(self):
        super().__init__()

        # Initialize the user interface
        self.initUI()

        self.scrape_thread = None


    def initUI(self):

        # Set window properties
        self.setFixedSize(360, 295)  # width, height
        self.setWindowTitle('Telegram Posts Scraper')
        self.setWindowIcon(QtGui.QIcon('icon.ico'))
        self.setWindowFlags(QtCore.Qt.Window)

        # Set background color
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(BG_COLOR))
        self.setPalette(palette)

        # Create a form layout for UI elements
        self.form_layout = QFormLayout()

        # Add channel name field
        self.channel_label = QLabel()
        self.channel_label.setText(f'''
            • telegram.org/k/#@<span style="color: {HL_COLOR};">XXXX</span><br>
            • t.me/<span style="color: {HL_COLOR};">XXXX</span>
            ''')
        self.channel_label.setStyleSheet(f"color: {FONT_COLOR}; font-size: 13px;")
        self.channel_label.setTextFormat(QtCore.Qt.RichText)
        self.channel_entry = QLineEdit()
        self.channel_entry.setPlaceholderText("XXXX")
        self.channel_entry.setStyleSheet(f"background-color: {BG_COLOR_ENTRY}; font-size: 13px;")
        self.form_layout.addRow(self.channel_label, self.channel_entry)

        # Add start date field
        self.start_date_label = QLabel(f'Start Date (<span style="color: {HL_COLOR};">YYYY</span>-<span style="color: {HL_COLOR};">MM</span>-<span style="color: {HL_COLOR};">DD</span>):')
        self.start_date_label.setStyleSheet(f"color: {FONT_COLOR}; font-size: 13px;")
        self.start_date_entry = QLineEdit(f"{datetime.today().year}-01-01")
        self.start_date_entry.setStyleSheet(f"background-color: {BG_COLOR_ENTRY}; font-size: 13px;")
        self.start_date_entry.textChanged.connect(self.format_date)
        self.form_layout.addRow(self.start_date_label, self.start_date_entry)

        # Add finish date field
        self.finish_date_label = QLabel(f'Finish Date (<span style="color: {HL_COLOR};">YYYY</span>-<span style="color: {HL_COLOR};">MM</span>-<span style="color: {HL_COLOR};">DD</span>):')
        self.finish_date_label.setStyleSheet(f"color: {FONT_COLOR}; font-size: 13px;")
        self.finish_date_entry = QLineEdit(f"{datetime.today().year}-12-31")
        self.finish_date_entry.setStyleSheet(f"background-color: {BG_COLOR_ENTRY}; font-size: 13px;")
        self.finish_date_entry.textChanged.connect(self.format_date)
        self.form_layout.addRow(self.finish_date_label, self.finish_date_entry)

        # Add radio buttons for verbosity
        self.verbose_label = QLabel('Include post contents?')
        self.verbose_label.setStyleSheet(f"color: {FONT_COLOR}; font-size: 13px;")
        self.verbose_yes = QRadioButton('Yes')
        self.verbose_yes.setStyleSheet(f"color: {FONT_COLOR}; font-size: 13px;")
        self.verbose_yes.setChecked(True)
        self.verbose_no = QRadioButton('No')
        self.verbose_no.setStyleSheet(f"color: {FONT_COLOR}; font-size: 13px;")
        self.verbose_group = QButtonGroup()
        self.verbose_group.addButton(self.verbose_yes)
        self.verbose_group.addButton(self.verbose_no)
        self.form_layout.addRow(self.verbose_label, self.verbose_yes)
        self.form_layout.addWidget(self.verbose_no)

        # Add button to start scraping
        self.scrape_button = QPushButton('Start Scraping', self)
        self.scrape_button.setStyleSheet(f"background-color: {HL_COLOR}; color: {BG_COLOR}; border: 1px solid {HL_COLOR}; border-radius: 4px; font-size: 13px;")
        self.scrape_button.clicked.connect(self.start_scraping)
        self.scrape_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.form_layout.addWidget(self.scrape_button)

        # Add exit button
        self.exit_button = QPushButton('Exit', self)
        self.exit_button.setStyleSheet("background-color: #dc3545; color: white; border: 1px solid #dc3545; border-radius: 4px; font-size: 13px;")
        self.exit_button.clicked.connect(self.exit_application)
        self.exit_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.form_layout.addWidget(self.exit_button)

        # Add space between buttons and status display
        spacer = QSpacerItem(40, 20)  # Adjust width and height as needed
        self.form_layout.addItem(spacer)

        # Add label for scraped posts count
        self.scraping_status_label = QLabel('Scraped Posts:')
        self.scraping_status_label.setStyleSheet(f"color: {FONT_COLOR}; font-size: 13px;")
        self.scraping_status_display = QLabel('0')
        self.scraping_status_display.setStyleSheet(f"color: {FONT_COLOR}; font-size: 13px;")
        self.form_layout.addRow(self.scraping_status_label, self.scraping_status_display)

        # Set layout for the widget
        self.setLayout(self.form_layout)

        # Add "Created by" text
        self.created_by_label = QLabel(f'Created by <a class="github-name" style="color: {HL_COLOR}; text-decoration: none;" href="https://github.com/cyterat">cyterat</a')
        self.created_by_label.setStyleSheet("color: grey; font-size: 10px; margin-top: 20px;")
        self.created_by_label.setAlignment(QtCore.Qt.AlignCenter)
        self.created_by_label.setOpenExternalLinks(True)
        self.form_layout.addRow(self.created_by_label)


    # Method to start scraping
    def start_scraping(self):
        channel_name = self.channel_entry.text().strip()
        start_date = self.start_date_entry.text().strip()
        finish_date = self.finish_date_entry.text().strip()
        verbose = 'y' if self.verbose_yes.isChecked() else 'n'

        if not channel_name:
            QMessageBox.critical(self, "Input Error", "A channel name was not provided.")
            return

        if not self.validate_date(start_date) or not self.validate_date(finish_date):
            QMessageBox.critical(self, "Input Error", "Invalid date format. Please enter dates in YYYY-MM-DD format.")
            return

        if not self.validate_year(start_date.split("-")[0]) or not self.validate_year(finish_date.split("-")[0]):
            QMessageBox.critical(self, "Input Error", "Invalid year. The year should not be earlier than the foundation date of Telegram.")
            return

        confirm = QMessageBox.question(self, "Confirm", f"You are about to scrape all posts from {channel_name} between {start_date} and {finish_date}. Proceed?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.No:
            return

        # Create and start the scrape thread
        self.scrape_thread = ScrapeThread(channel_name, start_date, finish_date, 0.1, verbose == 'y')
        self.scrape_thread.progress.connect(self.update_scraping_status)
        self.scrape_thread.finished.connect(self.handle_scraped_data)
        self.scrape_thread.start()

        self.scrape_button.setEnabled(False)


    # Method to handle scraped data
    def handle_scraped_data(self, scraped_data):
        if scraped_data:
            self.save_data(scraped_data, self.channel_entry.text().strip(), self.start_date_entry.text().strip(), self.finish_date_entry.text().strip())
        self.scrape_button.setEnabled(True)


    # Method to save scraped data
    def save_data(self, scraped_data, channel_name, start_date, finish_date):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Parquet files (*.parquet.gzip)")
        if not save_path:
            return

        table = Table.from_pylist(scraped_data)
        write_table(table, save_path)
        QMessageBox.information(self, "Success", f"Data saved as {os.path.basename(save_path)}")


    # Method to format date input
    def format_date(self):
        sender = self.sender()
        date = sender.text()
        formatted_date = ""
        if len(date) > 10:
            sender.setText(date[:-1])
            return

        for i in range(len(date)):
            if i == 4 or i == 7:
                formatted_date += "-"
            if not date[i].isdigit():
                continue
            formatted_date += date[i]
        sender.setText(formatted_date)


    # Method to validate date format
    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False


    # Method to validate year
    def validate_year(self, year_str):
        try:
            year = int(year_str)
            if year >= 2013:  # Foundation year of Telegram
                return True
            else:
                return False
        except ValueError:
            return False


    # Method to update scraping status
    def update_scraping_status(self, count):
        self.scraping_status_display.setText(str(count))


    # Method to exit application
    def exit_application(self):
        if self.scrape_thread and self.scrape_thread.isRunning():
            self.scrape_thread.stop()
            self.scrape_thread.wait()
        self.close()


# Main function to run the application
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = TelegramScraperApp()
    ex.show()
    sys.exit(app.exec_())