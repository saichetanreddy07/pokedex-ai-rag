"""Gradio chat interface for the Pokedex AI FastAPI backend."""

import os
from functools import partial
from pathlib import Path
import sys
from typing import Any

import gradio as gr
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import OLLAMA_MODEL, TARGET_GENERATION

API_BASE_URL = os.getenv("POKEDEX_API_URL", "http://127.0.0.1:8000").rstrip("/")
WELCOME_MESSAGE = (
	"Hi! I'm PokéDex AI.\nAsk me anything about Pokémon from Generation I."
)
EXAMPLE_QUESTIONS = (
	"What type is Pikachu?",
	"What abilities does Charizard have?",
	"How does Eevee evolve?",
	"What moves can Snorlax learn?",
	"Tell me about Mewtwo.",
)
GENERATION_REGIONS = {
	1: "Kanto",
	2: "Johto",
	3: "Hoenn",
	4: "Sinnoh",
	5: "Unova",
	6: "Kalos",
	7: "Alola",
	8: "Galar",
	9: "Paldea",
}
ROMAN_NUMERALS = (
	(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
	(100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
	(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
)
POKEMON_COUNT = 151
MOVE_COUNT = 592
EVOLUTION_CHAIN_COUNT = 78
INDEXED_DOCUMENT_COUNT = 821


def _to_roman(number: int) -> str:
	"""Convert a positive integer to a Roman numeral for display."""
	parts = []
	for value, numeral in ROMAN_NUMERALS:
		while number >= value:
			parts.append(numeral)
			number -= value
	return "".join(parts) or str(number)


def _generation_label() -> str:
	"""Build the active generation label from the project configuration."""
	roman = _to_roman(TARGET_GENERATION)
	region = GENERATION_REGIONS.get(TARGET_GENERATION)
	if region:
		return f"Generation {roman} ({region})"
	return f"Generation {roman}"


def _model_label() -> str:
	"""Format the configured Ollama model name for the sidebar."""
	model_name = OLLAMA_MODEL.split(":", maxsplit=1)[0].lower()
	known_models = {"phi3": "Phi-3", "llama3": "Llama 3"}
	return f"{known_models.get(model_name, model_name.title())} (Ollama)"

CUSTOM_CSS = """
:root {
    --dex-red: #d83243;
    --dex-red-dark: #ad2333;
    --dex-blue: #244e83;
    --dex-yellow: #f5c84c;
    --dex-ink: #19283d;
    --dex-muted: #66758a;
    --dex-line: #dfe6ef;
    --dex-surface: #ffffff;
    --dex-canvas: #f2f6fb;
}

body, .gradio-container {
    background: var(--dex-canvas) !important;
    color: var(--dex-ink) !important;
    font-family: "Trebuchet MS", "Segoe UI", sans-serif !important;
}

.gradio-container {
    max-width: 100% !important;
}

#page-shell {
    max-width: 1040px;
    margin: 0 auto;
    padding: 24px 20px 18px;
}

#backend-status {
    flex: 0 0 auto;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 8px 12px;
    border: 1px solid #b6e6cb;
    border-radius: 8px;
    background: #edfaf2;
    color: #167344;
    font-size: 13px;
    font-weight: 700;
}

.status-badge.offline {
    border-color: #f2c5c8;
    background: #fff2f2;
    color: #a32935;
}

.status-badge {
	border-color: rgba(67, 209, 158, .25);
	background: #102c2a;
	color: #70e6ba;
}

.status-badge.offline {
	border-color: rgba(255, 138, 147, .26);
	background: #351e2a;
	color: #ff9ba3;
}

#chat-panel {
    padding: 12px;
    border: 1px solid var(--dex-line);
    border-radius: 8px;
    background: var(--dex-surface);
    box-shadow: 0 8px 24px rgba(25, 40, 61, 0.06);
}

#chat-window {
    border: 0 !important;
    background: var(--dex-surface) !important;
}

#chat-window .message {
    border-radius: 8px !important;
}

#question-box textarea {
    min-height: 66px !important;
    border: 1px solid var(--dex-line) !important;
    border-radius: 8px !important;
    background: #fbfcfe !important;
    color: var(--dex-ink) !important;
    font-size: 16px !important;
}

#send-button {
    min-width: 112px;
    border: 0 !important;
    border-radius: 8px !important;
    background: var(--dex-red) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

#send-button:hover {
    background: var(--dex-red-dark) !important;
}

#new-chat-button {
    border: 1px solid var(--dex-line) !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    color: var(--dex-blue) !important;
    font-weight: 700 !important;
}

#example-heading {
    margin: 22px 0 8px;
    color: var(--dex-ink);
    font-size: 15px;
    font-weight: 700;
}

.example-button {
    min-height: 44px !important;
    border: 1px solid #cbd8e9 !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    color: var(--dex-blue) !important;
    text-align: left !important;
    white-space: normal !important;
}

.example-button:hover {
    border-color: var(--dex-yellow) !important;
    background: #fffaf0 !important;
}

#dex-footer {
    margin-top: 20px;
    padding: 12px 4px 2px;
    border-top: 1px solid var(--dex-line);
    color: var(--dex-muted);
    font-size: 12px;
    text-align: center;
}

@media (max-width: 640px) {
    #page-shell {
        padding: 12px 8px;
    }

    #chat-panel {
        padding: 7px;
    }

    #send-button {
        min-width: 84px;
    }
}
"""

CUSTOM_CSS += """
:root {
	--dex-bg: #090f1b;
	--dex-panel: #101a2b;
	--dex-card: #131f33;
	--dex-card-raised: #182741;
	--dex-line: #263751;
	--dex-text: #e8efff;
	--dex-muted: #9cabc2;
	--dex-blue: #57a7ff;
	--dex-blue-bright: #7bbaff;
	--dex-green: #43d19e;
}

html, body, .gradio-container {
	background: var(--dex-bg) !important;
	color: var(--dex-text) !important;
	font-family: Inter, "Segoe UI", sans-serif !important;
}

.gradio-container {
	max-width: none !important;
	min-height: 100vh !important;
}

.main.fillable {
	width: 100% !important;
	max-width: 1440px !important;
	margin: 0 auto !important;
}

#page-shell {
	width: 100%;
	box-sizing: border-box;
	max-width: 1440px;
	margin: 0 auto;
	padding: 18px 22px 24px;
}

/* Header-only reset: keep Gradio's HTML wrapper transparent and unframed. */
#dex-header,
#dex-header > div,
#dex-header .html-container {
	box-sizing: border-box;
	width: 100%;
	padding: 0 !important;
	border: 0 !important;
	border-radius: 0 !important;
	background: transparent !important;
	box-shadow: none !important;
}

/* Center the brand as one responsive group without adding a header card. */
.dex-header-content {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 14px;
	width: 100%;
	margin: 0 auto 22px;
	text-align: left;
}

.dex-header-mark {
	display: grid;
	width: 44px;
	height: 44px;
	flex: 0 0 auto;
	place-items: center;
	border-radius: 14px;
	background: linear-gradient(145deg, #1c3963, #13233a);
	color: var(--dex-blue-bright);
	font-size: 24px;
	line-height: 1;
}

.dex-header-copy {
	min-width: 0;
}

.dex-header-title {
	margin: 0;
	color: var(--dex-text);
	font-size: 29px;
	font-weight: 700;
	letter-spacing: -0.035em;
	line-height: 1.12;
}

.dex-header-subtitle {
	margin: 5px 0 0;
	color: var(--dex-muted);
	font-size: 14px;
	line-height: 1.4;
}

#dex-tagline {
	margin: 0 0 14px;
	color: #b1bfd3;
	font-size: 14px;
}

#main-layout {
	align-items: flex-start !important;
	gap: 20px;
}

#chat-column {
	min-width: 0;
}

#sidebar {
	position: sticky;
	top: 16px;
	min-width: 270px;
	gap: 12px;
}

.sidebar-card {
	overflow: hidden;
	padding: 15px 16px;
	border: 1px solid var(--dex-line);
	border-radius: 14px;
	background: linear-gradient(155deg, var(--dex-card-raised), var(--dex-card) 62%);
	box-shadow: 0 12px 30px rgba(0, 0, 0, .18);
}

.sidebar-card h3 {
	margin: 0 0 12px;
	color: var(--dex-text);
	font-size: 15px;
	font-weight: 700;
}

.knowledge-list {
	display: grid;
	grid-template-columns: 1fr auto;
	gap: 9px 12px;
	margin: 0;
	color: var(--dex-muted);
	font-size: 12px;
}

.knowledge-list strong {
	color: #e0eaff;
	font-size: 12px;
	font-weight: 650;
	text-align: right;
}

.stack-list {
	display: flex;
	flex-wrap: wrap;
	gap: 7px;
}

.stack-list span {
	padding: 5px 8px;
	border: 1px solid #2a4263;
	border-radius: 8px;
	background: #10213a;
	color: #c9ddf8;
	font-size: 11px;
}

.connected-status {
	color: var(--dex-green) !important;
}

.offline-status {
	color: #ff8a93 !important;
}

#chat-window {
	min-height: 56vh;
	border: 1px solid var(--dex-line) !important;
	border-radius: 14px !important;
	background: var(--dex-panel) !important;
	box-shadow: 0 14px 34px rgba(0, 0, 0, .16);
}

#chat-window .message {
	border-radius: 13px !important;
}

#chat-window .message.user {
	border: 1px solid rgba(87, 167, 255, .22) !important;
	background: #173252 !important;
}

#chat-window .message.bot {
	border: 1px solid var(--dex-line) !important;
	background: #172236 !important;
}

#question-box textarea {
	min-height: 60px !important;
	border: 1px solid var(--dex-line) !important;
	border-radius: 13px !important;
	background: #111c2e !important;
	color: var(--dex-text) !important;
	font-size: 15px !important;
}

#question-box textarea:focus {
	border-color: var(--dex-blue) !important;
	box-shadow: 0 0 0 2px rgba(87, 167, 255, .15) !important;
}

#send-button {
	min-width: 92px;
	border: 1px solid #65adff !important;
	border-radius: 12px !important;
	background: linear-gradient(145deg, #3188eb, #256dcc) !important;
	color: white !important;
	font-weight: 700 !important;
	box-shadow: 0 7px 18px rgba(37, 109, 204, .22);
}

#send-button:hover {
	background: linear-gradient(145deg, #499cf6, #2f7fe0) !important;
}

#new-chat-button {
	border: 1px solid var(--dex-line) !important;
	border-radius: 12px !important;
	background: #172338 !important;
	color: #d8e6fb !important;
}

#example-heading {
	margin: 17px 0 8px;
	color: var(--dex-muted);
	font-size: 12px;
	font-weight: 650;
}

.example-button {
	min-height: 42px !important;
	justify-content: flex-start !important;
	padding: 8px 11px !important;
	border: 1px solid var(--dex-line) !important;
	border-radius: 11px !important;
	background: #111c2e !important;
	color: #cbd9ed !important;
	font-size: 12px !important;
	text-align: left !important;
	white-space: normal !important;
}

.example-button:hover {
	border-color: rgba(87, 167, 255, .65) !important;
	background: #172944 !important;
	color: #ffffff !important;
}

@media (max-width: 850px) {
	#page-shell {
		padding: 14px 12px 20px;
	}
	#main-layout {
		flex-direction: column !important;
		align-items: stretch !important;
	}
	#chat-column,
	#sidebar {
		width: 100% !important;
	}

	#sidebar {
		position: static;
		min-width: 0;
	}

	#chat-window {
		min-height: 48vh;
	}
}

@media (max-width: 560px) {
	.dex-header-content {
		gap: 11px;
		margin-bottom: 18px;
	}

	.dex-header-mark {
		width: 38px;
		height: 38px;
		border-radius: 12px;
		font-size: 21px;
	}

	.dex-header-title {
		font-size: 24px;
	}

	.dex-header-subtitle {
		font-size: 12px;
	}

	#main-layout {
		gap: 14px;
	}

	#send-button {
		min-width: 72px;
	}
}

#feature-tabs {
	background: transparent !important;
}

#feature-tabs .tab-nav {
	border-bottom: 1px solid var(--dex-line) !important;
}

#feature-tabs .tab-nav button {
	background: transparent !important;
	color: var(--dex-muted) !important;
}

#feature-tabs .tab-nav button.selected {
	border-color: var(--dex-blue) !important;
	color: var(--dex-text) !important;
}

#recommend-query textarea,
#team-query textarea,
#team-input textarea {
	border: 1px solid var(--dex-line) !important;
	border-radius: 12px !important;
	background: #111c2e !important;
	color: var(--dex-text) !important;
}

#recommend-output,
#team-output,
#analysis-output {
	border: 1px solid var(--dex-line) !important;
	border-radius: 12px !important;
	background: var(--dex-panel) !important;
	color: var(--dex-text) !important;
}
"""


def _status_badge(online: bool) -> str:
	"""Render a status badge based on the latest API request."""
	if online:
		return '<span class="status-badge">🟢 Connected</span>'
	return '<span class="status-badge offline">🔴 Disconnected</span>'


def _knowledge_base_card(connected: bool) -> str:
	"""Render configured knowledge-base details and API connection status."""
	return f"""
<section class="sidebar-card">
	<h3>Knowledge Base</h3>
	<dl class="knowledge-list">
		<dt>Generation</dt><strong>{_generation_label()}</strong>
		<dt>Pokémon</dt><strong>{POKEMON_COUNT}</strong>
		<dt>Moves</dt><strong>{MOVE_COUNT}</strong>
		<dt>Evolution Chains</dt><strong>{EVOLUTION_CHAIN_COUNT}</strong>
		<dt>Indexed Documents</dt><strong>{INDEXED_DOCUMENT_COUNT}</strong>
		<dt>Embedding Model</dt><strong>all-MiniLM-L6-v2</strong>
		<dt>Vector Database</dt><strong>ChromaDB</strong>
		<dt>LLM</dt><strong>{_model_label()}</strong>
		<dt>Status</dt><strong>{_status_badge(connected)}</strong>
	</dl>
</section>
"""


def _send_question(
	question: str,
	history: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], str, str]:
	"""Send a question to FastAPI and append its final answer to chat history."""
	cleaned_question = question.strip()
	chat_history = list(history or [])
	if not cleaned_question:
		return chat_history, "", gr.skip()

	chat_history.append({"role": "user", "content": cleaned_question})
	connected = True
	try:
		response = requests.post(
			f"{API_BASE_URL}/ask",
			json={"question": cleaned_question},
			timeout=90,
		)
		if response.status_code == 422:
			answer = "Please enter a question about Pokémon."
		elif response.status_code >= 500:
			try:
				detail = response.json().get("detail")
			except ValueError:
				detail = None
			answer = (
				f"Backend error: {detail}"
				if isinstance(detail, str) and detail.strip()
				else f"Backend request failed with HTTP {response.status_code}."
			)
		else:
			response.raise_for_status()
			payload = response.json()
			answer = payload.get("answer")
			if not isinstance(answer, str) or not answer.strip():
				answer = "I couldn't get an answer just now. Please try again."
	except requests.ConnectionError:
		connected = False
		answer = "Unable to connect to the PokéDex AI backend."
	except requests.Timeout:
		connected = False
		answer = "Unable to connect to the PokéDex AI backend."
	except (requests.RequestException, ValueError):
		connected = False
		answer = "Unable to connect to the PokéDex AI backend."

	chat_history.append({"role": "assistant", "content": answer})
	return chat_history, "", _knowledge_base_card(connected)


def submit_question(
	question: str,
	history: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], str, str]:
	"""Handle textbox submissions from Send or Enter."""
	return _send_question(question, history)


def submit_example(
	question: str,
	history: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], str, str]:
	"""Submit one of the suggested questions to the backend."""
	return _send_question(question, history)


