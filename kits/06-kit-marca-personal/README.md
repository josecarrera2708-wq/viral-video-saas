# Kit 06 · Análisis de Marca Personal — para Claude Code

> ¿Primera vez? Abre **[`EMPIEZA-AQUI.md`](EMPIEZA-AQUI.md)**: 3 pasos y a analizar.

Le pasas un perfil — el tuyo o el de un cliente — y Claude Code analiza el
recorrido completo de un desconocido hasta cliente: **si te encuentran, si te
entienden, si te creen y si te contratan**. Te devuelve un **informe HTML** con la
nota de cada fase, **dónde está la fuga**, tu bio y tus ganchos reescritos, tres
pilares de contenido, diez ideas concretas y un **plan de 30 días**.

Funciona con el modelo que ya tienes en tu Claude Code — no hay que configurar
ningún modelo, ninguna API ni ninguna clave.

Sirve para dos cosas: **analizar tu propia marca** (y arreglarla) o **analizar la de
un cliente potencial** y enseñarle el informe. Un diagnóstico con sus frases, sus
números y su bio reescrita vende mucho mejor que una llamada a puerta fría.

## Cómo entra la información: el enlace + tus capturas

Hay que decirlo claro desde el principio: **Instagram y TikTok no se pueden leer
con un enlace.** Devuelven una pantalla de verificación o mandan el contenido como
imágenes. Le pasa a cualquier herramienta.

Por eso este kit trabaja con dos vías:

| Vía | Qué saca |
|---|---|
| **El enlace** | Qué sale al buscar tu nombre en Google, tu LinkedIn (ese sí se lee entero), tu web, menciones en medios |
| **5 capturas de pantalla** | Tu perfil, tu parrilla, un post con sus comentarios, **tus Estadísticas de 30 días** y tu mejor post |

Y eso no es un parche: la captura de **Estadísticas** de tu propia aplicación tiene
el alcance real, las visitas al perfil y los clics en tu enlace. Esos datos **solo
los ve el dueño de la cuenta** — ninguna herramienta que rastree internet los
consigue. Son exactamente los que dicen si la gente no te encuentra, no te entiende
o no te contrata.

Las capturas se hacen en un minuto desde el móvil y se sueltan en `entrada/`. El
guion exacto, con dónde encontrar cada pantalla en cada red, está en
**[`entrada/LEEME.md`](entrada/LEEME.md)**.

## El sistema: cuatro fases y una fuga

Una marca personal no falla "en general": falla en un punto concreto del recorrido.
El kit mide las cuatro puertas por las que pasa un desconocido, 25 puntos cada una:

| Fase | La pregunta | Las 3 dimensiones |
|---|---|---|
| **1 · ¿Te encuentran?** | ¿Existes para quien te busca? | Perfil buscable · Formatos y distribución · Ganchos |
| **2 · ¿Te entienden?** | ¿Se sabe a quién ayudas? | La prueba de los 5 segundos · Nicho y diferencia · Pilares de contenido |
| **3 · ¿Te creen?** | ¿Hay motivos para confiar? | Prueba y resultados · Criterio propio · Constancia y presencia |
| **4 · ¿Te contratan?** | ¿Se puede dar el paso? | Oferta visible · Camino sin fricción · Captación propia |

**La fuga** es el punto del embudo donde se te cae la mayoría de la gente. Es el
titular del informe y por donde empieza el plan, porque el embudo es secuencial: da
igual lo buena que sea tu oferta si nadie entiende a quién ayudas.

Cómo se localiza:

- **Si aportas la captura de Estadísticas**, con tus propios números: cuánta gente
  te ve, cuánta llega a tu perfil y cuánta pincha tu enlace. El salto donde se
  pierde más gente es la fuga, y la cuenta va a la vista en el informe.
- **Si no la aportas**, es la primera fase que baja de 15 sobre 25.

Un ejemplo de lo que sale: 18.000 personas te ven al mes, 260 entran en tu perfil y
4 pinchan tu enlace. Te encuentran de sobra; el agujero está en que nadie entiende
a quién ayudas. Tu problema no es publicar más. Es tu bio.

