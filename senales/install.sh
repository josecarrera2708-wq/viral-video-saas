#!/usr/bin/env bash
# Instalador de «Señales» en un VPS Ubuntu 22.04/24.04 limpio. Se puede volver a ejecutar para actualizar:
# conserva los datos (wallets, historial, contraseña) que viven en /opt/senales/data.
#   curl -fsSL https://raw.githubusercontent.com/<usuario>/<repo>/refs/heads/<rama>/senales/install.sh | sudo bash
set -euo pipefail

REPO="${SENALES_REPO:-josecarrera2708-wq/viral-video-saas}"
BRANCH="${SENALES_BRANCH:-claude/nifty-dirac-lbhzl5}"
RAW="https://raw.githubusercontent.com/${REPO}/refs/heads/${BRANCH}/senales"
DIR=/opt/senales
FILES="app/__init__.py app/chain.py app/db.py app/server.py app/buscador.py requirements.txt
app/static/index.html app/static/app.js app/static/style.css app/static/sw.js app/static/manifest.webmanifest
app/static/icon-192.png app/static/icon-512.png app/static/apple-touch-icon.png"

[ "$(id -u)" = 0 ] || { echo "Ejecuta con sudo"; exit 1; }
echo "==> Paquetes del sistema"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip curl ca-certificates gnupg debian-keyring debian-archive-keyring apt-transport-https >/dev/null
if ! command -v caddy >/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq && apt-get install -y -qq caddy >/dev/null
fi

echo "==> Descargando la app"
id senales >/dev/null 2>&1 || useradd --system --home "$DIR" --shell /usr/sbin/nologin senales
mkdir -p "$DIR/app/static" "$DIR/data"
for f in $FILES; do curl -fsSL "$RAW/$f" -o "$DIR/$f"; done

echo "==> Entorno de Python"
[ -d "$DIR/venv" ] || python3 -m venv "$DIR/venv"
"$DIR/venv/bin/pip" install -q --upgrade pip setuptools wheel
"$DIR/venv/bin/pip" install -q -r "$DIR/requirements.txt"
chown -R senales:senales "$DIR"
chmod 700 "$DIR/data"

IP="$(curl -fsS4 https://api.ipify.org || curl -fsS4 https://ifconfig.me)"
HOST="${SENALES_HOST:-${IP//./-}.sslip.io}"

echo "==> Servicios"
cat > /etc/systemd/system/senales.service <<EOF
[Unit]
Description=Señales (vigilante de wallets + app)
After=network-online.target
[Service]
User=senales
WorkingDirectory=$DIR
Environment=SENALES_DATA=$DIR/data
Environment=SENALES_SETUP_CODE=${SENALES_SETUP_CODE:-}
ExecStart=$DIR/venv/bin/uvicorn app.server:app --host 127.0.0.1 --port 8080 --proxy-headers --forwarded-allow-ips 127.0.0.1
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/senales-buscador.service <<EOF
[Unit]
Description=Señales: buscador diario de wallets
[Service]
Type=oneshot
User=senales
WorkingDirectory=$DIR
Environment=SENALES_DATA=$DIR/data
ExecStart=$DIR/venv/bin/python -m app.buscador
TimeoutStartSec=6h
EOF
cat > /etc/systemd/system/senales-buscador.timer <<EOF
[Unit]
Description=Señales: lanza el buscador cada noche
[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true
[Install]
WantedBy=timers.target
EOF
cat > /etc/caddy/Caddyfile <<EOF
$HOST {
    encode gzip
    reverse_proxy 127.0.0.1:8080
}
EOF
if command -v ufw >/dev/null && ufw status | grep -q active; then ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null; fi
systemctl daemon-reload
systemctl enable --now senales.service senales-buscador.timer >/dev/null
systemctl restart senales.service caddy

sleep 4
CODE="$(cat "$DIR/data/codigo_inicial.txt" 2>/dev/null || true)"
echo
echo "================================================================"
echo " Listo. Abre en el móvil:  https://$HOST"
if [ -n "$CODE" ]; then
  echo " Código inicial:           $CODE"
  echo " (lo pide solo la primera vez, para elegir tu contraseña)"
else
  echo " Ya estaba configurada: entra con tu contraseña."
fi
echo " El certificado HTTPS puede tardar 1 minuto la primera vez."
echo "================================================================"
