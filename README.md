# Concert Ticket CMS Minimal Sample

This is a proof-of-concept headless CMS for managing concert tickets using Wagtail, NextJS and Google Sheets API. It is a minimal example that demonstrates how to use Wagtail as a headless CMS and NextJS as a frontend.

## Demo

https://github.com/user-attachments/assets/09f61035-b9f7-4740-b200-ffaf00c8d92e


## Installation
```bash
cd backend/
python -m venv env
source env/bin/activate # or env\Scripts\activate on Windows
pip install -r requirements.txt
```

## Usage
You need two terminal windows to run the backend and frontend locally.
```bash
cd backend/
python manage.py runserver
```

```bash
cd frontend/
npm install
npm run dev
```

## Requirements

There are several requirements interpreted and assumed from the project description:

1. The CMS should be able to manage, and store concert data.
2. The CMS should allow third-party applications to perform CRUD operations on the concert data. Note that any authentication or authorization is not conducted in this project.
3. Google Sheets can be used as a read-only database for the concert data, meanwhile CRUD operations are performed on the Wagtail CMS / external sites.
4. The frontend should be able to display the concert data in a user-friendly manner. In this case, the frontend is minimal and only displays the concert data in a page format, as the emphasis is on the backend.
5. There are schema designed for the concert data, with the tickets as well. The tickets are not implemented in this project, but the schema is designed for future implementation.
6. The CMS should be able to handle multiple concerts, and each concert should have a unique identifier.
7. A real-time update between the CMS and the Google Sheet is required.

## Design Graph

The design graph for this project is as follows:

## API Endpoints

To retrieve all the concerts data available, you can use the following endpoint exposed by Wagtail CMS API:

```bash
http://localhost:8000/api/v2/pages/?type=api.ConcertIndexPage
```

This is one of the sample response you will get from the above endpoint:

```json
{
    "meta": {
        "total_count": 3
    },
    "items": [
        {
            "id": 10,
            "meta": {
                "type": "api.ConcertIndexPage",
                "detail_url": "http://localhost/api/v2/pages/10/",
                "html_url": "http://localhost/test-3/",
                "slug": "test-3",
                "first_published_at": "2025-01-28T17:04:39.310348Z"
            },
            "title": "THIS IS MC 3"
        },
        {
            "id": 11,
            "meta": {
                "type": "api.ConcertIndexPage",
                "detail_url": "http://localhost/api/v2/pages/11/",
                "html_url": "http://localhost/test-4/",
                "slug": "test-4",
                "first_published_at": "2025-01-28T17:24:02.957063Z"
            },
            "title": "念 - 2025"
        },
        {
            "id": 16,
            "meta": {
                "type": "api.ConcertIndexPage",
                "detail_url": "http://localhost/api/v2/pages/16/",
                "html_url": "http://localhost/newjeans-2025-concert/",
                "slug": "newjeans-2025-concert",
                "first_published_at": "2025-01-28T17:42:44.698453Z"
            },
            "title": "NewJeans 2025 Concert"
        }
    ]
}
```
To retrieve specific fields (e.g. title, date, artist), you can add a `fields` parameter to the URL:

```bash
http://localhost:8000/api/v2/pages/?type=api.ConcertIndexPage&fields=title,date,artist
```

This will be the sample response:

```json
{
    "meta": {
        "total_count": 3
    },
    "items": [
        {
            "id": 10,
            "title": "THIS IS MC 3",
            "date": "2025-01-28",
            "artist": "MC Cheung Tinfu"
        },
        {
            "id": 11,
            "title": "念 - 2025",
            "date": "2025-05-20",
            "artist": "Panther Chan"
        },
        {
            "id": 16,
            "title": "NewJeans 2025 Concert",
            "date": "2025-09-13",
            "artist": "NewJeans"
        }
    ]
}
```

For CRUD operations, they are several endpoints available. Note that you can already retrieve the data from the above endpoint, and Wagtail does not provide write permissions with their public API, so the following are custom endpoints for the rest of the CRUD operations:

### Create a concert
```bash
POST http://localhost:8000/api/create-concert/
```

You will need to attach a payload to the request body. Here is an example payload:

```json
{
  "title": "NewJeans 2025 Concert",
  "name": "NewJeans 2025 Concert",
  "date": "2025-09-13",
  "location": "HK",
  "price": "50.00",
  "description": "K-pop!",
  "start_time": "20:00:00",
  "end_time": "23:00:00",
  "concert_type": "K-POP",
  "artist": "NewJeans"
}
```

Here is a sample response you will get:

```json
{
    "status": "success",
    "page_id": 16,
    "slug": "newjeans-2025-concert",
    "message": "Concert page created and published successfully!"
}
```

### Update a concert
```bash
PUT http://localhost:8000/api/update-concert/{id}/
```

You will need to attach a payload to the request body. Note that you only need to include the fields you want to update.

```json
{
    "artist": "Panther Chan"
}
```

Here is a sample response you will get:

```json
{
    "status": "success",
    "message": "Concert 11 updated successfully!",
    "concert_metadata": {
        "id": 11,
        "title": "念 - 2025",
        "name": "panther chan spell",
        "date": "2025-05-20",
        "location": "Chicago",
        "price": "50.00",
        "description": "Relaxing jazz music.",
        "start_time": "20:00:00",
        "end_time": "23:00:00",
        "concert_type": "Jazz",
        "artist": "Panther Chan",
        "last_updated": "2025-01-28 17:54:45.324287+00:00"
    }
}
```

### Delete a concert
```bash
DELETE http://localhost:8000/api/remove-concert/{id}/
```

Note that there are no extra payload needed for this request. Here is a sample response you will get:

```json
{
    "status": "success",
    "message": "Concert 9 removed successfully!"
}
```

## Documentation

The documentation for the project can be referenced in the following folders:

- `backend/api/README.md`

## Further Improvements

There are several improvements that can be made to this project except working on the ticket logic:

- Implementing authentication and authorization for the API endpoints, as currently there is no security implemented. If this is deployed to production, it might be vulnerable to attacks. A JWT token-based authentication can be implemented, or cloud-based services like AWS Cognito can be used.
- Implementing a frontend that is more user-friendly and interactive. The current frontend is minimal and only displays the concert data in a page format. A more interactive frontend can be further designed with performance optimizations.
- Restructure the project to use a better file structure and naming conventions. The current project structure is minimal and can be further improved for better readability and maintainability.
- Implementing a CI/CD pipeline for the project. For CI, we could incorporate tools such as Pantsbuild, Black, and Flake8 for code quality checks within GitHub Actions. For CD, we could use tools like GitHub Actions for automated deployment. 
