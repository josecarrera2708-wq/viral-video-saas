# El informe HTML

Solo para kits cuyo entregable es un informe. Si el kit genera otra cosa, salta este
archivo.

El informe es lo que el usuario enseña o entrega. Es la cara del kit, y muchas veces
lo único que el cliente final llega a ver. Por eso tiene reglas.

---

## La regla número uno: autocontenido

**Un solo archivo `.html` que funciona sin internet, para siempre.** Se abre haciendo
doble clic, se manda por correo, se guarda en una carpeta y dentro de dos años sigue
viéndose igual.

Eso significa:

- **El CSS va dentro**, en una etiqueta `<style>`. Nada de hojas de estilo externas.
- **Nada de CDN**: ni Tailwind, ni Bootstrap, ni Google Fonts, ni librerías de
  gráficos. El día que ese enlace caiga, el informe del cliente se rompe.
- **Tipografías del sistema**:
  `font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;`
  Se ve bien en Mac y en Windows sin descargar nada.
- **Imágenes**: o incrustadas en base64, o no hay imágenes. Un `<img src="fotos/1.png">`
  se rompe en cuanto el archivo viaja solo.
- **Gráficos sin librerías**: las barras se hacen con `div` y anchos en porcentaje, y
  quedan perfectas. Si hace falta algo más, un SVG escrito a mano dentro del HTML.
- **JavaScript, el mínimo** y siempre dentro del archivo. Un informe que necesita JS
  para leerse es un informe que algún día no se lee.

---

## La estructura que funciona

En este orden, porque es el orden en que se lee un informe:

1. **Cabecera** — qué es, de quién o de qué, y la fecha. Si el kit se entrega a
   clientes, aquí va la firma del usuario (o nada, si es marca blanca).
2. **La nota o el veredicto, grande, arriba.** Con su banda y una frase que la
   explique. Quien abre el informe tiene que saber en 3 segundos si va bien o mal.
3. **Resumen ejecutivo** — de 5 a 8 líneas. Lo que diría el usuario si tuviera medio
   minuto en un ascensor.
4. **Las 3 acciones prioritarias**, ordenadas por lo que cambian dividido por lo que
   cuestan. Es la parte por la que se paga.
5. **El detalle por dimensiones o por fases**: cada una con su nota, su prueba al lado
   y qué hacer. Aquí van las citas literales, los datos medidos y las capturas.
6. **Lo que no se pudo medir** — la lista de "sin datos" y por qué. Esta sección da
   credibilidad, no la quita: demuestra que el resto de números son reales.
7. **Cómo se ha medido** — el sistema, los pesos y su versión. Para que el informe se
   pueda auditar y comparar con el del mes que viene.

Y en informes largos, un índice de anclas arriba (`<a href="#dimension-3">`) para
poder saltar. Con más de 6 secciones, sin índice se pierde.

---

## Presentación

- **Ancho de lectura limitado**: `max-width: 900px; margin: 0 auto;`. Un informe a
  todo el ancho de un monitor no se lee.
- **Escala de color con significado**, la misma que las bandas de la nota: rojo para
  crítico, naranja para flojo, amarillo para aceptable, verde para bueno. Y siempre
  con **texto además del color**, porque hay quien no distingue rojo de verde y porque
  el informe se imprime en blanco y negro.
- **Sin emojis.** Nunca en un documento que un cliente puede reenviar. Símbolos
  sobrios: ✓ y ✗, y las notas numéricas.
- **Tablas para comparar, no para maquetar.**
- **Imprimible**, porque se imprime más de lo que parece:

```css
@media print {
  body { font-size: 11pt; }
  .seccion { page-break-inside: avoid; }
  a[href^="http"]::after { content: " (" attr(href) ")"; }
}
```

Esa última línea es la que salva el informe impreso: los enlaces se leen en papel.

---

## Nombre y sitio

- Va **siempre a `workspace/`**, nunca a la raíz del kit.
- Nombre con caso y fecha: `workspace/informe-[caso]-[AAAA-MM-DD].html`. Sin fecha,
  el segundo informe pisa el primero y el usuario pierde la comparación.
- El kit **abre el informe al terminar** (`open` en Mac, `start` en Windows) y dice la
  ruta en el chat. Un informe que el usuario tiene que buscar es un informe que no ve.

---

## El cuaderno de trabajo (para informes largos)

Si el informe tarda en construirse — varias dimensiones, varias fuentes —, el kit va
apuntando lo que encuentra en `workspace/[caso]-hallazgos.md` **a medida que avanza**,
no al final. Dos razones, y las dos han pasado en este proyecto:

- Si la sesión se corta o se acaba el límite de uso, el trabajo no se pierde: se
  retoma por donde iba.
- El informe final se escribe de una vez, leyendo el cuaderno, y sale más coherente
  que escrito a trozos.

El cuaderno es material interno: no viaja al cliente.

---

## La comprobación final, antes de decir "listo"

- El archivo existe en `workspace/` y pesa más de unos pocos KB.
- Están todas las secciones prometidas y **ninguna vacía** (una sección con el título
  y nada debajo es el defecto más habitual del Paso 7).
- La nota global cuadra con las notas de las dimensiones y sus pesos. Hazla a mano una
  vez: en las pruebas de este proyecto, esta cuenta ha fallado.
- Ninguna dimensión "sin datos" tiene número, y su peso está repartido.
- No hay marcadores de plantilla sin sustituir (`[[algo]]`, `TODO`, `lorem`).
- No hay ni un dato inventado. Si hay una cifra, salió de algún sitio y ese sitio está
  citado.
