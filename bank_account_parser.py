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
import os
import glob
from constants import CATEGORIES_JSON, GOOGLE_CREDS_JSON, SHEET_ID, WORKBOOK_NAME, BATCH_SIZE, BANKS

def get_input_files(input_file_path):
    # Convert file path to Path object
    directory = Path(input_file_path)

    # Check if the file path is a directory
    if not directory.is_dir():
        print(f"Error: The specified path '{
            input_file_path}' is not a valid directory.")
        return None

    # Find all CSV files in directory
    else:
        csv_files = list(directory.glob('*csv'))

        # Check if there are any csv files
        if len(csv_files) >= 1:
            return csv_files

        else:
            print(f"No CSV files found in directory: '{directory}'.")
            return None


def get_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']


def get_nationwide_account_name(first_row):
    raw_string = first_row[1]
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


def get_nationwide_transaction_value(row):
    paid_in = row.get("Paid in")
    paid_out = row.get("Paid out")

    if paid_in:
        # Remove the currency symbol and return
        return float(paid_in[1:])

    if paid_out:
        # Remove the currency symbol and make negative
        return -float(paid_out[1:])


def get_nationwide_transaction_description(row, account_name):
    return row.get("Transactions") if account_name == "Nationwide Credit Card" else row.get("Description")


def load_json(file):
    with open(file, 'r') as file:
        return json.load(file)


def find_category(transaction_description, categories):
    """
    Check if any keywords from categories match the transaction description.
    Returns the assigned category or None if no match is found.
    """
    for category, keywords in categories.items():
        if any(keyword.lower() in transaction_description.lower() for keyword in keywords):
            return category
    return None


def prompt_user_for_category(categories, account_name, transaction_date, transaction_value, transaction_description):
    """
    Prompt the user to select a category if no category was found for the transaction.
    Returns the assigned category chosen by the user.
    """
    print(f"\nThe following transaction could not be categorised: \n")
    table = [
        ["Account:", account_name],
        ["Date:", transaction_date],
        ["Amount:", transaction_value],
        ["Description:", transaction_description]
    ]
    print(tabulate(table))
    print("\nSelect the category you would like to assign it to:\n")

    # Display category options
    for index, category in enumerate(categories, start=1):
        print(f"{index}: {category}")

    while True:
        try:
            assigned = int(input("\nEnter category id: "))
            if 1 <= assigned <= len(categories):
                assigned_category = list(categories.keys())[assigned - 1]
                print(f"\nTransaction '{transaction_description}' assigned to category: {
                      assigned_category}")
                return assigned_category
            else:
                print("\nInvalid input. Please enter a valid category ID.\n")
        except ValueError:
            print(
                "\nInvalid input. Please enter a number corresponding to a category ID.")


def add_transaction_to_category(transaction_description, assigned_category, categories):
    """
    Ask the user if they want to add the transaction description to the selected category.
    Updates the categories if the user agrees.
    """
    while True:
        decision = input(
            "Would you like to add this transaction to the categories for future use? (Y/N): ").strip().upper()
        if decision == "Y":
            if transaction_description not in categories[assigned_category]:
                categories[assigned_category].append(transaction_description)
                print(f"\nTransaction '{transaction_description}' added to the '{
                      assigned_category}' category.")
            else:
                print(f"\nTransaction '{transaction_description}' is already in the '{
                      assigned_category}' category.")
            break
        elif decision == "N":
            print(f"\nTransaction '{
                  transaction_description}' not added to any category.")
            break
        else:
            print("\nInvalid input. Please enter 'Y' or 'N'.")


def save_categories(categories, filename):
    """
    Save the updated categories to a JSON file.
    """
    save_updated_category_keywords_to_json_file(categories, filename)


def categorise_transaction(transaction_description, account_name, transaction_date, transaction_value):
    categories = load_json(CATEGORIES_JSON)

    # Find the assigned category based on transaction description
    assigned_category = find_category(transaction_description, categories)

    if not assigned_category:
        assigned_category = prompt_user_for_category(
            categories, account_name, transaction_date, transaction_value, transaction_description)
        add_transaction_to_category(
            transaction_description, assigned_category, categories)

    save_categories(categories, CATEGORIES_JSON)
    return assigned_category


