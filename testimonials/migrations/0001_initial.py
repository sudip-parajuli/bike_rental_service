# Generated by Django 5.1.6 on 2025-02-12 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Testimonial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='Content of the testimonial.', max_length=500)),
                ('rating', models.PositiveIntegerField(help_text='Rating given by the user (1–5 stars).')),
                ('is_approved', models.BooleanField(default=False, help_text='Indicates whether the testimonial is approved by the admin.')),
                ('is_featured', models.BooleanField(default=False, help_text='Indicates whether the testimonial is featured on the homepage.')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp for when the testimonial was submitted.')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Timestamp for the last update.')),
            ],
        ),
    ]
