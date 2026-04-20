from django.contrib import admin
from .models import *
from django.contrib.auth.models import User,Group

admin.site.unregister(User) 
admin.site.unregister(Group)

admin.site.register(User) 
admin.site.register(Author) 
admin.site.register(Category) 
admin.site.register(Book) 
admin.site.register(Review) 