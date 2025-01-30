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
    sold_out = models.BooleanField(default=False)

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
        FieldPanel('sold_out'),
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
        APIField('sold_out'),
    ]

class TicketVariant(models.Model):
    concert = models.ForeignKey(
        ConcertIndexPage,
        on_delete=models.CASCADE,
        related_name='ticket_variants'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seat_section = models.CharField(max_length=50, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    total_quantity = models.PositiveIntegerField()
    remaining_quantity = models.PositiveIntegerField()

class Ticket(models.Model):
    ticket_id = models.AutoField(primary_key=True)
    variant = models.ForeignKey(
        TicketVariant,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    user_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seat = models.CharField(max_length=100, blank=True, null=True) 
    status = models.CharField(max_length=100, default="Active")
    purchase_date = models.DateField(auto_now_add=True)
    purchase_time = models.TimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField(default=1)

class UpdateMeta(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
    ]

    sheet_id = models.AutoField(primary_key=True)
    sheet_name = models.CharField(max_length=100)
    action = models.CharField(max_length=100, choices=ACTION_CHOICES)
    concert = models.ForeignKey(
        ConcertIndexPage,
        on_delete=models.CASCADE,
        related_name="sheet_updates"
    )
    modified_date = models.DateField(auto_now=True)
    modified_time = models.TimeField(auto_now=True)