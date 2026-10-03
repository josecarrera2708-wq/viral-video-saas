import sys, pathlib, json, shutil, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from src.report.weekly import summarize, markdown, write_all
from src.report.panel import payload, build_panel, fragment
from src.lab import mejora
from test_desk import synth


def _account(tmp: pathlib.Path):
    idx = pd.date_range("2026-08-01", periods=120, freq="4h", tz="UTC")
    pd.DataFrame({"bar": idx, "equity": np.linspace(1000, 1040, 120), "units": 0.01, "price": 60000.0, "expo": 0.3, "signal": 0.5, "target": 0.3, "funding": 0.0, "flags": ""}).to_csv(tmp / "equity.csv", index=False)
    pd.DataFrame({"id": [1, 2], "bar": idx[[5, 60]], "side": ["BUY", "SELL"], "qty": 0.01, "price": 60000.0, "fee": [0.4, 0.4], "reason": "SEÑAL", "expo_before": 0, "expo_after": 0.2}).to_csv(tmp / "diario_ordenes.csv", index=False)
    pd.DataFrame({"posicion": [1], "abre": [idx[5]], "cierra": [idx[60]], "estado": ["CERRADA"], "resultado": ["GANA"], "pnl_usdt": [12.0]}).to_csv(tmp / "diario_posiciones.csv", index=False)
    pd.DataFrame({"lote": [1], "estado": ["CERRADO"], "resultado": ["GANA"]}).to_csv(tmp / "diario_lotes.csv", index=False)


def test_weekly_and_panel_on_empty_account():
    d = pathlib.Path(tempfile.mkdtemp())
    for f in ("equity", "diario_ordenes", "diario_posiciones", "diario_lotes"): (d / f"{f}.csv").write_text("")
    s = write_all(d, pd.Timestamp("2026-10-06", tz="UTC")); assert s["tiene_datos"] is False
    assert "aún no ha procesado velas" in (d / "semanal" / "informe_semanal.md").read_text()
    assert build_panel(d).exists()


def test_weekly_numbers_and_files():
    d = pathlib.Path(tempfile.mkdtemp()); _account(d); now = pd.Timestamp("2026-08-21", tz="UTC")
    s = write_all(d, now)
    assert abs(s["retorno_total"] - 0.04) < 1e-9 and s["posiciones"]["ganan"] == 1 and s["ordenes_total"] == 2
    assert 0 < s["retorno_semana"] < s["retorno_total"]
    md = (d / "semanal" / "informe_semanal.md").read_text(); assert "ganan 1 / pierden 0" in md and "Un mes no demuestra" in md
    import openpyxl
    wb = openpyxl.load_workbook(d / "semanal" / "diario.xlsx"); assert {"Resumen", "Equity", "Ordenes", "Lotes"} <= set(wb.sheetnames)
    assert (d / "semanal" / "operaciones.csv").exists()


def test_panel_embeds_valid_json_and_escapes():
    d = pathlib.Path(tempfile.mkdtemp()); _account(d)
    (d / "briefing.json").write_text(json.dumps({"ts": "2026-08-21 04:00:00+00:00", "estado": "OK", "decision": "Mantener </script> 0.3×", "veto": False, "organigrama": [],
                                               "departamentos": [{"dept": "Riesgos", "headline": "ok", "status": "OK", "notes": ["a"], "shadow": []}]}))
    html = fragment(d)
    assert html.count("</script>") == 1 and "<\\/script>" in html and "__DATA__" not in html   # el texto malicioso no cierra el script
    p = payload(d); assert p["equity"] and p["chat"][0]["de"] == "Dirección"


def test_mejora_operators_are_causal_and_ledger_stages():
    df = synth(1500); cut = 900; df2 = df.copy(); df2.iloc[cut + 1:, df2.columns.get_indexer(["open", "high", "low", "close"])] *= 1.5
    s = np.sign(np.sin(np.arange(len(df)) / 40.0))
    for name, fn in mejora.OPERADORES.items():
        a = np.asarray(fn(df, s), float); b = np.asarray(fn(df2, s), float)
        assert np.allclose(a[:cut + 1], b[:cut + 1], equal_nan=True), name
    # el stop nunca aumenta la exposición respecto a la señal base
    st = np.asarray(mejora.o4_stop_chandelier(df, s)); assert (np.abs(st) <= np.abs(s) + 1e-12).all()
    d = pathlib.Path(tempfile.mkdtemp()); led = d / "led.json"
    shutil.copy(mejora.LEDGER, led); f = pd.DataFrame({"time": df.index + pd.Timedelta("4h"), "funding_rate": 0.0001})
    out = mejora.update(df, f, df.index[1000], df.index[-1] + pd.Timedelta("4h"), ledger=led)
    assert all(v["forward"]["dias"] > 0 for k, v in out["candidatas"].items() if k in out["en_sombra"])
    assert not any(v["etapa"].startswith("E4") for v in out["candidatas"].values())         # < 90 días: nada se adopta
