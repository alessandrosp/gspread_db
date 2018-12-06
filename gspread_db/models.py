"""This module (gspread_db.py) adds a database-like API to gspread."""

import operator

import gspread
import pandas as pd


# The following dictionary is used to map operator names as strings to
# the actual functions they represent.
_COMPARISON_OPERATOR_MAP = {
  'eq': operator.eq,
  'ge': operator.ge,
  'gt': operator.gt,
  'le': operator.le,
  'lt': operator.lt,
  'ne': operator.ne,
}


class GSpreadDbError(Exception):
    """Generic error for the gspread_db package."""


class HeaderError(GSpreadDbError):
    """Raised when there's an issue with the header of a Table."""


class RecordError(GSpreadDbError):
    """Raised when there's an issue with a specific record."""


class Database(gspread.models.Spreadsheet):

    def __getitem__(self, table_name):
        """Gets the relevant worksheet and returns it as a Table object."""
        worksheet = self.worksheet(table_name)
        return Table(worksheet.spreadsheet, worksheet._properties)

    def create_table(self, table_name, header):
        """Creates a new Table (worksheet) in the DB (spreadsheet)."""
        table_names = [w.title for w in self.worksheets()]
        if table_name in table_names:
            raise GSpreadDbError('A table with that name already exists.')
        self.add_worksheet(table_name, 1, len(header))
        worksheet = self.worksheet(table_name)
        worksheet.insert_row(header, index=1)

    def delete_table(self, table_name):
        """Deletes a Table (wroksheet) from the DB (spreadsheet)."""
        to_delete = None
        for worksheet in self.worksheets():
            if worksheet.title == table_name:
                to_delete = worksheet
                break

        if not to_delete:
            raise GSpreadDbError('The name provided did not match a table.')

        self.del_worksheet(to_delete)

    def table_exists(self, table_name):
        """Checks whether a given Table (worksheet) exists."""
        for worksheet in self.worksheets():
            if worksheet.title == table_name:
                return True
        return False


