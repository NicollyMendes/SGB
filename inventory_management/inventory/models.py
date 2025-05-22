from django.db import models
from django.contrib.auth.models import User

class ItemInventario(models.Model):
    nome = models.CharField(max_length=200)
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, blank=True, null=True)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    data_criacao = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nome
    

class Categoria(models.Model):
    nome = models.CharField(max_length=200)
    class Meta:
        verbose_name_plural = 'categorias'
    def __str__(self):
        return self.nome


class Venda(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    item = models.ForeignKey('ItemInventario', on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField()
    data_venda = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Reduz a quantidade do item antes de salvar a venda
        if not self.pk:  # Só atualiza na primeira vez
            if self.item.quantidade >= self.quantidade:
                self.item.quantidade -= self.quantidade
                self.item.save()
            else:
                raise ValueError("Estoque insuficiente para essa venda.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantidade}x {self.item.nome} para {self.cliente.nome}"
