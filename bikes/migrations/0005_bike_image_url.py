from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [('bikes', '0004_bike_next_maintenance_date_alter_bike_chassis_no_and_more')]
    operations = [
        migrations.AddField(
            model_name='bike', name='image_url',
            field=models.URLField(blank=True, max_length=1000,
                                  validators=[django.core.validators.URLValidator(schemes=['https'])],
                                  help_text='Optional direct HTTPS image URL. Takes priority over an upload. Use a source you own or have permission to display, not a Google search-page URL.'),
        ),
        migrations.AlterField(
            model_name='bike', name='image',
            field=models.ImageField(blank=True, default='default_bike.png', upload_to='bikes/',
                                    help_text='Upload a photo, or use the external image URL below.'),
        ),
    ]
