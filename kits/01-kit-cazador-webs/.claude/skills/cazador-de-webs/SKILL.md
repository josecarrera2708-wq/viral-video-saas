---
name: cazador-de-webs
description: Caza una web de un negocio (URL) y la reconstruye como una película 3D inmersiva con el branding real del cliente, entregando web nueva + diagnóstico + propuesta comercial + zip listo para publicar. Usa esta skill siempre que el usuario diga "caza esta web", "cázame [URL]", pase la URL de un negocio para rediseñar, o pida analizar/rehacer la web de un cliente potencial.
---

# Cazador de Webs

Recibes la URL de la web de un negocio. Entregas, en `cazas/[dominio]/`:
`branding.json`, `diagnostico.md`, `index.html` (la película 3D inmersiva),
`web-lista.zip` (para publicar) y `propuesta.md` (para vender).
Trabaja SOLO con webs públicas de negocios. Si el usuario intenta pasarte código
privado o datos de clientes, recuérdale la regla de seguridad del kit y para.

**Dos reglas de supervivencia** (una caza es una sesión larga y puede cortarse):
- **Contexto ligero**: NO leas PDFs/PPTX/archivos pesados enteros — la
  información de cartas y menús casi siempre está también en los HTML. Si un
  archivo pesa, extrae solo lo que necesitas. Un contexto hinchado = cortes.
