import json
from datetime import date
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from clientes.models import Cliente
from barbeiros.models import Barbeiro
from servicos.models import Serviços
from .models import Agendamento
from .services import escolher_servicos, totais, periodos_livres, reservar

def erro(msg, status=400):
    if isinstance(msg, ValidationError):
        msg = '; '.join(msg.messages)
    return JsonResponse({'erro':str(msg)}, status=status)

def corpo(request):
    try:
        valor = json.loads(request.body)
        if not isinstance(valor, dict):
            raise ValueError()
        return valor
    except (ValueError, UnicodeDecodeError):
        raise ValidationError('Envie um objeto JSON válido.')

def parse_data(texto):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        raise ValidationError('Data inválida. Use AAAA-MM-DD.')

def inicio(request):
    return render(request, 'agendamentos/inicio.html')

@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({'ok': True})

@require_GET
def listar_servicos(request):
    return JsonResponse({'servicos':[{'id':s.id,'nome':s.nome,'preco':str(s.preco),'duracao':s.duracao,'descricao':s.descricao} for s in Serviços.objects.filter(ativo=True)]})

@require_POST
def cadastrar_cliente(request):
    try:
        d=corpo(request)
        nome=str(d.get('nome','')).strip()
        telefone=str(d.get('telefone','')).strip()
        endereco=str(d.get('endereco','')).strip()
        email=str(d.get('email','')).strip().lower()
        cpf=''.join(x for x in str(d.get('cpf','')) if x.isdigit())
        if not all([nome,telefone,endereco,email,cpf]):
            return erro('Preencha todos os campos.')
        if len(cpf)!=11 or len(set(cpf))==1 or not cpf_valido(cpf):
            return erro('CPF inválido.')
        cliente=Cliente(nome=nome, telefone=telefone, email=email, cpf=cpf)
        setattr(cliente, 'endereço', endereco)
        cliente.full_clean()
        cliente.save()
        return JsonResponse({'id':cliente.pk,'nome':cliente.nome}, status=201)
    except (ValidationError, IntegrityError) as e:
        return erro(e)

def cpf_valido(cpf):
    for n in (9,10):
        digito=(sum(int(cpf[i])*(n+1-i) for i in range(n))*10)%11
        if (0 if digito==10 else digito)!=int(cpf[n]):
            return False
    return True

@require_GET
def profissionais_disponiveis(request):
    try:
        dia=parse_data(request.GET.get('data'))
        ids=[int(x) for x in request.GET.getlist('servico_id')]
        _, duracao=totais(escolher_servicos(ids))
        dados=[{'id':b.id,'nome':b.nome} for b in Barbeiro.objects.filter(ativo=True) if periodos_livres(b,dia,duracao)]
        return JsonResponse({'profissionais':dados,'duracao_total':duracao})
    except (ValidationError,ValueError) as e:
        return erro(e)

@require_GET
def horarios_disponiveis(request):
    try:
        dia=parse_data(request.GET.get('data'))
        ids=[int(x) for x in request.GET.getlist('servico_id')]
        _,duracao=totais(escolher_servicos(ids))
        b=Barbeiro.objects.get(pk=int(request.GET.get('profissional_id')),ativo=True)
        return JsonResponse({'horarios':periodos_livres(b,dia,duracao)})
    except Barbeiro.DoesNotExist:
        return erro('Profissional não encontrado.',404)
    except (ValidationError,ValueError,TypeError) as e:
        return erro(e)

@require_POST
def resumo(request):
    try:
        d=corpo(request)
        servicos=escolher_servicos(d.get('servicos',[]))
        preco,duracao=totais(servicos)
        return JsonResponse({'servicos':[{'id':s.pk,'nome':s.nome,'preco':str(s.preco),'duracao':s.duracao} for s in servicos], 'valor_total':str(preco),'duracao_total':duracao})
    except (ValidationError,ValueError,TypeError) as e:
        return erro(e)

@require_POST
def confirmar(request):
    try:
        d=corpo(request)
        cliente=Cliente.objects.get(pk=int(d['cliente_id']))
        dia=parse_data(d.get('data'))
        agenda=reservar(cliente,int(d['profissional_id']),dia,str(d['horario']),d.get('servicos',[]))
        def enviar():
            send_mail('Agendamento confirmado', f'Olá, {cliente.nome}! Seu agendamento foi confirmado para {agenda.data:%d/%m/%Y} às {agenda.horario:%H:%M}. Total: R$ {agenda.valor_total}.', settings.DEFAULT_FROM_EMAIL,[cliente.email],fail_silently=False)
        transaction.on_commit(enviar)
        return JsonResponse({'id':agenda.pk,'status':agenda.status,'valor_total':str(agenda.valor_total),'duracao_total':agenda.duracao_total},status=201)
    except (Cliente.DoesNotExist,Barbeiro.DoesNotExist):
        return erro('Cliente ou profissional não encontrado.',404)
    except (KeyError,ValueError,TypeError,ValidationError,IntegrityError) as e:
        return erro(e)
