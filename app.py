# app.py

# --- 1. Importaciones Necesarias ---
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from groq import Groq
import json # Necesario para parsear argumentos de herramientas
import uuid # Necesario para generar tool_call_id
import re # Necesario para la detección de tool_calls en formato content/XML

# Importa las funciones de tu componente RAG
from rag_component import retrieve_documents 

# --- 2. Cargar Variables de Entorno y Inicializar Clientes ---
load_dotenv()

app = Flask(__name__)
# Habilita CORS para permitir solicitudes desde el frontend (vital para el desarrollo local)
CORS(app)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    # Es crucial que la API Key de Groq esté configurada para que la app funcione.
    raise ValueError("GROQ_API_KEY no encontrada en las variables de entorno. Por favor, configura tu archivo .env")

# --- 3. Definición de Función de Ayuda para Groq ---

# Modelo de Groq: "llama3-8b-8192" es un modelo gratuito y con límites generosos.
# Has cambiado a "meta-llama/llama-4-maverick-17b-128e-instruct", lo mantengo.
DEFAULT_GROQ_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct" 

def get_groq_completion(prompt_messages, model_name=DEFAULT_GROQ_MODEL, tools=None, tool_choice="auto"):
    """
    Envía un prompt a la API de Groq y devuelve el objeto de mensaje del LLM.
    Puede usar 'tools' para permitir que el LLM llame a funciones.
    """
    try:
        if tools:
            chat_completion = groq_client.chat.completions.create(
                messages=prompt_messages,
                model=model_name,
                temperature=0.5, # Equilibrio entre creatividad y precisión
                max_tokens=4000, # Límite superior de tokens para la respuesta del LLM
                top_p=1,
                stop=None,
                stream=False,
                tools=tools,
                tool_choice=tool_choice
            )
        else:
            chat_completion = groq_client.chat.completions.create(
                messages=prompt_messages,
                model=model_name,
                temperature=0.7, # Un poco más creativo si no usa herramientas
                max_tokens=4000,
                top_p=1,
                stop=None,
                stream=False,
            )
        # Devolvemos el objeto message completo para poder acceder a .content o .tool_calls
        return chat_completion.choices[0].message
    except Exception as e:
        print(f"Error al llamar a la API de Groq: {e}")
        # En caso de error, devolvemos un diccionario con el rol y un mensaje de error
        return {"role": "assistant", "content": "Lo siento, no pude procesar tu solicitud en este momento debido a un error en la API de Groq."}

# --- 4. Ruta Principal del Agente Inteligente: /ask_llm ---

