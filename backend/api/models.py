from django.db import models
from modelcluster.models import ClusterableModel
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from modelcluster.fields import ParentalKey
from wagtail.models import Page, Orderable
from wagtail.admin.panels import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.api import APIField
from rest_framework.serializers import ModelSerializer
from rest_framework.fields import IntegerField

class VenuePage(Page):
    ADMISSION_TYPES = (
        ('assigned', 'Assigned Seating Only'),
        ('general', 'General Admission Only'),
        ('mixed', 'Both Assigned and General Admission'),
    )
    admission_mode = models.CharField(
        max_length=10,
        choices=ADMISSION_TYPES,
        default='assigned',
        help_text="Allowed admission types for this venue"
    )
    name = models.CharField(max_length=100, help_text="Venue name")
    address = models.TextField(help_text="Venue address")
    capacity = models.IntegerField(help_text="Total seating capacity")
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    @property
    def seats(self):
        """Get all seats across all zones in this venue"""
        return Seat.objects.filter(zone__venue=self)

    content_panels = Page.content_panels + [
        FieldPanel('name'),
        FieldPanel('address'),
        FieldPanel('capacity'),
        FieldPanel('image'),
        InlinePanel('seat_zones', label="Seat Zones"),
    ]

    api_fields = [
        APIField('name'),
        APIField('address'),
        APIField('capacity'),
        APIField('image'),
        APIField('seats'),
    ]

# 2. Define SeatZone after VenuePage
class SeatZone(Orderable):
    venue = ParentalKey(VenuePage, on_delete=models.CASCADE, related_name='seat_zones')
    name = models.CharField(max_length=100, help_text="Zone name (e.g., Front Zone)")
    row_start = models.CharField(max_length=1, help_text="Starting row (e.g., A)", null=True)
    row_end = models.CharField(max_length=1, help_text="Ending row (e.g., D)", null=True)
    seat_start = models.PositiveIntegerField(help_text="Starting seat number (e.g., 1)", null=True)
    seat_end = models.PositiveIntegerField(help_text="Last seat number (e.g., 10)", null=True)
    slug = models.SlugField(max_length=50, unique=False, null=True)
    capacity = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.row_start and self.row_end and self.seat_start and self.seat_end:
            self.row_start = self.row_start.upper()
            self.row_end = self.row_end.upper()
            if not self.slug:
                self.slug = slugify(self.name)
            super().save(*args, **kwargs)
            self.generate_seats()
        else:
            super().save(*args, **kwargs)

    def generate_seats(self):
        # Only generate seats if this is an assigned zone
        if self.row_start and self.row_end and self.seat_start and self.seat_end:
            Seat.objects.filter(zone=self).delete()
            for row_code in range(ord(self.row_start), ord(self.row_end) + 1):
                row = chr(row_code)
                for seat_num in range(self.seat_start, self.seat_end + 1):
                    Seat.objects.create(
                        zone=self,
                        row=row,
                        number=seat_num,
                        identifier=f"{row}{seat_num}"
                    )
    @property
    def type(self):
        if self.capacity and not (self.row_start and self.row_end and self.seat_start and self.seat_end):
            return 'general'
        return 'assigned'
    @property
    def total_seats(self):
        print(self.capacity, self.name, self.row_start, self.row_end, self.seat_start, self.seat_end)
        if not (self.row_start and self.row_end and self.seat_start and self.seat_end):
            return self.capacity
        rows = ord(self.row_end) - ord(self.row_start) + 1
        seats_per_row = self.seat_end - self.seat_start + 1
        return rows * seats_per_row

# 3. Define Seat model
class Seat(models.Model):
    zone = models.ForeignKey(SeatZone, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=1)
    number = models.PositiveIntegerField()
    identifier = models.CharField(max_length=10)

    def __str__(self):
        return self.identifier

# 4. Define serializer AFTER all models are declared
class SeatZoneSerializer(ModelSerializer):
    total_seats = IntegerField(read_only=True)
    
    class Meta:
        model = SeatZone
        fields = [
            'id', 
            'name', 
            'row_start', 
            'row_end', 
            'seat_start', 
            'seat_end', 
            'total_seats'
        ]

# 5. Add seat_zones API field to VenuePage
VenuePage.api_fields.append(
    APIField('seat_zones', serializer=SeatZoneSerializer(many=True))
)

class ConcertPage(Page):
    date = models.DateField()
    venue = models.ForeignKey(
        VenuePage,
        on_delete=models.PROTECT,
        related_name='concerts',
        help_text="Select the venue for this concert"
    )
    artist = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    description = models.TextField(blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True, null=True)

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        PageChooserPanel('venue', 'api.VenuePage'),  # Ensure app name matches yours
        FieldPanel('artist'),
        FieldPanel('start_time'),
        InlinePanel('ticket_types', label="Ticket Pricing by Zone"),
        FieldPanel('end_time'),
        FieldPanel('image'),
        FieldPanel('description'),
        FieldPanel('genre'),
    ]

    api_fields = [
        APIField('date'),
        APIField('venue'),
        APIField('artist'),
        APIField('start_time'),
        APIField('end_time'),
        APIField('image'),
        APIField('description'),
        APIField('ticket_types'),
        APIField('genre'),
    ]

    @property
    def sold_out(self):
        """Check if all ticket types are sold out."""
        return all(tt.is_sold_out for tt in self.ticket_types.all())
    
    def clean(self):
        super().clean()
        venue_mode = self.venue.admission_mode
        
        # Validate ticket types against venue's admission mode
        if venue_mode == 'assigned' and self.ticket_types.filter(type='general').exists():
            raise ValidationError("This venue only allows assigned seating tickets.")
            
        if venue_mode == 'general' and self.ticket_types.filter(type='assigned').exists():
            raise ValidationError("This venue only allows general admission tickets.")

class SoldSeat(models.Model):
    concert = models.ForeignKey(ConcertPage, on_delete=models.CASCADE, related_name='sold_seats')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('concert', 'seat')  # Prevent duplicate sales

class TicketType(Orderable):
    TICKET_TYPES = (
        ('assigned', 'Assigned Seating'),
        ('general', 'General Admission'),
    )
    
    concert = ParentalKey(ConcertPage, on_delete=models.CASCADE, related_name='ticket_types')
    type = models.CharField(max_length=10, choices=TICKET_TYPES)
    slug = models.SlugField(max_length=50, unique=False, null=True)
    
    # For assigned seating
    seat_zone = models.ForeignKey(
        SeatZone, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text="Required for assigned seating tickets"
    )
    
    # For general admission
    ga_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum tickets for general admission"
    )
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sold = models.PositiveIntegerField(default=0)

    # Validation
    def clean(self):
        if self.type == 'assigned' and not self.seat_zone:
            raise ValidationError("Assigned tickets require a seat zone.")
            
        if self.type == 'general' and not self.ga_capacity:
            raise ValidationError("General admission tickets require capacity.")

    @property
    def remaining(self):
        if self.type == 'assigned':
            return self.seat_zone.seats.count() - SoldSeat.objects.filter(
                concert=self.concert, 
                seat__zone=self.seat_zone
            ).count()
        else:
            return self.ga_capacity - self.sold

    @property
    def is_sold_out(self):
        return self.remaining <= 0
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    panels = [
        FieldPanel('seat_zone'),
        FieldPanel('price'),
        FieldPanel('sold'),
        FieldPanel('ga_capacity'),
        FieldPanel('type'),
    ]

    api_fields = [
        APIField('seat_zone'),
        APIField('price'),
        APIField('remaining'),
        APIField('is_sold_out'),
        APIField('type'),
    ]