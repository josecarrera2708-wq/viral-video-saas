#!/bin/sh
# Comprueba desde ESTE servidor si los datos públicos de Binance/Bybit están accesibles.
for u in "https://fapi.binance.com/fapi/v1/ping" "https://api.binance.com/api/v3/ping" "https://api.bybit.com/v5/market/time"; do
  code=$(curl -s -o /dev/null -m 15 -w "%{http_code}" "$u")
  echo "$code  $u"
done
echo "200 = accesible. 451/403 = bloqueado por región (este VPS no sirve para el ejecutor)."