def reset_chat() -> tuple[list[dict[str, str]], str, str]:
	"""Start a new conversation with the greeting message."""
	return [{"role": "assistant", "content": WELCOME_MESSAGE}], "", gr.skip()


def _return_example(question: str) -> str:
	"""Return an example question for the textbox without submitting it."""
	return question


def _call_recommendation_api(
	endpoint: str,
	payload: dict[str, Any],
) -> dict[str, Any]:
	"""Call one recommendation endpoint and return its JSON or error detail."""
	try:
		response = requests.post(
			f"{API_BASE_URL}/{endpoint}",
			json=payload,
			timeout=120,
		)
		try:
			result = response.json()
		except ValueError:
			result = {}
		if not response.ok:
			detail = result.get("detail")
			return {
				"error": detail if isinstance(detail, str) else f"Request failed with HTTP {response.status_code}."
			}
		if isinstance(result, dict):
			return result
		return {"error": "The API returned an invalid response."}
	except requests.RequestException as error:
		return {"error": f"Unable to connect to the PokéDex AI backend: {error}"}


def _format_error_response(response: dict[str, Any]) -> str | None:
	"""Return a readable error when an API response contains one."""
	error = response.get("error")
	return f"**Request failed:** {error}" if error else None


def _format_types(pokemon: dict[str, Any]) -> str:
	"""Format a Pokémon's types as a slash-separated display string."""
	types = pokemon.get("types") or []
	return " / ".join(str(type_name) for type_name in types) or "Unknown"


