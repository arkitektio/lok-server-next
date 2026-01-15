from django.contrib import admin
from authapp import models

# Register your models here.
admin.site.register(models.OAuth2Client)
admin.site.register(models.OAuth2Token)
