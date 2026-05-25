import gradio as gr
import requests

# FastAPI backend endpoint
API_URL = "http://127.0.0.1:8000/chat"

# Send user query to backend
def chat_with_pokedex(message, history):

    payload = {
        "question": message
    }

    try:

        response = requests.post(
            API_URL,
            json=payload
        )

        data = response.json()

        return data["response"]

    except Exception as e:

        return f"Backend connection error: {str(e)}"

# Example prompts
examples = [
    ["Who is Pikachu?"],
    ["Tell me about Charizard"],
    ["Who created Mewtwo?"],
    ["Which Pokémon causes lightning storms?"],
    ["Tell me about legendary bird Pokémon"]
]

# Create Gradio chatbot UI
chatbot = gr.ChatInterface(

    fn=chat_with_pokedex,

    title="⚡ PokéDex AI",

    description="""
Pokémon Lore, Battle Knowledge,
and AI-Powered Pokédex Assistant
""",

    examples=examples
)

# Launch frontend application
chatbot.launch()