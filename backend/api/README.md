# API Documentation

This is the documentation for the API endpoints. The API endpoints are used to interact with the Google Sheet API to sync the data between the Google Sheet and the Django application.

The reason that Wagtail is used as the CMS is due to the following:

- As a long-term Python developer and someone who is more fond of ORM frameworks like Spring Boot, a Django-based CMS like Wagtail is more familiar to me
- Wagtail is a CMS that is built on top of Django, and it is easy to use and has a lot of community support. Institutions and enterprises such as M+ Museum used Wagtail as their CMS. If we think of this in long-term, Wagtail definitely provides more flexibility and scalability.

## API Endpoints Logic

There are multiple files that are note documenting here, as they are representing the main logic of the API endpoints.

### `config.py`

This file contains the configuration for the Google Sheet API. It is used to authenticate the API requests to the Google Sheet. The `SCOPES` variable is used to define the permissions required for the API requests. The `SERVICE_ACCOUNT_FILE` variable is used to define the path to the service account file. The `SPREADSHEET_ID` variable is used to define the ID of the Google Sheet.

This is widely used by the `views.py` file to establish requests to the Google Sheet API.

### `models.py`

This defines the schema for the models, including the `ConcertIndexPage` and `Tickets` models. They are both translated into SQL tables by Django ORM with the help of the `makemigrations` and `migrate` commands.

### `test_gs.py`

This file contains a preliminary connection with the Google Sheet API. It is used to test the connection and the data retrieval from the Google Sheet.

It is referenced from the official documentation of the Google Sheet API.

### `views.py`

This file contains the logic for the API endpoints. It is responsible for handling the requests and responses for the API. The decorator @csrf_exempt is used to disable the CSRF protection for the API endpoints, as mostly here we will be dealing with pure HTTP requests.

When there is a request to the API, the Google Sheet will sync the data by clearing the existing data, and then inserting the new data from the Google Sheet. This definitely has rooms for improvement, but given the time constraint, this would be the most efficient way to handle the data sync.

### `urls.py`

This file contains the URL patterns for the API endpoints. It is responsible for routing the requests to the appropriate view functions.