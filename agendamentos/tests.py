from datetime import date, time
from decimal import Decimal

from django.test import TestCase

from barbeiros.models import Barbeiro as Profissional
from servicos.models import Serviços
from .models import Agendamento, AgendamentoServico, Barbeiro


class CalcularTotaisTests(TestCase):
	def test_calcula_totais_dos_itens_contratados(self):
		profissional = Profissional.objects.create(nome='Profissional')
		barbeiro_legado = Barbeiro.objects.create(nome='Profissional')
		agendamento = Agendamento.objects.create(
			profissional=profissional,
			barbeiro=barbeiro_legado,
			cliente_nome='Cliente',
			cliente_telefone='11999999999',
			data=date(2026, 11, 2),
			horario=time(9, 0),
		)
		servico = Serviços.objects.create(
			nome='Corte', preco=Decimal('45.00'), duracao=30
		)
		AgendamentoServico.objects.create(
			agendamento=agendamento,
			servico=servico,
			preco_contratado=Decimal('40.00'),
			duracao_contratada=35,
		)

		agendamento.calcular_totais()
		agendamento.refresh_from_db()

		self.assertEqual(agendamento.valor_total, Decimal('40.00'))
		self.assertEqual(agendamento.duracao_total, 35)


class CsrfEndpointTests(TestCase):
	def test_endpoint_define_cookie_csrf(self):
		response = self.client.get('/api/csrf/')

		self.assertEqual(response.status_code, 200)
		self.assertIn('csrftoken', response.cookies)

	def test_preflight_cors_permite_origem_angular_local(self):
		response = self.client.options(
			'/api/clientes/',
			HTTP_ORIGIN='http://localhost:4200',
			HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
			HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type,x-csrftoken',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			response['Access-Control-Allow-Origin'], 'http://localhost:4200'
		)
		self.assertEqual(response['Access-Control-Allow-Credentials'], 'true')
