import json, urllib.request, datetime, os, re
API="https://resources.friscoisd.org/api/Calendar/Events"
FILTERS={"reedy":lambda e: e.get("isVarsity") and e.get("gender")=="Boys" and e.get("sport") in {"Basketball","Baseball","Soccer","Football"}}
SCHOOLS={"reedy":"Reedy HS Boys Varsity (Basketball, Baseball, Soccer, Football)","pioneer-heritage":"Pioneer Heritage MS Athletics"}
def fetch(slug):
    items,page=[],1
    to=(datetime.date.today()+datetime.timedelta(days=365)).isoformat()
    while True:
        u=f"{API}?school={slug}&pageSize=200&page={page}&toDate={to}"
        d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=60))
        items+=d["items"]
        if page>=d["totalPages"]: return items
        page+=1
def esc(s): return (s or "").replace("\\","\\\\").replace(";","\\;").replace(",","\\,").replace("\n","\\n")
def fold(line):
    out=[];b=line.encode()
    while len(b)>75:
        cut=75
        while (b[cut]&0xC0)==0x80: cut-=1
        out.append(b[:cut].decode()); b=b" "+b[cut:]
    out.append(b.decode()); return "\r\n".join(out)
def dt(s): return re.sub(r"[-:]","",s[:19])
def ics(name,items):
    now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    L=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//JLGG//FISD Athletics Feed//EN","CALSCALE:GREGORIAN","METHOD:PUBLISH",
       f"X-WR-CALNAME:{name}","X-WR-TIMEZONE:America/Chicago","REFRESH-INTERVAL;VALUE=DURATION:PT6H","X-PUBLISHED-TTL:PT6H","BEGIN:VTIMEZONE","TZID:America/Chicago","BEGIN:DAYLIGHT","TZOFFSETFROM:-0600","TZOFFSETTO:-0500","TZNAME:CDT","DTSTART:19700308T020000","RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU","END:DAYLIGHT","BEGIN:STANDARD","TZOFFSETFROM:-0500","TZOFFSETTO:-0600","TZNAME:CST","DTSTART:19701101T020000","RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU","END:STANDARD","END:VTIMEZONE"]
    for e in items:
        st=e.get("startDate");
        if not st: continue
        title=e.get("title","")
        if e.get("gameStatus") and e["gameStatus"]!="Scheduled": title=f"[{e['gameStatus']}] "+title
        L+=["BEGIN:VEVENT",f"UID:{e['id']}@fisd-athletics",f"DTSTAMP:{now}"]
        if e.get("startTimeTbd"):
            d=st[:10].replace("-","")
            nd=(datetime.date.fromisoformat(st[:10])+datetime.timedelta(days=1)).strftime("%Y%m%d")
            L+=[f"DTSTART;VALUE=DATE:{d}",f"DTEND;VALUE=DATE:{nd}"]; title+=" (time TBD)"
        else:
            L.append(f"DTSTART;TZID=America/Chicago:{dt(st)}")
            en=e.get("endDate")
            L.append(f"DTEND;TZID=America/Chicago:{dt(en)}" if en and not e.get("endTimeTbd") else "DURATION:PT1H30M")
        L.append("SUMMARY:"+esc(title))
        loc=", ".join(x for x in [e.get("facilityName"),e.get("fullAddress")] if x)
        if loc: L.append("LOCATION:"+esc(loc))
        desc=[f"{e.get('gender','')} {e.get('level','')} {e.get('sport','')}".strip(), e.get("homeAway") or "", e.get("gameType") or "",
              (f"Score: {e['teamScore']}-{e['opponentScore']}" if e.get("teamScore") else ""), e.get("specialNotes") or "",
              (f"Stream: {e['streamUrl']}" if e.get("streamUrl") else ""), (f"Map: {e['mapUrl']}" if e.get("mapUrl") else ""),
              "Source: https://www.friscoisd.org/page/high-school-varsity-athletics-schedule"]
        L.append("DESCRIPTION:"+esc("\n".join(x for x in desc if x)))
        L.append("END:VEVENT")
    L.append("END:VCALENDAR")
    return "\r\n".join(fold(x) for x in L)+"\r\n"
os.makedirs("docs",exist_ok=True)
for slug,name in SCHOOLS.items():
    items=fetch(slug)
    if slug in FILTERS: items=[e for e in items if FILTERS[slug](e)]
    open(f"docs/{slug}.ics","w",newline="").write(ics(name,items))
    print(slug,len(items))
