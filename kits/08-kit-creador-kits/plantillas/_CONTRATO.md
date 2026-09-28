# Contrato de construcción · [[Nombre del kit]]

> Documento de trabajo. Es la memoria de la construcción: se actualiza **a cada paso**,
> no al final. Si la sesión se corta, esto es lo que permite retomar sin repetir nada.
> **No viaja en el ZIP** que se entrega a un cliente.

- **Carpeta**: `mis-kits/[[NN-kit-nombre]]/`
- **Skill principal**: `[[nombre-de-la-skill]]`
- **Construido para**: [[uso propio / vender el servicio / entregar a un cliente]]
- **Marca blanca**: [[sí / no]]
- **Fecha de inicio**: [[AAAA-MM-DD]]

---

## 1 · La promesa

**Entra** [[qué le da el usuario al kit]] → **sale** [[qué recibe, con el nombre del
archivo de salida]].

En una frase de espectador: [[la misma promesa, como se la contarías a un cliente]]

---

## 2 · Los cuatro ejes

| Eje | Decisión |
|---|---|
| Qué entra | [[web pública / archivos en entrada/ / capturas / herramienta externa / API con clave / solo conversación]] |
| Qué sale | [[informe HTML puntuado / archivos generados / algo funcionando / datos estructurados]] |
| Qué hay que instalar | [[nada / un binario: cuál / node + dependencias / una clave de API: de qué servicio]] |
| Para quién es | [[él / vender el servicio / entregar el kit]] |

---

## 3 · El árbol del kit y los archivos de salida

El árbol exacto que se va a crear, con los nombres definitivos. Se escribe **antes** de
construir: si un nombre cambia después, se cambia aquí primero.

```
[[NN-kit-nombre]]/
├── EMPIEZA-AQUI.md
├── README.md
├── CLAUDE.md
├── .gitignore
├── _CONTRATO.md                          (no viaja en el ZIP)
├── .claude/
│   ├── settings.json
│   ├── commands/setup.md
│   └── skills/[[nombre-de-la-skill]]/SKILL.md
├── ejemplos/[[carpeta-del-ejemplo]]/
├── entrada/            (LEEME.md + .gitkeep)
└── workspace/          (.gitkeep)
```

Archivos de salida:

| Archivo | Cuándo se crea | Qué contiene |
|---|---|---|
| `workspace/[[nombre-con-fecha]]` | [[al terminar el análisis]] | [[qué lleva dentro]] |
| [[otro, si hay]] | | |

Y **cuántos son entregables**: [[los que el usuario recibe]]. Si hay archivos de trabajo
que se escriben en `workspace/` sin ser entregables (un cuaderno incremental, un caché),
dilo aquí y dilo también en la skill — si no, el `description` promete una cifra y el
cuerpo dice otra.

---

## 4 · El criterio de calidad

[[Si el kit puntúa: la tabla de dimensiones con sus pesos sumando 100, los anclajes
(qué es un 20, un 50, un 80) y las bandas de la nota global.]]

[[Si el kit genera o ejecuta: la lista comprobable de qué es un resultado bueno, y qué
mira el kit al terminar para saber que lo está.]]

| Dimensión | Peso | Anclaje 20 | Anclaje 50 | Anclaje 80 |
|---|---|---|---|---|
| [[...]] | [[..]] | [[...]] | [[...]] | [[...]] |
| | **100** | | | |

---

## 5 · Reglas duras de este kit

Lo que este kit **nunca** hace, escrito antes de construirlo:

- [[p. ej.: nunca completa una compra ni crea cuentas]]
- [[p. ej.: no entra en ningún panel privado; solo información pública]]
- No inventa datos: lo que no se puede comprobar se marca **"sin datos"**.
- Los resultados van siempre a `workspace/`.
- Ni claves ni contraseñas por el chat.

---

## 6 · Qué queda fuera

Lo que el usuario mencionó y **no** va a estar en este kit (esta lista evita el 90 % de
las decepciones):

- [[...]]
- [[...]]

---

## 7 · Comprobado el [[AAAA-MM-DD]] (no supuesto)

Paso 3. Cada vía de datos y cada dependencia, probada de verdad con el caso real del
usuario:

| Qué | Cómo se comprobó | Resultado |
|---|---|---|
| [[leer la web X]] | [[WebFetch sobre https://…]] | [[✓ devuelve el contenido / ✗ devuelve login]] |
| [[abrir su PDF]] | [[Read sobre ejemplos/…]] | [[✓ / ✗]] |
| [[el programa X]] | [[which X && X --version]] | [[✓ versión … / ✗ no está, instalado con …]] |

**Consecuencias en el contrato**: [[qué se cambió de la promesa por lo que salió ✗, o
"ninguna: todo funcionó"]]

---

## 8 · El ejemplo de práctica

- **Carpeta**: `ejemplos/[[nombre]]/`
- **Qué es**: [[el caso ficticio, en una línea]]
- **Errores plantados ([[N]])**:
  1. [[...]]
  2. [[...]]
  3. [[...]]
- **Huecos a propósito**:
  - El que debe acabar como "sin datos": [[cuál]]
  - El que debe provocar que el kit pregunte: [[cuál]]
- **Resultado calibrado**: [[la nota o el resultado que da el ejemplo, apuntado tras el
  Paso 7 — sirve para saber si una copia del kit funciona bien]]

---

## 9 · Defectos encontrados al ejecutar el kit (Paso 7)

| Defecto | Cómo se arregló |
|---|---|
| [[...]] | [[...]] |

Errores plantados que encontró: [[N]] de [[N]].

---

## 10 · Estado

- [ ] Paso 1 · Entrevista y promesa confirmada
- [ ] Paso 2 · Contrato aprobado por el usuario
- [ ] Paso 3 · Vías de datos comprobadas
- [ ] Paso 4 · Criterio de calidad definido
- [ ] Paso 5 · Kit construido
- [ ] Paso 6 · Ejemplo de práctica con errores plantados
- [ ] Paso 7 · Kit ejecutado contra su ejemplo y defectos corregidos
- [ ] Paso 8 · Lista de calidad pasada y estado de primer arranque limpio
- [ ] Paso 9 · Entregado

**Fecha de finalización**: [[AAAA-MM-DD]]
