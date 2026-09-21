# SPEC 001 — Pipeline Autónomo de LinkedIn

> QUÉ hace el sistema. Basado en la constitución del proyecto.

## 1. Descripción General

El sistema extrae ofertas de LinkedIn (máx. 20-30 diarias, ver constitución Art. IV), las evalúa con un LLM contra los filtros del usuario, las clasifica en un semáforo (ROJO/NARANJA/VERDE) y genera mensajes personalizados de postulación para las ofertas NARANJA y VERDE.

## 2. Requisitos: Criterios de Evaluación (EL SEMÁFORO)

### REQ-1: Compensación

- **R1.1** Objetivo ideal: $5,000 – $7,000+ USD/mes.
- **R1.2** Excepción condicional: $4,000 – $4,999 USD/mes es aceptable SOLO SI el rol es `full-time` con contrato `long-term`. Si es por horas en este rango, descartar.
- **R1.3** Descarte inmediato: salario explícito < $4,000 USD/mes en contratos mensuales, o salario explícito < $35/h SOLO si el contrato es por pago por hora laborada.
- **R1.4** Si el salario NO aparece en la descripción, NO descartar. Clasificar como 🟠 NARANJA por falta de información salarial.

### REQ-2: Stack Tecnológico

- **R2.1** Core principal: Node.js, TypeScript, React, Next.js. Preferencia por AI.
- **R2.2** Flexibilidad Python (transición): aceptar vacantes que pidan Python SI Y SOLO SI el rol también incluye Node.js/TypeScript en el stack general (oportunidad híbrida).
- **R2.3** Descarte inmediato: roles EXCLUSIVAMENTE de Python que exijan seniority/alta experiencia en Python.
- **R2.4** Descarte inmediato: roles estrictamente "DevOps-first" o backends corporativos monolíticos (Java, .NET).

### REQ-3: Contratación

- **R3.1** Remoto internacional (contractor para Colombia/LATAM).
- **R3.2** Evitar consultoras pasivas que inflan bases de datos (ej. Solvd).

## 3. Requisitos: Clasificación (Scoring)

El output del LLM (Pydantic) se mapea a la entidad de dominio `JobOffer` con:

- 🔴 **ROJO:** incumple filtros críticos (ej. paga $4.5k por horas, es 100% Python senior, o usa Java). Detener proceso para esa oferta.
- 🟠 **NARANJA:** cumple filtros críticos, falta habilidad secundaria.
- 🟢 **VERDE:** match perfecto con stack, salario y condiciones.

## 4. Requisitos: Generador de Mensajes (Drafts WOW)

Para ofertas 🟢 VERDE o 🟠 NARANJA:

- **R4.1** Longitud máxima: 700 caracteres absolutos.
- **R4.2** Personalización: 2 o 3 highlights del CV del usuario con match exacto contra la oferta.
- **R4.3** Estructura: Saludo → Gancho sobre el rol y seniority del usuario → Logros técnicos → CTA suave.
- **R4.4** Tono: profesional, directo. Nivel Staff/Lead Engineer.

## 5. Criterios de Aceptación

- **CA-1:** Una oferta con pago por hora < $35/h se clasifica ROJO y no genera mensaje.
- **CA-2:** Una oferta de $4,500/mes full-time long-term se clasifica al menos NARANJA.
- **CA-3:** Un rol 100% Python senior se clasifica ROJO.
- **CA-4:** Un rol híbrido Python + Node.js/TypeScript remoto internacional con salario ≥ $5k se clasifica VERDE y genera mensaje ≤ 700 caracteres.
- **CA-5:** Ante captcha, el proceso aborta y registra el error sin reintentos.
- **CA-6:** El sistema no procesa más de 30 ofertas en un día calendario (America/Bogota).

## 6. Fuera de Alcance (v1)

- Postulación automática en LinkedIn (solo se generan drafts).
- Evaluación de otras plataformas (GetOnBoard, Torre, etc.).
- UI/dashboard web.
