# El sistema de medida

Solo para kits que **valoran, puntúan o auditan** algo. Si el kit genera o ejecuta,
salta a la última sección de este archivo.

Un número sin sistema detrás es una opinión disfrazada. Y una opinión disfrazada de
número es peor que ninguna nota, porque el usuario la enseña a un cliente. Este
archivo es para que la nota signifique lo mismo hoy, dentro de un mes y con otro caso.

---

## Los dos sistemas que funcionan

### A · Dimensiones ponderadas (el habitual)

Se mira el caso por partes, cada parte tiene una nota de 0 a 100 y un peso, y la nota
global es la media ponderada. Sirve para casi todo: auditar una web, un negocio, un
canal, una tienda, un contrato, una carta de restaurante.

```
Dimensión                        Peso    Qué mide
Propuesta de valor                15     ¿Se entiende en 5 segundos qué vende?
Confianza y prueba social         12     Reseñas, casos, garantías verificables
Captación de contacto             12     ¿Hay una vía clara de contacto?
…
                                 ───
                                 100
```

Reglas del reparto:

- Entre **6 y 14 dimensiones**. Menos de 6 es superficial; más de 14 no se sostiene
  en un informe ni se defiende en una reunión.
- **Los pesos suman 100 exactos.** Se comprueba sumando, no a ojo.
- El peso lo decide **el impacto en lo que le importa al usuario**, no lo fácil que
  sea de medir. La tentación es dar peso alto a lo que se mide con un comando; es
  justo el sesgo que hay que evitar.
- Ninguna dimensión pesa más de 20: si una vale 30, en realidad son dos.

### B · Embudo por fases (para procesos)

Cuando lo que se audita es un recorrido con orden — el camino de un cliente, un
proceso de contratación, una secuencia de correos —, se divide en 4 fases de 25
puntos. La ventaja: un fallo en la fase 1 explica los de la fase 4, y eso se ve.

```
Fase 1 · Que te encuentren        25
Fase 2 · Que entiendan qué vendes 25
Fase 3 · Que se decidan           25
Fase 4 · Que compren y vuelvan    25
```

Se elige **uno** de los dos sistemas. Mezclarlos produce informes que nadie entiende.

---

## Los anclajes: lo que convierte la nota en algo repetible

Cada dimensión necesita escrito **qué es un 20, qué es un 50 y qué es un 80**, con
hechos observables. Sin anclajes no hay sistema.

Mal (no es un anclaje, es un adjetivo):

> 80 = la propuesta de valor es buena.

Bien (se puede comprobar mirando):

