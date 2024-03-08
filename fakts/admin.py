from django.contrib import admin
from fakts.models import *

# Register your models here.
admin.site.register(App)
admin.site.register(Release)
admin.site.register(Composition)
admin.site.register(Service)
admin.site.register(ServiceInstance)
admin.site.register(Client)
admin.site.register(DeviceCode)
