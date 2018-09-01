import gspread

from .client import Client
from .models import Database, Table


def authorize(credentials, client_class=gspread.client.Client):
    """Login to Google API using OAuth2 credentials."""
    client = gspread.authorize(credentials, client_class)
    return Client(client.auth, client.session)
