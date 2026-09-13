#!/usr/bin/env python3
import json, re, time
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "history.json"
ARCHIVE = "https://www.superenalotto.it/archivio-estrazioni/{year}/{month}"
SITE = "https://www.superenalotto.it"

MONTHS_IT = {
  1:"gennaio",2:"febbraio",3:"marzo",4:"aprile",5:"maggio",6:"giugno",
  7:"luglio",8:"agosto",9:"settembre",10:"ottobre",11:"novembre",12:"dicembre"
}
MONTH_NUM = {v:k for k,v in MONTHS_IT.items()}
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; SE90LabHistoryUpdater/1.1; GitHub-Actions)"}
session=requests.Session()
session.headers.update(HEADERS)

def euro_value(text):
    t=(text or "").replace("\xa0"," ").strip()
    if not t or t=="-" or "€" not in t: return None
    m=re.search(r"([\d.]+(?:,\d+)?)",t)
    if not m:return None
    return float(m.group(1).replace(".","").replace(",", "."))

def month_iter(end_date, months_back=8):
    y,m=end_date.year,end_date.month
    out=[]
    for _ in range(months_back):
        out.append((y,m));m-=1
        if m==0:m=12;y-=1
    return out

def parse_month(year,month):
    url=ARCHIVE.format(year=year,month=MONTHS_IT[month])
    r=session.get(url,timeout=30);r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    draws=[]
    for tr in soup.find_all("tr"):
        cells=tr.find_all(["td","th"])
        if len(cells)<2:continue
        c0=cells[0].get_text(" ",strip=True)
        mm=re.search(r"Concorso\s+N?[º°]?\s*(\d+)\s+del\s+(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})",c0,re.I)
        if not mm:continue
        conc=int(mm.group(1));day=int(mm.group(2));mon=MONTH_NUM.get(mm.group(3).lower());yr=int(mm.group(4))
        if not mon:continue
        nums=[int(x) for x in re.findall(r"\b\d{1,2}\b",cells[1].get_text(" ",strip=True))]
        if len(nums)!=6 or len(set(nums))!=6 or not all(1<=x<=90 for x in nums):continue
        jolly=star=None
        if len(cells)>=3:
            z=re.search(r"\b(\d{1,2})\b",cells[2].get_text(" ",strip=True))
            if z:jolly=int(z.group(1))
        if len(cells)>=4:
            z=re.search(r"\b(\d{1,2})\b",cells[3].get_text(" ",strip=True))
            if z:star=int(z.group(1))
        a=tr.find("a",href=re.compile(r"/archivio-estrazioni/concorso-",re.I))
        detail=urljoin(SITE,a["href"]) if a and a.get("href") else None
        draws.append({"n":conc,"date":f"{yr:04d}-{mon:02d}-{day:02d}","nums":sorted(nums),"jolly":jolly,"star":star,"detail_url":detail})
    return draws

def parse_prizes(detail_url):
    if not detail_url:return None,None
    r=session.get(detail_url,timeout=30);r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    wanted={"Punti 6":"6","Punti 5+1":"5+1","Punti 5":"5","Punti 4":"4","Punti 3":"3","Punti 2":"2"}
    prizes={};winners={}
    for tr in soup.find_all("tr"):
        cells=tr.find_all(["td","th"])
        if len(cells)<3:continue
        cat=cells[0].get_text(" ",strip=True)
        if cat not in wanted:continue
        key=wanted[cat]
        win_text=cells[1].get_text(" ",strip=True).replace(".","")
        wm=re.search(r"\d+",win_text)
        winners[key]=int(wm.group(0)) if wm else 0
        prizes[key]=euro_value(cells[2].get_text(" ",strip=True))
    return (prizes,winners) if len(prizes)>=5 else (None,None)

def load_existing():
    try:
        data=json.loads(OUT.read_text(encoding="utf-8"))
        return { (int(d["n"]),d["date"]):d for d in data.get("draws",[]) }
    except Exception:
        return {}

def main():
    existing=load_existing()
    all_draws={}
    errors=[]
    for y,m in month_iter(date.today(),8):
        try:
            for d in parse_month(y,m):all_draws[(d["n"],d["date"])]=d
        except Exception as e:errors.append(f"archivio {y}-{m:02d}: {e}")

    if not all_draws:raise SystemExit("Nessuna estrazione valida recuperata.")

    rows=sorted(all_draws.values(),key=lambda x:(x["date"],x["n"]),reverse=True)
    latest=datetime.strptime(rows[0]["date"],"%Y-%m-%d").date()
    cutoff=latest-timedelta(days=183)
    rows=[d for d in rows if datetime.strptime(d["date"],"%Y-%m-%d").date()>=cutoff]
    if len(rows)<60:raise SystemExit(f"Archivio sospetto: solo {len(rows)} concorsi.")

    enriched=[]
    for i,d in enumerate(rows):
        old=existing.get((d["n"],d["date"]),{})
        # Reuse quotas already archived; otherwise fetch detail page.
        if old.get("prizes"):
            d["prizes"]=old.get("prizes")
            d["prize_winners"]=old.get("prize_winners")
            if not d.get("detail_url"):d["detail_url"]=old.get("detail_url")
        else:
            try:
                p,w=parse_prizes(d.get("detail_url"))
                d["prizes"]=p;d["prize_winners"]=w
                time.sleep(0.10)
            except Exception as e:
                d["prizes"]=None;d["prize_winners"]=None
                errors.append(f"quote concorso {d['n']}: {e}")
        enriched.append(d)

    payload={
      "updated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "source":"https://www.superenalotto.it/archivio-estrazioni",
      "window":"rolling_183_days_from_latest_official_draw",
      "latest":{"n":enriched[0]["n"],"date":enriched[0]["date"]},
      "count":len(enriched),
      "draws":enriched
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    npr=sum(1 for d in enriched if d.get("prizes"))
    print(f"Aggiornato: {len(enriched)} concorsi; quote premio disponibili per {npr}. Ultimo: {enriched[0]['n']} del {enriched[0]['date']}")
    if errors:print("Avvisi:",*errors,sep="\n- ")

if __name__=="__main__":
    main()