def _format_recommendations(response: dict[str, Any]) -> str:
	"""Convert structured recommendation data into readable Markdown."""
	if error := _format_error_response(response):
		return error
	items = response.get("recommendations") or []
	if not items:
		return "No matching Pokémon were found."
	sections = ["## Recommended Pokémon"]
	for index, pokemon in enumerate(items, start=1):
		sections.append(f"### {index}. {pokemon.get('name', 'Unknown Pokémon')}\n**Type:** {_format_types(pokemon)}")
		if pokemon.get("role"):
			sections.append(f"**Role:** {pokemon['role']}")
		reason = pokemon.get("reason") or "No recommendation reason was provided."
		sections.append(f"**Reason:**\n{reason}")
	return "\n\n".join(sections)


def _format_team(response: dict[str, Any]) -> str:
	"""Convert a generated team and its coverage summary into Markdown."""
	if error := _format_error_response(response):
		return error
	team = response.get("team") or []
	if not team:
		return "No team could be generated."
	sections = ["# Recommended Team"]
	for index, pokemon in enumerate(team, start=1):
		sections.append(
			f"{index}. **{pokemon.get('name', 'Unknown Pokémon')}** "
			f"({_format_types(pokemon)})\n"
			f"Role: {pokemon.get('role', 'Role not specified')}\n\n"
			f"Reason:\n{pokemon.get('reason') or 'No selection reason was provided.'}"
		)
	analysis = response.get("analysis") or {}
	sections.append("## Team Summary")
	for key, label in (("offensive_coverage", "Offensive coverage"), ("defensive_coverage", "Defensive coverage")):
		values = analysis.get(key) or []
		sections.append(f"- **{label}:** {', '.join(map(str, values)) or 'Not available'}")
	for key, label in (("strengths", "Strengths"), ("weaknesses", "Weaknesses")):
		values = analysis.get(key) or []
		if not values:
			values = ["None identified." if key == "weaknesses" else "Not available."]
		sections.extend([f"- **{label}:**", *[f"  - {value}" for value in values]])
	return "\n\n".join(sections)


