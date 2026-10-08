#!/usr/bin/env python3
"""Convierte un guion con líneas '>' (lo que se dice) al formato que lee gen_voz.py.

Uso: python3 herramientas/guion_a_voz.py <guion.md> <salida_voz.md>

- Cada '## [mm:ss] TÍTULO' pasa a '## N. TÍTULO'; cada párrafo hablado es un bloque.
- Quita las indicaciones *[...]*, los ids *(F1)* y los [PAUSA Ns] (gen_voz.py ya pone sus pausas).
- Normas del canal: números en palabras, nada en mayúsculas (las mayúsculas se deletrean): EPOC -> epoc.
- Los párrafos largos se parten por frases en bloques de ≈400 caracteres (más fáciles de revisar con whisper).
"""
import re, sys

_U = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce",
      "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno",
      "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
_D = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_C = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos",
      7: "setecientos", 8: "ochocientos", 9: "novecientos"}
FEMENINAS = {"series", "serie", "repeticiones", "repetición", "semanas", "semana", "comidas", "horas", "personas",
             "veces", "kilocalorías", "calorías", "sentadillas", "flexiones", "vez", "comparaciones", "abdominales",
             "piernas", "palabras", "cosas"}
MASCULINAS = {"kilo", "gramo", "minuto", "día", "segundo", "mes", "estudio", "año", "ensayo", "adulto", "hombre", "grado"}


def menos_1000(n):
    if n == 100:
        return "cien"
    c, r = divmod(n, 100)
    out = [_C[c]] if c else []
    if r:
        if r < 30:
            out.append(_U[r])
        else:
            d, u = divmod(r, 10)
            out.append(_D[d] + (" y " + _U[u] if u else ""))
    return " ".join(out)


def apocope(s, g):
    s = re.sub(r"veintiuno$", "veintiún" if g != "f" else "veintiuna", s)
    s = re.sub(r"\buno$", "un" if g != "f" else "una", s)
    return s.replace("cientos", "cientas") if g == "f" else s


def palabras(n, g="n"):
    if n == 0:
        return "cero"
    mil, resto = divmod(n, 1000)
    p = []
    if mil:
        p.append("mil" if mil == 1 else apocope(menos_1000(mil), "f" if g == "f" else "m") + " mil")
    if resto:
        w = menos_1000(resto)
        p.append(apocope(w, g) if g in ("m", "f") else w)
    return " ".join(p)


def genero(sig):
    if not sig:
        return "n"
    p = sig.lower()
    if p in FEMENINAS or p.endswith(("ción", "ciones")):
        return "f"
    if p in {"o", "y", "a", "de", "por", "del", "en", "al", "con", "para", "que"}:
        return "n"
    return "m" if p.endswith("s") or p in MASCULINAS else "n"


NUM = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?(\s*%)?")


def numeros(t):
    def sub(m):
        ent, dec, pct = int(m.group(1).replace(".", "")), m.group(2), m.group(3)
        resto = t[m.end():]
        s = re.match(r"\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)", resto)
        sig = s.group(1) if s else None
        if sig and sig.lower() in {"o", "y", "a"}:
            m2 = re.match(r"\s+(?:o|y|a)\s+\d[\d.,]*\s*%?\s*([A-Za-zÁÉÍÓÚáéíóúñÑ]+)", resto)
            sig = m2.group(1) if m2 else sig
        if dec is not None:
            d = palabras(int(dec)) if len(dec) == 1 else " ".join(palabras(int(c)) for c in dec)
            out = palabras(ent) + " coma " + d
        else:
            out = palabras(ent, "n" if pct else genero(sig))
        return out + (" por ciento" if pct else "")
    return NUM.sub(sub, t)


def limpiar(t):
    t = re.sub(r"\*\([^)]*\)\*", "", t)
    t = re.sub(r"\*\[[^\]]*\]\*", "", t)
    t = re.sub(r"\[PAUSA \d+s\]", "", t)
    t = t.replace("**", "").replace("*", "")
    t = re.sub(r"\bEPOC\b", "epoc", t)
    t = numeros(t)
    return re.sub(r"\s+", " ", t).strip()


def partir(texto, maximo=400):
    frases, trozos, act = re.split(r"(?<=[.!?…:])\s+", texto), [], ""
    for f in frases:
        if act and len(act) + 1 + len(f) > maximo:
            trozos.append(act)
            act = f
        else:
            act = (act + " " + f).strip()
    if act:
        trozos.append(act)
    return trozos


def main(src, dst):
    secciones, cur, para = [], None, []

    def cerrar():
        nonlocal para
        if para and cur is not None:
            t = limpiar(" ".join(para))
            if t and re.search(r"\w", t):
                cur[1].extend(partir(t))
        para = []
    for linea in open(src, encoding="utf-8").read().splitlines():
        if linea.startswith("## Notas de producción"):
            break
        if linea.startswith("## ["):
            cerrar()
            titulo = re.sub(r"^## \[[^\]]*\]\s*", "", linea).strip()
            cur = [titulo, []]
            secciones.append(cur)
        elif linea.startswith(">"):
            t = linea[1:].strip()
            if t:
                para.append(t)
            else:
                cerrar()
        else:
            cerrar()
    cerrar()
    out = [f"# Voz: {src}", "", "Generado por herramientas/guion_a_voz.py a partir del guion (números en palabras, sin mayúsculas sueltas).", ""]
    total_pal = 0
    for i, (titulo, bloques) in enumerate(secciones, 1):
        if not bloques:
            continue
        out += [f"## {i}. {titulo}", ""]
        for b in bloques:
            out += [b, ""]
            total_pal += len(b.split())
        out += ["---", ""]
    open(dst, "w", encoding="utf-8").write("\n".join(out))
    mayus = sorted({w for s in secciones for b in s[1] for w in re.findall(r"\b[A-ZÁÉÍÓÚ]{2,}\b", b)})
    print(f"{sum(len(s[1]) > 0 for s in secciones)} secciones, {sum(len(s[1]) for s in secciones)} bloques, {total_pal} palabras")
    if mayus:
        print("AVISO, palabras en mayúsculas (se deletrearían):", mayus)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
