from django.contrib import admin

from users.models import User, OwnerProfile

# Register your models here.
admin.site.register([User,OwnerProfile])