def _format_team_analysis(response: dict[str, Any]) -> str:
	"""Convert structured team analysis into a concise Markdown report."""
	if error := _format_error_response(response):
		return error
	rating = response.get("overall_rating") or {}
	score = rating.get("score", 0)
	rating_text = f"{float(score) / 10:.1f} / 10"
	if rating.get("label"):
		rating_text += f" ({rating['label']})"
	sections = ["# Team Analysis", "## Overall Rating", rating_text]
	team = response.get("team") or []
	weaknesses = response.get("type_weaknesses") or {}
	duplicate_weaknesses = response.get("duplicate_weaknesses") or {}
	resistances = response.get("type_resistances") or {}
	balance = response.get("offensive_balance") or {}
	strengths = []
	if team:
		type_count = len({kind for pokemon in team for kind in pokemon.get("types", [])})
		strengths.append(f"The team has {len(team)} Pokémon with {type_count} distinct types.")
	if balance.get("label"):
		strengths.append(str(balance["label"]))
	if resistances:
		strengths.append("Has resistances or immunities to " + ", ".join(sorted(resistances)) + ".")
	if response.get("explanation"):
		strengths.append(str(response["explanation"]))
	sections.extend(["## Strengths", *[f"- {item}" for item in (strengths or ["No strengths were reported."])]] )
	weakness_items = [f"{name}: {count} team member(s) are weak to this type." for name, count in weaknesses.items()]
	sections.extend(["## Weaknesses", *[f"- {item}" for item in (weakness_items or ["No repeated type weaknesses were identified."])]] )
	improvements = []
	missing_roles = response.get("missing_roles") or []
	if missing_roles:
		improvements.append("Add a Pokémon that fills the missing role(s): " + ", ".join(missing_roles) + ".")
	if duplicate_weaknesses:
		improvements.append("Address repeated weaknesses to " + ", ".join(duplicate_weaknesses) + ".")
	elif weaknesses:
		improvements.append("Add defensive coverage for " + ", ".join(weaknesses) + ".")
	sections.extend(["## Suggested Improvements", *[f"- {item}" for item in (improvements or ["No specific improvement was identified."])]] )
	replacements = response.get("suggested_replacements") or []
	replacement_lines = [
		f"**{item.get('name', 'Unknown Pokémon')}** ({_format_types(item)}) — "
		f"{item.get('reason') or 'Suggested as a team option.'}"
		for item in replacements
	]
	sections.extend(["## Recommended Replacements", *[f"- {item}" for item in (replacement_lines or ["No replacements suggested."])]] )
	return "\n\n".join(sections)


