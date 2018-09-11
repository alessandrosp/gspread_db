# gSpread DB

Anton Burnashev's [gspread](https://github.com/burnash/gspread) is a great package to interact with Google Spreadsheet in Python. The package offers a spreadsheet-like interface where users can create and remove worksheets, update cell values, append new values, etc. For many users that may be the most intuitive and convenient way to interact with Google Spreadsheet but for many applications Google Spreadsheet is fundamentally just another database and thus a database-like interface may make more sense.

**gSpread DB** adds a new API to gspread that supports the most common database operations like insert, delete, select and update. Specifically, a spreadsheet is considered a database, a worksheet a table and the first row of each table/worksheet the header of the table. All operations thus rely on this header to understand which fields is what.

You can install gspread_db via Pip:

```python
pip3 install gspread_db
```

Then, you can start moving data around:

```python
import gspread_db

# You can learn more about how to register your
# service and get API credentials at:
# https://gspread.readthedocs.io/en/latest/oauth2.html
spreadsheet_key = 'spreadsheet-key'
keyfile_dict = {
  'type': 'service_account',
  'project_id': 'you-project-id',
  'private_key_id': 'prive-key-id',
  'private_key': 'a-very-long-string',
  '...': '...'
}

scope = ['https://spreadsheets.google.com/feeds']
auth = oauth2client.service_account.ServiceAccountCredentials
credentials = auth.from_json_keyfile_dict(keyfile_dict, scope)

client = gspread_db.authorize(credentials)
db = client.open_by_key(spreadsheet_key)

db.create_table(table_name='Users', header=['Username', 'Email'])
users = db['Users']
users.insert({'Username': 'annoys_parrot', 'Email': 'not-my-email@email.com'})
alessandro = users.select('Username', 'annoys_parrot')
```

Note that `select` operations return `pd.DataFrame` by default. This can be changed by setting the `as_pandas` argument to `False`.

It's important to note the header of the table (i.e. first row of the spreadsheet) is not just an aesthetic element. If we try to insert a new record with fields that are not contained in the header the operation will fail.

```python
>>> _ = users.select(limit=1)
>>> users.header
['Username', 'Email']
>>> user.insert({'Password': '123456'})
RecordError: Keys in record must be a sub-set of header.
```

Note that as of version 1.0 in order for `Table().header` to return anything an operation must have been performed first (which is the reason why in the first line of the example above we select one row). This is because the header in the spreadsheet is parsed before every operation but not at instantiation time.

A more comprehensive example:

```python
db.create_table(table_name='Users', header=['Username', 'Email'])
db['Users'].insert({'Username': 'Alan', 'Email': 'alan@turing.com'})

# There are multiple ways to select users.
alan = db['Users'].select('Username', 'Alan', as_pandas=False)
turing = db['Users'].select(where=[('Username', 'eq', 'Alan')], as_pandas=False)

alan == turing  # True

print(alan)
# {
#   'Username': 'Alan',
#   'Email': 'alan@turing.com'
# }

# We can also limit the number of fields returned.
alan_email = db['Users'].select('Username', 'Alan', fields=['Email'])

# We can update values for records matching some criteria.
db['Users'].update('Username', 'Alan', new_values={'Email': 'new@email.com'})

# Lastly, we can delete records that match some criteria.
db['Users'].delete('Username', 'Alan')

# Note that for both update and delete all matching records will be updated
# or deleted. Make sure your conditions only match the right records!
```

# Documentation

Note that because gspread_db is just a wrapper around gspread, all methods available in gspread for [Spreasheet](https://gspread.readthedocs.io/en/latest/#gspread.models.Spreadsheet) and [Worksheet](https://gspread.readthedocs.io/en/latest/#gspread.models.Worksheet) are also available in gspread_db for Database and Table.