class Table(gspread.models.Worksheet):

    def _parse_header(self):
        """Parses the header of the Table.

        This function is expected to be called before any operation, this is
        because a spreadsheet can easily be changed manually.
        """

        self.fields_map = {}  # Given a field, it returns the index.
        self.idx_map = {}  # Given an index, it returns the field.
        self.header = self.row_values(1)

        # Validate the header makes sense.
        if not self.header:
            raise HeaderError('Worksheet must have a valid header.')
        if len(self.header) != len(set(self.header)):
            raise HeaderError('Fields\' names must be unique.')
        if '' in self.header:
            raise HeaderError(
                'An empty string cannot be used as a field\'s name.')

        for idx, field in enumerate(self.header):
            self.fields_map[field] = idx
            self.idx_map[idx] = field

    def _convert_record_to_dict(self, record, fields):
        """Converts a list of values (record) to a dictionary.

        Args:
          record: [str], an instance of data normally referring to the
            same entity. Each attribute should be a distinct key.
          fields: [str], the fields that should be used
            in the outputted dictionary. A list-record may contain
            more values then needed, so fields can be used to specified
            which values to convert.

        Returns:
          A dictionary.
        """

        if not fields:
            fields = self.header
        output = {}
        for field, idx in self.fields_map.items():
            if field in fields:
                output[field] = record[idx]
        return output

    def _convert_record_to_list(self, record):
        """Converts a record (dict) to a list of values.

        Args:
          record: {str: str}, an instance of data normally referring to
            the same entity.

        Returns:
          A list.
        """

        if not set(record.keys()).issubset(self.header):
            raise RecordError('Keys in record must be a sub-set of header.')
        output = []
        for idx in range(len(self.idx_map)):
            # Record could have less fields than the header, so if KeyError
            # we append an empty string to output.
            try:
                value = record[self.idx_map[idx]]
            except KeyError:
                value = ''
            output.append(value)
        return output

    def _record_matches_conditions(self, record, conditions):
        """Checks when a given record matches certain conditions.

        Args:
          record: {str: str}, an instance of data normally referring to
            the same entity.
          conditions: [(str, str, str)], each tuple should have exactly
            three elements: a field, an operator's name and a value to compare.

        Returns:
          Bool, specifically True if the record matches all conditions and
          False if not.
        """

        for condition in conditions:
            if len(condition) != 3:
                raise GSpreadDbError(
                    'Where conditions must have three elements.')
            field = condition[0]
            operator = _COMPARISON_OPERATOR_MAP[condition[1]]
            compared = str(condition[2])
            if field not in self.header:
                raise GSpreadDbError(
                    'Fields in conditions must be in table\'s header.')
            if not operator(record[self.fields_map[field]], compared):
                return False
            return True

    def delete(self, field=None, value=None, row_numbers=None, where=None):
        """Deletes all records that match certian conditions.

        Conditions can be specified in many different ways. For simple cases, a
        field/value pair can be used; in this cases all records where
        record[field] = value are deleted. If the row numbers to delete are
        known in advance, row_numbers can be used instead. Lastly, where
        can be used to pass complex conditions.

        Args:
          field: str. Name of the field to check.
          value: str. Value record[field] should have to be deleted.
          row_numbers: [int], the rows to delete.
          where: [(str, str, str)], the conditions a record must match in order
            to be deleted.
        """

        if field or value:
            if not field and value:
                raise GSpreadDbError(
                    'Field and value must both be assigned or both be None.')
            if row_numbers or where:
                raise GSpreadDbError('Only one way to select rows can be used '
                                     'at the same time.')

            if row_numbers and where:
                raise GSpreadDbError('Only one way to select rows can be used '
                                     'at the same time.')

            if not any([field, value, row_numbers, where]):
                raise GSpreadDbError(
                    'Cannot delete rows without a select mechanism.')

        self._parse_header()

        if not row_numbers:
            if field:
                where = [(field, 'eq', value)]
            row_numbers = []
            for row_number, record in enumerate(self.get_all_values()[1:], 2):
                if self._record_matches_conditions(record, where):
                    row_numbers.append(row_number)

        # It's important to delete rows from the bottom-up.
        for row_number in reversed(row_numbers):
            self.delete_row(row_number)

    def insert(self, record):
        """Inserts a new record into the Table.

        Args:
          record: {str: str}, the new record to add.
        """

        if not isinstance(record, dict):
            raise TypeError('Record must be a dictionary.')
        self._parse_header()
        row = self._convert_record_to_list(record)
        self.append_row(row)

    def select(self, field=None, value=None, fields=None, as_pandas=True,
               as_rows=False, where=None, limit=None):
        """Select records from the Table if they match certain conditions.

        Conditions can be expressed in two ways: either as a field/value pair
        or as a list of tuple each being an individual condition
        (where). Using field and value is equivalent to be
        using where = [(field, 'eq', value)].

        The matched records can be returned either as a pd.DataFrame (default),
        as a list of dictionaries or just as a list of row_numbers.

        Args:
          field: str, the field to check.
          value: str, the value to check record[field] against.
          fields: [str], which fields to return. None to get them all.
          as_pandas: bool, whether to return the matched records as
            pd.DataFrame. If False, then records are returned as
            a list of dictionaries.
          as_rows: bool, whether to return matched records just as a list of
            row numbers. If as_rows is True then as_pandas is ignored.
          where: [(str, str, str)], list of conditions.
          limit: int, how many records to return.

        Returns:
          Either a pd.DataFrame or a list. List is either list of dicts, if
          as_pandas is True and as_rows False, or list of ints, if as_rows
          is True.
        """

        if field and value and where:
            raise GSpreadDbError(
                'Either field/value or where can be used but not both.')
        if bool(field) != bool(value):
            raise GSpreadDbError(
                'Field and value must both be assigned or both be None.')

        self._parse_header()

        if isinstance(fields, str):
            fields = [fields]
        elif not fields:
            fields = self.header

        if not set(fields).issubset(self.header):
            raise GSpreadDbError('Fields must be a sub-set of header.')

        if isinstance(where, tuple):
            where = [where]
        elif field:
            where = [(field, 'eq', value)]

        results = []
        row_numbers = []
        for row_number, record in enumerate(self.get_all_values()[1:], 2):
            if self._record_matches_conditions(record, where):
                results.append(self._convert_record_to_dict(record, fields))
                row_numbers.append(row_number)
                if limit:
                    if len(results) == limit:
                        break

        if as_rows:
            return row_numbers

        if as_pandas:
            return pd.DataFrame(results, index=row_numbers)

        return results

    def update(self, field=None, value=None, row_numbers=None,
               where=None, new_values=None):
        """Updates the values for records matching certain conditions.

        Args:
          field: str, the field to check.
          value: str, the value to check record[field] against.
          row_numbers: [int], which rows to update.
          where: [(str, str, str)], list of conditions (tuples).
          new_values: {str: str}, the values to replace. Keys should match
            fields in header, and values are the new values.
        """

        if field or value:
            if not field and value:
                raise GSpreadDbError(
                    'Field and value must both be assigned or both be None.')
            if row_numbers or where:
                raise GSpreadDbError('Only one way to select rows can be'
                                     'used at the same time.')

        if row_numbers and where:
            raise GSpreadDbError(
                'Only one way to select rows can be used at the same time.')

        if not any([field, value, row_numbers, where]):
            raise GSpreadDbError(
                'Cannot update records without a select mechanism.')

        self._parse_header()

        if not row_numbers:
            if field:
                where = [(field, 'eq', value)]
            row_numbers = []
            for row_number, record in enumerate(self.get_all_values()[1:], 2):
                if self._record_matches_conditions(record, where):
                    row_numbers.append(row_number)

            for row_number in row_numbers:
                for field_to_update, new_value in new_values.items():
                    # fields_map is 0-based, while coordinates are passed
                    # as 1-based values, thus the +1.
                    col_number = self.fields_map[field_to_update] + 1
                    self.update_cell(row_number, col_number, new_value)
