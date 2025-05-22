from django.contrib import admin
from .models import ItemInventario, Categoria
from .models import Cliente

admin.site.register(ItemInventario)
admin.site.register(Categoria)


admin.site.register(Cliente)


# Register your models here.
