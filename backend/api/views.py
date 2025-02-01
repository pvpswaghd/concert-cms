import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from wagtail.models import Page
from .models import VenuePage, ConcertPage, TicketType, SoldSeat, SeatZone, Seat
from django.db.models.deletion import ProtectedError
from django.utils.text import slugify
from .config import build_service, SPREADSHEET_ID
import json


def sync_to_google_sheets():
    """
    Full data sync with Google Sheets including all relationships
    """
    try:
        service = build_service()
        spreadsheet_id = SPREADSHEET_ID

        # Prepare venue data with image URLs
        venues_data = []
        for venue in VenuePage.objects.all():
            image_url = venue.image.file.url if venue.image else None
            venues_data.append([
                venue.name,
                venue.address,
                venue.capacity,
                venue.admission_mode,
                image_url
            ])

        # Prepare concert data with proper date/time formatting
        concerts_data = []
        for concert in ConcertPage.objects.all():
            image_url = concert.image.file.url if concert.image else None
            concerts_data.append([
                concert.title,
                concert.date.isoformat() if concert.date else '',  # Convert date to string
                concert.artist,
                concert.venue.name,
                concert.start_time.isoformat() if concert.start_time else '',  # Convert time to string
                concert.end_time.isoformat() if concert.end_time else '',  # Convert time to string
                concert.description or '',
                concert.genre or '',
                image_url
            ])

        # Prepare seat zones data with calculated totals
        seat_zones_data = []
        for zone in SeatZone.objects.select_related('venue').all():
            if zone.row_start and zone.row_end:
                rows = ord(zone.row_end.upper()) - ord(zone.row_start.upper()) + 1
                seats_per_row = zone.seat_end - zone.seat_start + 1
                total = rows * seats_per_row
            else:
                total = zone.capacity or 0
                
            seat_zones_data.append([
                zone.venue.name,
                zone.name,
                zone.row_start,
                zone.row_end,
                zone.seat_start,
                zone.seat_end,
                total,
                'Assigned' if zone.row_start else 'General'
            ])

        # Prepare ticket types data with explicit conversions
        ticket_types_data = []
        for tt in TicketType.objects.select_related('seat_zone').all():
            ticket_types_data.append([
                tt.concert.title,
                tt.type,
                float(tt.price),  # Convert Decimal to float
                tt.seat_zone.name if tt.seat_zone else '',
                tt.seat_zone.total_seats if tt.type == 'assigned' else tt.ga_capacity,
                tt.ga_capacity or 0,
                tt.sold,
                tt.remaining,
                tt.is_sold_out
            ])

        # Define sheets structure with properly formatted data
        sheets_config = {
            "Venues": {
                "headers": ["Name", "Address", "Capacity", "Admission Mode", "Image URL"],
                "data": venues_data
            },
            "SeatZones": {
                "headers": ["Venue Name", "Zone Name", "Row Start", "Row End", 
                          "Seat Start", "Seat End", "Total Seats", "Zone Type"],
                "data": seat_zones_data
            },
            "Concerts": {
                "headers": ["Name", "Date", "Artist", "Venue Name", 
                          "Start Time", "End Time", "Description", "Genre", "Image URL"],
                "data": concerts_data
            },
            "TicketTypes": {
                "headers": ["Concert Name", "Type", "Price", "Seat Zone", 
                          "Available", "Capacity", "Sold", "Remaining", "Is Sold Out"],
                "data": ticket_types_data
            }
        }

        for sheet_name, config in sheets_config.items():
            clear_range = f"{sheet_name}!A2:Z"
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=clear_range,
                body={}
            ).execute()

            if config['data']:
                body = {"values": config['data']}
                service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet_name}!A2",
                    valueInputOption="USER_ENTERED",
                    body=body
                ).execute()

        return True
    except Exception as e:
        print(f"Sync failed: {str(e)}")
        return False

# Helper functions
def add_hateoas_links(obj, links):
    """Add HATEOAS links to API responses"""
    return {**obj, '_links': links}

