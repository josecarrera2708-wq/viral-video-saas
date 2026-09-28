# scripts/ · el dibujante de los mapas

Aquí vive `excalidraw.py`, el programa que dibuja los dos mapas de proceso del
informe: **cómo funciona hoy** el negocio y **cómo funcionaría** una vez
automatizado.

**No tienes que ejecutar nada.** Claude lo usa solo cuando hace la auditoría. Esta
carpeta está documentada por si algún día quieres cambiar cómo se ven los mapas.

## Qué produce

De una sola descripción del flujo salen dos archivos:

| Archivo | Para qué |
|---|---|
| `.excalidraw` | El dibujo **editable**. Se abre en excalidraw.com o con la extensión Excalidraw de VS Code. Puedes mover cajas, cambiar textos y exportar en PNG para una presentación. |
| `.svg` | El mismo dibujo, que se **incrusta dentro del informe HTML**. Por eso el informe se ve igual sin internet. |

Los dos salen de la misma descripción, así que el dibujo editable y el del
informe **no pueden decir cosas distintas**.

## No necesita instalar nada

Es Python de librería estándar: nada de `pip install`. Python ya viene en Mac y en
Windows lo trae la instalación de Git.

Si en tu ordenador no hubiera Python, la auditoría se hace igual: Claude escribe
los archivos a mano. Los mapas salen algo más simples, el informe entero no
cambia.

## Cómo se le describe un flujo

La descripción es un JSON con nodos colocados en una rejilla de columnas y filas.
Un ejemplo mínimo:

```json
{
  "titulo": "Estudio Lúa",
  "diagramas": [
    {
      "id": "mapa-1",
      "titulo": "Cómo funciona hoy",
      "nodos": [
        {"id": "n1", "texto": "La clienta llama", "tipo": "inicio", "estado": "neutro", "col": 1, "fila": 0},
        {"id": "n2", "texto": "Se apunta en la agenda de papel", "tipo": "caja", "estado": "manual", "col": 1, "fila": 1},
        {"id": "f1", "texto": "Solo se ve desde el mostrador", "tipo": "caja", "estado": "fuga", "col": 2, "fila": 1}
      ],
      "flechas": [
        {"de": "n1", "a": "n2"},
        {"de": "n2", "a": "f1", "estilo": "discontinua"}
      ]
    }
  ]
}
```

Formas (`tipo`): `inicio` y `fin` son elipses, `decision` es un rombo, `caja` es
un paso normal y `nota` es un comentario al margen. Un nodo puede ocupar dos
columnas con `"ancho": 2`.

Colores (`estado`), que son los que dan de leer el mapa de un vistazo:

| `estado` | Cómo se pinta | Qué significa |
|---|---|---|
| `neutro` | gris | Paso normal |
| `manual` | naranja | Lo hace una persona a mano |
| `fuga` | rojo | Aquí se pierde cliente, tiempo o dinero |
| `auto` | azul | Va solo, sin que nadie lo toque |
| `ok` | verde | Ya funciona bien |

Las flechas admiten `texto` (una etiqueta, "sí", "12 %"…) y
`"estilo": "discontinua"` para lo que no es el camino principal.

## Cómo se ejecuta

```
python3 scripts/excalidraw.py workspace/[negocio]-mapas.json --salida workspace/auditoria-[negocio]
```

Escribe un `.excalidraw` con todos los diagramas y un `.svg` por diagrama, con el
`id` del diagrama en el nombre. Con el ejemplo de arriba saldrían
`auditoria-[negocio].excalidraw` y `auditoria-[negocio]-mapa-1.svg`. Después se
valida a sí mismo.

Para comprobar un archivo ya generado:

```
python3 scripts/excalidraw.py --validar workspace/auditoria-[negocio].excalidraw
```

## Lo que se revisa solo

- **Que el archivo abra en Excalidraw.** Cada elemento se comprueba clave por
  clave; si le faltara alguna, Excalidraw lo rechazaría con un error confuso.
- **Que el texto quepa en su forma.** Las cajas crecen para no cortar lo que
  dicen.
- **Que las flechas no atraviesen cajas ajenas.** Si pasa, avisa por pantalla
  diciendo qué nodo mover. El archivo se genera igual, pero se lee peor.

Si ves uno de esos avisos, dile a Claude "arregla la colocación del mapa" y
recoloca los nodos.
