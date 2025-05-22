from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegisterForm, ItemInventarioForm
from .models import ItemInventario, Categoria, Cliente, Venda, ItemVenda
from decimal import Decimal
from django.db import transaction
from django.contrib import messages
import datetime
from openpyxl import Workbook
from django.http import HttpResponse




class Index(TemplateView):
    template_name = 'inventory/index.html'

class Dashboard(LoginRequiredMixin, View):
	def get(self, request):
		items = ItemInventario.objects.filter(user=self.request.user.id).order_by('id')
		return render(request, 'inventory/dashboard.html', {'items': items})

class SignUpView(View):
    def get(self, request):
        form = UserRegisterForm()
        return render(request, 'inventory/signup.html', {'form': form})
    def post(self, request):
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )

            login(request, user)
            return redirect('index')
        
        return render(request, 'inventory/signup.html', {'form': form})
    
class AddItem(LoginRequiredMixin, CreateView):
    model = ItemInventario
    form_class = ItemInventarioForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    

class EditItem(LoginRequiredMixin, UpdateView):
    model = ItemInventario 
    form_class = ItemInventarioForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('dashboard')

class DeleteItem(LoginRequiredMixin, DeleteView):
    model = ItemInventario
    template_name = 'inventory/delete_item.html'
    success_url = reverse_lazy('dashboard')
    context_object_name = 'item'
    
class RealizarVenda(View):
    def get(self, request):
        itens = ItemInventario.objects.filter(quantidade__gt=0, user=request.user)
        clientes = Cliente.objects.all()
        return render(request, 'inventory/realizar_venda.html', {
            'itens': itens,
            'clientes': clientes
        })

    def post(self, request):
        itens = ItemInventario.objects.filter(quantidade__gt=0, user=request.user)
        clientes = Cliente.objects.all()
        cliente_id = request.POST.get('cliente')

        if not cliente_id:
            return render(request, 'inventory/realizar_venda.html', {
                'itens': itens,
                'clientes': clientes,
                'erro': 'Selecione um cliente.'
            })

        cliente = Cliente.objects.get(id=cliente_id)
        itens_selecionados = []
        total = Decimal('0.00')

        for item in itens:
            qtd = request.POST.get(f'quantidade_{item.id}')
            if qtd and int(qtd) > 0:
                quantidade = int(qtd)
                if quantidade > item.quantidade:
                    return render(request, 'inventory/realizar_venda.html', {
                        'itens': itens,
                        'clientes': clientes,
                        'erro': f'Estoque insuficiente para o item {item.nome}.'
                    })
                subtotal = item.preco * quantidade
                total += subtotal
                itens_selecionados.append((item, quantidade, item.preco))

        if not itens_selecionados:
            return render(request, 'inventory/realizar_venda.html', {
                'itens': itens,
                'clientes': clientes,
                'erro': 'Nenhum item selecionado para venda.'
            })

        with transaction.atomic():
            venda = Venda.objects.create(cliente=cliente)
            for item, quantidade, preco_unitario in itens_selecionados:
                ItemVenda.objects.create(
                    venda=venda,
                    item=item,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario
                )
                item.quantidade -= quantidade
                item.save()

        messages.success(request, f'Venda #{venda.id} realizada com sucesso!')
        return redirect('realizar_venda')

class RelatorioSemanalExcel(LoginRequiredMixin, View):
    def get(self, request):
        hoje = datetime.date.today()
        segunda = hoje - datetime.timedelta(days=hoje.weekday())  # início da semana
        vendas = Venda.objects.filter(data_venda__date__gte=segunda)

        total_geral = 0
        wb = Workbook()
        ws = wb.active
        ws.title = "Relatório Semanal"

        ws.append(["ID Venda", "Data", "Cliente", "Total da Venda (R$)"])

        for venda in vendas:
            total = sum(item.quantidade * item.preco_unitario for item in venda.itens.all())
            total_geral += total
            ws.append([
                venda.id,
                venda.data_venda.strftime('%d/%m/%Y %H:%M'),
                venda.cliente.nome,
                f"{total:.2f}".replace('.', ',')
            ])

        ws.append([])
        ws.append(["", "", "Total Geral:", f"{total_geral:.2f}".replace('.', ',')])

        # Salvar na pasta media/relatorios
        from django.conf import settings
        import os

        nome_arquivo = f"relatorio_semanal_{hoje.strftime('%Y%m%d')}.xlsx"
        caminho_pasta = os.path.join(settings.MEDIA_ROOT, 'relatorios')
        os.makedirs(caminho_pasta, exist_ok=True)
        caminho_arquivo = os.path.join(caminho_pasta, nome_arquivo)

        wb.save(caminho_arquivo)

        # Também retornar como download
        with open(caminho_arquivo, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={nome_arquivo}'
            return response
