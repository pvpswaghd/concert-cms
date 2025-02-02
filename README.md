# Concert Ticket CMS Minimal Sample

This is a proof-of-concept headless CMS for managing concert tickets using Wagtail, NextJS and Google Sheets API. It is a minimal example that demonstrates how to use Wagtail as a headless CMS and NextJS as a frontend.

## Demo

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

1. The CMS should create a schema for venues, concerts, tickets and seats.
2. The CMS should allow third-party applications to perform CRUD operations on the concert data. Note that any authentication or authorization is not conducted in this project.
3. Google Sheets can be used as a read-only database for the concert data, meanwhile CRUD operations are performed on the Wagtail CMS / external sites.
4. The frontend should be able to display the concert data in a user-friendly manner. In this case, the frontend is minimal and only displays the concert data in a page format, as the emphasis is on the backend.
5. The CMS should be able to handle multiple concerts, and each concert should have a unique identifier.
6. A real-time update between the CMS and the Google Sheet is required.

## Architecture

The project is divided into three main components:

1. `backend/`: This is the Wagtail CMS backend that is used to manage CRUDs and URLs for the concert data. The backend is built using Django and Wagtail, and RESTful API endpoints are exposed for third-party applications to interact with the concert data. Techniques such as HATEOAS are used to improve the API endpoints.
2. `frontend/`: This is the NextJS frontend that is used to display the concert data in a user-friendly manner. The frontend is built using React, NextJS and shadcn/ui component library and it fetches the concert data from the Wagtail CMS API. The frontend is minimal and only displays the concert data in a page format. 
3. `crud-js/`: This is a simple JavaScript script that is used to perform CRUD operations on the concert data. The script uses the Fetch API to interact with the Wagtail CMS API, and it can be run in the browser console to perform CRUD operations. The script is minimal and only demonstrates how to perform CRUD operations on the concert data.
## API Endpoints

### Introduction
A hierarchical design is used for the API endpoints, following the HATEOAS principle. This means that the API endpoints are designed in a way that the response contains links to related resources, which can be used to navigate the API. This improves the discoverability of the API and makes it easier to use.

The hierarchy is as below:
> `venue -> concerts -> zones`

To retrieve all the concerts available as of now, you can use the following endpoint exposed by Wagtail CMS API:

```bash
GET http://localhost:8000/api/venues/
```

This is one of the sample response you will get from the above endpoint:

```json
[
    {
        "slug": "kai-tak-stadium",
        "name": "Kai Tak Stadium",
        "address": "1 Stadium Road, HK",
        "capacity": 40000,
        "admission_mode": "mixed",
        "_links": {
            "self": "/api/venues/kai-tak-stadium/",
            "concerts": "/api/venues/kai-tak-stadium/concerts/",
            "zones": "/api/venues/kai-tak-stadium/zones/"
        }
    },
    {
        "slug": "hong-kong-cultural-centre",
        "name": "Hong Kong Cultural Centre",
        "address": "Hong Kong Cultural Centre, L5, Auditoria Building, 10 Salisbury Rd, Tsim Sha Tsui",
        "capacity": 5000,
        "admission_mode": "mixed",
        "_links": {
            "self": "/api/venues/hong-kong-cultural-centre/",
            "concerts": "/api/venues/hong-kong-cultural-centre/concerts/",
            "zones": "/api/venues/hong-kong-cultural-centre/zones/"
        }
    },
    {
        "slug": "hung-hum-coliseum",
        "name": "Hung Hum Coliseum",
        "address": "Hung Hum",
        "capacity": 50000,
        "admission_mode": "mixed",
        "_links": {
            "self": "/api/venues/hung-hum-coliseum/",
            "concerts": "/api/venues/hung-hum-coliseum/concerts/",
            "zones": "/api/venues/hung-hum-coliseum/zones/"
        }
    },
    {
        "slug": "jockey-club-town-hall",
        "name": "Jockey Club Town Hall",
        "address": "9 Lung Wah Street",
        "capacity": 200,
        "admission_mode": "mixed",
        "_links": {
            "self": "/api/venues/jockey-club-town-hall/",
            "concerts": "/api/venues/jockey-club-town-hall/concerts/",
            "zones": "/api/venues/jockey-club-town-hall/zones/"
        }
    }
]
```

To retrieve a specific concert, you can use the following endpoint:

```bash
GET http://localhost:8000/api/venues/{venue-slug}/
```

In this case, let's assume the venue slug is `kai-tak-stadium`. Here is a sample response you will get:

```json
{
    "address": "1 Stadium Road, HK",
    "slug": "kai-tak-stadium",
    "title": "Kai Tak Stadium",
    "name": "Kai Tak Stadium",
    "capacity": 40000,
    "admission_mode": "mixed",
    "zones": [
        {
            "id": 5,
            "slug": "vip-zone",
            "name": "VIP Zone",
            "total_seats": 400,
            "row_start": "A",
            "row_end": "D",
            "seat_start": 1,
            "seat_end": 100,
            "ga_capacity": null,
            "type": "assigned"
        },
        {
            "id": 6,
            "slug": "general-standing",
            "name": "General Standing",
            "total_seats": 1200,
            "row_start": null,
            "row_end": null,
            "seat_start": null,
            "seat_end": null,
            "ga_capacity": 1200,
            "type": "general"
        }
    ],
    "_links": {
        "concerts": "/api/venues/kai-tak-stadium/concerts/",
        "zones": "/api/venues/kai-tak-stadium/zones/"
    }
}
```