- **Escribe cada entregable EN CUANTO lo tengas** (no acumules trabajo en
  memoria). Si la sesión se corta, lo escrito queda — y al reanudar ("continúa
  la caza donde la dejaste") retomas por el primer archivo que falte.

## Fase 1 · Reconocimiento

1. Descarga la web: `curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" [URL]`
   (guarda el HTML en `cazas/[dominio]/original/`). Si la respuesta es un 403,
   una página de challenge o pesa menos de 2 KB, la web está bloqueando la
   descarga: usa el navegador (Playwright/Chrome) para obtener el HTML
   renderizado. Si no hay navegador disponible: prueba con WebFetch; si tampoco,
   ofrece instalar Chromium (`npx playwright install chromium`) y, si el
   usuario prefiere no instalarlo, proponle cazar otra web.
   **Caza de práctica**: si el usuario pide cazar "la web de ejemplo", no
   descargues nada — copia `ejemplos/web-de-practica/` a
   `cazas/web-de-practica/original/` y sigue las fases normales desde ahí.
2. Si hay navegador disponible (Playwright/Chrome), haz captura completa de la
   página en escritorio Y en móvil (375px) y guárdalas. Analiza las capturas con
   visión: jerarquía, primer pantallazo, dónde se pierde el ojo.
3. Extrae el branding REAL y guárdalo en `branding.json`:
   - **Logo**: busca en el HTML (`<img>` del header, `og:image`, favicon de mayor
     resolución, `apple-touch-icon`). Descárgalo a `original/logo.*`.
   - **Colores**: los que el negocio usa de verdad (CSS del sitio, color del logo,
     botones). Elige: primario, secundario, fondo, texto. En hex.
   - **Tipografías**: las que cargan (Google Fonts del HTML) o las más parecidas.
   - **Copy y datos — EXHAUSTIVO**: nombre, claim, teléfono, WhatsApp, dirección,
     horario completo, redes. Y TODO el contenido que la web tenga: carta/menús
     con sus precios reales, lista completa de servicios/especialidades, historia
     del negocio (fechas, generaciones, origen), eventos/celebraciones que
     ofrecen, reseñas literales de clientes, premios o menciones. La película
     final debe poder contar el negocio ENTERO — si extraes poco, quedará corta.
     Recorre también las páginas interiores (carta, historia, contacto…), no
     solo la portada. Textuales — no inventes NADA.
4. Formato de `branding.json`:

```json
{
  "negocio": "", "claim": "", "logo": "assets/logo.png",
  "colores": { "primario": "#", "secundario": "#", "fondo": "#", "texto": "#" },
  "tipografias": { "titulos": "", "texto": "" },
  "contacto": { "tel": "", "whatsapp": "", "direccion": "", "horario": "" },
  "servicios": [], "pruebas_sociales": [],
  "carta": [ { "nombre": "", "precio": "" } ],
  "menu_del_dia": { "precio": "", "incluye": "" },
  "historia": "", "eventos": [], "premios": [], "resenas": []
}
```

Todo lo extraído en el punto 3 tiene su campo: la Fase 3 construye la película
SOLO desde este JSON — lo que no esté aquí no existirá en la web nueva.

## Fase 2 · Diagnóstico (`diagnostico.md`)

Exactamente 5 problemas CONCRETOS y observables de su web actual, cada uno con:
qué está mal → por qué le cuesta clientes → cómo lo resuelve la nueva. Nada de
vaguedades ("mejorar el diseño" NO; "el teléfono no aparece hasta el tercer scroll
y en móvil no es clicable" SÍ).

## Fase 3 · Reconstrucción (`index.html`)

Una landing de UNA página, autocontenida (CSS y JS inline o del motion-kit copiado
al lado), responsive, con el branding extraído. **Copia `motion-kit/motion.css` y
`motion-kit/motion.js` junto al `index.html` y úsalos** — no improvises la animación.
**Copia también el logo y las fotos que uses de `original/` a una carpeta
`assets/` junto al `index.html`, y referéncialas SIEMPRE como `assets/...`** —
así la web funciona igual en el preview local y publicada (nada debe apuntar a
`original/`, que no viaja en el zip).

**La landing ES UN VUELO 3D A TRAVÉS DEL NEGOCIO.** Nada de secciones: la
pantalla queda fija y el scroll conduce una cámara que VUELA HACIA DENTRO — cada
contenido vive a una profundidad del túnel, emerge del fondo, llega a foco y lo
atravesamos (nos metemos por dentro de sus fotos) para llegar al siguiente.
Estructura obligatoria (el patrón exacto está comentado en `motion.css`):

```
<body>
  <header> barra fija: logo pequeño + teléfono clicable + botón reservar </header>
  <div class="mk-film" data-mk-scrolly data-mk-shots="16" style="--mk-nshots:16">
    <div class="mk-film-stage mk-tunnel"> …los .mk-zshot con --zi:0…15… </div>
  </div>
  <footer> cierre estático: CTA gigante + contacto + mapa (SIN efectos) </footer>
</body>
```

Cada `.mk-zshot` lleva su índice `--zi` (0, 1, 2…). El sistema hace el resto:
emerge desde el fondo con niebla (`mk-zfog` en sus fotos), pasa a foco y lo
atraviesas. Dentro de un zshot puedes dar VOLUMEN con `mk-zdepth` (capas a
distinta `--z`: la foto al fondo, el plato a media distancia, el texto delante
— al atravesarlo se abre en paralaje). Dentro de los zshots usa SOLO los efectos
que funcionan ahí: `mk-split` (titulares), `mk-counter` (cifras), `mk-marquee`,
y para el volumen `mk-zdepth` y `mk-zfog`. Los `mk-fx-*` y `mk-seq` pertenecen a
la película plana v4 y dentro de un zshot no hacen nada — no los uses aquí.

**LA PELÍCULA CUENTA EL NEGOCIO ENTERO — mínimo 14-18 zshots.** Nada de
resumir: toda la información extraída en Fase 1 tiene su momento. Storyboard
tipo (adapta contenidos y número al negocio real):

1. Su logo a oscuras, emergiendo del fondo del túnel.
2. Titular editorial (`mk-split`) + su mejor foto ambiente detrás (`mk-zdepth`).
3. ENTRAMOS por dentro de esa foto → statement de historia ("Desde 1973…").
4. La historia en 2-3 zshots: origen, generaciones, lo que les hace únicos
   (frases grandes + fotos de fondo con `mk-zfog`).
5. El producto estrella en volumen: foto de fondo + plato a media profundidad
   (`mk-zdepth`) + nombre y precio REAL delante.
6. 2-3 zshots más de carta/especialidades CON SUS PRECIOS (del menú real).
7. El menú del día si existe: qué incluye y su precio, como plano propio.
8. Atravesamos otra foto potente (cocina, horno, terraza…).
9. Cifras con `mk-counter` (años, clientes, reseñas — reales).
10. Eventos/celebraciones si los ofrecen: qué, para cuántos.
11. Reseñas literales de clientes, 2 zshots de citas.
12. Dónde están: dirección + horario completo, grande y claro.
13. CTA final: "Reserva tu mesa" + teléfono ENORME con `mk-pulse`.
    Al soltar la película, el scroll aterriza en el footer estático.

`data-mk-shots` y `--mk-nshots` = número REAL de zshots que uses.

**Reglas de la experiencia**:
- El scroll NUNCA se secuestra (nada de hijacking): scroll nativo, los efectos
  van pegados al dedo. En móvil todo debe funcionar igual de fluido.
- Solo `transform`/`opacity`/`clip-path` en los efectos (nada de animar layout).
- El teléfono/reserva SIEMPRE alcanzable: la barra fija vive fuera de la película.
- El footer final, estático y claro — la conversión no se anima. Todo el
  contenido importante (dirección, horario, teléfono) debe existir también ahí.
- **Legibilidad obligatoria**: texto sobre foto SIEMPRE con `text-shadow` fuerte
  o scrim oscuro detrás.

**Dirección de arte**: tipografía display grande para titulares (una de Google
Fonts que respete el carácter del negocio — máximo 2 fuentes), fotos del cliente
a sangre completa (nunca thumbnails flotando), y decide fondo claro u oscuro
según el branding extraído — no siempre oscuro por defecto.

Reglas duras: cero lorem ipsum (reescribe el copy real, mejorado); cero datos
inventados; el teléfono/WhatsApp SIEMPRE clicable y visible en el primer pantallazo;
sin fechas; máximo 2 tipografías; los colores del CLIENTE, no los tuyos.
**Control de calidad antes de entregar (obligatorio — la web solo se entrega
cuando pasa TODO):**

- **Móvil (375px)**: sin scroll horizontal, textos legibles, la película fluida.
  Si hay navegador, captura a 375px y revísala con visión; si no, audita el CSS:
  media queries presentes, tamaños con `clamp()`, imágenes con `max-width:100%`,
  nada de anchos fijos en px que desborden.
- **Conversión**: el teléfono/WhatsApp clicable (`tel:`/`wa.me`) visible en el
  primer pantallazo (barra fija) Y en el footer estático.
- **Imágenes**: ninguna rota, todas con ruta relativa `assets/...`.
- **Legibilidad**: todo texto sobre foto lleva scrim oscuro o `text-shadow` fuerte.
- **Técnica**: `<meta name="viewport">` presente, `<title>` con el nombre del
  negocio, `data-mk-shots` y `--mk-nshots` coinciden con el número real de zshots.

Si algo falla, corrígelo y vuelve a comprobar antes de seguir.

Al terminar, sírvela en local desde la carpeta de la caza y dile al usuario la
URL (http://localhost:8777). El comando depende del sistema — si `/setup` dejó
anotada la herramienta en `.claude/setup-completado.json`, usa esa; si no,
prueba en orden y usa el primero que exista: `python3 -m http.server 8777`
(Mac/Linux) → `py -3 -m http.server 8777` → `python -m http.server 8777`
(Windows; evita `python3` en Windows: suele ser un falso acceso a la tienda de
Microsoft).

## Fase 4 · Empaquetado (`web-lista.zip`)

Antes de empaquetar, comprueba que ninguna imagen está rota abriendo el
`index.html` servido en local: todas las rutas deben ser relativas (`assets/...`).

Crea un zip con TODO lo que la web necesita para publicarse — `index.html`,
`motion.css`, `motion.js` y la carpeta `assets/` (logo y fotos usadas). NO
incluyas `original/` ni los `.md`. Usa el comando de empaquetado EXACTO anotado
en `.claude/setup-completado.json` (lo dejó `/setup` ya probado); si no existe
el marcador, decide tú sin preguntar al usuario:

- Mac/Linux: `zip -r cazas/[dominio]/web-lista.zip ...` ejecutado desde la
  carpeta de la caza, o mejor en un solo comando desde la raíz del kit:
  `tar -a -cf cazas/[dominio]/web-lista.zip -C cazas/[dominio] index.html motion.css motion.js assets`
  (el tar de Mac es bsdtar y crea ZIP de verdad con `-a`).
- Windows: usa la ruta completa
  `/c/Windows/System32/tar.exe -a -cf cazas/[dominio]/web-lista.zip -C cazas/[dominio] index.html motion.css motion.js assets`.
  CUIDADO: el `tar` a secas de Git Bash es GNU tar y crea en silencio un
  archivo que NO es un zip — no lo uses.
- Alternativa portable: `[python elegido] -m zipfile -c web-lista.zip index.html motion.css motion.js assets/`
  desde la carpeta de la caza.

Evita encadenar `cd ... && comando` (los permisos pre-aprobados del kit no
cubren los comandos encadenados): usa `-C` o rutas relativas desde donde estés.

**Verifica el zip antes de darlo por bueno**: sus dos primeros bytes deben ser
`PK` (compruébalo con `[python elegido] -m zipfile -t cazas/[dominio]/web-lista.zip`,
que debe decir "Done testing"). Si no pasa, reempaqueta con la alternativa
portable.

Este zip es lo que el usuario arrastra a Netlify Drop (preview gratis) o sube al
Administrador de archivos de Hostinger (publicación final) — el paso a paso está
en `despliegue.md` del kit. Menciónaselo al entregar.

## Fase 5 · Propuesta (`propuesta.md`)

Rellena `plantilla-propuesta.md` (está en la raíz del kit) con: los 5 puntos del
diagnóstico, 3 mejoras estrella de la nueva web, y los precios del kit. Tono cercano
y directo, sin jerga técnica — la lee el dueño del negocio.

Firma: `[TU NOMBRE]` y `[TU CONTACTO]` se rellenan con los datos guardados en
`.claude/setup-completado.json` (los preguntó `/setup`); si no están, pregúntalos
ahora y guárdalos ahí. `[LINK A LA DEMO]` se queda tal cual: recuérdale al
usuario que se rellena tras publicar la preview (ver `despliegue.md`).

## Al entregar

Resume en 5 líneas: qué encontraste, qué construiste, dónde está cada archivo,
cuánto ha costado la caza aproximadamente (unos pocos euros de uso de API o una
fracción del uso del plan — recuérdale que ese coste ínfimo respalda un
servicio que se cobra desde 800 €) y el siguiente paso (enseñárselo al cliente).
