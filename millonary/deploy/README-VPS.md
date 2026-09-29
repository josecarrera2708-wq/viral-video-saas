# Millonary · Paper trading en tu VPS (guía paso a paso)

**Es paper trading: NO usa claves de API ni envía órdenes reales.** Solo lee precios públicos y simula
una cuenta de 1.000 USDT. Puedes pararlo o borrarlo cuando quieras sin ningún riesgo económico.

## 0. Requisitos
- Un VPS Linux (Ubuntu/Debian), 1 GB de RAM, acceso por SSH (o consola del panel).
- **Que el VPS esté en una región desde la que Binance o Bybit respondan.** Compruébalo primero.

## 1. Comprobar la región (30 segundos)
```
curl -s -o /dev/null -w "%{http_code}\n" https://fapi.binance.com/fapi/v1/ping
curl -s -o /dev/null -w "%{http_code}\n" https://api.bybit.com/v5/market/time
```
Con `200` en al menos uno, sirve (el ejecutor usa uno como principal y el otro como respaldo; si los
dos responden, además compara los precios). Con `451`/`403` en ambos, no sirve: prueba otra región.

## 2. Instalar Docker (si no lo tienes)
```
curl -fsSL https://get.docker.com | sh
```
(En Hostinger con EasyPanel, Docker ya viene instalado.)

## 3. Descargar el proyecto y arrancar
```
git clone -b claude/optimistic-bohr-fjhr18 https://github.com/josecarrera2708-wq/viral-video-saas.git
cd viral-video-saas/millonary/deploy
docker compose up -d --build
```
(El repositorio es privado: usa tu usuario de GitHub y un token personal con permiso de solo lectura,
o `git clone` con SSH.)

## 4. Ver que funciona
```
docker logs -f millonary-paper                 # registro en vivo
docker exec millonary-paper python -m src.live.runner --status
```
Al arrancar evalúa enseguida (y recupera las velas que se hubiera perdido) y luego **en cada cierre de vela de 4h** (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC),
unos 45 segundos después. La primera evaluación llega en el próximo cierre. Es normal ver "ya
procesada" o esperas largas entre velas.

## 5. Qué esperar
- La exposición objetivo de este sistema es baja (media ≈ 0,25× del capital) y opera pocas veces
  (≈ 8 veces el capital al año). **Semanas sin operaciones son normales.**
- Con 1.000 USDT y BTC alto, el lote mínimo (0,001 BTC) es una parte grande del objetivo; las órdenes
  demasiado pequeñas se omiten y quedan anotadas (`OMITIDA_MIN_ORDEN`).
- Necesitamos **8–12 semanas** para comparar con el backtest antes de plantear nada más.

## 6. Freno de emergencia
```
docker exec millonary-paper touch /data/KILL       # en el siguiente cierre aplana todo y se para
# Para reanudar (solo cuando tú lo decidas):
docker exec millonary-paper rm /data/KILL
docker exec millonary-paper python -m src.live.runner --reset-halt
```
Se para solo, y avisa, si la caída desde máximos llega al 30 % o si el día pierde un 7 % (reinicio manual con
`--reset-halt`). Si los datos no son fiables, mantiene la posición y no opera; si además está parado o hay
KILL, aplana igualmente con el último precio.

## 7. Copia de seguridad y exportación de resultados
```
docker cp millonary-paper:/data/state.db ./state-$(date +%F).db     # la base con todas las operaciones
docker cp millonary-paper:/data/ ./datos-millonary/                   # incluye los CSV legibles
```
Pásame ese archivo y comparo los resultados con el backtest.

## 8. Avisos por Telegram (opcional)
Crea un bot con @BotFather, copia el token y tu `chat_id`, ponlos en un archivo `.env` junto a
`docker-compose.yml`:
```
TELEGRAM_TOKEN=123456:ABC...
TELEGRAM_CHAT=123456789
```
y `docker compose up -d`. No compartas ese token con nadie.

## 9. Parar y borrar todo
```
docker compose down
```