def request_recommendations(query: str, limit: int) -> str:
	"""Request recommendations and render the response as Markdown."""
	return _format_recommendations(_call_recommendation_api(
		"recommend", {"query": query, "limit": int(limit)}
	))


def request_team(query: str) -> str:
	"""Request a team and render its members and summary as Markdown."""
	return _format_team(_call_recommendation_api("team", {"query": query}))


def request_team_analysis(team: str) -> str:
	"""Request team analysis and render it as Markdown."""
	return _format_team_analysis(_call_recommendation_api("analyze-team", {"team": team}))


def build_app() -> gr.Blocks:
	"""Create the PokéDex AI chat interface."""
	stack_card = """
<section class="sidebar-card">
  <h3>Project Stack</h3>
  <div class="stack-list">
    <span>Python</span><span>FastAPI</span><span>LangChain</span>
    <span>ChromaDB</span><span>Sentence Transformers</span>
    <span>Ollama</span><span>Gradio</span>
  </div>
</section>
"""
	with gr.Blocks(title="PokéDex AI") as demo:
		with gr.Column(elem_id="page-shell"):
			# Header-only markup: a transparent wrapper contains one centered brand group.
			gr.HTML(
				"<header class='dex-header-content' role='banner'>"
				"<span class='dex-header-mark' aria-hidden='true'>⚡</span>"
				"<div class='dex-header-copy'>"
				"<h1 class='dex-header-title'>PokéDex AI</h1>"
				"<p class='dex-header-subtitle'>"
				"Retrieval-Augmented Generation Assistant"
				"</p></div></header>",
				elem_id="dex-header",
				container=False,
				padding=False,
				show_label=False,
			)
			with gr.Tabs(elem_id="feature-tabs"):
				with gr.Tab("Ask Pokémon"):
					with gr.Row(elem_id="main-layout"):
						with gr.Column(scale=3, min_width=460, elem_id="chat-column"):
							gr.Markdown(
								"Ask questions about Pokémon, moves, abilities, "
								"evolutions, and game mechanics.",
								elem_id="dex-tagline",
							)
							chatbot = gr.Chatbot(
								value=[{"role": "assistant", "content": WELCOME_MESSAGE}],
								label=None,
								show_label=False,
								height=590,
								layout="bubble",
								elem_id="chat-window",
							)
							with gr.Row():
								question_box = gr.Textbox(
									placeholder="Ask about Pokémon...",
									lines=2,
									max_lines=5,
									show_label=False,
									container=False,
									elem_id="question-box",
								)
								send_button = gr.Button(
									"Send",
									variant="primary",
									elem_id="send-button",
								)
							with gr.Row():
								new_chat_button = gr.Button(
									"New Chat",
									variant="secondary",
									scale=0,
									elem_id="new-chat-button",
								)

						with gr.Column(
							scale=1,
							min_width=270,
							elem_id="sidebar",
						):
							knowledge_base_card = gr.HTML(
								value=_knowledge_base_card(True)
							)
							with gr.Column(elem_classes="sidebar-card"):
								gr.Markdown("### Example Questions")
								for question in EXAMPLE_QUESTIONS:
									button = gr.Button(
										f"• {question}",
										elem_classes="example-button",
									)
									button.click(
										fn=partial(_return_example, question),
										inputs=None,
										outputs=question_box,
										show_progress="hidden",
									)
							gr.HTML(stack_card)

				with gr.Tab("Recommend Pokémon"):
					gr.Markdown("Filter and rank Pokémon using types, stats, abilities, and species data.")
					recommend_query = gr.Textbox(
						label="Recommendation request",
						placeholder="Recommend a fast Electric Pokémon",
						lines=2,
						elem_id="recommend-query",
					)
					recommend_limit = gr.Slider(
						minimum=1, maximum=10, value=5, step=1,
						label="Number of recommendations",
					)
					recommend_button = gr.Button("Recommend Pokémon", variant="primary")
					recommend_output = gr.Markdown(elem_id="recommend-output")
					recommend_button.click(
						fn=request_recommendations,
						inputs=[recommend_query, recommend_limit],
						outputs=recommend_output,
					)

				with gr.Tab("Team Builder"):
					gr.Markdown("Build a six-Pokémon team from the selected generation's structured dataset.")
					team_query = gr.Textbox(
						label="Team request",
						placeholder="Build a balanced Generation I team without legendary Pokémon",
						lines=2,
						elem_id="team-query",
					)
					team_button = gr.Button("Build Team", variant="primary")
					team_output = gr.Markdown(elem_id="team-output")
					team_button.click(
						fn=request_team,
						inputs=team_query,
						outputs=team_output,
					)

				with gr.Tab("Team Analyzer"):
					gr.Markdown("Paste one Pokémon name per line or separate names with commas (up to six).")
					team_input = gr.Textbox(
						label="Your team",
						placeholder="Charizard\nLapras\nJolteon\nSnorlax\nGengar\nExeggutor",
						lines=8,
						elem_id="team-input",
					)
					analysis_button = gr.Button("Analyze Team", variant="primary")
					analysis_output = gr.Markdown(elem_id="analysis-output")
					analysis_button.click(
						fn=request_team_analysis,
						inputs=team_input,
						outputs=analysis_output,
					)

			send_outputs = [chatbot, question_box, knowledge_base_card]
			send_event_options = {"show_progress": "minimal"}
			send_button.click(
				fn=submit_question,
				inputs=[question_box, chatbot],
				outputs=send_outputs,
				**send_event_options,
			)
			question_box.submit(
				fn=submit_question,
				inputs=[question_box, chatbot],
				outputs=send_outputs,
				**send_event_options,
			)
			new_chat_button.click(
				fn=reset_chat,
				inputs=None,
				outputs=send_outputs,
				show_progress="hidden",
			)

	return demo


if __name__ == "__main__":
    build_app().queue().launch(
        inbrowser=True,
        server_name="127.0.0.1",
        show_error=False,
        theme=gr.themes.Base(
            primary_hue="blue",
            secondary_hue="blue",
            neutral_hue="slate",
        ),
        css=CUSTOM_CSS,
    )
