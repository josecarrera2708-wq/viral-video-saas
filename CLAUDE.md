# Habilidades disponibles en este repo

Skills, agente y comandos de Claude Code instalados en `.claude/`. Su código, plantillas y datos viven en `kits/<kit>/`;
las rutas relativas de cada skill se refieren a esa carpeta (cada skill lo indica al inicio).

| Skill | Cuándo usarla | Comandos |
|---|---|---|
| `cazador-de-webs` | Rediseñar la web de un negocio a partir de su URL (kit 01) | `/kit-cazador-webs-setup` |
| `auditoria-negocio` | Auditoría externa + interna de un negocio (kit 03) | `/auditoria` |
| `analisis-canal-youtube` | Analizar un canal de YouTube con yt-dlp (kit 04) | `/canal` |
| `editor-vertical` | Editar vídeo a vertical 1080x1920 con subtítulos (kit 05) | `/editar`, `/editor-doctor` |
| `analisis-marca-personal` | Auditar una marca personal (kit 06) | `/marca` |
| `analisis-ecommerce` | Auditar una tienda online (kit 07) | `/analiza` |
| `creador-de-kits` | Crear nuevos kits de Claude Code (kit 08) | `/nuevo-kit`, `/revisa-kit`, `/empaqueta` |

- Agente `kit-onboarding`: diagnóstico técnico del agente de WhatsApp (kit 02, `kits/02-kit-agente-whatsapp`).
- Agente `doctor-pc`: diagnostica y arregla problemas del PC (audio, auriculares, micro). Comando `/doctor-pc`. Hay que usarlo con Claude Code instalado en tu PC, no en la nube.
- Comandos del kit 02: `/kit-agente-whatsapp-setup`, `/whatsapp-personaliza`, `/whatsapp-deploy`.
- Cada kit tiene su `/kit-<nombre>-setup` para instalar dependencias.
- Los permisos amplios de cada kit (`curl`, `python`, `powershell`) NO se activaron globalmente: Claude pedirá confirmación.

# Guiones de vídeo (La Ciencia de la Salud)

- Agente `guionista-viral`: escribe y mejora guiones que retienen (gancho, bucles abiertos, ritmo por minuto).
- Agente `especialista-salud-fitness`: verifica con fuentes primarias cualquier afirmación de ejercicio, fisiología o alimentación y le pone nivel de certeza.
- Los guiones viven en `guiones/<tema>/` con `guion.md` y `fuentes.md`. Ningún guion se da por bueno sin su tabla de fuentes.