Ojo con esto, porque es la diferencia entre un informe útil y un informe tonto: una
nota baja no es automáticamente la fuga. Si tus números dicen que te encuentran, la
fase 1 no es tu problema aunque tus portadas tengan mala nota — ahí son margen de
mejora, no la causa.

## Cómo puntúa (para que la nota signifique algo)

Cada una de las 12 dimensiones se puntúa de 0 a 100 con anclajes fijos, no "a ojo":

| Nota | Qué significa |
|---|---|
| 0-20 | No existe |
| 21-40 | Existe pero está mal o abandonado |
| 41-60 | Cumple lo mínimo, sin nada que le diferencie |
| 61-80 | Bien hecho, con fallos concretos identificados |
| 81-100 | Referencia de su sector |

La nota de cada fase es la media de sus tres dimensiones llevada a 25, y la
**nota global** es la suma de las cuatro fases. La operación va a la vista en el
informe.

- Cada nota va con **evidencia**: tu bio literal, un pie de foto citado, un número
  de una captura, una URL. Sin evidencia no hay nota.
- Si algo **no se pudo comprobar** (no aportaste esa captura), queda como *sin
  datos*: no puntúa, no entra en la media de su fase y el informe explica por qué.
  Nunca se lo inventa.

Bandas de la nota global: **0-39 crítico · 40-59 flojo · 60-74 aceptable · 75-89
bueno · 90-100 referencia**. La mayoría de marcas personales pequeñas están entre
30 y 55, y decirlo claro es el servicio.

## Qué hay en el kit

| Pieza | Qué es |
|---|---|
| `EMPIEZA-AQUI.md` | Los 3 pasos para dejarlo funcionando (empieza por aquí) |
| `.claude/commands/setup.md` | El asistente `/setup`: comprueba todo y te explica las capturas |
| `.claude/commands/marca.md` | El comando `/marca`: lanza un análisis nuevo |
| `.claude/skills/analisis-marca-personal/` | La skill: el sistema completo de las 4 fases (esto es lo que garantiza el resultado) |
| `entrada/` | Donde sueltas tus capturas. `LEEME.md` tiene el guion de las cinco |
| `ejemplos/marca-de-practica/` | Una nutricionista ficticia con errores metidos a propósito, para tu primer análisis sin usar un caso real |
| `workspace/` | Donde aparecen tus informes |

## Cómo se usa

Después de `/setup`, una frase:

```
analiza esta marca personal: [enlace del perfil]
```

Claude te preguntará el contexto en dos bloques (el perfil y las capturas · a quién
quieres llegar, qué vendes, qué objetivo tienes), leerá todo narrando lo que va
encontrando, y al terminar tendrás en `workspace/`:

- **`marca-personal-[handle].html`** — el informe completo: nota global y por fase,
  la fuga señalada, la prueba de los 5 segundos, el embudo dibujado, las 12
  dimensiones con su evidencia, tu bio reescrita en 2 versiones, tres de tus
  ganchos con su antes/después, tus tres pilares, diez ideas de contenido y el plan
  de 30 días.
- **`[handle]-plan-30-dias.md`** — el mismo plan con casillas para ir marcando.
- **`[handle]-hallazgos.md`** — el cuaderno de trabajo: de ahí sale cada afirmación
  del informe.

El HTML es autocontenido: se abre en cualquier navegador, se ve bien en el móvil y
se imprime a PDF para mandarlo.

Si quieres profundizar después: *"profundiza en la fase 2"*, *"dame diez ideas
más"* o *"reescríbeme la bio con otro tono"* amplía solo esa parte.

## Puedes empezar sin las capturas

Si aún no las tienes, di el enlace igualmente: Claude adelanta todo lo público
(buscador, LinkedIn, tu web) mientras las haces. Y si analizas a un cliente que no
te va a dar sus estadísticas, el análisis se hace igual: esas dimensiones quedan
marcadas como *sin datos* y se dice en el informe.

