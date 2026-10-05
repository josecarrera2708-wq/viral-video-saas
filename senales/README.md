# Señales

Vigilante de wallets de Solana en tiempo real con app web privada (se instala en el móvil como una app).

- **Avisos al instante** (1-5 s) cuando una wallet de tu lista compra o vende, con token, importe, hora, precio y MC. Usa los webhooks de Helius (el plan gratuito vale) y un sondeo de respaldo cada 90 s por si se pierde alguno.
- **Seguimiento de cada token comprado** durante 14 días: x hasta el máximo desde la compra, x actual y el resultado del método «vender el 50% en cada x2».
- **Ganancia de cada venta**: cuánto ganó o perdió la wallet frente a su precio medio de compra. Si la compra fue antes de empezar a vigilarla, la busca en el historial.
- **Listados**: cada 10 min mira qué tokens de Solana dan de alta MEXC, Gate, Bitget y KuCoin (por contrato). Si una wallet de tu lista lo compró, te avisa. Las compras de tokens jóvenes que aún no cotizan en ningún exchange llevan la marca «posible listado», y la app cuenta cuántas de esas acaban listándose.
- **Buscador diario**: cada noche revisa los nuevos listados de memecoins de Solana en Gate, Bitget, KuCoin, MEXC, OKX y BingX. Busca las wallets que compraron antes y las mide en otros tokens. Las que pasan el corte aparecen como candidatas.
- **Privada**: contraseña, HTTPS automático y avisos push en iPhone (iOS 16.4+, añadida a la pantalla de inicio) y Android.

Las wallets no van en el código: se introducen desde la app (Ajustes → Wallets) y se guardan solo en el servidor.

## Instalar

En un VPS con Ubuntu 22.04 o 24.04 (1 vCPU y 1 GB de RAM bastan), como root:

```bash
curl -fsSL https://raw.githubusercontent.com/josecarrera2708-wq/viral-video-saas/refs/heads/claude/nifty-dirac-lbhzl5/senales/install.sh | sudo bash
```

Al terminar, el instalador muestra la dirección (`https://<ip>.sslip.io`) y un código inicial. Ábrela en el móvil, escribe el código y elige tu contraseña.

Para actualizar, vuelve a ejecutar el mismo comando: los datos se conservan.

## Primeros pasos en la app

1. **Ajustes → Wallets**: una por línea, `Nombre | dirección | origen | cuentas que pagan (opcional)`.
2. **Ajustes → Tiempo real**: pega tu clave de Helius (gratis en dashboard.helius.dev) y pulsa «Guardar y conectar».
3. **Ajustes → Avisos**: en iPhone, primero Compartir → «Añadir a pantalla de inicio», abre la app desde el icono y pulsa «Activar avisos».

## Comandos útiles en el VPS

```bash
systemctl status senales            # estado del servidor
journalctl -u senales -f            # registro en vivo
systemctl start senales-buscador    # lanzar el buscador ahora (si no, va solo a las 02:30)
journalctl -u senales-buscador -f   # ver el buscador
```