def validate_seat_zone(zone_data, index, admission_mode):
    """Enhanced validation considering venue admission mode"""
    try:
        validated_data = {
            'row_start': None,
            'row_end': None,
            'seat_start': None,
            'seat_end': None,
            'capacity': None
        }

        if admission_mode == 'mixed':
            zone_type = zone_data.get('type')
            if not zone_type:
                raise ValidationError(f"Missing 'type' in zone {index+1} for mixed venue")
            
            if zone_type == 'assigned':
                # Validate assigned seating
                row_validation = _validate_row(zone_data, index)
                seats_validation = _validate_seats(zone_data, index)
                validated_data.update({
                    'row_start': row_validation['start'],
                    'row_end': row_validation['end'],
                    'seat_start': seats_validation['start'],
                    'seat_end': seats_validation['end']
                })
            elif zone_type == 'general':
                # Validate general admission
                ga_validation = _validate_ga_fields(zone_data, index)
                validated_data['capacity'] = ga_validation['capacity']
            else:
                raise ValidationError(f"Invalid zone type '{zone_type}' in zone {index+1}")

        elif admission_mode == 'assigned':
            # Validate assigned seating
            row_validation = _validate_row(zone_data, index)
            seats_validation = _validate_seats(zone_data, index)
            validated_data.update({
                'row_start': row_validation['start'],
                'row_end': row_validation['end'],
                'seat_start': seats_validation['start'],
                'seat_end': seats_validation['end']
            })

        elif admission_mode == 'general':
            # Validate general admission
            ga_validation = _validate_ga_fields(zone_data, index)
            validated_data['capacity'] = int(ga_validation['capacity'])
        else:
            raise ValidationError(f"Invalid admission mode: {admission_mode}")
        return validated_data

    except KeyError as e:
        raise ValidationError(f"Missing required field {e} in zone {index+1}")
    except ValueError:
        raise ValidationError(f"Invalid number format in zone {index+1}")

# Helper validators
def _validate_row(zone_data, index):
    """Validate row format for assigned seating"""
    row_start = str(zone_data['row_start']).upper()
    row_end = str(zone_data['row_end']).upper()
    
    if len(row_start) != 1 or not row_start.isalpha():
        raise ValidationError(f"Invalid row_start in zone {index+1}")
    if len(row_end) != 1 or not row_end.isalpha():
        raise ValidationError(f"Invalid row_end in zone {index+1}")
    
    return {'start': row_start, 'end': row_end}

def _validate_seats(zone_data, index):
    """Validate seat range for assigned seating"""
    seat_start = int(zone_data['seat_start'])
    seat_end = int(zone_data['seat_end'])
    
    if seat_start < 1 or seat_end < seat_start:
        raise ValidationError(f"Invalid seat range in zone {index+1}")
    
    return {'start': seat_start, 'end': seat_end}

def _validate_ga_fields(zone_data, index):
    """Validate general admission parameters"""
    if 'ga_capacity' not in zone_data:
        raise ValidationError(f"GA zones require capacity in zone {index+1}")
    if int(zone_data.get('ga_capacity', 0)) <= 0:
        raise ValidationError(f"Invalid GA capacity in zone {index+1}")
    
    return {'capacity': zone_data['ga_capacity']}

def _validate_zone_type(zone_data, index):
    """Validate zone type for mixed venues"""
    zone_type = zone_data.get('type')
    if zone_type not in ['assigned', 'general']:
        raise ValidationError(f"Invalid zone type in zone {index+1}")
    return zone_type

