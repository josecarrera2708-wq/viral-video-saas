# Kits de Claude Code

Ocho kits independientes (agentes, skills y comandos para Claude Code). Cada uno es un proyecto autónomo:
abre Claude Code **dentro de la carpeta del kit** y ejecuta `/setup`.

| Kit | Qué hace |
|---|---|
| 01-kit-cazador-webs | Detecta webs mejorables y genera propuestas |
| 02-kit-agente-whatsapp | Agente de WhatsApp con IA (Next.js + Baileys) y subagente `kit-onboarding` |
| 03-kit-auditoria-negocio | Auditoría de negocio |
| 04-kit-analisis-youtube | Análisis de canales de YouTube |
| 05-kit-editor-video | Editor de vídeo vertical (ffmpeg, subtítulos, cortes) |
| 06-kit-marca-personal | Análisis de marca personal |
| 07-kit-analisis-ecommerce | Análisis de tiendas online |
| 08-kit-creador-kits | Creador de nuevos kits |

## Revisión de seguridad (integración)
- Sin ejecución remota ofuscada, exfiltración, lectura de credenciales ni instrucciones ocultas en prompts. Sin secretos reales.
- Descargas: `05/scripts/instalar_ffmpeg.py` (ffmpeg desde GitHub), `04` `/setup` (yt-dlp oficial).
- `05/scripts/transcribir.py` puede subir audio a AssemblyAI (opt-in).
- Cada `.claude/settings.json` de kit permite `curl`, `python` y `powershell`: solo aplican al abrir Claude Code dentro de ese kit. No se fusionaron con la configuración raíz.
