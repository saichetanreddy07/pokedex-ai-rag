from langchain_ollama import OllamaLLM

# Load local Llama 3 model using Ollama
llm = OllamaLLM(
    model="llama3",
    temperature=0.2
)

# Generate grounded AI response
def generate_response(query, context):

    prompt = f"""
You are PokéDex AI, an expert Pokémon assistant.

Answer the user's question using ONLY the provided Pokémon context.

If the context does not contain enough information,
say:
"I could not find enough Pokémon data."

================ CONTEXT ================

{context}

================ QUESTION ================

{query}

================ ANSWER ================
"""

    response = llm.invoke(prompt)

    return response