from django.urls import path
from . import views

urlpatterns = [
    # Venue endpoints
    path("venues/", views.venue_list_create, name="venue_list_create"),
    path("venues/<slug:venue_slug>/", views.venue_detail, name="venue_detail"),
    path("venues/<slug:venue_slug>/zones/", views.zone_list, name="zone_list"),
    
    # Concert endpoints (nested under venues)
    path("venues/<slug:venue_slug>/concerts/", views.concert_list_create, name="concert_list_create"),
    path("venues/<slug:venue_slug>/concerts/<slug:concert_slug>/", views.concert_detail, name="concert_detail"),
    
    # Seat operations
    path("venues/<slug:venue_slug>/concerts/<slug:concert_slug>/reserve-seats/", 
         views.reserve_seats, name="reserve_seats"),
    path("venues/<slug:venue_slug>/concerts/<slug:concert_slug>/availability/", 
         views.get_concert_availability, name="concert_availability"),
    
    # Ticket types
    path("ticket-types/<slug:ticket_type_slug>/", views.ticket_type_detail, name="ticket_type_detail"),
]