> - **20** — No se entiende qué vende. El titular es un lema ("Pasión por lo
>   auténtico") o el nombre de la empresa.
> - **50** — Se entiende el producto, pero no para quién es ni en qué se diferencia.
> - **80** — En la primera pantalla: qué es, para quién, y una diferencia concreta y
>   comprobable ("entrega en 24 h en toda la península").
> - **100** — Lo anterior más una prueba a la vista (dato, cifra, caso, garantía).

Cómo se escriben rápido: pídele al usuario en la entrevista **dos casos reales, uno
bueno y uno malo, de su oficio**. Los anclajes salen de la diferencia entre esos dos.
Vale más que una hora de explicaciones y además usa su criterio, no el tuyo.

Los intermedios (30, 40, 60, 70) se interpolan: no hace falta escribirlos.

---

## Las bandas de la nota global

Sin bandas, un 61 y un 74 parecen lo mismo. Las bandas y **qué implica cada una**:

| Nota | Banda | Qué significa para el usuario |
|---|---|---|
| 0-39 | Crítico | Hay algo roto que cuesta dinero ahora mismo |
| 40-54 | Flojo | Funciona a medias; las mejoras obvias están sin hacer |
| 55-69 | Aceptable | Correcto y sin brillo; mejora con trabajo fino |
| 70-84 | Bueno | Por encima de su competencia en lo que se ha medido |
| 85-100 | Excelente | Referencia del sector |

Un 85+ tiene que ser **raro**. Si en las primeras pruebas todo el mundo saca 80, los
anclajes están regalados y el informe no vale nada: nadie paga por que le digan que
todo está bien. Recalíbralos.

---

## Las tres reglas que evitan informes falsos

1. **El dato medido manda sobre el juicio.** Si un número se puede medir (tiempo de
   carga, número de reseñas, precio, caracteres del titular), la nota sale del número.
   El juicio solo entra donde no hay nada que medir.
2. **Lo que no se pudo comprobar queda "sin datos": no puntúa, no se estima.** Su
   peso **se reparte proporcionalmente** entre las dimensiones que sí tienen datos, y
   el informe dice qué se quedó sin medir y por qué. Poner un 50 "por si acaso"
   convierte el informe en ficción.
3. **Cada nota lleva su prueba al lado.** Una línea que diga por qué es esa nota y no
   otra: el dato, la frase citada, la captura, el comando. Un informe que no se puede
   auditar no se puede defender delante de un cliente.

Y una cuarta, de forma: **la nota nunca va sola**. Siempre acompañada de las 3
acciones que más la subirían, ordenadas por lo que cambia dividido por lo que cuesta.
El usuario paga por saber qué hacer el lunes, no por un número.

### El límite de "sin datos", que hay que escribir en la skill

"Sin datos" es de la **dimensión entera**, y solo cuando la dimensión **no se puede juzgar
en absoluto**. Si falta un detalle pero lo que decide esa dimensión sí se pudo ver, la
dimensión **puntúa** y lo que falta se pide aparte.

Es la trampa más fácil de pisar, y es peligrosa porque **esconde justo lo que hay que
ver**: marcar la dimensión entera como sin datos borra del informe la prueba que sí
existía. Pasó en la prueba de fuego de este kit — faltaba el anexo de la renta de un
contrato, y poner toda la dimensión "Dinero" en sin datos habría hecho desaparecer del
informe la cláusula que dejaba fijar la subida a una sola parte, que era el peor problema
del contrato.

Escríbelo en la skill con un ejemplo del propio dominio del kit, no en abstracto.

### Si el kit ordena una lista ("las 5 que más cuestan"), el criterio va escrito

Cuando un kit destaca los N hallazgos más importantes, el orden **no se deja al juicio del
momento**: se escribe el criterio, en niveles, en la skill. Si no está escrito, cada
ejecución ordena distinto y el usuario no puede defender el orden delante de nadie.

Para dinero, el orden que salió de la prueba de fuego y que sirve casi siempre:

1. dinero que **se pierde** y no vuelve;
2. dinero que se queda **inmovilizado** pero en principio vuelve;
3. dinero **imprevisible**, que no se puede presupuestar porque lo decide otro;
4. lo que **ata sin cobrar** (plazos, exclusividades).

A empate, gana lo que actúa antes o lo que no se ve venir. Y cada elemento de la lista con
**su cifra**, aunque sea un orden de magnitud razonado a partir de los datos del propio
caso: "mucho dinero" no es un hallazgo.

---

## Cómo se escribe todo esto en el kit

- Las dimensiones, pesos, anclajes y bandas van **en el `SKILL.md`** del kit nuevo,
  como una tabla y una lista. Es el sistema; su sitio es el cerebro, no el README.
- El `README.md` explica **cómo puntúa, en cristiano**, y enseña la tabla de pesos.
  El usuario tiene que poder entender su nota sin leer la skill.
- **El nombre de cada dimensión se escribe una vez y se copia literal** al README, a la
  skill y al informe. Ni glosas en un sitio y no en otro ("Cláusulas mudas" en el README
  y "Cláusulas mudas: lo que no dice" en la skill), ni sinónimos: el cliente compara la
  tabla del README con las secciones del informe, y dos nombres para una dimensión le
  hacen buscar una novena que no existe. Se comprueba con un comando, extrayendo los
  nombres de las dos tablas y comparándolos, no leyendo.
- El `_CONTRATO.md` guarda la versión definitiva: es lo que permite recalibrar dentro
  de tres meses sin volver a inventarlo.
- Si el sistema cambia después, **súbele la versión** ("sistema v2") y dilo en el
  informe. Comparar notas de sistemas distintos es el error clásico.

---

## Si el kit no puntúa: el criterio de calidad

Un kit que genera textos, transforma archivos o ejecuta algo también necesita
criterio, o el resultado sale distinto cada día. Se escribe como **lista comprobable**,
nunca como adjetivos.

Mal:

> El texto tiene que ser atractivo y profesional.

Bien:

> - El titular tiene menos de 60 caracteres.
> - Dice el beneficio, no la característica.
> - No usa "descubre", "revoluciona" ni "solución integral".
> - El nombre del producto aparece en la primera línea.
> - Hay una sola llamada a la acción, y es un verbo.

Y además, **cómo se comprueba solo**: lo que el kit mira al terminar para saber que lo
que ha hecho está bien.

| Si el kit produce… | Comprueba al terminar |
|---|---|
| un archivo | que existe, dónde debía, y que no está vacío |
| un informe | que están todas las secciones prometidas y ninguna en blanco |
| un HTML | que abre y que no tiene enlaces ni imágenes rotas |
| imágenes o vídeo | dimensiones y duración con el comando correspondiente |
| datos (CSV/JSON) | número de filas, columnas esperadas, y huecos marcados y no inventados |
| varios textos | que cumple la lista comprobable, punto por punto |

Esa comprobación va como último paso del `SKILL.md` del kit nuevo, y se prueba en el
Paso 7 con el ejemplo de práctica.