```bash
GET http://localhost:8000/api/venues/{venue-slug}/concerts/
```

A sample response is as below:

```json
[
    {
        "slug": "newjeans-2025-concert-in-hong-kong",
        "title": "NewJeans 2025 Concert in Hong Kong",
        "date": "2025-02-21",
        "artist": "NewJeans",
        "_links": {
            "self": "/api/venues/kai-tak-stadium/concerts/newjeans-2025-concert-in-hong-kong/",
            "availability": "/api/venues/kai-tak-stadium/concerts/newjeans-2025-concert-in-hong-kong/availability/",
            "reservations": "/api/venues/kai-tak-stadium/concerts/newjeans-2025-concert-in-hong-kong/reserve-seats/"
        }
    }
]
```

Note that for availability and reservations here, they are not yet accessible as the seating arrangement logic is not yet implemented.

For CRUD operations, they are several endpoints available. Note that you can already retrieve the data from the above endpoints. Below are the sample endpoints for CRUD operations:

### Create a venue
```bash
POST http://localhost:8000/api/venues/
```

You will need to attach a payload to the request body. Here is an example payload:

```json
{
  "name": "Jockey Club Town Hall",
  "slug": "jockey-club-town-hall",
  "address": "9 Lung Wah Street",
  "capacity": 200,
  "admission_mode": "mixed",
  "seat_zones": [
    {
      "name": "VIP Zone",
      "type": "assigned",
      "row_start": "A",
      "row_end": "D",
      "seat_start": 1,
      "seat_end": 10
    },
    {
      "name": "General Standing",
      "type": "general",
      "ga_capacity": 200
    }
  ]
}
```

### Update a venue
```bash
PUT http://localhost:8000/api/venues/{venue-slug}/
```

Note that you can only update the specific field you want. For example, if you only want to update the address of venue, you can attach the following payload to the request body:

```json
{
  "address": "10 Lung Wah Street, Hong Kong"
}
```

Here will be a sample response from the server:

```json
{
    "message": "Venue updated successfully",
    "_links": {
        "self": "/api/venues/jockey-club-town-hall/",
        "concerts": "/api/venues/jockey-club-town-hall/concerts/",
        "zones": "/api/venues/jockey-club-town-hall/zones/"
    }
}
```

### Delete a venue
```bash
DELETE http://localhost:8000/api/venues/{venue-slug}/
```

Make sure that all concerts under the venue are deleted before deleting the venue.
No payload is needed.


### Create a concert under a venue
Note that since we are adopting a hierarchical design, you need to create a concert under a venue. Here is the endpoint to create a concert under a venue:
```bash
POST http://localhost:8000/api/venues/{venue-slug}/concerts/
```

Here is an example payload you need to attach to the request body:

```json
{
  "name": "Global Music Fest 2024",
  "date": "2024-12-31",
  "artist": "International Artists",
  "start_time": "20:00",
  "end_time": "23:30",
  "description": "Annual music festival featuring global artists",
  "genre": "Multi-Genre",
  "image": "/path/to/image.jpg",
  "ticket_types": [
    {
      "type": "assigned",
      "seat_zone_slug": "vip-zone",
      "price": "1500.00"
    },
    {
      "type": "general",
      "seat_zone_slug": "general-standing",
      "ga_capacity": 1000,
      "price": "500.00"
    }
  ]
}
```

Here is a sample response:
```json
{
    "slug": "global-music-fest-2024",
    "message": "Concert Global Music Fest 2024 created",
    "ticket_types": [
        "global-music-fest-2024-vip-zone",
        "global-music-fest-2024-general-standing"
    ],
    "_links": {
        "self": "/api/venues/jockey-club-town-hall/concerts/global-music-fest-2024/",
        "availability": "/api/venues/jockey-club-town-hall/concerts/global-music-fest-2024/availability/"
    }
}
```

### Retrieve all available concerts
```bash
GET http://localhost:8000/api/concerts/
```

The sample response is as below:
```json
[
    {
        "id": 19,
        "title": "NewJeans 2025 Concert in Hong Kong",
        "slug": "newjeans-2025-concert-in-hong-kong",
        "date": "2025-02-21",
        "artist": "NewJeans",
        "venue": "Kai Tak Stadium",
        "start_time": "19:30:00",
        "end_time": "22:30:00",
        "sold_out": false,
        "description": "Bunnies come!",
        "genre": "",
        "image_url": null,
        "_links": {
            "self": "/api/venues/kai-tak-stadium/concerts/newjeans-2025-concert-in-hong-kong/",
            "tickets": "/api/venues/kai-tak-stadium/concerts/newjeans-2025-concert-in-hong-kong/availability/"
        }
    },
    {
        "id": 24,
        "title": "Global Music Fest 2024",
        "slug": "global-music-fest-2024",
        "date": "2024-12-31",
        "artist": "International Artists",
        "venue": "Jockey Club Town Hall",
        "start_time": "20:00:00",
        "end_time": "23:30:00",
        "sold_out": false,
        "description": "Annual music festival featuring global artists",
        "genre": "",
        "image_url": null,
        "_links": {
            "self": "/api/venues/jockey-club-town-hall/concerts/global-music-fest-2024/",
            "tickets": "/api/venues/jockey-club-town-hall/concerts/global-music-fest-2024/availability/"
        }
    }
]
```

