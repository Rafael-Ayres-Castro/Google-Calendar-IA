import datetime
import json
from zoneinfo import ZoneInfo

from google import genai

import calendar_service

MODEL = "gemini-3.5-flash"
TIME_ZONE = "America/Sao_Paulo"

global dicCalendarsId

def build_system_instruction():
	now = datetime.datetime.now(tz=ZoneInfo(TIME_ZONE))
	return (
		"Você é um assistente que gerencia a agenda do usuário via Google Calendar. "
		f"A data e hora atuais são {now.isoformat()} (fuso {TIME_ZONE}). Use isso "
		"para calcular datas relativas como 'amanhã', 'essa semana' ou 'sexta-feira'. "
		"O usuário pode ter vários calendários (ex: pessoal, trabalho, faculdade)"
		f"sempre que precisar do ID de um calendário utilize o dicionario {dicCalendarsId}"
		"Depois, decida: se o usuário mencionar um calendário específico pelo nome, "
		"use apenas o ID desse calendário. Se o pedido for genérico e não citar "
		"nenhum calendário (ex: 'o que eu tenho essa semana?', 'estou livre amanhã?'), "
		"chame list_events uma vez para cada calendário do usuário e combine os "
		"resultados antes de responder. "
		"Quando o pedido tiver um dia ou período específico, use time_min/time_max "
		"em list_events para filtrar por esse intervalo, sempre em RFC3339 com o "
		"fuso horário incluído (ex: '2026-08-15T00:00:00-03:00'). Sem isso, a busca "
		"traz só os próximos eventos a partir de agora, o que pode não ser o que o "
		"usuário pediu. "
		"Para criar, mover ou deletar eventos também é preciso saber o ID do "
		"calendário certo — use list_calendars se precisar, e pergunte ao usuário "
		"qual calendário usar se o pedido for ambíguo demais pra decidir sozinho. "
		"Depois de executar uma ação, confirme em poucas palavras o que foi feito."
	)


TOOLS = [
	{
		"type": "function",
		"name": "list_events",
		"description": (
			"Lista os eventos de um calendário do usuário, opcionalmente "
			"dentro de um intervalo de datas."
		),
		"parameters": {
			"type": "object",
			"properties": {
				"calendar_id": {
					"type": "string",
					"description": "ID do calendário a consultar (ex: 'primary').",
				},
				"time_min": {
					"type": "string",
					"description": (
						"Início do intervalo de busca, em RFC3339 com fuso horário "
						"(ex: '2026-08-15T00:00:00-03:00'). Se omitido, busca a "
						"partir de agora. Para eventos de um dia específico, use a "
						"meia-noite desse dia."
					),
				},
				"time_max": {
					"type": "string",
					"description": (
						"Fim do intervalo de busca, em RFC3339 com fuso horário "
						"(ex: '2026-08-16T00:00:00-03:00'). Para eventos de um dia "
						"específico, use a meia-noite do dia seguinte."
					),
				},
				"max_results": {
					"type": "integer",
					"description": "Número máximo de eventos a retornar.",
				},
			},
			"required": ["calendar_id"],
		},
	},
	{
		"type": "function",
		"name": "create_event",
		"description": "Cria um novo evento em um calendário.",
		"parameters": {
			"type": "object",
			"properties": {
				"calendar_id": {"type": "string", "description": "ID do calendário onde criar o evento."},
				"summary": {"type": "string", "description": "Título do evento."},
				"start": {"type": "string", "description": "Início em ISO 8601, ex: 2026-08-12T14:00:00."},
				"end": {"type": "string", "description": "Término em ISO 8601."},
				"description": {"type": "string", "description": "Descrição opcional do evento."},
			},
			"required": ["calendar_id", "summary", "start", "end"],
		},
	},
	{
		"type": "function",
		"name": "move_event",
		"description": "Reagenda um evento existente para um novo horário, no mesmo calendário.",
		"parameters": {
			"type": "object",
			"properties": {
				"calendar_id": {"type": "string", "description": "ID do calendário onde o evento está."},
				"event_id": {"type": "string", "description": "ID do evento a ser movido."},
				"new_start": {"type": "string", "description": "Novo início, ISO 8601."},
				"new_end": {"type": "string", "description": "Novo término, ISO 8601."},
			},
			"required": ["calendar_id", "event_id", "new_start", "new_end"],
		},
	},
	{
		"type": "function",
		"name": "delete_event",
		"description": "Remove um evento de um calendário.",
		"parameters": {
			"type": "object",
			"properties": {
				"calendar_id": {"type": "string", "description": "ID do calendário onde o evento está."},
				"event_id": {"type": "string", "description": "ID do evento a ser deletado."},
			},
			"required": ["calendar_id", "event_id"],
		},
	},
]


def dispatch(name, args, service):
	if name == "list_events":
		return calendar_service.list_events(service, **args)
	if name == "create_event":
		return calendar_service.create_event(service, **args)
	if name == "move_event":
		return calendar_service.move_event(service, **args)
	if name == "delete_event":
		calendar_service.delete_event(service, **args)
		return {"status": "deleted", "event_id": args["event_id"]}
	raise ValueError(f"Ferramenta desconhecida: {name}")


def handle_message(service, user_message, max_rounds=5):
	client = genai.Client()
	system_instruction = build_system_instruction()

	interaction = client.interactions.create(
		model=MODEL,
		input=user_message,
		system_instruction=system_instruction,
		tools=TOOLS,
	)

	function_calls = [step for step in interaction.steps if step.type == "function_call"]
	print(function_calls)

	if not function_calls:
		return interaction.output_text

	results = []
	for call in function_calls:
		output = dispatch(call.name, call.arguments, service)
		results.append({
			"type": "function_result",
			"name": call.name,
			"call_id": call.id,
			"result": [{"type": "text", "text": json.dumps(output, default=str)}],
		})

	interaction = client.interactions.create(
		model=MODEL,
		input=results,
		system_instruction=system_instruction,
		tools=TOOLS,
		previous_interaction_id=interaction.id,
	)

	return interaction.output_text


if __name__ == "__main__":
	service = calendar_service.get_service()
	dicCalendarsId = calendar_service.list_calendars(service)
	resposta = handle_message(service, "Crie um evento ammanhã para mim na agenda faculdade com o nome Materia nova as 19 horas  ")
	print(resposta)
