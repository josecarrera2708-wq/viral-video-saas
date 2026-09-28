# entrada/ · aquí va el formulario relleno

Cuando el negocio te devuelva el cuestionario, **guarda el archivo aquí** y
escríbele a Claude:

```
audita este formulario
```

Claude lo lee de esta carpeta, te dice qué ha encontrado y qué falta, y genera el
informe en `workspace/`.

## Qué formatos valen

- Texto pegado en un `.txt` o `.md` — lo más cómodo. Vale copiar y pegar el email
  o la conversación de WhatsApp tal cual, con sus faltas y su desorden.
- Un `.pdf` (por ejemplo el formulario impreso y rellenado a mano, escaneado o
  fotografiado).
- Un `.docx`.
- Varios archivos a la vez, si te lo mandó por partes. Claude los junta.

No hace falta que ordenes ni limpies nada. De eso se encarga el kit.

## Si no tienes el formulario relleno

Hay dos caminos más, y los dos funcionan igual de bien:

| Situación | Qué le dices a Claude |
|---|---|
| Tienes las respuestas en un email o un chat y no quieres crear el archivo | Pega el texto en el chat y di "audita estas respuestas" |
| Lo estás hablando con el cliente por teléfono | "hazme la auditoría en modo entrevista" — Claude te va preguntando bloque a bloque y tú vas contestando lo que te diga |

## Qué no debe entrar aquí

Datos de los clientes de ese negocio (listados, fichas, historiales),
contraseñas, claves de acceso, facturas o exportaciones de bases de datos.

Si aparece algo así en un archivo de esta carpeta, Claude se para, te avisa y no
lo mete en el informe. La auditoría se hace con lo que el negocio cuenta de sus
procesos, no con los datos de sus clientes.

## Privacidad

Esta carpeta está en `.gitignore`: si algún día subes el kit a un repositorio, lo
que haya aquí **no se sube**. Los formularios de tus clientes se quedan en tu
ordenador.