## Lo que este kit NO hace

Ser honesto con esto evita decepciones:

- **No entra en tu cuenta.** Nunca pide una contraseña ni un acceso. Todo lo privado
  que ve son las capturas que tú decides darle.
- **No lee Instagram ni TikTok por su cuenta.** Esas redes lo bloquean. Para eso
  están las capturas.
- **No publica ni programa nada.** Analiza y planifica; publicar lo haces tú.
- **No inventa métricas.** Si no hay captura de estadísticas, no hay números: se
  marca *sin datos*. Y no compara tus cifras con "la media del sector", porque esa
  media no se puede demostrar; compara tus propios números entre sí, que es lo que
  de verdad enseña dónde está la fuga.
- **No juzga a la persona.** Analiza el perfil, el contenido y el recorrido. No
  opina de tu aspecto, tu voz ni tu vida privada.
- **No escribe tus posts.** Te da los pilares, los ganchos y diez ideas listas; la
  ejecución es tuya (o es lo que le vas a cobrar a tu cliente).

## Privacidad

- Tus capturas se quedan en tu ordenador. La carpeta `entrada/` está excluida de
  git: no se sube ni se comparte con el kit.
- **Ningún nombre de quien comenta** en tus publicaciones aparece en el informe. Se
  usan para ver si hay preguntas sin responder, nada más.
- Las capturas **no se incrustan** en el informe: puedes enseñarlo sin miedo.
- Nunca hacen falta capturas de mensajes privados.
- Si analizas a otra persona, recuerda que el informe es un análisis de lo que esa
  persona publica. Preséntalo como diagnóstico profesional, no como una lista de
  reproches.
- Anthropic no entrena sus modelos con el tráfico de API ni con tu uso de Claude
  Code.

## Si usas Windows

- Claude Code necesita **Git para Windows** (git-scm.com/download/win): es quien le
  da a Claude la terminal que usa por dentro. Se instala dándole a "siguiente"
  hasta el final.
- Los comandos los ejecuta Claude por ti — tú no abres ninguna terminal.
- Para pasar las capturas del móvil al ordenador: mándatelas por WhatsApp a tu
  propio chat y descárgalas, o por correo. Llegan como `.jpg` y sirven igual.
- Cuando este kit muestra rutas de ejemplo, la tuya será del estilo
  `C:\Users\tu-nombre\Escritorio\06-kit-marca-personal`.

## Si el análisis se corta a mitad

Una sesión larga puede interrumpirse (la conexión, el límite de uso de tu plan…).
**No pierdes nada**: mientras analiza, la skill va escribiendo un cuaderno en
`workspace/[handle]-hallazgos.md` — cada dimensión cerrada, con su evidencia y su
nota — antes de montar el HTML final.

- Abre de nuevo la conversación y di *"continúa el análisis donde lo dejaste"*.
- Retoma por la primera dimensión que falte; lo ya analizado no se repite.

## Cuánto cuesta cada análisis

El kit usa el modelo que ya tienes en Claude Code, así que el coste es el de tu
cuenta de Claude:

- **Con suscripción (Pro o superior)**: el análisis consume el uso incluido en tu
  plan — no pagas nada aparte.
- **Con cuenta API**: pagas por uso. Un análisis completo suele salir por unos
  pocos euros.

No hay ninguna otra suscripción, clave ni herramienta de pago.

## Cómo se cobra (rangos de mercado 2026)

- **Análisis de marca personal** de un profesional individual: 200-500 €
- **Análisis + presentación en directo + plan de contenidos**: 600-1.200 €
- **Gestión mensual de contenidos**: 400-1.500 €/mes
- **Ghostwriting de LinkedIn**: 800-2.500 €/mes
- **Mentoría por horas**: 90-200 €/hora

El análisis es la puerta de entrada: quien te paga el diagnóstico te contrata la
ejecución. Los precios los pones tú — estos son rangos de referencia.

---

> Cualquier duda → pregúntala en la comunidad donde conseguiste el kit. Allí te
> ayudamos a aplicarlo a tu caso real.
