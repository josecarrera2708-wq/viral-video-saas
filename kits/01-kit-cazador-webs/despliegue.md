# Publicar la web cazada — sin terminal, todo por interfaz

Cada caza termina con un archivo `web-lista.zip` en la carpeta de la caza.
Ese zip contiene todo lo que la web necesita (HTML, animaciones, logo, fotos).
Publicarla son dos momentos distintos:

## Momento 1 · La preview para ENSEÑAR al cliente (gratis, 30 segundos)

Antes de cobrar nada, necesitas una URL que mandarle con la propuesta.

1. Entra en **Netlify Drop** (app.netlify.com/drop) — cuenta gratuita.
2. **Arrastra SOLO el archivo `web-lista.zip`** a la ventana (Netlify acepta
   zips). No subas la carpeta entera de la caza: contiene tu diagnóstico y tu
   propuesta con precios, y quedarían visibles en la URL que le mandas al
   cliente — el zip es la versión limpia.
3. Netlify te da una URL pública al instante (tipo `algo-aleatorio.netlify.app`).
4. Pega esa URL en la propuesta, donde dice `[LINK A LA DEMO]`.

Eso es todo. Sin dominio, sin pagar, sin configurar nada. La preview es fea de
URL a propósito — es una muestra, no el producto final.

## Momento 2 · La publicación REAL cuando el cliente dice sí

Ahora sí: dominio propio y hosting serio. Con Hostinger, todo por el panel
(pasos verificados contra su documentación oficial — los nombres de los menús
son literales):

1. **Crea el sitio**: en hPanel, **Sitios web → Agregar sitio web** (el plan más
   básico sobra para una landing; los planes normales admiten varios sitios —
   añade el del cliente al tuyo).
2. **Dominio**: si el cliente ya tiene dominio, conéctalo (hPanel te muestra los
   DNS que hay que cambiar — los datos que le dicen a internet dónde vive la
   web); si no, cómpraselo desde el propio panel (y factúraselo — detalle que
   suma).
3. **Abre el Administrador de Archivos**: **Sitios web → Administrar** (en el
   sitio del cliente) → **"Administrador de Archivos"** en la barra lateral
   izquierda.
4. **Sube el zip**: entra en la carpeta **`public_html`** → botón **Upload**
   (arriba a la derecha) → opción **"Archivo"** → selecciona `web-lista.zip`.
5. **Extráelo**: clic derecho sobre `web-lista.zip` → **"Desarchivar"** → en el
   diálogo, como destino deja `public_html` → botón **Desarchivar**.
   Importante: el `index.html` debe quedar DIRECTAMENTE dentro de
   `public_html` (no en una subcarpeta). Si se extrajo en una subcarpeta, mueve
   su contenido a `public_html`. Borra el zip al terminar.
6. **Abre el dominio**. Ya está publicada.
7. El SSL (candado https) se activa solo en unos minutos; si no: hPanel →
   Seguridad → SSL → Instalar.

## Actualizar una web ya publicada (los cambios del mantenimiento)

Cuando el cliente pida un cambio: se lo pides a tu Cazador ("cambia X en la web
de [cliente]"), que edita la caza y regenera `web-lista.zip`. Para resubirla:

1. hPanel → Administrador de Archivos → `public_html` del sitio del cliente.
2. Sube el `web-lista.zip` nuevo → clic derecho → **Desarchivar** en
   `public_html`, aceptando sobrescribir lo que haya.
3. Borra el zip. Abre el dominio y comprueba el cambio. Listo.

## El truco del negocio recurrente

El hosting de esa landing te cuesta ~2-4 €/mes. El mantenimiento que cobras son
99 €/mes (cambios incluidos — los hace tu Cazador en minutos). Esa diferencia,
multiplicada por cada cliente que acumulas, es el ingreso recurrente del sistema.

> Consejo: agrupa todas las webs de tus clientes en un mismo plan de Hostinger
> mientras el plan lo permita — un solo panel, un solo pago, muchos clientes.
