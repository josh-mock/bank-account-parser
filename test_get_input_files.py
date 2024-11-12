import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from bank_account_parser import get_input_files  # Importing from your module

class TestGetInputFiles(unittest.TestCase):

    @patch('bank_account_parser.Path')  # Mock Path with the correct module name
    def test_valid_directory_with_csv_files(self, mock_path):
        # Mock the Path object behavior
        mock_directory = MagicMock()
        mock_directory.is_dir.return_value = True
        mock_directory.glob.return_value = ['file1.csv', 'file2.csv']  # Simulate CSV files

        mock_path.return_value = mock_directory
        result = get_input_files("mock_directory_path")

        self.assertEqual(result, ['file1.csv', 'file2.csv'])
        mock_directory.is_dir.assert_called_once()
        mock_directory.glob.assert_called_once_with('*csv')

    @patch('bank_account_parser.Path')  # Mock Path
    def test_valid_directory_without_csv_files(self, mock_path):
        # Mock the Path object behavior
        mock_directory = MagicMock()
        mock_directory.is_dir.return_value = True
        mock_directory.glob.return_value = []  # No CSV files

        mock_path.return_value = mock_directory
        result = get_input_files("mock_directory_path")

        self.assertIsNone(result)
        mock_directory.is_dir.assert_called_once()
        mock_directory.glob.assert_called_once_with('*csv')

    @patch('bank_account_parser.Path')  # Mock Path
    def test_invalid_directory_path(self, mock_path):
        # Mock the Path object behavior
        mock_directory = MagicMock()
        mock_directory.is_dir.return_value = False

        mock_path.return_value = mock_directory
        result = get_input_files("invalid_directory_path")

        self.assertIsNone(result)
        mock_directory.is_dir.assert_called_once()
        mock_directory.glob.assert_not_called()

    @patch('bank_account_parser.Path')  # Mock Path
    def test_file_path_instead_of_directory(self, mock_path):
        # Mock the Path object behavior
        mock_directory = MagicMock()
        mock_directory.is_dir.return_value = False  # Simulate a file path, not a directory

        mock_path.return_value = mock_directory
        result = get_input_files("file_path.txt")

        self.assertIsNone(result)
        mock_directory.is_dir.assert_called_once()
        mock_directory.glob.assert_not_called()

if __name__ == '__main__':
    unittest.main()
