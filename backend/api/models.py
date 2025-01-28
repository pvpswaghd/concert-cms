from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.images.models import Image
from wagtail.admin.panels import FieldPanel
from django.db import models
from wagtail.api import APIField

class ConcertIndexPage(Page):
    name = models.CharField(max_length=100)
    date = models.DateField()
    location = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = RichTextField(blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    concert_type = models.CharField(max_length=100)
    artist = models.CharField(max_length=100)

    content_panels = Page.content_panels + [
        FieldPanel('name'),
        FieldPanel('date'),
        FieldPanel('location'),
        FieldPanel('price'),
        FieldPanel('description'),
        FieldPanel('image'),
        FieldPanel('start_time'),
        FieldPanel('end_time'),
        FieldPanel('concert_type'),
        FieldPanel('artist'),
    ]

    api_fields = [
        APIField('name'),
        APIField('date'),
        APIField('location'),
        APIField('price'),
        APIField('description'),
        APIField('image'),
        APIField('start_time'),
        APIField('end_time'),
        APIField('concert_type'),
        APIField('artist'),
    ]

class Ticket(models.Model):
    ticket_id = models.AutoField(primary_key=True)
    concert = models.ForeignKey(ConcertIndexPage, on_delete=models.CASCADE, related_name="tickets")
    user_name = models.CharField(max_length=100) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seat = models.CharField(max_length=100)
    status = models.CharField(max_length=100)  
    purchase_date = models.DateField()
    purchase_time = models.TimeField()
    quantity = models.IntegerField()

    def __str__(self):
        return f"Ticket for {self.concert.name} - Seat {self.seat}"

class GoogleSheetUpdateMeta(models.Model):
    sheet_id = models.AutoField(primary_key=True)
    sheet_name = models.CharField(max_length=100)
    action = models.CharField(max_length=100)  
    concert = models.ForeignKey(ConcertIndexPage, on_delete=models.CASCADE, related_name="sheet_updates")
    modified_date = models.DateField()
    modified_time = models.TimeField()

    def __str__(self):
        return f"GoogleSheetUpdate for {self.concert.name} ({self.action})"