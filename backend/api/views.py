import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from wagtail.models import Page
from .models import VenuePage, ConcertPage, TicketType, SoldSeat, SeatZone, Seat
from django.db.models.deletion import ProtectedError
from django.utils.text import slugify

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
            'ga_capacity': None
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
                validated_data['ga_capacity'] = ga_validation['capacity']
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
            validated_data['ga_capacity'] = ga_validation['capacity']
        else:
            raise ValidationError(f"Invalid admission mode: {admission_mode}")
        print(validated_data)
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
    print("hi")
    if request.method == 'GET':
        venues = VenuePage.objects.live().values('slug', 'name', 'address', 'capacity', 'admission_mode')
        return JsonResponse(list(venues), safe=False)
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            parent = Page.objects.get(slug='home')
            admission_mode = data.get('admission_mode', 'assigned')
            print(data)
            # Set BOTH title (Page) and name (VenuePage) from data['name']
            venue = VenuePage(
                title=data['name'],    # Wagtail's Page.title
                name=data['name'],     # VenuePage.name (your custom field)
                slug=data.get('slug') or slugify(data['name']),
                address=data['address'],
                admission_mode=admission_mode,
                capacity=data['capacity'],
            )
            print("Hi")
            parent.add_child(instance=venue)
            venue.save_revision().publish()

            print("Bye")
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
            print("oops")
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
                'slug': z.slug,
                'name': z.name,
                'total_seats': z.total_seats
            } for z in venue.seat_zones.all()]
        }
        return JsonResponse(add_hateoas_links(data, {
            'concerts': f'/api/venues/{venue.slug}/concerts/',
            'zones': f'/api/venues/{venue.slug}/zones/'
        }))
    
    elif request.method in ['PUT', 'PATCH']:
        try:
            data = json.loads(request.body)
            venue.title = data.get('name', venue.title)
            venue.address = data.get('address', venue.address)
            venue.capacity = data.get('capacity', venue.capacity)
            venue.admission_mode = data.get('admission_mode', venue.admission_mode)
            
            if 'seat_zones' in data:
                venue.seat_zones.all().delete()
                for zone_data in data['seat_zones']:
                    validated = validate_seat_zone(zone_data, 0)
                    venue.seat_zones.create(
                        slug=zone_data.get('slug') or slugify(zone_data['name']),
                        **validated
                    )
            
            venue.save_revision().publish()
            return JsonResponse({'message': 'Venue updated successfully'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        try:
            venue.delete()
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
                tt_type = tt_data['type']
                if tt_type == 'assigned':
                    zone = get_object_or_404(SeatZone, 
                        slug=tt_data['seat_zone_slug'],
                        venue=venue
                    )
                    ticket_types.append(TicketType(
                        concert=concert,
                        type=tt_type,
                        seat_zone=zone,
                        price=tt_data['price'],
                        slug=tt_data.get('slug') or slugify(f"{concert.slug}-{zone.slug}")
                    ))
                elif tt_type == 'general':
                    ticket_types.append(TicketType(
                        concert=concert,
                        type=tt_type,
                        ga_capacity=tt_data['ga_capacity'],
                        price=tt_data['price'],
                        slug=tt_data.get('slug') or slugify(f"{concert.slug}-general")
                    ))
                else:
                    raise ValidationError(f"Invalid ticket type: {tt_type}")
            
            # Save everything
            venue.add_child(instance=concert)
            TicketType.objects.bulk_create(ticket_types)
            concert.save_revision().publish()

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
            concert.title = data.get('name', concert.title)
            concert.date = data.get('date', concert.date)
            concert.artist = data.get('artist', concert.artist)
            concert.start_time = data.get('start_time', concert.start_time)
            concert.end_time = data.get('end_time', concert.end_time)
            concert.description = data.get('description', concert.description)
            
            if 'venue_slug' in data and concert.venue.slug != data['venue_slug']:
                new_venue = get_object_or_404(VenuePage, slug=data['venue_slug'])
                concert.move(new_venue, pos='last-child')
            
            concert.save_revision().publish()
            return JsonResponse({'message': 'Concert updated successfully'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        try:
            concert.delete()
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