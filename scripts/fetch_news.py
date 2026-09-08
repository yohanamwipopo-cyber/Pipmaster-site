#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PipMaster news auto-fetch: ForexFactory -> TradingView -> data/news.json (EAT, high+normal tu)."""
import json, urllib.request, datetime, pathlib

UA = {"User-Agent":"Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36"}
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "news.json"

def get(url, timeout=20):
    r = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.read()

def eat(ts_ms):
    return datetime.datetime.utcfromtimestamp(ts_ms/1000) + datetime.timedelta(hours=3)

def from_ff():
    j = json.loads(get("https://nfs.faireconomy.media/ff_calendar_thisweek.json"))
    items = []
    for x in j:
        imp = x.get("impact","")
        if imp not in ("High","Medium"): continue
        ts = 0
        try: ts = int(datetime.datetime.fromisoformat(x["date"].replace("Z","+00:00")).timestamp()*1000)
        except Exception: pass
        e = eat(ts) if ts else None
        items.append({"cur":x.get("country",""), "impact":"high" if imp=="High" else "normal",
            "time":e.strftime("%H:%M") if e else "", "date":e.strftime("%a %d %b") if e else "",
            "title":x.get("title",""), "fc":str(x.get("forecast") or "—"), "prev":str(x.get("previous") or "—"), "ts":ts})
    return items, "ForexFactory"

def from_tv():
    now = datetime.datetime.utcnow()
    frm = (now - datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    to  = (now + datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    j = json.loads(get("https://economic-calendar.tradingview.com/events?from=%s&to=%s&importances=1,2" % (frm,to)))
    CN = {"US":"USD","EU":"EUR","GB":"GBP","JP":"JPY","CH":"CHF","AU":"AUD","CA":"CAD","NZ":"NZD","CN":"CNY"}
    items = []
    for e in j.get("result",[]):
        ts = 0
        try: ts = int(datetime.datetime.fromisoformat(e["date"].replace("Z","+00:00")).timestamp()*1000)
        except Exception: pass
        d = eat(ts) if ts else None
        items.append({"cur":CN.get(e.get("country",""), e.get("currency") or e.get("country","")),
            "impact":"high" if e.get("importance")==2 else "normal",
            "time":d.strftime("%H:%M") if d else "", "date":d.strftime("%a %d %b") if d else "",
            "title":e.get("title",""),
            "fc":str(e.get("forecastRaw") if e.get("forecastRaw") is not None else (e.get("forecast") or "—")),
            "prev":str(e.get("previousRaw") if e.get("previousRaw") is not None else (e.get("previous") or "—")), "ts":ts})
    return items, "TradingView"

items, src = [], "none"
try:
    items, src = from_ff()
    print("FF:", len(items))
except Exception as ex:
    print("FF fail:", ex)
if not items:
    try:
        items, src = from_tv()
        print("TV:", len(items))
    except Exception as ex:
        print("TV fail:", ex)

items.sort(key=lambda x: x.get("ts") or 9e15)
now = datetime.datetime.utcnow()
# acha zilizopita zaidi ya saa 6 + zote zijazo, hadi 48
fresh = [x for x in items if x.get("ts",0) > int((now - datetime.timedelta(hours=6)).timestamp()*1000)][:48]
out = {"updated": now.strftime("%Y-%m-%d %H:%M UTC"), "source": src, "items": fresh}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("news.json:", src, len(fresh), "items")
