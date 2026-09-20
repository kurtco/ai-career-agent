# CONSTITUCIÓN DEL PROYECTO: AI CAREER AGENT

> Principios inmutables del proyecto. Toda spec, plan y tarea DEBE cumplirlos.
> Modificar este documento requiere justificación explícita.

## Artículo I — Rol y Propósito

El sistema es una aplicación autónoma en Python que extrae ofertas de LinkedIn, las evalúa contra los filtros del usuario y genera mensajes de alto impacto. El código está diseñado para enseñar Python a un desarrollador senior experto en TypeScript y NestJS.

## Artículo II — Estilo de Código y Comentarios Didácticos

1. El idioma de los comentarios SHALL ser español.
2. Cada comentario MUST tener máximo 200 caracteres.
3. Los comentarios MUST ubicarse solo en partes críticas: uniones arquitectónicas o inyección de dependencias.
4. Todo comentario SHALL explicar "qué hace esto" e incluir una analogía rápida con el ecosistema Node/NestJS (ej. _"Inyectamos la dependencia aquí mediante el constructor, igual que un Provider en Nest"_ o _"Pydantic valida el DTO aquí, similar a class-validator"_).

## Artículo III — Arquitectura (Clean Architecture)

1. El proyecto MUST estructurarse siguiendo Clean Architecture.
2. Queda ESTRICTAMENTE PROHIBIDO mezclar lógica de scraping, llamadas al LLM y lógica de negocio en una misma capa o módulo.
3. Las capas SHALL ser:
   - **Dominio:** entidades puras (ej. `JobOffer`) e interfaces (puertos). Sin dependencias externas.
   - **Casos de Uso:** lógica de orquestación (ej. `EvaluateJobUseCase`).
   - **Adaptadores:** controladores y formato de salida.
   - **Infraestructura:** implementaciones concretas (scraper de Playwright, cliente de LLM con Pydantic).
4. Las dependencias MUST apuntar siempre hacia adentro (infraestructura → dominio, nunca al revés).

## Artículo IV — Seguridad de la Cuenta (Anti-Ban)

La integridad de la cuenta de LinkedIn es NO NEGOCIABLE. El scraper, en la capa de infraestructura, MUST cumplir:

1. **Navegador indetectable:** Playwright con extensiones stealth.
2. **Persistencia de sesión:** carga de archivo de estado/cookies. Cero logins manuales automatizados.
3. **Comportamiento humano:** delays aleatorios orgánicos y scroll antes de extraer el DOM.
4. **Límites de tasa:** máximo estricto de 20-30 ofertas diarias.
5. **Manejo de errores:** ante captcha o bloqueo, el sistema SHALL abortar y registrar el error. PROHIBIDO reintentar a la fuerza.

## Artículo V — Stack Tecnológico

1. La gestión de dependencias SHALL usar `uv` o `poetry`.
2. El scraping MUST implementarse con `playwright`.
3. La validación de datos y schemas del LLM MUST usar `Pydantic`.
4. El LLM principal SHALL ser **Google Gemini (free tier vía Google AI Studio)**, con **DeepSeek V4 Flash como fallback** (vía platform.deepseek.com, API compatible con OpenAI). Ambos detrás del puerto `LLMClient`, sin intermediarios (no OpenRouter).
5. El sistema MUST intentar primero el cliente Gemini; ante rate limit o error 5xx SHALL caer automáticamente a DeepSeek.
6. Las API keys MUST vivir únicamente en `.env` (nunca en código ni en el repositorio).

## Artículo VI — Operación

1. El punto de entrada SHALL ser `main.py`.
2. El scheduler MUST ejecutarse a las 9:00 AM, zona horaria `America/Bogota` (Medellín, Colombia).
