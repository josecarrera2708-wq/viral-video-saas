import subprocess, json, sys
from concurrent.futures import ThreadPoolExecutor
Q=["cuántos días entrenar para ganar músculo","cuántos días a la semana entrenar","frecuencia de entrenamiento hipertrofia","cuántas series por músculo a la semana","entrenar 3 días o 6 días a la semana","rutina full body vs torso pierna","cuántas veces por semana entrenar cada músculo"]
ids={}
def s(q):
    o=subprocess.run(["yt-dlp","--flat-playlist","-J",f"ytsearch40:{q}"],capture_output=True,text=True,timeout=170).stdout
    try: return q,json.loads(o)["entries"]
    except Exception as e: return q,[]
with ThreadPoolExecutor(4) as ex:
    for q,es in ex.map(s,Q):
        print(q,len(es))
        for e in es:
            ids.setdefault(e["id"],{"q":[],"flat":e})["q"].append(q)
json.dump(ids,open("ids.json","w"),ensure_ascii=False)
print(len(ids),"vídeos únicos")
