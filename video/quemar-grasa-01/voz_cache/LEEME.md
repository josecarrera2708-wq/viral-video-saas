# Bloques de voz ya generados (Alejandro, sonic-3.5)
Cartesia cortó con 402 (créditos agotados) en el bloque 69 de 95. Estos son los bloques 000-068, ya pagados.
**Válidos solo si `guiones/quemar-grasa-voz-01.md` no ha cambiado** (huella en GUION.sha1): gen_voz.py guarda los bloques por número, no por texto.
Para terminar la voz cuando haya créditos:
  mkdir -p /tmp/voz_qg && cp video/quemar-grasa-01/voz_cache/[0-9][0-9][0-9].mp3 /tmp/voz_qg/
  MODEL=sonic-3.5 VOICE_ID=3a35daa1-ba81-451c-9b21-59332e9db2f3 PAUSA=0.4 PAUSA_MAX=0.6 PAUSA_SECCION=0.6 ATEMPO=1.08 GUION=guiones/quemar-grasa-voz-01.md OUT_DIR=video/quemar-grasa-01 VOZ_TMP=/tmp/voz_qg python3 herramientas/gen_voz.py
(solo pedirá los 26 bloques que faltan, 4.046 caracteres).