# Venue Endpoints
@csrf_exempt
def venue_list_create(request):
    if request.method == 'GET':
        venues = VenuePage.objects.live().values('slug', 'name', 'address', 'capacity', 'admission_mode')
        return JsonResponse(list(venues), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            parent = Page.objects.get(slug='home')
            admission_mode = data.get('admission_mode', 'assigned')
            # Set BOTH title (Page) and name (VenuePage) from data['name']
            venue = VenuePage(
                title=data['name'],    # Wagtail's Page.title
                name=data['name'],     # VenuePage.name (your custom field)
                slug=data.get('slug') or slugify(data['name']),
                address=data['address'],
                admission_mode=admission_mode,
                capacity=data['capacity'],
            )
            parent.add_child(instance=venue)
            venue.save_revision().publish()

            # Now create seat zones
            seat_zones = []
            for idx, zone_data in enumerate(data.get('seat_zones', [])):
                validated = validate_seat_zone(zone_data, idx, admission_mode)
                
                zone = SeatZone(
                    venue=venue,  # Now venue has ID
                    name=zone_data['name'],
                    slug=zone_data.get('slug') or slugify(zone_data['name']),
                    row_start=validated.get('row_start'),
                    row_end=validated.get('row_end'),
                    seat_start=validated.get('seat_start'),
                    seat_end=validated.get('seat_end'),
                    capacity=validated.get('ga_capacity')
                )
                seat_zones.append(zone)
            
            # Bulk create after venue exists in DB
            SeatZone.objects.bulk_create(seat_zones)
            sync_to_google_sheets()
            return JsonResponse(add_hateoas_links(
                {
                    'slug': venue.slug,
                    'message': f'Venue {venue.title} created',
                    'zones': [z.slug for z in seat_zones]
                },
                {
                    'self': f'/api/venues/{venue.slug}/',
                    'concerts': f'/api/venues/{venue.slug}/concerts/',
                    'zones': f'/api/venues/{venue.slug}/zones/'
                }
            ), status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def venue_detail(request, venue_slug):
    """Handle venue CRUD operations"""
    venue = get_object_or_404(VenuePage, slug=venue_slug)
    
    if request.method == 'GET':
        data = {
            'address': venue.address,
            'slug': venue.slug,
            'title': venue.title,
            'name': venue.name,
            'capacity': venue.capacity,
            'admission_mode': venue.admission_mode,
            'zones': [{
                'id': z.id,
                'slug': z.slug,
                'name': z.name,
                'total_seats': z.total_seats,
                'row_start': z.row_start,
                'row_end': z.row_end,
                'seat_start': z.seat_start,
                'seat_end': z.seat_end,
                'total_seats': z.total_seats,
                'ga_capacity': z.capacity,
                'type': z.type,
            } for z in venue.seat_zones.all()]
        }
        return JsonResponse(add_hateoas_links(data, {
            'concerts': f'/api/venues/{venue.slug}/concerts/',
            'zones': f'/api/venues/{venue.slug}/zones/'
        }))
    
    elif request.method in ['PUT', 'PATCH']:
        from django.db import transaction
        try:
            with transaction.atomic():
                data = json.loads(request.body)
                venue.title = data.get('name', venue.title)
                venue.address = data.get('address', venue.address)
                venue.capacity = data.get('capacity', venue.capacity)
                venue.admission_mode = data.get('admission_mode', venue.admission_mode)

                if 'seat_zones' in data:
                    seen_slugs = set()
                    
                    # Process seat zones
                    for zone_data in data['seat_zones']:
                        validated = validate_seat_zone(zone_data, 0, zone_data.get("type"))
                        slug = zone_data.get('slug') or slugify(zone_data['name'])
                        seen_slugs.add(slug)
                        
                        # Wagtail-friendly update_or_create
                        zone, created = SeatZone.objects.update_or_create(
                            venue=venue,
                            slug=slug,
                            defaults={**validated}
                        )
                    # Delete unused zones (not referenced by TicketType)
                    for zone in venue.seat_zones.exclude(slug__in=seen_slugs):
                        if not TicketType.objects.filter(seat_zone=zone).exists():
                            zone.delete()

                # Wagtail revision system
                revision = venue.save_revision()
                revision.publish()
                sync_to_google_sheets()
                
                return JsonResponse({'message': 'Venue updated successfully'})

        except Exception as e:
            print(e)
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        try:
            venue.delete()
            sync_to_google_sheets()
            return JsonResponse({'message': f'Venue {venue.title} deleted'})
        except ProtectedError:
            return JsonResponse({
                'error': 'Cannot delete venue with existing concerts',
                'solution': 'Delete all associated concerts first'
            }, status=409)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Concert Endpoints
@csrf_exempt
def concert_list_create(request, venue_slug):
    """Handle concert creation and listing under a venue"""
    venue = get_object_or_404(VenuePage, slug=venue_slug)
    
    if request.method == 'GET':
        concerts = venue.concerts.live().values('slug', 'title', 'date', 'artist')
        return JsonResponse(list(concerts), safe=False)
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            concert = ConcertPage(
                title=data['name'],
                slug=data.get('slug') or slugify(data['name']),
                date=data['date'],
                venue=venue,
                artist=data['artist'],
                start_time=data['start_time'],
                end_time=data.get('end_time'),
                description=data.get('description'),
            )
            
            # Create ticket types
            ticket_types = []
            for tt_data in data.get('ticket_types', []):
                # Get zone from submitted data
                print(tt_data)
                zone = get_object_or_404(SeatZone, 
                    slug=tt_data['seat_zone_slug'],
                    venue=venue
                )
                
                # Determine ticket type from zone type
                ticket_type = 'assigned' if zone.type == 'assigned' else 'general'
                
                ticket_types.append(TicketType(
                    concert=concert,
                    type=ticket_type,
                    seat_zone=zone,
                    price=tt_data['price'],
                    # For general admission, use zone's capacity
                    ga_capacity=zone.capacity if zone.type == 'general' else None,
                    slug=tt_data.get('slug') or slugify(f"{concert.slug}-{zone.slug}")
                ))
            
            # Save everything
            venue.add_child(instance=concert)
            TicketType.objects.bulk_create(ticket_types)
            concert.save_revision().publish()
            sync_to_google_sheets()
            return JsonResponse(add_hateoas_links(
                {
                    'slug': concert.slug,
                    'message': f'Concert {concert.title} created',
                    'ticket_types': [tt.slug for tt in ticket_types]
                },
                {
                    'self': f'/api/venues/{venue.slug}/concerts/{concert.slug}/',
                    'availability': f'/api/venues/{venue.slug}/concerts/{concert.slug}/availability/'
                }
            ), status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def concert_list(request):
    """List all concerts across all venues"""
    try:
        concerts = []
        for concert in ConcertPage.objects.select_related('venue').all():
            concerts.append({
                'id': concert.id,
                'title': concert.title,
                'slug': concert.slug,
                'date': concert.date.isoformat() if concert.date else '',
                'artist': concert.artist,
                'venue': concert.venue.name,
                'start_time': concert.start_time.isoformat() if concert.start_time else '',
                'end_time': concert.end_time.isoformat() if concert.end_time else '',
                'sold_out': concert.sold_out,
                'description': concert.description or '',
                'genre': concert.genre or '',
                'image_url': concert.image.file.url if concert.image else None,
                '_links': {
                    'self': f'/api/venues/{concert.venue.slug}/concerts/{concert.slug}/',
                    'tickets': f'/api/venues/{concert.venue.slug}/concerts/{concert.slug}/availability/'
                }
            })
        return JsonResponse(concerts, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# views.py
@csrf_exempt
def concert_detail_by_slug(request, concert_slug):
    """Get concert details by slug without requiring venue slug"""
    print(concert_slug)
    try:
        concert = get_object_or_404(ConcertPage, slug=concert_slug)

        ticket_types = []
        for tt in concert.ticket_types.all():
            ticket_data = {
                'type': tt.type,
                'price': float(tt.price),  # Convert Decimal to float
                'remaining': tt.remaining,
                'is_sold_out': tt.is_sold_out
            }
            
            if tt.type == 'assigned':
                ticket_data['seat_zone'] = {
                    'name': tt.seat_zone.name,
                    'total_seats': tt.seat_zone.total_seats
                } if tt.seat_zone else None
            else:
                ticket_data['seat_zone'] = {
                    'name': tt.seat_zone.name,
                }
                ticket_data['ga_capacity'] = tt.ga_capacity
                
            ticket_types.append(ticket_data)
        print(ticket_types)
        data = {
            'id': concert.id,
            'title': concert.title,
            'slug': concert.slug,
            'date': concert.date.isoformat() if concert.date else '',
            'artist': concert.artist,
            'venue': concert.venue.name,
            'venue_slug': concert.venue.slug,  # Include venue slug for compatibility
            'start_time': concert.start_time.isoformat() if concert.start_time else '',
            'end_time': concert.end_time.isoformat() if concert.end_time else '',
            'sold_out': concert.sold_out,
            'description': concert.description or '',
            'genre': concert.genre or '',
            'image_url': concert.image.file.url if concert.image else None,
            'ticket_types': ticket_types,
            '_links': {
                'venue': f'/api/venues/{concert.venue.slug}/',
                'self': f'/api/concerts/{concert.slug}/'
            }
        }
        return JsonResponse(data)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def concert_detail(request, venue_slug, concert_slug):
    """Handle concert CRUD operations"""
    concert = get_object_or_404(ConcertPage, slug=concert_slug, venue__slug=venue_slug)

    if request.method == 'GET':
        try:
            ticket_types = []
            for tt in concert.ticket_types.all():
                ticket_type_data = {
                    'slug': tt.slug,
                    'type': tt.type,
                    'price': str(tt.price),
                    'remaining': tt.remaining,
                    'is_sold_out': tt.is_sold_out
                }
                if tt.type == 'assigned':
                    ticket_type_data['seat_zone'] = tt.seat_zone.slug if tt.seat_zone else None
                else:
                    ticket_type_data['seat_zone'] = tt.seat_zone.slug if tt.seat_zone else None
                    ticket_type_data['ga_capacity'] = tt.ga_capacity
                ticket_types.append(ticket_type_data)

            print(ticket_types)

            return JsonResponse({
                'slug': concert.slug,
                'name': concert.title,
                'date': concert.date.isoformat(),
                'artist': concert.artist,
                'start_time': concert.start_time.strftime('%H:%M'),
                'end_time': concert.end_time.strftime('%H:%M') if concert.end_time else None,
                'description': concert.description,
                'genre': concert.genre,
                'ticket_types': ticket_types,
                '_links': {
                    'image': concert.image.file.url if concert.image else None
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method in ['PUT', 'PATCH']:
        try:
            data = json.loads(request.body)
            
            # Update core concert data
            concert.title = data.get('name', concert.title)
            concert.date = data.get('date', concert.date)
            concert.artist = data.get('artist', concert.artist)
            concert.start_time = data.get('start_time', concert.start_time)
            concert.end_time = data.get('end_time', concert.end_time)
            concert.description = data.get('description', concert.description)
            concert.genre = data.get('genre', concert.genre)

            # Handle venue change
            if 'venue' in data and concert.venue.slug != data['venue']:
                new_venue = get_object_or_404(VenuePage, slug=data['venue'])
                concert.move(new_venue, pos='last-child')

            # Process ticket types
            if 'ticket_types' in data:
                existing_tickets = {tt.slug: tt for tt in concert.ticket_types.all()}
                print("existing_tickets:", existing_tickets)
                seen_slugs = set()

                for tt_data in data['ticket_types']:
                    # Generate slug if missing
                    print(tt_data)
                    slug = tt_data.get('slug') or slugify(f"{concert.slug}-{tt_data['type']}-{len(seen_slugs)}")
                    seen_slugs.add(slug)
                    
                    # Validate seat zone for assigned tickets
                    seat_zone = get_object_or_404(
                        SeatZone, 
                        slug=tt_data['seat_zone_slug'], 
                        venue=concert.venue
                    )

                    # Create or update ticket type
                    tt, created = TicketType.objects.update_or_create(
                        concert=concert,
                        slug=slug,
                        defaults={
                            'type': tt_data['type'],
                            'price': tt_data['price'],
                            'seat_zone': seat_zone,
                            'ga_capacity': tt_data.get('ga_capacity')
                        }
                    )

                # Delete removed ticket types
                for slug in existing_tickets.keys() - seen_slugs:
                    TicketType.objects.filter(concert=concert, slug=slug).delete()
            print("Updated payload:", data)
            concert.save_revision().publish()
            sync_to_google_sheets()
            return JsonResponse({'message': 'Concert updated successfully'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        try:
            concert.delete()
            sync_to_google_sheets()
            return JsonResponse({'message': f'Concert {concert.title} deleted'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Seat Operations
@csrf_exempt
def reserve_seats(request, venue_slug, concert_slug):
    """Reserve seats for a concert"""
    concert = get_object_or_404(ConcertPage, 
        slug=concert_slug, 
        venue__slug=venue_slug
    )
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ticket_type = get_object_or_404(
                TicketType, 
                slug=data['ticket_type_slug'],
                concert=concert
            )
            
            if ticket_type.type != 'assigned':
                return JsonResponse({'error': 'Ticket type does not support seat selection'}, 400)
                
            seats = list(Seat.objects.filter(
                zone__venue=concert.venue,
                identifier__in=data['seat_ids']
            ).distinct())
            
            if len(seats) != len(data['seat_ids']):
                return JsonResponse({'error': 'Invalid seat selection'}, 400)
                
            if SoldSeat.objects.filter(concert=concert, seat__in=seats).exists():
                return JsonResponse({'error': 'Some seats already taken'}, 409)
            
            SoldSeat.objects.bulk_create([
                SoldSeat(concert=concert, seat=seat) for seat in seats
            ])
            sync_to_google_sheets()
            return JsonResponse({
                'reserved_seats': data['seat_ids'],
                'remaining': ticket_type.remaining,
                'is_sold_out': ticket_type.is_sold_out
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def get_concert_availability(request, venue_slug, concert_slug):
    """Get concert ticket availability"""
    concert = get_object_or_404(ConcertPage, 
        slug=concert_slug, 
        venue__slug=venue_slug
    )
    
    availability = []
    for tt in concert.ticket_types.all():
        availability.append({
            'slug': tt.slug,
            'type': tt.type,
            'price': str(tt.price),
            'remaining': tt.remaining,
            'is_sold_out': tt.is_sold_out,
            'zone': tt.seat_zone.slug if tt.seat_zone else None
        })
    return JsonResponse({'ticket_types': availability})

# Ticket Type Operations
@csrf_exempt
def ticket_type_detail(request, ticket_type_slug):
    """Handle ticket type updates"""
    tt = get_object_or_404(TicketType, slug=ticket_type_slug)
    
    if request.method in ['PUT', 'PATCH']:
        try:
            data = json.loads(request.body)
            
            if 'price' in data:
                tt.price = data['price']
            
            if tt.type == 'general' and 'ga_capacity' in data:
                if data['ga_capacity'] < tt.sold:
                    raise ValidationError('Capacity cannot be less than sold tickets')
                tt.ga_capacity = data['ga_capacity']
            
            tt.save()
            sync_to_google_sheets()            
            return JsonResponse({
                'remaining': tt.remaining,
                'is_sold_out': tt.is_sold_out
            })
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
@csrf_exempt
def zone_list(request, venue_slug):
    """List and manage seat zones for a venue"""
    venue = get_object_or_404(VenuePage, slug=venue_slug)
    
    if request.method == 'GET':
        zones = []
        for zone in venue.seat_zones.all():
            zones.append({
                'slug': zone.slug,
                'name': zone.name,
                'row_start': zone.row_start,
                'row_end': zone.row_end,
                'seat_start': zone.seat_start,
                'seat_end': zone.seat_end,
                'total_seats': zone.total_seats,
                'type': zone.type,
                '_links': {
                    'self': f'/api/venues/{venue.slug}/zones/{zone.slug}/',
                    'seats': f'/api/venues/{venue.slug}/zones/{zone.slug}/seats/'
                }
            })
        return JsonResponse(zones, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            validated = validate_seat_zone(data, 0)  # index 0 for single zone
            zone = SeatZone(
                venue=venue,
                slug=data.get('slug') or slugify(data['name']),
                name=data['name'],
                **validated
            )
            zone.save()
            sync_to_google_sheets()            
            return JsonResponse(add_hateoas_links(
                {
                    'slug': zone.slug,
                    'message': 'Zone created',
                    'total_seats': zone.total_seats
                },
                {
                    'self': f'/api/venues/{venue.slug}/zones/{zone.slug}/',
                    'seats': f'/api/venues/{venue.slug}/zones/{zone.slug}/seats/'
                }
            ), status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def zone_detail(request, venue_slug, zone_slug):
    """Get/modify a specific zone in a venue"""
    zone = get_object_or_404(SeatZone, slug=zone_slug, venue__slug=venue_slug)
    
    if request.method == 'GET':
        data = {
            'slug': zone.slug,
            'name': zone.name,
            'row_start': zone.row_start,
            'row_end': zone.row_end,
            'seat_start': zone.seat_start,
            'seat_end': zone.seat_end,
            'total_seats': zone.total_seats,
            '_links': {
                'seats': f'/api/venues/{venue_slug}/zones/{zone_slug}/seats/'
            }
        }
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def zone_seats(request, venue_slug, zone_slug):
    """List seats in a specific zone"""
    seats = Seat.objects.filter(zone__slug=zone_slug, zone__venue__slug=venue_slug)
    return JsonResponse({
        'seats': [seat.identifier for seat in seats]
    })