def save_updated_category_keywords_to_json_file(categories, categories_file):
    with open(categories_file, 'w') as file:
        # Pretty-print with indentation
        json.dump(categories, file, indent=4)


def get_transaction_type(transaction_category, transaction_value):
    if transaction_category == "Transfer":
        return "Transfer"
    elif float(transaction_value) > 0:
        return "Income"
    else:
        return "Expense"


def parse_transactions(input_file, bank):
    # Create empty list of transactions
    transactions = []
    with open(input_file, "r", encoding=get_encoding(input_file)) as infile:
        # Set up account-specific logic
        if bank == "Nationwide":
            reader = csv.reader(infile)
            first_row = next(reader)
            account_name = get_nationwide_account_name(first_row)
            find_headings(infile)
            reader = csv.DictReader(infile)
        elif bank == "Amex":
            reader = csv.DictReader(infile)
            account_name = "Amex"
        elif bank == "Starling":
            reader = csv.DictReader(infile)
            account_name = "Starling"
        else:
            raise ValueError("Unsupported account type")

        # Iterate over account rows
        for row in reader:
            # Get transaction date
            transaction_date = get_transaction_date(row)

            # Handle transaction value based on account type
            if bank == "Nationwide":
                transaction_value = get_nationwide_transaction_value(row)
                transaction_description = get_nationwide_transaction_description(
                    row, account_name)
            elif bank == "Amex":
                transaction_value = -1 * float(row.get("Amount"))
                transaction_description = row.get("Description")
            elif bank == "Starling":
                transaction_value = row.get("Amount (GBP)")
                transaction_description = row.get("Reference")

            # Categorize the transaction
            transaction_category = categorise_transaction(
                transaction_description, account_name, transaction_date, transaction_value)

            # Assign a transaction type
            transaction_type = get_transaction_type(
                transaction_category, transaction_value)

            # Create a transaction dictionary and add to the list
            transaction = [transaction_date,
                           transaction_value,
                           transaction_description,
                           transaction_category,
                           transaction_type,
                           account_name]

            transactions.append(transaction)
    return transactions


def connect_to_google_sheets():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = Credentials.from_service_account_file(
        GOOGLE_CREDS_JSON, scopes=scopes)
    client = gspread.authorize(creds)

    sheet_id = SHEET_ID
    workbook = client.open_by_key(sheet_id)
    return workbook.worksheet(WORKBOOK_NAME)


def upload_to_google_sheet(transactions, google_connection):
    print("\nOpening spreadsheet...\n")

    # Split transactions into batches
    for i in range(0, len(transactions), BATCH_SIZE):
        batch = transactions[i:i + BATCH_SIZE]
        try:
            # Append the current batch to the sheet
            google_connection.append_rows(
                batch, value_input_option='USER_ENTERED')
        except APIError as e:
            if 'Quota exceeded' in str(e):
                print("API quota exceeded, stopping the update.")
                break
            else:
                print(f"API error occurred: {e}")
                break

        time.sleep(2)

    print("Upload completed.")


def process_transactions(input_folder, bank):
    input_files = get_input_files(input_folder)
    if input_files:
        transactions = []
        for input_file in input_files:
            transactions.extend(parse_transactions(input_file, bank))
        return transactions
    return []



def delete_csv_files(directory):
    # Create the path for the CSV files
    csv_files = glob.glob(os.path.join(directory, '*.csv'))

    # Loop through the list of files and delete each one
    for csv_file in csv_files:
        try:
            os.remove(csv_file)
            print(f"Deleted: {csv_file}")
        except Exception as e:
            print(f"Error deleting {csv_file}: {e}")


def main():
    # Initialise empty transactions list
    parsed_transactions = []

    # Process transactions for each bank
    for bank, input_folder in BANKS.items():
        bank_transactions = process_transactions(input_folder, bank)
        parsed_transactions.extend(bank_transactions)

    # Sort transactions by date
    parsed_transactions.sort(key=lambda x: x[0])

    # Connect to Google Sheets
    google_connection = connect_to_google_sheets()

    # Ensure connection was successful
    if google_connection:
        upload_to_google_sheet(parsed_transactions, google_connection)
        for _, input_file in BANKS.items():
            delete_csv_files(input_file)
    else:
        print("Failed to connect to Google Sheets.")


if __name__ == "__main__":
    main()
