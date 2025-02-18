# Generated by Django 5.1.6 on 2025-02-12 08:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bikes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='bike',
            name='owner',
            field=models.ForeignKey(help_text='Owner of the bike.', on_delete=django.db.models.deletion.CASCADE, related_name='bikes', to=settings.AUTH_USER_MODEL),
        ),
    ]
