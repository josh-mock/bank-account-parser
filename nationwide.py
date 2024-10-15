import csv
import chardet
import json
from dateutil import parser
from pathlib import Path
from tabulate import tabulate
import time
from gspread.exceptions import APIError
import gspread
from google.oauth2.service_account import Credentials


# Name of folder containing input CSVs
INPUT_FILE_PATH = "inputs"

# Location of the Nationwide Account name on the first line pf the CSV statements
ACCOUNT_NAME_LOCATION = 1

# Category file
CATEGORIES_JSON = "categories.json"

# Google upload batch size
BATCH_SIZE = 100

# Google credentials
GOOGLE_CREDS_JSON = "google_creds_json"
# Google sheet ID
SHEET_ID = ...

# Google sheets workbook name
WORKBOOK_NAME = ...

def get_input_files(input_file_path):
    # Convert file path to Path object
    directory = Path(input_file_path)

    # Check if the file path is a directory
    if not directory.is_dir():
        exit(f"Error: The specified path '{
             input_file_path}' is not a valid directory.")

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


def get_transaction_value(row):
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


def load_json(file):
    with open(file, 'r') as file:
        return json.load(file)


def categorise_transaction(transaction_description, account_name, transaction_date, transaction_value):
    categories = load_json(CATEGORIES_JSON)

    # Iterate through each category and its associated list of keywords
    for category, keywords in categories.items():
        # Check if any keyword matches the transaction string snd return category if match
        if any(keyword.lower() in transaction_description.lower() for keyword in keywords):
            return category
        # If not, prompt the user to enter a category
        else:
            table = [["Account:", account_name], ["Date:", transaction_date], [
                "Amount:", transaction_value], ["Description:", transaction_description]]
            print(f"\nThe following transaction could not be categorised: \n")
            # Print the transaction
            print(tabulate(table))
            print("\nSelect the category you would like to assign it to:\n")
            # Display category options
            for index, category in enumerate(categories, start=1):
                print(f"{index}: {category}")

                while True:
                    # Prompt the user to input a category ID
                    assigned = int(input("\nEnter category id: "))

                    # Validate the input and check if it matches a category
                    if 1 <= assigned <= len(categories):
                        category = list(categories.keys())[assigned - 1]
                        print(
                            f"\nTransaction '{transaction_description}' assigned to category: {category}")

                        while True:
                            decision = input(
                                "Would you like to add this to categories for future use? (Y/N): ").upper()

                            if decision == "Y":
                                # Add the transaction as a keyword under the selected category
                                if transaction_description not in categories[category]:
                                    categories[category].append(
                                        transaction_description)
                                    print(
                                        f"\nTransaction '{transaction_description}' added to the '{category}' category.")
                                else:
                                    print(
                                        f"\nTransaction '{transaction_description}' is already in the '{category}' category.")
                                break
                            elif decision == "N":
                                print(
                                    f"\nTransaction '{transaction_description}' not added to any category.")
                                break
                            else:
                                print(
                                    "\nInvalid input. Please enter 'Y' or 'N'.")
                    else:
                        print(
                            "\nInvalid input. Please enter a valid category ID.\n")
        save_updated_category_keywords_to_json_file(categories, CATEGORIES_JSON)
        return category


def save_updated_category_keywords_to_json_file(categories, categories_file):
    with open(categories_file, 'w') as file:
        # Pretty-print with indentation
        json.dump(categories, file, indent=4)


def get_transaction_type(transaction_category, transaction_value):
    if transaction_category == "Transfer":
        return "Transfer"
    elif transaction_value > 0:
        return "Income"
    else:
        return "Expense"


def parse_transactions(input_files):
    # Create empty list of transactions
    transactions = []
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
                transaction_category = categorise_transaction(
                    transaction_description, account_name, transaction_date, transaction_value)

                # Give the transaction a type
                transaction_type = get_transaction_type(
                    transaction_category, transaction_value)

                # Return a transaction dictionary and append to the list of transactions
                transaction = {"date": transaction_date, "value": transaction_value, "description": transaction_description,
                               "category": transaction_category, "type": transaction_type, "account": account_name}

                transactions.append(transaction)
    transactions.sort(key=lambda x: x['date'])
    return transactions


def connect_to_google_sheets():

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDS_JSON, scopes=scopes)
    client = gspread.authorize(creds)

    sheet_id = SHEET_ID
    workbook = client.open_by_key(sheet_id)
    return workbook.worksheet(WORKBOOK_NAME)


def upload_to_google_sheet(transactions):
    print("\nOpening spreadsheet...\n")

    # Format list of lists for Google Sheets
    rows = [[transaction] for transaction in transactions]

    # Split transactions into batches
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        try:
            # Append the current batch to the sheet
            sheet.append_rows(batch, value_input_option='USER_ENTERED')
        except APIError as e:
            if 'Quota exceeded' in str(e):
                print("API quota exceeded, stopping the update.")
                break
            else:
                print(f"API error occurred: {e}")
                break

        time.sleep(2)

    print("Upload completed.")


def main():
    # Get files from the user
    input_files = get_input_files(INPUT_FILE_PATH)

    # Parse transactions
    transactions = parse_transactions(input_files)

    upload_to_google_sheet(transactions)
