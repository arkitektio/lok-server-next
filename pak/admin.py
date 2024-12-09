from django.contrib import admin

# Register your models here.

from .models import Stash, StashItem

admin.site.register(Stash)
admin.site.register(StashItem)
