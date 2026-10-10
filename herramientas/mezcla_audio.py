"""Mezcla voz + música (volumen por tramos) + efectos en puntos clave. Uso: python3 mezcla_audio.py <carpeta_video> <musica.mp3> <salida.mp3>"""
import json, subprocess, sys, os
D, MUS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SFX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "video/efectos")
t = json.load(open(f"{D}/tiempos.json"))
ini = {}
for b in t: ini.setdefault(b["seccion"], b["inicio"])
total = t[-1]["fin"]
# (efecto, volumen, secciones)  volúmenes = mitad de la primera demo
plan = [("whoosh", 0.35, [2,5,9,13,17,20,23]), ("disco", 0.5, [3,19]), ("latido", 0.4, [8]),
        ("pop", 0.3, [7,16,22]), ("exito", 0.3, [15,24])]
ent = ["-i", f"{D}/voz.mp3", "-stream_loop", "-1", "-i", MUS]
filt = [f"[1:a]atrim=0:{total+1},asetpts=PTS-STARTPTS,"
        f"volume='0.13+0.09*clip((100-t)/10,0,1)+0.07*clip((t-{total-110})/10,0,1)':eval=frame,"
        f"afade=t=out:st={total-5}:d=5[m]"]
etiq = ["[0:a]", "[m]"]; n = 2
for fx, vol, secs in plan:
    for s in secs:
        if s not in ini: continue
        ms = int(ini[s] * 1000)
        ent += ["-i", f"{SFX}/{fx}.mp3"]
        filt.append(f"[{n}:a]volume={vol},adelay={ms}|{ms}[e{n}]"); etiq.append(f"[e{n}]"); n += 1
filt.append("".join(etiq) + f"amix=inputs={n}:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5,aformat=channel_layouts=mono[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y"] + ent + ["-filter_complex", ";".join(filt), "-map", "[a]", "-t", str(total), "-b:a", "64k", OUT], check=True)
print("ok", round(total / 60, 2), "min,", n - 2, "efectos")
