from django.contrib import admin
from .models import User

class AppAdmin(admin.ModelAdmin):
    search_fields = ('email',)

# Register your models here.
admin.site.register(User, AppAdmin)

        
