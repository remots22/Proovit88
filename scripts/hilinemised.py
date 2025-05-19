# see script võtab reaalajas andmed peatuste kohta (liinidele, mis soidavad samade peatuste vahel)
# analüüsiks - kogutud andmete põhjal saab oletada, kui palju võib buss hilineda
import requests
import time
import csv
import os
import threading
import sys
import select

toored = "../data/raw"
töödeldud = "../data/processed"

urlid = {
    "https://transport.tallinn.ee/siri-stop-departures.php?stopid=822": {
        "kalapulk": os.path.join(toored, "koik822.csv"),
        "toodeldud_andmed": os.path.join(töödeldud, "822_norm.csv")
    },
    "https://transport.tallinn.ee/siri-stop-departures.php?stopid=1769": {
        "kalapulk": os.path.join(toored, "koik1769.csv"),
        "toodeldud_andmed": os.path.join(töödeldud, "1769_norm.csv")
    }
}
liinid = ["8", "21", "21B", "41", "41B"]
töötab = True
def kraabi(): # kysib endpointist bussipeatuste kohta andmed (Transport,RouteNum,ExpectedTimeInSeconds,ScheduleTimeInSeconds) ja kirjutab faili
    for url, failid in urlid.items():
        toor_väljundfail = failid["kalapulk"]
        try:
            vastus = requests.get(url); vastus.raise_for_status()
            read = vastus.text.strip().split("\n"); andmed_alanud = False; salvestatavad_toorread = []
            for rida in read:
                if not andmed_alanud and rida.startswith("stop,"): andmed_alanud = True; continue
                if not andmed_alanud: continue
                osad = rida.split(',')
                if len(osad) > 1 and osad[0].strip().lower() == "bus": salvestatavad_toorread.append(osad)
            if salvestatavad_toorread:
                with open(toor_väljundfail, 'a', newline='') as csvfail: csv.writer(csvfail).writerows(salvestatavad_toorread)
        except Exception: pass
def kratt(): # tõlgendab toored andmed ümber unikaalseteks väljumisteks (ScheduleTimeInSeconds abil)
    for url, failid in urlid.items():
        toorandmete_fail = failid["kalapulk"]; töödeldud_fail = failid["toodeldud_andmed"]; kõik_read = []
        try:
            with open(toorandmete_fail, 'r', newline='') as sisendfail:
                kõik_read = [r for r in csv.reader(sisendfail) if len(r) > 1 and r[0].strip().lower() == "bus" and r[1].strip() in liinid]
        except Exception: continue
        töödeldud_read_sorteerimiseks = []
        for rida in kõik_read:
            if len(rida) < 4: continue
            try:
                sk = int(rida[3]); elem = rida[2:4] + (rida[5:len(rida)-1] if len(rida) > 5 else [])
                töödeldud_read_sorteerimiseks.append({'sorteerimisvõti': sk, 'andmed': elem})
            except ValueError: continue
        töödeldud_read_sorteerimiseks.sort(key=lambda x: x['sorteerimisvõti'])
        filtreeritud_elemendid = []
        if töödeldud_read_sorteerimiseks:
            min_element_sorteerimisvõtme_grupi_kohta = {}
            for element in töödeldud_read_sorteerimiseks:
                svõti = element['sorteerimisvõti']; andmerida = element['andmed']
                if not andmerida or not andmerida[-1]: continue
                try: viimane_väärtus_arv = int(andmerida[-1])
                except ValueError: continue
                parim_hetkel = min_element_sorteerimisvõtme_grupi_kohta.get(svõti)
                if parim_hetkel is None or viimane_väärtus_arv < parim_hetkel['min_väärtus']: min_element_sorteerimisvõtme_grupi_kohta[svõti] = {'min_väärtus': viimane_väärtus_arv, 'elemendi_andmed': element}
            filtreeritud_elemendid = [kirje['elemendi_andmed'] for kirje in min_element_sorteerimisvõtme_grupi_kohta.values()]
            filtreeritud_elemendid.sort(key=lambda x: x['sorteerimisvõti'])
        try:
            with open(töödeldud_fail, 'w', newline='') as väljundfail: csv.writer(väljundfail).writerows(e['andmed'] for e in filtreeritud_elemendid)
        except Exception: pass
def ott(): # väljub vajutades q ja töötleb kui vajutada b
    global töötab
    while töötab:
        if select.select([sys.stdin], [], [], 0.1)[0]:
            klahv = sys.stdin.read(1)
            if klahv == 'b': kratt()
            elif klahv == 'q': töötab = False; break
        time.sleep(0.1)
if __name__ == "__main__":
    for failid in urlid.values():
        for faili_tee in failid.values():
            try:
                with open(faili_tee, 'a', newline=''): pass
            except Exception: pass
    sisendi_lõim = threading.Thread(target=ott); sisendi_lõim.daemon = True; sisendi_lõim.start()
    try:
        while töötab: kraabi(); time.sleep(15)
    except KeyboardInterrupt: töötab = False
    finally: töötab = False 