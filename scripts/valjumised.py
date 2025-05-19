import csv
import os

gtfsk = "../data/gtfs"
alg = "822" #zoo
peatus2 = "1769" #toompark
valjund_file = "../output/zoo_toompark_valjumised.csv"


cal = os.path.join(gtfsk, "calendar.txt")
trips = os.path.join(gtfsk, "trips.txt")
ajad = os.path.join(gtfsk, "stop_times.txt")
liinid = os.path.join(gtfsk, "routes.txt")

# teeb tund-minut-sekund vormi otse ainult sekunditeks - hiljem on lihtsam töödelda
def ajastring_sekunditeks(aja_str):
    if not aja_str:
        return None
    osad = aja_str.split(':')
    if len(osad) == 3:
        t, m, s = map(int, osad) #t - tund, m - minut, s - sekund
        return t * 3600 + m * 60 + s


esmaspaevad = set()
with open(cal, mode='r', encoding='utf-8-sig') as sisendfail:
    lugeja = csv.DictReader(sisendfail)
    for rida in lugeja:
        #see kontrollib, kas liin soidab esmaspaeval - 1 tahistab "jah"
        if rida.get('monday') == '1':
            esmaspaevad.add(rida.get('service_id'))

#siia laheb iga trip id ja liin ja teenus - siis saab csv-sse panna liini ka
soit_liin = {}
with open(trips, mode='r', encoding='utf-8-sig') as sisendfail:
    lugeja = csv.DictReader(sisendfail)
    for rida in lugeja:
        soit_liin[rida.get('trip_id')] = (rida.get('service_id'), rida.get('route_id'))

#see votab "lühinime" - lühinimi on nt 21B või 41
liin_luhinimega = {}
with open(liinid, mode='r', encoding='utf-8-sig') as sisendfail:
    lugeja = csv.DictReader(sisendfail)
    for rida in lugeja:
        liin_luhinimega[rida.get('route_id')] = rida.get('route_short_name')

#siia kogutakse algpeatus, sihtpeatus, ajad
soidu_peatuse_andmed = {}
with open(ajad, mode='r', encoding='utf-8-sig') as sisendfail:
    lugeja = csv.DictReader(sisendfail)
    for rida in lugeja:
        reisi_id = rida.get('trip_id')
        t_id_soit, _ = soit_liin.get(reisi_id, (None, None))

        # votame ainult esmaspaevad
        if t_id_soit not in esmaspaevad:
            continue
        if reisi_id not in soidu_peatuse_andmed:
            soidu_peatuse_andmed[reisi_id] = {}

        peatuse_id = rida.get('stop_id')
        peatuse_jarjekord = rida.get('stop_sequence')
        praegune_soidu_kirje = soidu_peatuse_andmed[reisi_id]

        if peatuse_jarjekord:
            try:
                jarjekord_taisalt = int(peatuse_jarjekord)
                if peatuse_id == alg:
                    praegune_soidu_kirje['algpeatuse_jarjekord'] = jarjekord_taisalt
                    praegune_soidu_kirje['algpeatuse_valjumisaeg'] = rida.get('departure_time')
                elif peatuse_id == peatus2:
                    praegune_soidu_kirje['sihtpeatuse_jarjekord'] = jarjekord_taisalt
                    praegune_soidu_kirje['sihtpeatuse_saabumisaeg'] = rida.get('arrival_time')
            except ValueError:
                pass


valjundandmed = []
for reisi_id, detailid in soidu_peatuse_andmed.items():
    algpeatuse_jarjekord = detailid.get('algpeatuse_jarjekord')
    sihtpeatuse_jarjekord = detailid.get('sihtpeatuse_jarjekord')

    # kontrollib et algpeatus on enne sihtpeatust
    if algpeatuse_jarjekord is not None and sihtpeatuse_jarjekord is not None and algpeatuse_jarjekord < sihtpeatuse_jarjekord:
        valjumisaeg_str = detailid.get('algpeatuse_valjumisaeg')
        saabumisaeg_str = detailid.get('sihtpeatuse_saabumisaeg')


        valjumise_sekundid = ajastring_sekunditeks(valjumisaeg_str)
        saabumise_sekundid = ajastring_sekunditeks(saabumisaeg_str)

        if valjumise_sekundid is not None and saabumise_sekundid is not None:
            # leiame soidu liini id ja lühinime
            _, liini_id = soit_liin.get(reisi_id, (None, None))
            luhinimi = liin_luhinimega.get(liini_id)
            if luhinimi is not None:
                 valjundandmed.append([luhinimi, valjumise_sekundid, saabumise_sekundid])

# sordib valijumisaja jargi (sekundites)
valjundandmed.sort(key=lambda x: x[1])


with open(valjund_file, mode='w', newline='', encoding='utf-8') as valjundfail:
    kirjutaja = csv.writer(valjundfail)
    kirjutaja.writerow(['liin', 'zoo_valjumine', 'toompark_saabumine'])
    for rea_andmed in valjundandmed:
        kirjutaja.writerow(rea_andmed)