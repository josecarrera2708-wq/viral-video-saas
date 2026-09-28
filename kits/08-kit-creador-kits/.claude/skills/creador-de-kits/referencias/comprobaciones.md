# Comprobar antes de escribir una línea

Este archivo es el Paso 3 de la skill. Su regla es una: **nada se da por supuesto**.
No supongas que una página se puede leer, que un programa está instalado, que un
formato se abre o que una clave funciona. Se prueba, con un comando, antes de escribir
el kit. Y el resultado se apunta en el contrato con ✓ o ✗, la fecha y lo que devolvió.

Se comprueba con **el caso real del usuario**. Si el kit va a leer la web de su
gestoría, se prueba esa web — no `example.com`.

---

## Lo que ya se sabe (comprobado en este proyecto, no lo vuelvas a descubrir)

| Fuente | Qué pasa | Vía que sí funciona |
|---|---|---|
| Página de canal o vídeo de **YouTube** con lectura de webs | Devuelve solo el pie de página: ni títulos, ni visitas, ni suscriptores | `yt-dlp` (binario único, Mac y Windows), que devuelve títulos, duraciones, visitas, etiquetas, capítulos, descripción, miniaturas y subtítulos automáticos |
| **Instagram, TikTok, Facebook** | Devuelven una página de inicio de sesión. No es un fallo del kit: es su diseño | Capturas de pantalla del propio usuario. Y las capturas de *Estadísticas* de la app aportan datos privados (alcance, visitas al perfil, clics) que ningún raspador consigue |
| **LinkedIn** | Los perfiles públicos sí se suelen leer | Lectura de webs normal |
| **Buscadores por `curl`** (DuckDuckGo lite, Mojeek…) | Captcha o "verification required" | La herramienta de búsqueda del propio Claude Code (`WebSearch`) |
| **Carritos y pasarelas de pago** | Se montan con JavaScript: casi nunca se leen bien | Navegador automatizado (Playwright/Chrome) o pedirle al usuario que recorra él el proceso y cuente los pasos |
| **Tiendas online medianas y grandes** | Protección anti-bots (Cloudflare y similares): 403, 401 o HTML vacío | Navegador automatizado; si no, el HTML crudo, el sitemap, la versión móvil o el feed de producto |
| **Paneles privados** (analítica, pedidos, facturación) | No se entra, y no se intenta | Que el usuario dé los números o una captura. Se piden como opcionales |

Y una regla de seguridad heredada: **nunca se completa una compra, ni se crea una
cuenta, ni se entra en el panel de nadie** al comprobar nada.

---

## Las comprobaciones, una por eje de entrada

### Leer páginas web

```bash
# ¿Responde y con qué código?
curl -sIL -o /dev/null -w "%{http_code}\n" "URL_REAL_DEL_USUARIO"
```

Y en paralelo, lectura con la herramienta de webs sobre esa misma URL. Las cuatro
respuestas posibles:

- Devuelve el contenido → ✓.
- Devuelve una página de login → esa fuente no se puede leer: capturas o dato del
  usuario.
- Devuelve HTML casi vacío → la página se monta con JavaScript: navegador
  automatizado, o buscar la versión estática (sitemap, feed, versión móvil, AMP).
- 403 o 401 → protección anti-bots. Navegador automatizado, y si no, se cae del kit.

### Buscar información

Una búsqueda corta con un término real del usuario (el nombre de su negocio, de su
competidor, de su sector). Se comprueba que devuelve resultados **útiles**, no solo
que devuelve algo.

### Leer archivos del usuario

Pídele un archivo de muestra y **ábrelo de verdad**. Un PDF, un `.docx`, una hoja de
cálculo o una imagen se abren o no se abren, y eso cambia el kit entero.

- Si el PDF es un escaneo (una foto del documento), el texto no está: se lee como
  imagen. Compruébalo con un caso suyo, porque es la diferencia entre un kit que
  funciona con sus documentos y uno que no.
- Si es una hoja de cálculo con fórmulas, comprueba si necesitas los valores o las
  fórmulas.
- Comprueba también el caso **vacío**: qué hará el kit si la carpeta `entrada/` está
  vacía. Tiene que decirlo, no romperse.

### Ver capturas de pantalla

Abre una imagen y descríbela. Si se ve, ✓. Comprueba además el caso incómodo: una
captura de móvil larga, con letra pequeña. Si no se lee, el guion de las capturas
tiene que pedirlas de otra manera (por partes, o en horizontal).

### Un programa externo

```bash
which PROGRAMA   || echo "no está (Mac/Linux)"
where PROGRAMA   || echo "no está (Windows)"
PROGRAMA --version
```

Si no está, **instálalo ahora** y comprueba que funciona, para saber que el wizard del
kit va a poder hacerlo:

```bash
brew install PROGRAMA                    # Mac
winget install ID.DEL.PROGRAMA           # Windows
```

Plan B si el gestor falla: descargar el binario dentro del kit en `bin/` y guardar esa
ruta en `setup-completado.json`. Este plan B ya está probado en el proyecto y es lo
que salva la instalación en ordenadores con permisos limitados.

Después prueba **el comando real que va a usar el kit**, con un caso pequeño. Que el
programa esté instalado no significa que haga lo que crees.

### Una API con clave

Una llamada mínima con la clave del usuario, comprobando que responde 200 y que
devuelve lo esperado. Reglas:

- La clave **no** se pide por el chat: se guarda en `.env.local` (el wizard del kit
  guiará al usuario) y desde ahí se usa.
- Comprueba también qué devuelve cuando la clave es incorrecta, para poder escribir esa
  fila en la tabla de errores del kit.
- Apunta el coste en el contrato con **órdenes de magnitud** ("unos céntimos por
  informe"), nunca con precios exactos sellados: cambian.

### Escribir y abrir resultados

Comprueba lo que el kit necesitará hacer al final:

```bash
mkdir -p mis-kits/NN-kit-nombre/workspace   # crear carpetas
open ARCHIVO      # Mac: abrir el resultado en el navegador
start ARCHIVO     # Windows: lo mismo
```

Si el kit genera imágenes, vídeo o audio, comprueba el comando que los produce con un
caso de dos segundos antes de prometer nada.

---

## Las tres salidas posibles, y ninguna es "seguir igual"

1. **✓ Funciona.** Apunta en el contrato el comando exacto que lo demostró. Ese comando
   se convierte en la comprobación del wizard del kit.
2. **✗ No funciona, pero hay vía alternativa.** Pruébala. Y considera siempre la mejor
   de todas: **cambiar cómo entran los datos**. Lo que no se puede raspar, muchas veces
   el usuario lo tiene en dos capturas o en un archivo que baja de su panel — y encima
   con datos privados que valen más que lo público.
3. **✗ No funciona y no hay vía.** Se cambia el contrato: esa parte se cae del kit, se
   apunta en "qué queda fuera" y se le dice al usuario en el momento, sin adornos.

Lo que **nunca** se hace: construir el kit igual y dejar que el fallo aparezca en manos
del usuario o de su cliente.

---

## Cómo contarlo

Dos líneas, con ✓ y ✗, en cristiano:

> ✓ La web de tu gestoría se lee bien (devuelve el texto completo).
> ✗ Su zona de clientes pide contraseña: eso no lo va a poder leer el kit. Lo
> resolvemos con el PDF que te descargas tú, que además trae más datos.
>
> Siguiente paso: te enseño el contrato y, si lo apruebas, construyo.

Este paso es el que le da confianza en todo lo demás. No lo cuentes como un trámite:
es la parte del trabajo que impide que el kit falle delante de un cliente.
