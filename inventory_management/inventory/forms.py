from django import forms 
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Categoria, ItemInventario 

class UserRegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2' ]

class ItemInventarioForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(queryset= Categoria.objects.all(), initial = 0)
    class Meta:
        model = ItemInventario
        fields = ['nome', 'categoria', 'quantidade', 'preco']
