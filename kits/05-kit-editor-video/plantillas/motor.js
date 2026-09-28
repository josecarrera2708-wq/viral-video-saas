/* Motor de animación de las plantillas.
 *
 * La regla de oro: aquí no hay animaciones de CSS ni relojes. Cada plantilla
 * expone una función que, dado un instante en segundos, coloca la pantalla
 * exactamente en ese estado. Así capturar.py puede pedir el fotograma 37 y
 * salir siempre igual, en cualquier ordenador y sin depender de la velocidad
 * del navegador. Con animaciones de CSS o requestAnimationFrame las capturas
 * salen descuadradas y el resultado cambia de un día para otro.
 *
 * Prohibido dentro de una plantilla: transition, animation, Date.now(),
 * Math.random(), setTimeout. Todo se calcula a partir de t.
 */

const Motor = (() => {
  const tope = (v, a, b) => Math.min(Math.max(v, a), b);

  /* Suavizados. Reciben 0..1 y devuelven 0..1 (el resorte se pasa un poco). */
  const suavizados = {
    lineal: u => u,
    suave: u => u * u * (3 - 2 * u),
    entra: u => u * u,
    frena: u => 1 - Math.pow(1 - u, 3),
    // Se pasa de largo y vuelve: da sensación de peso.
    rebote: u => {
      const s = 1.9;
      const v = u - 1;
      return 1 + (s + 1) * v * v * v + s * v * v;
    },
    // Oscila y se asienta, como un resorte.
    resorte: u => (u >= 1 ? 1 : 1 - Math.exp(-6.5 * u) * Math.cos(8.2 * u)),
  };

  /* Trozo de tiempo normalizado: 0 antes de empezar, 1 al acabar. */
  function tramo(t, inicio, duracion, suavizado) {
    const u = tope((t - inicio) / Math.max(duracion, 0.0001), 0, 1);
    return (suavizados[suavizado] || suavizados.suave)(u);
  }

  /* Entra, se queda y sale. Devuelve 0..1..0 */
  function presencia(t, inicio, entrada, visible, salida) {
    if (t < inicio) return 0;
    const fin = inicio + entrada + visible;
    if (t <= inicio + entrada) return tramo(t, inicio, entrada, "frena");
    if (t <= fin) return 1;
    return 1 - tramo(t, fin, Math.max(salida, 0.0001), "suave");
  }

  /* Retraso en cascada para listas: el elemento i entra un poco después. */
  const cascada = (i, paso) => i * paso;

  const numero = (u, desde, hasta) => desde + (hasta - desde) * u;

  /* Cuántas letras se han escrito ya. Se redondea hacia abajo para que la
     letra aparezca de golpe: a medias parpadea. */
  function escrito(texto, u) {
    return texto.slice(0, Math.floor(u * texto.length + 0.0001));
  }

  /* Coloca un elemento. Solo toca transform y opacity: son las dos cosas
     que el navegador dibuja sin recalcular la página, así la captura es
     rápida incluso con muchos elementos. */
  function poner(el, p) {
    if (!el) return;
    const partes = [];
    if (p.x || p.y) {
      partes.push(`translate3d(${p.x || 0}px, ${p.y || 0}px, 0)`);
    }
    if (p.escala !== undefined && p.escala !== 1) {
      partes.push(`scale(${p.escala})`);
    }
    if (p.giro) partes.push(`rotate(${p.giro}deg)`);
    el.style.transform = partes.length ? partes.join(" ") : "none";
    el.style.opacity = p.opacidad === undefined ? 1 : p.opacidad;
    if (p.difuminado !== undefined) {
      el.style.filter = p.difuminado > 0.05 ? `blur(${p.difuminado}px)` : "none";
    }
  }

  /* Entrada estándar del kit: sube, aparece y se asienta con un rebote. */
  function entrada(el, t, inicio, duracion, opciones) {
    const o = opciones || {};
    const u = tramo(t, inicio, duracion || 0.42, o.suavizado || "resorte");
    const uo = tramo(t, inicio, (duracion || 0.42) * 0.5, "frena");
    poner(el, {
      y: numero(u, o.desdeY === undefined ? 46 : o.desdeY, 0),
      x: numero(u, o.desdeX || 0, 0),
      escala: numero(u, o.desdeEscala === undefined ? 0.9 : o.desdeEscala, 1),
      opacidad: uo * (o.opacidadFinal === undefined ? 1 : o.opacidadFinal),
      difuminado: numero(1 - uo, 0, o.difuminado || 0),
    });
  }

  /* Lo que cada plantilla llama al final para darse de alta. */
  function registrar(definicion) {
    window.PLANTILLA = definicion;
    window.LIENZO = definicion.lienzo || { ancho: 1080, alto: 1920 };
    // capturar.py llama a estas tres desde fuera.
    window.cargar = datos => definicion.cargar(datos || {});
    window.duracion = () => definicion.duracion();
    window.fotograma = t => definicion.fotograma(t);
  }

  /* Atajos para escribir las plantillas sin repetir document.querySelector. */
  const uno = sel => document.querySelector(sel);
  const todos = sel => Array.from(document.querySelectorAll(sel));
  const crear = (etiqueta, clase, html) => {
    const el = document.createElement(etiqueta);
    if (clase) el.className = clase;
    if (html !== undefined) el.innerHTML = html;
    return el;
  };
  /* Texto del usuario: se escapa siempre, nunca se inyecta tal cual. */
  const texto = s => String(s === undefined || s === null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  /* Marca en negrita naranja lo que venga entre *asteriscos*. */
  const marcado = s => texto(s).replace(/\*([^*]+)\*/g,
    '<span class="resalte">$1</span>');

  return { tope, suavizados, tramo, presencia, cascada, numero, escrito,
           poner, entrada, registrar, uno, todos, crear, texto, marcado };
})();
