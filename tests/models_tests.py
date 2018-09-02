import unittest
import unittest.mock as mock

import gspread_db


class MockWorksheet(object):
    """Simple mock-like to mirror some of the properties for worksheets."""

    def __init__(self):
        self.title = 'test'


class TestDatabaseMethods(unittest.TestCase):

    @mock.patch.object(gspread_db.Database, '__init__', return_value=None)
    @mock.patch.object(
        gspread_db.Database, 'worksheets', return_value=[MockWorksheet()])
    def test_create_table_raises_error_when_already_exists(
            self, mock_worksheet, mock_init):
        del mock_worksheet, mock_init
        db = gspread_db.Database()
        with self.assertRaises(gspread_db.GSpreadDbError):
            db.create_table(table_name='test', header=[''])

    @mock.patch.object(gspread_db.Database, '__init__', return_value=None)
    @mock.patch.object(
        gspread_db.Database, 'worksheets', return_value=[MockWorksheet()])
    @mock.patch.object(gspread_db.Database, 'del_worksheet')
    def test_delete_table_deletes_once(
            self, mock_delete, mock_worksheets, mock_init):
        del mock_worksheets, mock_init
        db = gspread_db.Database()
        db.delete_table('test')
        mock_delete.assert_called_once()

    @mock.patch.object(gspread_db.Database, '__init__', return_value=None)
    @mock.patch.object(
        gspread_db.Database, 'worksheets', return_value=[MockWorksheet()])
    @mock.patch.object(gspread_db.Database, 'del_worksheet')
    def test_delete_table_raises_error_when_table_doesnt_exist(
            self, mock_delete, mock_worksheets, mock_init):
        del mock_delete, mock_worksheets, mock_init
        db = gspread_db.Database()
        with self.assertRaises(gspread_db.GSpreadDbError):
            db.delete_table('another_test')

    @mock.patch.object(gspread_db.Database, '__init__', return_value=None)
    @mock.patch.object(
        gspread_db.Database, 'worksheets', return_value=[MockWorksheet()])
    def test_table_exists(self, mock_worksheets, mock_init):
        mock_init.return_value = None
        del mock_worksheets, mock_init
        db = gspread_db.Database()
        self.assertTrue(db.table_exists('test'))


if __name__ == '__main__':
    unittest.main()