@app.route('/ask_llm', methods=['POST'])
def ask_llm():
    """
    Endpoint principal para interactuar con el asistente LLM.
    Procesa la consulta del usuario y utiliza la función de RAG si es necesario,
    pero puede responder con conocimiento general si no hay documentos relevantes.
    """
    data = request.get_json()
    user_query = data.get('query')

    if not user_query:
        return jsonify({"error": "Falta el campo 'query' en la petición"}), 400
    
    # 1. Definición de Herramientas (SOLO RAG)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "retrieve_documents",
                "description": "Busca y recupera documentos relevantes de la base de conocimiento interna de Terra basados en una consulta. Utiliza esta herramienta para responder preguntas sobre procesos internos, SEO, marketing digital, o cualquier tema específico de Terra.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "La consulta del usuario para buscar documentos relevantes en la base de conocimiento."
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    # 2. Mensajes Iniciales al LLM
    # El mensaje del sistema ahora enfatiza que puede usar conocimiento general
    # si los documentos internos no son suficientes.
    messages = [
        {"role": "system", "content": """Eres un asistente virtual de Terra. Tu función principal es ayudar a los usuarios respondiendo a sus preguntas.

**Directrices de respuesta:**
- **Prioridad de la Base de Conocimiento (RAG):** Siempre que una pregunta pueda ser respondida usando la base de conocimiento interna de Terra, utiliza la herramienta `retrieve_documents`. Si la información proviene de la base de conocimiento, menciónalo explícitamente.
- **Conocimiento General:** Si la pregunta del usuario no está relacionada con la base de conocimiento interna de Terra, o si la herramienta `retrieve_documents` no encuentra información relevante, **puedes responder usando tu conocimiento general**.
- **Claridad y Concisión:** Responde de forma clara, concisa y en español, manteniendo un tono profesional, amable y servicial. Nunca te niegues a responder.
- **Resumen Final:** Al final de tu respuesta, si es extensa, presenta un resumen claro y fácil de leer destacando los puntos clave.
"""
        },
        {"role": "user", "content": user_query}
    ]

    print(f"\n--- DEBUG: Mensajes enviados en la PRIMERA llamada al LLM (decisión de herramienta): ---")
    for msg in messages:
        print(f"  - {msg.get('role', 'N/A')}: {msg.get('content', 'N/A')[:100]}...")
    print("-------------------------------------------\n")

    # Primera llamada al LLM: Decide si necesita la herramienta RAG o responde directamente
    first_llm_response_message = get_groq_completion(messages, tools=tools)

    print(f"\n--- DEBUG: Respuesta de la PRIMERA llamada al LLM (decisión de herramienta): ---")
    if isinstance(first_llm_response_message, dict):
        print(f"  - Error en la primera llamada al LLM: {first_llm_response_message.get('content')}")
        return jsonify({"response": first_llm_response_message.get('content', "Error en la primera llamada al LLM.")})
    else:
        print(f"  - {first_llm_response_message}")
    print("-------------------------------------------\n")

    tool_call_found = False
    function_name = None
    function_args = {}
    tool_output_content_string = ""
    llm_response_content = ""

    # 3. Procesar la Respuesta del LLM (Tool Call o Contenido Directo)
    if first_llm_response_message.tool_calls:
        # El LLM decidió usar una herramienta en el formato Groq nativo
        tool_call = first_llm_response_message.tool_calls[0]
        function_name = tool_call.function.name
        try:
            function_args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            print(f"ERROR: No se pudo parsear los argumentos JSON para {function_name}: {tool_call.function.arguments}")
            function_args = {} 
        tool_call_found = True
        print(f"DEBUG: Llamada a herramienta detectada (formato Groq 'tool_calls'): {function_name} con argumentos: {function_args}")
    elif first_llm_response_message.content:
        # El LLM puede haber generado una llamada a herramienta en el campo 'content' (formato XML)
        content = first_llm_response_message.content
        match = re.search(r'<(\w+)>(.*?)</\1>', content, re.DOTALL)
        if match:
            function_name = match.group(1)
            try:
                function_args = json.loads(match.group(2))
            except json.JSONDecodeError:
                print(f"ERROR: No se pudo parsear los argumentos JSON para {function_name} desde content: {match.group(2)}")
                function_args = {} 
            tool_call_found = True
            print(f"DEBUG: Llamada a herramienta detectada (formato 'content'/'XML'): {function_name} con argumentos: {function_args}")
        else:
            # Si no hay tool_call y tampoco se detecta en el contenido,
            # el LLM ya ha generado su respuesta directamente desde su conocimiento general.
            llm_response_content = first_llm_response_message.content
            print("DEBUG: Primera llamada al LLM respondió directamente (sin herramienta).")
    
    # 4. Ejecución de la Herramienta (si se detectó 'retrieve_documents')
    if tool_call_found and function_name == "retrieve_documents":
        query_rag = function_args.get("query")
        if query_rag:
            retrieved_docs = retrieve_documents(query_rag)

            print(f"DEBUG RAG: Contenido recuperado de retrieve_documents (primeros 2 chunks): {retrieved_docs[:2] if retrieved_docs else 'Ninguno'}")

            if retrieved_docs:
                tool_output_content_string = (
                    f"Resultados de la búsqueda en la base de conocimiento de Terra para la consulta '{query_rag}':\n\n"
                    + "\n\n---\n\n".join(retrieved_docs)
                )
            else:
                # Informamos al LLM que no se encontraron documentos
                tool_output_content_string = (
                    f"La búsqueda en la base de conocimiento interna de Terra para la consulta '{query_rag}' no arrojó documentos relevantes. "
                    "Por favor, responde a la pregunta del usuario utilizando tu conocimiento general si es posible."
                )
        else:
            tool_output_content_string = "Error: La consulta para retrieve_documents no fue proporcionada. Por favor, responde con tu conocimiento general."

        print(f"\n--- DEBUG: Contenido FINAL de la herramienta para el LLM (primeros 500 caracteres): ---")
        print(f"{tool_output_content_string[:500]}...")
        print("-------------------------------------------\n")

        # 5. Segunda Llamada al LLM: Procesar el resultado de la herramienta (o la falta de él)
        generated_tool_call_id = str(uuid.uuid4())

        messages_for_second_call = [
            {"role": "system", "content": messages[0]["content"]}, # Mantenemos el prompt del sistema original
            {"role": "user", "content": user_query},
            {
                "role": "tool",
                "tool_call_id": generated_tool_call_id,
                "name": function_name,
                "content": tool_output_content_string
            }
        ]
        
        print(f"\n--- DEBUG: Mensajes enviados en la SEGUNDA llamada al LLM (generación de respuesta): ---")
        for msg in messages_for_second_call:
            content_to_print = msg.get('content', 'N/A')
            print(f"  - Role: {msg['role']}, Content: {content_to_print[:100]}...")
        print("-------------------------------------------\n")

        final_llm_response_message = get_groq_completion(messages_for_second_call)

        if isinstance(final_llm_response_message, dict):
            llm_response_content = final_llm_response_message.get('content', "Error: La segunda llamada al LLM falló inesperadamente.")
            print(f"DEBUG: La segunda respuesta del LLM fue un DICCIONARIO (indicando un error de Groq). Contenido: {llm_response_content}")
        else:
            llm_response_content = final_llm_response_message.content
            print(f"DEBUG: Contenido de 'final_llm_response_message.content': {llm_response_content[:100]}...")
        print("-------------------------------------------\n")

        if not llm_response_content:
            print("ADVERTENCIA: El LLM no generó contenido en la respuesta final después de la herramienta.")
            llm_response_content = "Lo siento, obtuve información, pero no pude generar una respuesta clara."

    # Si la primera llamada al LLM ya dio una respuesta directa (no tool_call)
    # y `llm_response_content` no se ha establecido por la ejecución de una herramienta,
    # significa que el LLM ya respondió con conocimiento general.
    # No necesitamos un 'else' que imponga un mensaje limitado.
    elif not llm_response_content: # Esto maneja el caso donde first_llm_response_message.content ya tiene una respuesta.
        llm_response_content = first_llm_response_message.content if first_llm_response_message.content else "Lo siento, no pude encontrar información relevante en nuestra base de conocimiento interna ni generar una respuesta coherente."


    # --- 6. Limpieza Final de la Respuesta Antes de Enviar al Frontend ---
    # Reemplaza los caracteres de salto de línea escapados (\\n) por saltos de línea reales (\n)
    # y las tabulaciones escapadas (\\t) por tabulaciones reales (\t).
    llm_response_content = llm_response_content.replace('\\n', '\n').replace('\\t', '\t')

    return jsonify({"response": llm_response_content})


# --- 7. Ejecutar la Aplicación Flask ---
if __name__ == '__main__':
    # Ejecuta el servidor Flask en modo depuración.
    # debug=True permite recarga automática y depuración.
    app.run(debug=True, port=5000)
    print("Servidor Flask en ejecución en http://127.0.0.1:5000/")