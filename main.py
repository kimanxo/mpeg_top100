from movies_data_push import categorize_top_movies
from series_data_push import categorize_top_series
from settings import BASE_URL, SERVER_ID
from utils import login


# Main logic
session = login(BASE_URL)
if session:
    categorize_top_movies(session, SERVER_ID, BASE_URL)
    categorize_top_series(session, SERVER_ID, BASE_URL)
