# Entregable 2 — Resumen ejecutivo de una página

Este es el documento recomendado para comprender la solución completa de Spot2 en **3 a 5 minutos**.

- [Abrir versión visual en HTML](ONE_PAGER_SPOT2_AESTHETIC.html)
- [Abrir versión PDF](ONE_PAGER_SPOT2.pdf)

## El problema

El equipo recibe muchos leads con distinta intención comercial y, al mismo tiempo, el inventario cambia constantemente.

Priorizar sólo por “qué lead parece mejor” puede desperdiciar esfuerzo si su necesidad ya no puede atenderse. Priorizar sólo por inventario tampoco resuelve el problema, porque no todos los leads tienen la misma probabilidad de avanzar.

## La solución

La propuesta separa dos preguntas:

**1. ¿Qué tan probable es que este lead avance a una visita agendada?**  
Esto se resume en **Calidad del lead**.

**2. ¿Existe inventario conocido que pueda atender razonablemente su necesidad?**  
Esto se resume en **Capacidad del inventario**.

Después se combinan ambas señales en un **Puntaje de oportunidad**, sin ocultar ninguna de las dos.

## Datos utilizados

- 5,000 leads;
- 22,576 consultas;
- 3,000 inmuebles;
- 30,000 registros históricos de disponibilidad;
- contexto de mercado.

La evaluación principal ocurre en **T1: después de registrar la primera consulta y antes de conocer la respuesta del intermediario**.

## Resultado principal

El modelo de Calidad del lead alcanza **Lift@10 = 1.689x**. En términos sencillos, el 10% de leads mejor puntuados concentra aproximadamente **69% más visitas agendadas** que una selección aleatoria equivalente.

El Puntaje de oportunidad alcanza **Lift@10 = 1.370x**. Es mejor que seleccionar al azar, pero no supera a Calidad del lead cuando el único objetivo es predecir la visita agendada. Esto no invalida el inventario: indica que responde a **otra necesidad de negocio**, saber si la oportunidad puede realmente atenderse.

## Qué ocurre si el inmueble original no sirve

El sistema:

1. busca alternativas compatibles;
2. usa únicamente información que ya era conocida en ese momento;
3. puede mostrar hasta cinco alternativas;
4. distingue entre “no disponible” y “no sabemos”;
5. devuelve **sin resultado** si no existe una recomendación defendible.

## Uso de inteligencia artificial

Se probó GPT-5 nano para revisar la coherencia semántica del catálogo. Fue barato y útil para descubrir patrones, pero **no aportó suficiente mejora para incluirlo en el modelo de priorización**.

La decisión fue usar IA donde sí aporta valor —control de calidad semántico y descubrimiento— sin convertirla en una dependencia innecesaria del sistema.

## Recomendación

**No automatizar inmediatamente.** Primero ejecutar la solución sobre una cohorte nueva sin afectar decisiones reales, comprobar que la señal se mantiene y, después, realizar un experimento controlado para medir impacto real.
