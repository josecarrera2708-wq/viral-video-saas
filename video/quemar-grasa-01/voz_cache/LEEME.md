# Bloques de voz (Alejandro, sonic-3.5): completos, 95 de 95
Son los bloques de voz ya generados y pagados. Los bloques 023 y 078 son la toma elegida por `regen_bloques.py` (whisper).
**Válidos solo si `guiones/quemar-grasa-voz-01.md` no ha cambiado** (huella en GUION.sha1): `gen_voz.py` guarda los bloques por número, no por texto.
Para reconstruir `voz.mp3` sin gastar créditos (cambiar ATEMPO, pausas, etc.):
  mkdir -p /tmp/voz_qg && cp video/quemar-grasa-01/voz_cache/[0-9][0-9][0-9].mp3 /tmp/voz_qg/
  MODEL=sonic-3.5 VOICE_ID=3a35daa1-ba81-451c-9b21-59332e9db2f3 PAUSA=0.4 PAUSA_MAX=0.6 PAUSA_SECCION=0.6 ATEMPO=1.08 GUION=guiones/quemar-grasa-voz-01.md OUT_DIR=video/quemar-grasa-01 VOZ_TMP=/tmp/voz_qg python3 herramientas/gen_voz.py
Mezcla con música: python3 herramientas/mezcla_fondo.py video/quemar-grasa-01/voz.mp3 video/quemar-grasa-01/musica/motivation-to-wake-up.mp3 video/quemar-grasa-01/audio_final_musica.mp3
Si cambias una palabra del guion de voz, hay que regenerar desde ese bloque (los números de bloque se desplazan).