### Retrieve all available concerts under a venue
```bash
GET http://localhost:8000/api/venues/{venue-slug}/concerts/
```

Here is a sample response:

```json
[
    {
        "id": 19,
        "title": "NewJeans 2025 Concert in Hong Kong",
        "slug": "newjeans-2025-concert-in-hong-kong",
        "date": "2025-02-21",
        "artist": "NewJeans",
        "venue": "Kai Tak Stadium",
        "start_time": "19:30:00",
        "end_time": "22:30:00",
        "sold_out": false,
        "description": "Bunnies come!",
        "genre": "",
        "image_url": null,
        "_links": {
            "self": "/api/venues/kai-tak-stadium/concerts/newjeans-2025-concert-in-hong-kong/",
            "tickets": "/api/venues/kai-tak-stadium/concerts/newjeans-2025-concert-in-hong-kong/availability/"
        }
    },
    {
        "id": 24,
        "title": "Global Music Fest 2024",
        "slug": "global-music-fest-2024",
        "date": "2024-12-31",
        "artist": "International Artists",
        "venue": "Jockey Club Town Hall",
        "start_time": "20:00:00",
        "end_time": "23:30:00",
        "sold_out": false,
        "description": "Annual music festival featuring global artists",
        "genre": "",
        "image_url": null,
        "_links": {
            "self": "/api/venues/jockey-club-town-hall/concerts/global-music-fest-2024/",
            "tickets": "/api/venues/jockey-club-town-hall/concerts/global-music-fest-2024/availability/"
        }
    }
]
```


### Update a concert
```bash
PUT http://localhost:8000/api/venues/{venue-slug}/concerts/{concert-slug}/
```
Same as updating a venue, you can only update the specific field you want. For example, if you only want to update the artist of the concert, you can attach the following payload to the request body:

```json
{
  "description": "NewJeans is coming!"
}
```

Here is a sample response from the payload:

```json
{
    "message": "Concert updated successfully",
    "_links": {
        "self": "/api/venues/hong-kong-cultural-centre/concerts/newjeans-2025-concert-in-hong-kong/",
        "availability": "/api/venues/hong-kong-cultural-centre/concerts/newjeans-2025-concert-in-hong-kong/availability/",
        "reservations": "/api/venues/hong-kong-cultural-centre/concerts/newjeans-2025-concert-in-hong-kong/reserve-seats/"
    }
}
```

### Delete a concert
```bash
DELETE http://localhost:8000/api/venues/{venue-slug}/concerts/{concert-slug}/
```

No payload is needed. If it is successful, then it will prompt a response like this:
```json
{
    "message": "Concert aespa 2025 concert deleted",
    "_links": {
        "venue_concerts": "/api/venues/hong-kong-cultural-centre/concerts/",
        "all_concerts": "/api/concerts/"
    }
}
```
## Documentation for individual components

The documentation for the individual components can be referenced in the following folders:

- [`backend/api/README.md`](https://github.com/pvpswaghd/concert-cms/tree/main/backend/api#api-documentation)
- [`crud-js/README.md`](https://github.com/pvpswaghd/concert-cms/tree/main/crud-js#crud-operations-page)
- [`frontend/README.md`](https://github.com/pvpswaghd/concert-cms/tree/main/backend/api#api-documentation)

## Further Improvements

There are several improvements that can be made to this project except on diving too deep into the seating arrangement logic:

- Using Swagger 3.0 for API documentation, and schema validation. This will help in documenting the API endpoints and the request/response schema. It will also help in validating the request/response data against the schema, especially since we are opening our CMS for third-party applications.
- Implementing authentication and authorization for the API endpoints, as currently there is no security implemented. If this is deployed to production, it might be vulnerable to attacks. A JWT token-based authentication can be implemented, or cloud-based services like AWS Cognito can be used.
- Implementing a frontend that is more user-friendly and interactive. The current frontend is minimal and only displays the concert data in a page format. A more interactive frontend can be further designed.
- Restructure the project to use a better file structure and naming conventions. The current project structure is minimal and can be further improved for better readability and maintainability.
- Implementing a CI/CD pipeline for the project. For CI, we could incorporate tools such as Pantsbuild, Black, and Flake8 for code quality checks within GitHub Actions. For CD, we could use tools like GitHub Actions for automated deployment. 
- CORS headers should be closed, but opened due to local development. In production, the CORS headers should be closed to prevent unauthorized access to the API endpoints.
