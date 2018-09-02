import gspread

from .models import Database


class Client(gspread.Client):

    def open(self, title):
        """Opens a spreadsheet."""
        spreadsheet = super(Client, self).open(title)
        return Database(spreadsheet.client, spreadsheet._properties)

    def open_by_key(self, key):
        """Opens a spreadsheet specified by key."""
        spreadsheet = super(Client, self).open_by_key(key)
        return Database(spreadsheet.client, spreadsheet._properties)

    def open_by_url(self, url):
        """Opens a spreadsheet specified by url."""
        spreadsheet = super(Client, self).open_by_url(url)
        return Database(spreadsheet.client, spreadsheet._properties)

    def openall(self, title=None):
        """Opens all available spreadsheets."""
        spreadsheets = super(Client, self).openall(title)
        return [Database(spreadsheet.client, spreadsheet._properties)
                for spreadsheet in spreadsheets]
