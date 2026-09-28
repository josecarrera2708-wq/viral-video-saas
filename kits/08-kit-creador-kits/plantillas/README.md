# [[Kit NN]] · [[Nombre del kit]]

[[La promesa en dos o tres líneas: qué le das, qué hace y qué te llevas. Escrito para
alguien que no estuvo cuando se construyó el kit.]]

Entra [[X]] → sale [[Y]].

---

## Qué hace exactamente

[[El trabajo del kit, por partes. Si mira cosas, la lista de qué mira. Si transforma,
qué transforma y en qué. Concreto: el lector tiene que poder decidir si esto le sirve.]]

- [[…]]
- [[…]]
- [[…]]

## [[Cómo puntúa / Qué genera]]

[[Si el kit puntúa: la tabla de dimensiones y pesos, y las bandas de la nota. En
cristiano, para que el usuario entienda su nota sin leer nada más.]]

| Dimensión | Peso | Qué mide |
|---|---|---|
| [[…]] | [[..]] | [[…]] |
| | **100** | |

| Nota | Banda | Qué significa |
|---|---|---|
| 0-39 | Crítico | [[…]] |
| 40-54 | Flojo | [[…]] |
| 55-69 | Aceptable | [[…]] |
| 70-84 | Bueno | [[…]] |
| 85-100 | Excelente | [[…]] |

[[Y la regla de honestidad: lo que no se puede comprobar queda "sin datos", no puntúa y
su peso se reparte. Nada se estima.]]

## Cómo se usa

1. `/setup` — una vez, la primera. [[Qué hace.]]
2. [[La frase de la tarea real, en un bloque de código.]]
3. El resultado aparece en `workspace/[[nombre]]`.

| Comando | Para qué |
|---|---|
| `/setup` | Comprobar la instalación. Una sola vez |
| [[`/otro`]] | [[…]] |

Y las frases que conviene saber: [[«continúa …», «profundiza en …», «analiza el
ejemplo»]].

## Qué hay dentro

```
[[NN-kit-nombre]]/
├── EMPIEZA-AQUI.md      Arrancar en 5 minutos
├── README.md            Este archivo
├── CLAUDE.md            El cerebro: cómo se comporta Claude en este kit
├── ejemplos/            [[El caso de práctica ficticio]]
├── entrada/             [[Solo si el usuario deja archivos aquí]]
├── workspace/           Aquí aparecen los resultados
└── .claude/             Los comandos y la skill
```

## Qué NO hace

[[Decirlo claro ahorra decepciones. Entre 4 y 7 puntos, incluidos los que se cayeron en
el Paso 3 por no poder comprobarse.]]

- **[[…]]**
- **[[…]]**
- **No inventa datos.** Lo que no se puede comprobar se marca "sin datos" y se dice por
  qué.

## Seguridad

- [[Las reglas propias del kit: no se completan compras, no se entra en paneles, no se
  publica nada, los datos no salen del ordenador.]]
- Las claves de API nunca se pegan en el chat: van a `.env.local`, que no viaja en los
  ZIP.
- [[Si el kit maneja datos de clientes o personales, dilo aquí y di qué se hace con
  ellos.]]

## Windows

Todo funciona igual. Las diferencias las gestiona Claude por ti:
[[los comandos que cambian: `start` en vez de `open`, `winget` en vez de `brew`,
`Compress-Archive` en vez de `zip`]]. Necesitas Git para Windows instalado
(git-scm.com/download/win).

## Qué cuesta usarlo

[[Con órdenes de magnitud y sin sorpresas: si no cuesta nada aparte de la cuenta de
Claude Code, dilo — tranquiliza. Si hay una clave de API, di el servicio y el coste
aproximado por uso.]]

## Si algo falla

Escribe **"tengo un error"** y pega el mensaje tal cual: Claude tiene una tabla de
errores conocidos con la causa y la solución de cada uno. Si tras dos intentos sigue
atascado, pregunta en la comunidad donde conseguiste el kit pegando el error literal.
