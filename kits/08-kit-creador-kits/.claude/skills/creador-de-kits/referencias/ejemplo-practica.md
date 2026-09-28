# El ejemplo de práctica

Todo kit lleva uno. Es un caso ficticio, guardado en `ejemplos/`, con el que el kit se
puede probar **sin datos reales, sin conexión y sin gastar nada**.

Sirve para tres cosas, y las tres importan:

1. Que el usuario vea un resultado en los primeros cinco minutos, antes de arriesgar
   sus datos.
2. Que **tú** puedas ejecutar el kit en el Paso 7 y descubrir sus defectos antes de que
   los descubra un cliente.
3. Que el kit se pueda demostrar delante de alguien sin exponer a nadie.

---

## Las cinco condiciones

### 1 · Ficticio y verosímil

Un negocio, una persona o un documento inventados, con nombre, ciudad y detalles que
suenen reales: "Panadería Lasa, Errenteria, 3 empleados, abrió en 2019".

**Nunca datos de una persona o empresa de verdad**, ni aunque el usuario ofrezca los
de un cliente suyo. Los ejemplos viajan en el ZIP, se enseñan en pantalla y acaban en
sitios que nadie previó. Si el usuario insiste, cámbiale los nombres y los números y
dile por qué.

Verosímil es tan importante como ficticio: un ejemplo obviamente falso ("Empresa
S.A., producto A, precio 100") no destapa defectos, porque el kit no se enfrenta a
nada de lo que se va a encontrar de verdad.

### 2 · Offline

El ejemplo tiene que funcionar sin internet, con la única excepción de un kit cuya
tarea *sea* buscar en internet.

| Si el kit lee… | El ejemplo es… |
|---|---|
| páginas web | archivos `.html` guardados en `ejemplos/web-lasa/` — HTML sencillo pero completo, con sus fallos dentro |
| PDFs o documentos | un PDF o un `.md` que lo imite, con la estructura del documento real |
| capturas de pantalla | imágenes propias generadas para el ejemplo, o descripciones en texto de lo que se vería |
| hojas de cálculo | un `.csv` con 20-40 filas: suficientes para que aparezcan casos raros |
| vídeos o audio | un archivo de pocos segundos, o los metadatos ya volcados en un `.json` |
| solo conversación | un `caso-practica.md` con el encargo escrito como lo escribiría un cliente, con sus ambigüedades |

Regla de tamaño: **el ejemplo cabe en el kit sin engordarlo**. Un ejemplo de 40 MB no
viaja bien en un ZIP; si el kit trabaja con vídeo, basta un clip de tres segundos.

### 3 · Con errores plantados y contados

Aquí está el valor del ejemplo. Se meten **entre 10 y 16 fallos a propósito**, de
varios tipos y de varias gravedades, y se apunta la lista completa en el
`_CONTRATO.md`:

```
Errores plantados en ejemplos/web-lasa/ (13):
 1. El teléfono de la cabecera y el del pie no coinciden
 2. No hay ninguna dirección física en toda la web
 3. El titular es un lema ("Pasión por el pan de verdad"), no dice qué vende
 4. Los precios están en la foto, no en texto
 5. El formulario de contacto pide 9 campos
 6. Falta el aviso de cookies
 7. Tres imágenes de 4 MB cada una
 8. El enlace a "nuestros productos" está roto
 9. El horario dice "abierto todos los días" y más abajo "cerrado los lunes"
10. Ninguna reseña ni prueba social
11. La página no dice a qué ciudad reparte
12. El pie tiene el copyright en 2021
13. No hay ninguna vía de contacto por WhatsApp ni teléfono en móvil
```

Reglas del reparto:

- **Que haya de todos los tamaños**: dos o tres graves, la mayoría medianos, y un par
  finos que solo un buen sistema encuentra. Los finos son los que distinguen un kit
  serio de uno que solo enumera lo obvio.
- **Reparte por dimensiones**: al menos un error por cada dimensión que el kit puntúe.
  Si una dimensión no tiene ningún error plantado, en el Paso 7 no se prueba.
- **Alguna contradicción interna** (dos datos que se pisan). Son las que obligan al kit
  a comparar en vez de leer.
- **Nada de errores imposibles**: todos tienen que ser cosas que pasan de verdad en
  ese oficio.

### 4 · Con huecos a propósito

Dos, y con papeles distintos:

- **Un hueco que tiene que acabar como "sin datos"** en el resultado: un dato que no
  está en ninguna parte y que el kit no puede deducir. Si el kit se lo inventa o lo
  estima, ese es el defecto más grave posible y se arregla antes de seguir.
- **Un hueco que tiene que provocar que el kit pregunte**: algo que el usuario sí
  podría saber ("¿cuánto te cuesta captar un cliente?"). Si el kit no pregunta y sigue
  como si nada, le falta el paso de preguntar.

Estos dos huecos son la prueba de honestidad del kit. Ningún otro test la sustituye.

### 5 · Con su `LEEME.md`

Dentro de `ejemplos/`, un archivo corto que diga:

- **Qué es** y que es **ficticio** (en la primera línea, sin letra pequeña).
- Qué contiene cada archivo.
- **Cómo se usa**: la frase exacta que el usuario escribe para lanzarlo ("analiza el
  ejemplo de práctica").
- Qué resultado debería salir, más o menos: la banda de la nota o el tipo de
  entregable. Así el usuario sabe si su instalación funciona bien.
- **Lo que NO dice**: la lista de errores plantados. Esa vive en el `_CONTRATO.md`. Si
  está en el ejemplo, el usuario la lee y ya no prueba nada.

---

## Enchufar el modo práctica en el kit

Que el ejemplo exista no basta: hay que poder lanzarlo con una frase.

- **En el `CLAUDE.md`** del kit nuevo, fila en la tabla de decisión:
  `| "analiza el ejemplo", "quiero probarlo primero", "modo práctica" | Skill principal
  sobre ejemplos/, avisando de que es un caso ficticio |`
- **En el `SKILL.md`**, el **Paso 0** de la skill: *¿caso real o de práctica?* Si es de
  práctica, la entrada sale de `ejemplos/` y el resultado se guarda como
  `workspace/practica-…` para no confundirlo con un trabajo real.
- **En el wizard `/setup`**, el último paso lo ofrece: "¿lo probamos con el ejemplo de
  práctica? Tarda un par de minutos y no gasta nada".
- **En el `EMPIEZA-AQUI.md`**, como paso 3 de los tres.

---

## La nota calibrada

Después del Paso 7 ya sabes qué nota o qué resultado da el ejemplo. **Apúntala** en el
`_CONTRATO.md` y en el `LEEME.md` de `ejemplos/`, como referencia:

> El ejemplo de práctica saca 48/100 (banda "flojo") y encuentra 11 de los 13 errores
> plantados.

Sirve de dos maneras: el usuario sabe si su copia funciona bien, y si un día el kit
empieza a dar 70 con el mismo ejemplo, algo se ha tocado sin querer.
