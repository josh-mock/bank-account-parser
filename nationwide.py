import csv
import chardet
from dateutil import parser
from pathlib import Path

INPUT_FILE_PATH = "inputs"
ACCOUNT_NAME_LOCATION = 1


def get_input_files(input_file_path):
    # Convert file path to Path object
    directory = Path(input_file_path)

    # Check if the file path is a directory
    if not directory.is_dir():
        exit(f"Error: The specified path '{input_file_path}' is not a valid directory.")
    
    # Find all CSV files in directory
    else:
        csv_files = list(directory.glob('*csv'))

        # Check if there are any csv files
        if len(csv_files) >= 1:
            return csv_files
        
        else:
            exit(f"No CSV files found in directory: '{directory}'.")


def get_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']


def get_account_name(first_row):
    raw_string = first_row[ACCOUNT_NAME_LOCATION]
    return raw_string.split('****')[0].strip()


def find_headings(infile):
    for _ in range(3):
        next(infile)

def get_transaction_date(row):
    # Get date from row
    date_string = row.get("Date")

    # Convert date to date object
    date_object = parser.parse(date_string, dayfirst=True)

    # Return in yyyy-mm-dd format
    return date_object.strftime("%Y-%m-%d")

def get_transaction_ammount(row):
    paid_in = row.get("Paid in")
    paid_out = row.get("Paid out")

    if paid_in:
        # Remove the currency symbol and return
        return float(paid_in[1:])
    
    if paid_out:
        # Remove the currency symbol and make negative
        return -float(paid_out[1:])


def get_transaction_description(row, account_name):
    return row.get("Transactions") if account_name == "Nationwide Credit" else row.get("Description")

def main():
    # Get files from the user
    input_files = get_input_files(INPUT_FILE_PATH)
    # Iterate over files
    for input in input_files:
        with open(input, "r", encoding=get_encoding(input)) as infile:
            reader = csv.reader(infile)
            # Parse the first row to get account name
            first_row = next(reader)
            account_name = get_account_name(first_row)

            # Find the headings
            find_headings(infile)
            reader = csv.DictReader(infile)

            # Iterate over account rows
            for row in infile:
                # Get the transaction date
                transaction_date = get_transaction_date(row)

                # Get the transaction value 
                transaction_value = get_transaction_value()

                # Get the transaction description
                transaction_description = get_transaction_description()

                # Categorise the transaction
                transaction_category = categorise_transaction(transaction_description)

                # Give the transaction a type 

                # Return a transaction dictionary and append to the list of transactions 