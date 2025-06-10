# Asistente Inteligente de Terra (Agencia de Marketing Digital)
![image-1-RAG-e1713883898899](https://github.com/user-attachments/assets/d1ea2aba-7caa-473f-be29-b375d1b0498b)

> **¡ATENCIÓN! Lee esto primero para poner en marcha el proyecto:**
>
> Os comparto una parte del código que hemos estado probando para hacer un chatbot. Este funciona con la **API de Groq**, que de momento es **gratis** y con límites de uso generosos.
>
> Para empezar, **hay que registrarse aquí y obtener vuestra API Key de Groq:**
> 👉 **[https://console.groq.com/keys](https://console.groq.com/keys)**
>
> Una vez que tengáis vuestra clave, debéis **pegarla en el archivo `.env`** (creándolo si no existe) dentro de este proyecto. Con eso, el asistente ya debería poder **responder preguntas generales** y también **leer documentos** que hayáis puesto en la carpeta `knowledge`.
>
> Para **integrarlo en una página web**, solo requiere correr `app.py` con todo lo anterior hecho. Podéis conectar la API que genera Flask (el endpoint `/ask_llm`) con el backend de la página web que estéis creando.
>
> Para **probarlo rápidamente** en vuestro ordenador: podéis correr `app.py` con `python app.py` y luego abrir el `index.html` de ejemplo en el navegador y hacer preguntas al LLM.

---
**Responde preguntas sobre terra, desde los documentos**
---
<img width="619" alt="Captura de pantalla 2025-06-10 122212" src="https://github.com/user-attachments/assets/a8fc1747-3149-4c1e-b9c9-cb2569e4988a" />


---
**Tambien respuestas de forma general o de codigo**
---
<img width="605" alt="Captura de pantalla 2025-06-10 122306" src="https://github.com/user-attachments/assets/db7d31bf-d9ed-418d-8c12-c4039c3c7a57" />

## Descripción del Proyecto

Este proyecto es una aplicación web Flask que actúa como un asistente inteligente para la agencia de marketing digital Terra. Utiliza un modelo de lenguaje grande (LLM) de Groq con capacidad de usar herramientas para interactuar con APIs internas simuladas y una base de conocimiento (RAG) para responder preguntas y realizar tareas relacionadas con campañas de marketing, creación de contenido y búsqueda de información interna.

## Estructura del Proyecto y Función de los Archivos

Aquí te explico la función de los archivos y carpetas principales en este repositorio:

* **`app.py`**
    * **Función:** Este es el **corazón de tu aplicación Flask (el backend)**. Aquí se define la lógica principal de la API. Se encarga de:
        * Crear la instancia de la aplicación Flask.
        * Configurar el endpoint `/ask_llm` para recibir las preguntas.
        * Cargar la API Key de Groq desde el `.env`.
        * Inicializar el modelo LLM de Groq.
        * Integrar las herramientas (definidas en `tools.py`) y el componente RAG (definido en `rag_component.py`).
        * Enviar la pregunta del usuario al LLM y devolver la respuesta.
        * Habilitar CORS para permitir la comunicación con el frontend.

* **`rag_component.py`**
    * **Función:** Este archivo contiene la lógica específica para la parte de **Retrieval Augmented Generation (RAG)**. Se encarga de:
        * Cargar documentos de tu base de conocimiento (la carpeta `knowledge`).
        * Procesar estos documentos para hacerlos "buscables" (por ejemplo, creando embeddings o índices).
        * Realizar la "recuperación" de información relevante de esos documentos basándose en la pregunta del usuario.
        * Proporcionar el contexto recuperado al LLM para que genere una respuesta más informada.

* **`requirements.txt`**
    * **Función:** Es un archivo de texto que lista **todas las librerías de Python** (con sus versiones específicas) que tu proyecto necesita para funcionar. Es crucial para:
        * Permitir que otras personas instalen fácilmente todas las dependencias del proyecto (`pip install -r requirements.txt`).
        * Asegurar que el proyecto se ejecute con las mismas versiones de librerías en diferentes entornos, evitando conflictos.

* **`.env`**
    * **Función:** Este archivo es para almacenar **variables de entorno sensibles**, como tu `GROQ_API_KEY`.
    * **Importancia:** Mantiene tus credenciales seguras y separadas del código, y **NO debe subirse a GitHub** (por eso lo incluimos en `.gitignore`). Cada desarrollador que use el proyecto debe crear su propio archivo `.env` con sus propias claves.

* **`index.html`**
    * **Función:** Este es un archivo de **frontend (interfaz de usuario)** de ejemplo. Contiene el código HTML, CSS y JavaScript necesario para:
        * Mostrar un campo de texto para que el usuario escriba su pregunta.
        * Un botón para enviar esa pregunta.
        * Un área donde se mostrará la respuesta que viene de tu API de Flask.
        * Es un frontend simple para probar la API de Flask desde el navegador.

* **`knowledge/` (Carpeta)**
    * **Función:** Esta carpeta está diseñada para almacenar los **documentos o archivos de texto** que tu componente RAG utilizará como su "base de conocimiento". Cuando haces una pregunta, el sistema RAG buscará información relevante dentro de estos archivos para proporcionar contexto al LLM.


---

## Características

Actualmente, el asistente puede:

* **Consultar Rendimiento de Campañas:** Obtener métricas y estado de campañas de marketing digital simuladas.
* **Crear Briefs de Contenido:** Generar borradores de briefs detallados para artículos o publicaciones de blog.
* **Responder preguntas con la Base de Conocimiento (RAG):** Buscar y recuperar información relevante de una base de datos interna sobre procesos, políticas y otros temas de la agencia (los documentos para RAG deben estar en la carpeta `knowledge`).

## Requisitos

Antes de empezar, asegúrate de tener instalado:

* **Python 3.9+** (Recomendado Python 3.10 o superior)
* **pip** (Administrador de paquetes de Python)
* **Git** (Para clonar el repositorio)

## Configuración del Proyecto

Sigue estos pasos para poner en marcha el proyecto en tu máquina local:

1.  **Clonar el Repositorio:**
    ```bash
    git clone [https://github.com/TU_USUARIO/TU_REPOSITORIO.git](https://github.com/TU_USUARIO/TU_REPOSITORIO.git)
    cd TU_REPOSITORIO
    ```
    (Reemplaza `TU_USUARIO/TU_REPOSITORIO` con la ubicación real de tu proyecto en GitHub)

2.  **Crear y Activar el Entorno Virtual:**
    Es una buena práctica crear un entorno virtual para aislar las dependencias del proyecto.
    ```bash
    python -m venv .venv
    ```
    * **En Windows:**
        ```bash
        .venv\Scripts\activate
        ```
    * **En macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

3.  **Instalar Dependencias:**
    Una vez activado el entorno virtual, instala todas las librerías necesarias:
    ```bash
    pip install -r requirements.txt
    ```
    Asegúrate de que `Flask-CORS` esté instalado, es crucial para la integración con un frontend. Si no lo está:
    ```bash
    pip install Flask-CORS
    ```

4.  **Configurar Variables de Entorno (`.env`):**
    Este proyecto requiere la API Key de Groq para funcionar. **Nunca subas tu archivo `.env` a GitHub.**

    * Crea un nuevo archivo llamado `.env` en la raíz de tu proyecto (en la misma carpeta donde está `app.py`).
    * Abre este archivo y añade tu clave de API de Groq:

        ```
        GROQ_API_KEY="TU_CLAVE_API_DE_GROQ_AQUI"
        # Si en el futuro se re-integran funcionalidades de ClickUp u otros servicios,
        # sus claves también se añadirían aquí (ejemplo):
        # CLICKUP_API_KEY="TU_CLAVE_API_DE_CLICKUP_AQUI"
        # CLICKUP_LIST_ID="TU_ID_DE_LISTA_DE_CLICKUP_AQUI"
        ```
    * **Importante:** Reemplaza `TU_CLAVE_API_DE_GROQ_AQUI` con tu clave API real de Groq obtenida de [https://console.groq.com/keys](https://console.groq.com/keys).

5.  **Asegurar `Flask-CORS` en `app.py`:**
    Abre tu archivo `app.py` y verifica que `CORS(app)` esté correctamente configurado. Es vital para permitir que el frontend se comunique con el backend.

    ```python
    from flask import Flask, request, jsonify
    from flask_cors import CORS # <-- Importa Flask-CORS
    # ... (otras importaciones)

    app = Flask(__name__)
    CORS(app) # <--- Asegúrate de que esta línea esté presente y activada
    # ... (resto de tu código)
    ```

## Ejecutar la Aplicación y Probar con el Frontend de Ejemplo

1.  **Iniciar el Servidor Flask:**
    Abre tu terminal, activa tu entorno virtual y ejecuta:
    ```bash
    python app.py
    ```
    Deja esta terminal abierta y el servidor de Flask corriendo. El servidor estará en ejecución en `http://172.0.0.1:5000`.

2.  **Abrir el Frontend de Prueba:**
    Localiza el archivo `index.html` (el que te proporcioné de ejemplo) en tu ordenador y ábrelo directamente en tu navegador web (simplemente haciendo doble click en él).

3.  **Interactuar con el Asistente:**
    En la interfaz HTML, escribe tus preguntas en el cuadro de texto y haz clic en "Enviar Pregunta". La respuesta de tu API de Flask aparecerá en la pantalla.

## Uso de la API (Endpoint `/ask_llm`)

Si estás desarrollando tu propio frontend o consumiendo la API desde otra aplicación, el endpoint principal es `/ask_llm`.

**URL Base:** `http://172.0.0.1:5000` (para desarrollo local)
**Endpoint:** `/ask_llm`
**Método:** `POST`

**Cuerpo de la Solicitud (JSON):**
