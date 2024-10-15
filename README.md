# Bank Account Parser
Categorise bank transactions and upload to a google sheet. 
## Overview
This Python script automates the process of categorising financial transactions from CSV files for different banking accounts (Nationwide, Starling, Amex) and uploads the processed data to Google Sheets. The tool utilizes various libraries for file handling, date parsing, Google Sheets API interaction, and user interaction for category assignment.

## Features
- **Read CSV Files**: Load CSV files from specified directories for different banking accounts.
- **Categorize Transactions**: Automatically categorize transactions based on pre-defined keywords, with an option for user input when a match is not found.
- **Upload to Google Sheets**: Append categorized transaction data to a specified Google Sheet.
- **Dynamic Category Management**: Allow users to add new transaction descriptions to categories for future categorization.
- **Error Handling**: Manage errors during file operations and Google Sheets API interactions.

## Requirements
- Python 3.6 or higher
- Required Python packages:
    - `gspread`
    - `google-auth`
    - `python-dateutil`
    - `tabulate`
    - `chardet`

You can install the required packages using pip:

```bash
pip install -r requirements.txt
```
## Configuration
Before running the script, configure the following:

### Google Sheets API:
1. Create a Google Cloud project.
2. Enable the Google Sheets API.
3. Create credentials and download the JSON key file. Rename this file to `google_creds.json` and place it in the project directory.

### Categories:
Define your transaction categories in a `categories.json` file. The format should be as follows:

```json
{
    "Category1": ["keyword1", "keyword2"],
    "Category2": ["keyword3", "keyword4"]
}
```
### Google Sheets Setup
1. Create a Google Sheet and note the `SHEET_ID` and `WORKBOOK_NAME`.
2. Update the script with your `SHEET_ID` and `WORKBOOK_NAME`.

### Input Folders
Ensure that the directories for the input CSV files are correctly set up:

- `inputs/nationwide`
- `inputs/starling`
- `inputs/amex`

## Usage
1. Place the script in your desired directory.
2. Organize your input CSV files into the corresponding folders.
3. Run the script:

```bash
python main.py
```
## Functions

### Main Functions
- `get_input_files(input_file_path)`: Fetches all CSV files in the specified directory.
- `parse_nationwide_transactions(input_files)`: Parses transactions from Nationwide CSV files.
- `parse_amex_transactions(input_files)`: Parses transactions from Amex CSV files.
- `parse_starling_transactions(input_files)`: Parses transactions from Starling CSV files.
- `connect_to_google_sheets()`: Establishes a connection to the specified Google Sheets.
- `upload_to_google_sheet(transactions, google_connection)`: Uploads the categorized transactions to Google Sheets.

### Helper Functions
- `get_encoding(file_path)`: Determines the encoding of a CSV file.
- `categorise_transaction(...)`: Categorizes a transaction and prompts for user input if no category is found.
- `delete_csv_files(directory)`: Deletes CSV files in the specified directory after processing.

## Error Handling
The script includes basic error handling for file operations and Google Sheets API interactions, including checks for:

- Valid input directory
- Successful Google Sheets connection
- Handling of API errors (e.g., quota exceeded)

## License
This project is licensed under the MIT License. See the LICENSE file for details.






