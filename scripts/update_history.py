#!/usr/bin/env python3
import json, re, sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "history.json"
BASE = "https://www.superenalotto.it/archivio-estrazioni/{year}/{month}"

MONTHS_IT = {
  1:"gennaio",2:"febbraio",3:"marzo",4:"aprile",5:"maggio",6:"giugno",
  7:"luglio",8:"agosto",9:"settembre",10:"ottobre",11:"novembre",12:"dicembre"
}
MONTH_NUM = {v:k for k,v in MONTHS_IT.items()}

HEADERS = {
  "User-Agent":"Mozilla/5.0 (compatible; SE90LabHistoryUpdater/1.0; +GitHub-Actions)"
}

def month_iter(end_date, months_back=7):
    y,m=end_date.year,end_date.month
    out=[]
    for _ in range(months_back):
        out.append((y,m))
        m-=1
        if m==0: m=12;y-=1
    return out

def parse_month(year, month):
    url=BASE.format(year=year, month=MONTHS_IT[month])
    r=requests.get(url,headers=HEADERS,timeout=30)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    draws=[]
    for tr in soup.find_all("tr"):
        cells=tr.find_all(["td","th"])
        if len(cells)<2: continue
        c0=cells[0].get_text(" ",strip=True)
        mm=re.search(r"Concorso\s+N?[º°]?\s*(\d+)\s+del\s+(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})",c0,re.I)
        if not mm: continue
        conc=int(mm.group(1))
        day=int(mm.group(2)); mon_name=mm.group(3).lower(); yr=int(mm.group(4))
        mon=MONTH_NUM.get(mon_name)
        if not mon: continue
        comb_text=cells[1].get_text(" ",strip=True)
        nums=[int(x) for x in re.findall(r"\b\d{1,2}\b",comb_text)]
        if len(nums)!=6 or len(set(nums))!=6 or not all(1<=x<=90 for x in nums):
            continue  # "In programmazione" or malformed
        jolly=None; star=None
        if len(cells)>=3:
            jm=re.search(r"\b(\d{1,2})\b",cells[2].get_text(" ",strip=True))
            if jm: jolly=int(jm.group(1))
        if len(cells)>=4:
            sm=re.search(r"\b(\d{1,2})\b",cells[3].get_text(" ",strip=True))
            if sm: star=int(sm.group(1))
        draws.append({
            "n":conc,
            "date":f"{yr:04d}-{mon:02d}-{day:02d}",
            "nums":sorted(nums),
            "jolly":jolly,
            "star":star
        })
    return draws

def main():
    today=date.today()
    all_draws={}
    errors=[]
    for y,m in month_iter(today,8):
        try:
            for d in parse_month(y,m):
                all_draws[(d["n"],d["date"])]=d
        except Exception as e:
            errors.append(f"{y}-{m:02d}: {e}")

    if not all_draws:
        raise SystemExit("Nessuna estrazione valida recuperata. " + "; ".join(errors))

    rows=sorted(all_draws.values(), key=lambda x:(x["date"],x["n"]), reverse=True)
    latest=datetime.strptime(rows[0]["date"],"%Y-%m-%d").date()
    cutoff=latest-timedelta(days=183)
    rows=[d for d in rows if datetime.strptime(d["date"],"%Y-%m-%d").date()>=cutoff]

    # At least six months should normally contain many draws; fail safely on suspicious scrape.
    if len(rows)<60:
        raise SystemExit(f"Archivio sospetto: solo {len(rows)} concorsi nella finestra mobile.")

    payload={
      "updated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "source":"https://www.superenalotto.it/archivio-estrazioni",
      "window":"rolling_183_days_from_latest_official_draw",
      "latest":{"n":rows[0]["n"],"date":rows[0]["date"]},
      "count":len(rows),
      "draws":rows
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Aggiornato: {len(rows)} concorsi. Ultimo: {rows[0]['n']} del {rows[0]['date']}")
    if errors:
        print("Avvisi:", *errors, sep="\n- ")

if __name__=="__main__":
    main()
