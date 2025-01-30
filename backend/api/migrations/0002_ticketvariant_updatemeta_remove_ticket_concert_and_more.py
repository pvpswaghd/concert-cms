# Generated by Django 4.2.18 on 2025-01-30 16:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TicketVariant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, null=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "seat_section",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                ("is_available", models.BooleanField(default=True)),
                ("total_quantity", models.PositiveIntegerField()),
                ("remaining_quantity", models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="UpdateMeta",
            fields=[
                ("sheet_id", models.AutoField(primary_key=True, serialize=False)),
                ("sheet_name", models.CharField(max_length=100)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("CREATE", "Create"),
                            ("UPDATE", "Update"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=100,
                    ),
                ),
                ("modified_date", models.DateField(auto_now=True)),
                ("modified_time", models.TimeField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name="ticket",
            name="concert",
        ),
        migrations.AddField(
            model_name="concertindexpage",
            name="sold_out",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="purchase_date",
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="purchase_time",
            field=models.TimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="quantity",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="seat",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="status",
            field=models.CharField(default="Active", max_length=100),
        ),
        migrations.DeleteModel(
            name="GoogleSheetUpdateMeta",
        ),
        migrations.AddField(
            model_name="updatemeta",
            name="concert",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sheet_updates",
                to="api.concertindexpage",
            ),
        ),
        migrations.AddField(
            model_name="ticketvariant",
            name="concert",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ticket_variants",
                to="api.concertindexpage",
            ),
        ),
        migrations.AddField(
            model_name="ticket",
            name="variant",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tickets",
                to="api.ticketvariant",
            ),
            preserve_default=False,
        ),
    ]
