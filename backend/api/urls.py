from django.urls import path
from . import views

urlpatterns = [
    path("concerts/", views.concert_list, name="concert_list"),
    path("concerts/<slug:concert_slug>/", views.concert_detail_by_slug, name="concert_detail_by_slug"),
    path("venues/", views.venue_list_create, name="venue_list_create"),
    path("venues/<slug:venue_slug>/", views.venue_detail, name="venue_detail"),
    path("venues/<slug:venue_slug>/zones/", views.zone_list, name="zone_list"),
    
    path("venues/<slug:venue_slug>/concerts/", views.concert_list_create, name="concert_list_create"),
    path("venues/<slug:venue_slug>/concerts/<slug:concert_slug>/", views.concert_detail, name="concert_detail"),
    
    path("venues/<slug:venue_slug>/concerts/<slug:concert_slug>/reserve-seats/", 
         views.reserve_seats, name="reserve_seats"),
    path("venues/<slug:venue_slug>/concerts/<slug:concert_slug>/availability/", 
         views.get_concert_availability, name="concert_availability"),
    
    path("ticket-types/<slug:ticket_type_slug>/", views.ticket_type_detail, name="ticket_type_detail"),
    path("venues/<slug:venue_slug>/zones/<slug:zone_slug>/", views.zone_detail, name="zone_detail"),
    path("venues/<slug:venue_slug>/zones/<slug:zone_slug>/seats/", views.zone_seats, name="zone_seats"),
]