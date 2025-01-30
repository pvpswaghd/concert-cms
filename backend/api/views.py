import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from wagtail.models import Page

from .models import ConcertIndexPage
from .config import build_service, SPREADSHEET_ID

def sync_sheets() -> None:
    """
    Syncs the ConcertIndexPage data with Google Sheets.
    """
    print("hi")
    service = build_service()
    service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range="Table!A2:L"
    ).execute()
    ConcertIndexPage.objects.all()
    concert_data = []
    for concert in ConcertIndexPage.objects.all():
        concert_data.append([
            concert.id,  
            concert.date.strftime('%Y-%m-%d') if concert.date else None,  # Convert date to string format
            concert.location,  
            concert.title,  
            float(concert.price) if concert.price else None,  
            concert.description, 
            concert.image.file.url if concert.image else "No Image",  
            concert.start_time.strftime('%H:%M:%S') if concert.start_time else None,  
            concert.end_time.strftime('%H:%M:%S') if concert.end_time else None,  
            concert.concert_type,  
            concert.artist,  
            concert.sold_out,
        ])
    
    body = { "values": concert_data }
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="Table!A2",
        valueInputOption="RAW",
        body=body
    ).execute()

@csrf_exempt
def create_concert(request) -> JsonResponse:
    """
    Example JSON payload to POST:
    {
        "title": "Awesome Concert",
        "name": "An Evening to Remember",
        "date": "2025-01-01",
        "location": "Carnegie Hall",
        "price": "49.99",
        "description": "<p>This is a <strong>great</strong> concert</p>",
        "start_time": "19:00",
        "end_time": "22:00",
        "concert_type": "Classical",
        "artist": "John Doe",
        "sold_out": false
    }
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            parent_page = Page.objects.get(slug="home")
            concert_page = ConcertIndexPage(
                title=data.get("title", ""),  # required by Wagtail
                name=data.get("name", ""),
                date=data.get("date", None),
                location=data.get("location", ""),
                price=data.get("price", 0),
                description=data.get("description", ""),
                start_time=data.get("start_time", None),
                end_time=data.get("end_time", None),
                concert_type=data.get("concert_type", ""),
                artist=data.get("artist", ""),
                sold_out=data.get("sold_out", False),
            )
            parent_page.add_child(instance=concert_page)
            concert_page.save_revision().publish()
            sync_sheets()
            return JsonResponse({
                "status": "success",
                "page_id": concert_page.id,
                "slug": concert_page.slug,
                "message": "Concert page created and published successfully!"
            }, status=201)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)

    # If not a POST request, return method not allowed.
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def remove_concert(request, concert_id: int) -> JsonResponse:
    """
    DELETE request to remove a single ConcertIndexPage by ID.
    """
    try:
        concert_page = ConcertIndexPage.objects.get(id=concert_id)
    except ConcertIndexPage.DoesNotExist:
        return JsonResponse({"error": "Concert not found"}, status=404)

    # Delete the page
    concert_page.delete()
    sync_sheets()

    return JsonResponse({
        "status": "success",
        "message": f"Concert {concert_id} removed successfully!"
    }, status=200)

@csrf_exempt
def update_concert(request, concert_id: int) -> JsonResponse:
    """
    PUT or PATCH request to update a single ConcertIndexPage by ID.
    Example request payload:
    {
      "title": "Updated Title",
      "name": "A Brand New Name",
      "date": "2025-02-02",
      "price": "59.99",
      ...
    }
    """
    if request.method not in ["PUT", "PATCH"]:
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        concert_page = ConcertIndexPage.objects.get(id=concert_id)
    except ConcertIndexPage.DoesNotExist:
        return JsonResponse({"error": "Concert not found"}, status=404)

    try:
        data = json.loads(request.body)
    except Exception as e:
        return JsonResponse({"error": "Invalid JSON payload", "details": str(e)}, status=400)

    if "date" in data and not data["date"]:
        return JsonResponse({"error": "date cannot be empty"}, status=400)

    # For demonstration, we handle fields only if they appear in data
    if "title" in data:
        concert_page.title = data["title"]
    if "name" in data:
        concert_page.name = data["name"]
    if "date" in data:
        concert_page.date = data["date"]
    if "location" in data:
        concert_page.location = data["location"]
    if "price" in data:
        concert_page.price = data["price"]
    if "description" in data:
        concert_page.description = data["description"]
    if "start_time" in data:
        concert_page.start_time = data["start_time"]
    if "end_time" in data:
        concert_page.end_time = data["end_time"]
    if "concert_type" in data:
        concert_page.concert_type = data["concert_type"]
    if "artist" in data:
        concert_page.artist = data["artist"]
    if "sold_out" in data:
        concert_page.sold_out = data["sold_out"]

    # Save and publish
    concert_page.save_revision().publish()
    sync_sheets()

    # Serialize the concert page metadata
    concert_metadata = {
        "id": concert_page.id,
        "title": concert_page.title,
        "name": concert_page.name,
        "date": str(concert_page.date),
        "location": concert_page.location,
        "price": str(concert_page.price),
        "description": concert_page.description,
        "start_time": str(concert_page.start_time) if concert_page.start_time else None,
        "end_time": str(concert_page.end_time) if concert_page.end_time else None,
        "concert_type": concert_page.concert_type,
        "artist": concert_page.artist,
        "last_updated": str(concert_page.latest_revision_created_at) if concert_page.latest_revision_created_at else None,
        "sold_out": concert_page.sold_out,
    }

    return JsonResponse({
        "status": "success",
        "message": f"Concert {concert_id} updated successfully!",
        "concert_metadata": concert_metadata,
    }, status=200)