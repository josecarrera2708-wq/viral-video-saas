# Evidencia 5 · Más capturas de "Equipos" del Trading Floor (aportadas por el dueño, 2026-09-29)

Fuente: 5 fotografías. **Marketing/afirmaciones del autor: no son resultados verificados.** Cuenta mostrada: patrimonio 100.046 $, hoy +46 $ (+0,05 %), caída 0,04 %, RISK-ON (cuenta de PAPEL).

## Mesa de opciones BTC (31,7 días)
Vol. implícita ATM 40,5 % vs vol. real 30d 35 % (prima −5,5 pts según la pantalla), sesgo 25Δ (puts−calls) 0,7 pts, put 10 % OTM cuesta 0,87 % (0,82 %/mes).
Mensaje: "las opciones están baratas: protegerse sale a buen precio". "Protección de cola: desactivada (no se puede validar con histórico; actívala en Ajustes si quieres pagarla)".

## Coberturas
Cobertura de beta 0,0000 BTC, posición +0 $, latente +0 $; "Resultado de la mesa (coberturas y opciones)"; "Estrategias revisadas".

## Equipo cuantitativo · Factores (atribución mercado · tendencia · carry)
Por trader-setup: α anualizado (t), β BTC, β tendencia, R²: Nico Setup_3646 α 60,98 % (t 2,67) β 0,027 R² 0,015; Andrei 28,36 % (2,26);
Óscar 40,93 % (2,22); Lara 42,98 % (2,21); Hana 93,78 % (2,15); Valeria 76,11 % (1,89). Todos con β≈0 y R² < 0,06.

## Mesa de arbitraje (Bybit ↔ Hyperliquid, funding)
Traders de la incubadora con posición: Ibrahim·XRP 9,42 % anual, Sara·LTC 11,58 % anual. "Revisión con dos años de funding (diferencial actual, anual)":
LINK 7 % (PF fuera de muestra 13,52, 7 periodos), NEAR 15,79 % (3,04/15), LTC 11,91 % (2,73/11), AVAX 11,93 % (2,5/14), XRP 9,75 % (2,13/15),
ADA 4,66 % (1,69/13), SOL 7,19 % (1,35/17), BNB 12,01 % (1,35/18), DOGE 13,9 % (1,3/16); sin ✔: ETH 8,23 % (1,32/14), TRX 6,81 % (1,07/26), BTC 6,35 % (0,93/7).
Nota: "En demo y real la pata de Hyperliquid no se puede ejecutar desde la sala: esta mesa opera en simulado."

## Tabla de derivados por activo (funding, OI, liquidaciones)
Columnas (funding anual, percentil, cambio de OI) y lectura textual: "funding muy negativo: cortos saturados; baja por liquidación de largos", "baja con cortos nuevos", "sube con dinero nuevo (el interés abierto crece)". Activos: LTC, NEAR, SOL, TRX, XAUT, XRP.

## Mensajes de chat visibles
"Yo sigo a lo mío.", "nada claro todavía.", "Ya te digo.", "estudiando «…»: El ATR tiene que estar por encima de su media…".

## Lectura crítica
- Alfas de 28–94 % con t≈2 y β≈0 entre muchos setups: compatible con selección por azar (comparaciones múltiples). BTC (el único activo de Millonary) sale con PF 0,93 en 7 periodos en su propia mesa de arbitraje: sin ventaja.
- Arbitraje de funding a 5–15 % anual es carry conocido; requiere dos plataformas y ejecución real; ellos mismos lo dejan en simulado.
- Replicable para BTC: mesa de opciones (IV vs RV, sesgo, coste de put), atribución de factores, tabla de funding/OI/liquidaciones (ya tenemos funding/OI en `src/data`).
