import pyodbc
import os
import time
import csv
import datetime
import logging
import dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from logger import setup_logging

# Set up logging config
setup_logging()

# Init logger
logger = logging.getLogger(__name__)

dotenv.load_dotenv()


class MyHandler(FileSystemEventHandler):
    def __init__(self, conn_str, email_address):
        super().__init__()
        self.conn_str = conn_str
        self.email_address = email_address

    def on_modified(self, event):
        if event.is_directory:
            return None
        elif event.event_type == 'modified' and event.src_path.endswith('Vericelusers.txt'):
            print(f"Detected change in {event.src_path}")
            self.process_file(event.src_path)

            # send email with logs
            logs = self.get_logs()
            if logs:
                self.send_email(logs)

    def process_file(self, filepath):
        with pyodbc.connect(self.cnxn_string) as conn:
            c = conn.cursor()
            with open(filepath, 'r') as f:
                lines = f.readlines()[3:]  # start reading from 4th line
                reader = csv.reader(lines, delimiter='|')
                message_body = ''
                for row in reader:
                    lastname, firstname = row[1], row[2]
                    name = f"{lastname}, {firstname}"
                    print(name)

                    # execute SQL query to check if name is in the database
                    query = f"SELECT COUNT(*) FROM Employees WHERE EmployeeName='{name}'"
                    c.execute(query)
                    result = c.fetchone()

                    # add the result of the query to the message body
                    message_body += f"{query}:\n{result}\n\n"

                    if result[0] == 0:
                        # name is not in database, add it
                        print(f"{name} not in the database, adding...")
                        query = f"INSERT INTO Employees (EmployeeName) VALUES ('{name}')"
                        c.execute(query)
                        print(f"Added {name} to the database")

                        # add the result of the query to the message body
                        message_body += f"{query}:\nAdded {name} to the database\n\n"
                    else:
                        print(f"{name} already in the database")

                conn.commit()

                return message_body

    def send_email(self, message_body):
        # create message object
        msg = MIMEMultipart()
        msg['From'] = self.email_address
        msg['To'] = self.email_address
        msg['Subject'] = f'{datetime.datetime.now().strftime("%Y-%m-%d")}: Logs for ComplianceWire/OPCenter SQL Automation'

        # attach message body as a text file
        txt = MIMEText(message_body)
        msg.attach(txt)

        # create SMTP session and send message
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            # replace with your email password
            smtp.login(self.email_address, 'password')
            smtp.send_message(msg)
            print('Email sent')

    def get_logs(self):
        # read logs from a file and return as a string
        with open('logs.txt', 'r') as f:
            logs = f.read()
            return logs


def main():
    try:

        # establish database connection
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.environ.get('SERVER')};DATABASE={os.environ.get('DATABASE')};COLLATION=SQL_Latin1_General_CP1_CI_AS;Trusted_Connection=yes;"

        # set up watchdog observer to monitor directory for changes to text files
        path = '.'
        event_handler = MyHandler(conn_str, email_address='EMAIL_ADDRESS')
        observer = Observer()
        observer.schedule(event_handler, path, recursive=False)

        observer.start()
        print(f"Watching directory {path} for changes...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

        # close database connection
        conn.close()

        logger.info("Program exited successfully")

    except pyodbc.Error as pyodbc_error:
        logger.error(
            f"An error occurred while connecting to the database: {str(pyodbc_error)}")
    except pyodbc.OperationalError as e:
        logger.error(f"An error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

    if not logger.hasHandlers():
        logging.disable()
        os.remove('logs.txt')


if __name__ == "__main__":
    main()
