import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os
from scipy import stats
from sklearn.isotonic import IsotonicRegression

def sek_kellaaeg(sekundid):
    if pd.isna(sekundid):
        return None
    tunnid = int((sekundid // 3600) % 24)
    minutid = int((sekundid % 3600) // 60)
    return f"{tunnid:02d}:{minutid:02d}"

def lae_ja_töötle_andmed(csv_faili_tee):
    # csv (822_norm.csv ja 1769_norm.csv) esimeses veerus on tegelik aeg (oodatav, kuid uuendatakse - seetõttu võtsin ka aegasid iga 15 sekundi kohta)
    # csv teises veerus on plaanijärgne aeg
    andmestik = pd.read_csv(csv_faili_tee, header=None, usecols=[0, 1], names=['tegelik_aeg_s', 'plaanijärgne_aeg_s'])
    andmestik = andmestik.dropna().astype(int)

    # hilinemine = plaanijärgne - tegelik aeg -> kui on miinuses, jõudis varem
    andmestik['hilinemine_s'] = andmestik['tegelik_aeg_s'] - andmestik['plaanijärgne_aeg_s']
        
    andmestik = andmestik.sort_values(by='plaanijärgne_aeg_s').reset_index(drop=True) # enne kui kellaajad külje panen, sorteerin sekundite järgi väiksemast suuremaks
    andmestik['plaanijärgne_kellaaeg_str'] = andmestik['plaanijärgne_aeg_s'].apply(sek_kellaaeg)

    # värvib graafikul hilinevad bussid punaseks, vastasel juhul roheline
    andmestik['värv'] = np.where(andmestik['hilinemine_s'] > 0, 'red', 'green')
    return andmestik


def statistika_hilinemised(andmestik, faili_alusnimi):

    # tulpdiagramm
    diagrammi_pealkiri = f"Liini 8 hilinemised ({faili_alusnimi})"
    diagramm = alt.Chart(andmestik, title=diagrammi_pealkiri).mark_bar().encode(
        x=alt.X('plaanijärgne_kellaaeg_str:N', 
                  title='Plaanijärgne Aeg (HH:MM)', 
                  sort=alt.EncodingSortField(field="plaanijärgne_aeg_s", op="min", order='ascending')
                 ),
        y=alt.Y('hilinemine_s:Q', title='Hilinemine (sekundites)'),
        color=alt.Color('värv:N', scale=None, legend=None),
        tooltip=[
            alt.Tooltip('plaanijärgne_kellaaeg_str:N', title='Planeeritud (HH:MM)'),
            alt.Tooltip('tegelik_aeg_s:Q', title='tegelik (s)'),
            alt.Tooltip('hilinemine_s:Q', title='hilinemine (s)')
        ]
    )
    st.altair_chart(diagramm, use_container_width=True)

    # statistika hilinemiste kohta
    st.markdown("---")
    hilinenud_bussid_andmestik = andmestik[andmestik['hilinemine_s'] > 0]
    busse_kokku = len(andmestik)
    
    veerud1, veerud2, veerud3 = st.columns(3)
    if busse_kokku > 0:
        hilinenute_protsent = (len(hilinenud_bussid_andmestik) / busse_kokku) * 100
        keskmine_hilinemine = andmestik['hilinemine_s'].mean()
        mediaan_hilinemine = andmestik['hilinemine_s'].median()
        with veerud1:
            st.metric(label="Hilinemiste %", value=f"{hilinenute_protsent:.2f}%")
        with veerud2:
            st.metric(label="Keskmine hilinemine", value=f"{keskmine_hilinemine:.2f} s")
        with veerud3:
            st.metric(label="Mediaan", value=f"{mediaan_hilinemine:.2f} s")
    else:
        st.write("vale fail jalle")

    # Ajavahemiku statistika
    st.markdown("#### Hilinemised ajavahemikus 07:54 kuni 08:59")
    ajavahemik_alumine = 29277
    ajavahemik_ülemine = 33147
    ajavahemiku_andmestik = andmestik[(andmestik['plaanijärgne_aeg_s'] >= ajavahemik_alumine) & (andmestik['plaanijärgne_aeg_s'] <= ajavahemik_ülemine)]
    
    tf_veerud1, tf_veerud2, tf_veerud3 = st.columns(3)
    if not ajavahemiku_andmestik.empty:
        hilinenud_ajavahemikus_andmestik = ajavahemiku_andmestik[ajavahemiku_andmestik['hilinemine_s'] > 0]
        kokku_ajavahemikus = len(ajavahemiku_andmestik)
        
        hilinenute_protsent_ajavahemikus = (len(hilinenud_ajavahemikus_andmestik) / kokku_ajavahemikus) * 100
        keskmine_hilinemine_ajavahemikus = ajavahemiku_andmestik['hilinemine_s'].mean()
        mediaan_hilinemine_ajavahemikus = ajavahemiku_andmestik['hilinemine_s'].median()

        with tf_veerud1:
            st.metric(label=f"Hilinemiste %", value=f"{hilinenute_protsent_ajavahemikus:.2f}%")
        with tf_veerud2:
            st.metric(label=f"Keskmine hilinemine", value=f"{keskmine_hilinemine_ajavahemikus:.2f} s")
        with tf_veerud3:
            st.metric(label=f"Mediaan", value=f"{mediaan_hilinemine_ajavahemikus:.2f} s")
    else:
        st.write(f"Ajavahemikus {ajavahemik_alumine}s - {ajavahemik_ülemine}s ei leitud busse.")
    st.markdown("---")

def rita_analüüs():
    zoo_andmed = pd.read_csv(os.path.join(andmete_kaust, "822_norm.csv"), 
                           header=None, names=['tegelik_aeg', 'plaanijärgne_aeg', 'kasutamata'])
    toompark_andmed = pd.read_csv(os.path.join(andmete_kaust, "1769_norm.csv"), 
                                header=None, names=['tegelik_aeg', 'plaanijärgne_aeg', 'kasutamata'])
    
    # Lae võrdlusgraafik - see sisaldab GTFS-põhiseid ametlikke bussigraafikuid
    # vajalik kuna 822_norm ja 1769_norm failides on kogutud reaalsed ajad,
    # kuid need ei pruugi täpselt vastata ametlikule graafikule
    võrdlusgraafik = pd.read_csv(os.path.join(os.path.dirname(andmete_kaust), "raw", "zoo_toompark_valjumised.csv"))
    
    # Rita koosolek on kell 9:05 = 9*3600+5*60=32700 sekundit
    koosoleku_aeg = 9 * 3600 + 5 * 60 
    kõndimine_bussini = 300 
    kõndimine_bussist = 240 
    
    # siia paneb võrdluse jargi saadud reisid
    reisi_tulemused = []
    
    # kuna kogutud andmetel eeldatav saabumine ja gtfs andmetel saabumine erineb ss see vajalik
    for _, võrdlus_reis in võrdlusgraafik.iterrows():
        # leiab lähima vaste 822_norm (Zoo) failist plaanijärgse aja järgi - see ok kui buss ei hiline nii palju et jargmine tuleb enne eelmist
        zoo_erinevus = np.abs(zoo_andmed['plaanijärgne_aeg'] - võrdlus_reis['zoo_saabumine_sek'])
        zoo_idx = zoo_erinevus.idxmin()
        zoo_vaste = zoo_andmed.loc[zoo_idx]
        
        # sama nagu eelmine aga toompark
        toompark_erinevus = np.abs(toompark_andmed['plaanijärgne_aeg'] - võrdlus_reis['toompark_saabumine_sek'])
        toompark_idx = toompark_erinevus.idxmin()
        toompark_vaste = toompark_andmed.loc[toompark_idx]
        
        # lisab ainult kui max 5min vahe.
        if zoo_erinevus[zoo_idx] < 300 and toompark_erinevus[toompark_idx] < 300:
            tegelik_reisiaeg = toompark_vaste['tegelik_aeg'] - zoo_vaste['tegelik_aeg']
            plaanijärgne_reisiaeg = võrdlus_reis['toompark_saabumine_sek'] - võrdlus_reis['zoo_saabumine_sek']
            
            # lisab koik reisiajad mis kestavad al 10m kuni 40m (toenaoliselt peaks vahem kui 10 ka?)
            if 600 < tegelik_reisiaeg < 2400:
                reisi_tulemused.append({
                    'zoo_plaanijärgne': zoo_vaste['plaanijärgne_aeg'],
                    'zoo_tegelik': zoo_vaste['tegelik_aeg'],
                    'toompark_plaanijärgne': toompark_vaste['plaanijärgne_aeg'],
                    'toompark_tegelik': toompark_vaste['tegelik_aeg'],
                    'zoo_hilinemine': zoo_vaste['tegelik_aeg'] - zoo_vaste['plaanijärgne_aeg'],
                    'toompark_hilinemine': toompark_vaste['tegelik_aeg'] - toompark_vaste['plaanijärgne_aeg'],
                    'plaanijärgne_reisiaeg': plaanijärgne_reisiaeg,
                    'tegelik_reisiaeg': tegelik_reisiaeg
                })
    
    reisid_df = pd.DataFrame(reisi_tulemused)
    
    if reisid_df.empty:
        st.error("Zoo ja Toomparki vahel ei leitud vastavaid reise")
        return

    st.markdown("### Bussireisi aja jaotus (Zoo → Toompark)")
    
    keskmine_aeg = reisid_df['tegelik_reisiaeg'].mean()
    standardhälve = reisid_df['tegelik_reisiaeg'].std()
    
    reisiajad_sek = reisid_df['tegelik_reisiaeg'].values
    
    vahemiku_piirid = np.arange(reisiajad_sek.min(), reisiajad_sek.max() + 30, 30)  # 30-sekundilised vahemikud histogrammi jaoks
    hist, vahemikud = np.histogram(reisiajad_sek, bins=vahemiku_piirid)
    vahemiku_keskkohad = (vahemikud[:-1] + vahemikud[1:]) / 2
    
    # lisab normaaljaotuse kihina histogrammile
    x_vahemik = np.linspace(reisiajad_sek.min(), reisiajad_sek.max(), 100)
    normaaljaotus = stats.norm.pdf(x_vahemik, keskmine_aeg, standardhälve)
    normaaljaotus = normaaljaotus * len(reisiajad_sek) * 30 
    
    hist_df = pd.DataFrame({
        'reisiaeg_sek': vahemiku_keskkohad,
        'reisiaeg_min': vahemiku_keskkohad / 60,
        'arv': hist
    })
    
    normal_df = pd.DataFrame({
        'reisiaeg_sek': x_vahemik,
        'reisiaeg_min': x_vahemik / 60,
        'tihedus': normaaljaotus
    })
    
    hist_diagramm = alt.Chart(hist_df).mark_bar(
        opacity=0.7,
        color='steelblue'
    ).encode(
        x=alt.X('reisiaeg_min:Q', title='Reisiaeg (minutites)'),
        y=alt.Y('arv:Q', title='Reiside arv'),
        tooltip=[
            alt.Tooltip('reisiaeg_min:Q', format='.1f', title='Reisiaeg (min)'),
            alt.Tooltip('arv:Q', title='Reiside arv')
        ]
    )
    
    # siin lisatakse normaaljaotuse jaoks joon
    normaal_diagramm = alt.Chart(normal_df).mark_line(
        color='red',
        strokeWidth=3
    ).encode(
        x='reisiaeg_min:Q',
        y=alt.Y('tihedus:Q', title='Reiside arv')
    )
    
    # merge
    ühendatud_diagramm = (hist_diagramm + normaal_diagramm).properties(
        width=700,
        height=400,
        title='Tegelike reisiaegade jaotus'
    )
    
    st.altair_chart(ühendatud_diagramm, use_container_width=True)
    
    veerg1, veerg2, veerg3, veerg4 = st.columns(4)
    with veerg1:
        st.metric("Keskmine", f"{keskmine_aeg/60:.1f} min ({keskmine_aeg:.0f}s)")
    with veerg2:
        st.metric("Standardhälve", f"{standardhälve/60:.1f} min ({standardhälve:.0f}s)")
    with veerg3:
        st.metric("Min", f"{reisid_df['tegelik_reisiaeg'].min()/60:.1f} min")
    with veerg4:
        st.metric("Max", f"{reisid_df['tegelik_reisiaeg'].max()/60:.1f} min")
    
    
    st.markdown("### Rita hilinemise tõenäosus")
    
    # votab ainult hommikused reisid - peaks al 8?
    hommikused_reisid = reisid_df[
        (reisid_df['zoo_plaanijärgne'] >= 7.5 * 3600) &  # Alates 7:30
        (reisid_df['zoo_plaanijärgne'] <= 9 * 3600)      # Kuni 9:00
    ].copy().sort_values('zoo_plaanijärgne')
    
    # siit saab muuta valjumise aega
    kodust_lahkumise_algus = 8 * 3600  # 8:00
    kodust_lahkumise_lõpp = 9 * 3600    # 9:00
    kodust_lahkumise_ajad = np.arange(kodust_lahkumise_algus, kodust_lahkumise_lõpp, 60)  # Iga minut
    
    tõenäosused = []
    
    for lahkumisaeg in kodust_lahkumise_ajad:

        peatusesse_jõudmine = lahkumisaeg + kõndimine_bussini
        
        järgmised_bussid = hommikused_reisid[hommikused_reisid['zoo_tegelik'] >= peatusesse_jõudmine]
        
        if järgmised_bussid.empty:
            tõenäosused.append(1.0)  # kui busse pole, jaab hiljaks : D
            continue
        
        # see votab esimese saadaval oleva bussi
        järgmine_buss = järgmised_bussid.iloc[0]
        
        # monte carlo simulatsioon....
        hilinejate_arv = 0
        simulatsioonid = 10000
        
        for _ in range(simulatsioonid):
            reisiaeg = np.random.normal(keskmine_aeg, standardhälve)
            reisiaeg = max(reisiaeg, 600)
            
            # Zoo peatuse viivitus - põhineb tegelikel andmetel (keskmine ~104s hommikusel ajal)
            zoo_viivitus = np.random.normal(104, 30)  # keskmine 104s, standardhälve 30s
            
            # bussi tegelik väljumine(plaanijärgne + viivitus, kuid mitte varem kui plaanijärgne)
            bussi_väljumine = järgmine_buss['zoo_plaanijärgne'] + max(0, zoo_viivitus)
            toomparki_saabumine = bussi_väljumine + reisiaeg
            koosolekule_jõudmine = toomparki_saabumine + kõndimine_bussist
            
            if koosolekule_jõudmine > koosoleku_aeg:
                hilinejate_arv += 1
        
        hilinemisoht = hilinejate_arv / simulatsioonid
        tõenäosused.append(hilinemisoht)
    
    # see "silub" tulemusi S-kõvera jaoks
    akna_suurus = 3
    tõenäosused = pd.Series(tõenäosused).rolling(window=akna_suurus, center=True, min_periods=1).mean().values

    #andmed graafiku jaoks
    tõenäosuse_df = pd.DataFrame({
        'kodust_lahkumise_aeg': kodust_lahkumise_ajad,
        'kodust_lahkumise_str': [sek_kellaaeg(t) for t in kodust_lahkumise_ajad],
        'hilinemise_tõenäosus': tõenäosused
    })
    
    
    # graafik ise
    graafik = alt.Chart(tõenäosuse_df).mark_line(
        point=True,
        strokeWidth=3,
        color='darkblue'
    ).encode(
        x=alt.X('kodust_lahkumise_str:N', 
                title='Rita kodust lahkumise aeg',
                sort=alt.EncodingSortField(field="kodust_lahkumise_aeg", order='ascending')),
        y=alt.Y('hilinemise_tõenäosus:Q', 
                title='Hilinemise tõenäosus',
                scale=alt.Scale(domain=[0, 1])),
        tooltip=[
            alt.Tooltip('kodust_lahkumise_str:N', title='Kodust lahkumine'),
            alt.Tooltip('hilinemise_tõenäosus:Q', title='P(Hilinemine)', format='.2%')
        ]
    ).properties(
        width=800,
        height=400
    )
    
    st.altair_chart(graafik, use_container_width=True)
    
    

st.set_page_config(layout="wide")

rakenduse_path = os.path.dirname(__file__)
andmete_kaust = os.path.abspath(os.path.join(rakenduse_path, "..", "data", "processed"))

fail_822_nimi = "822_norm.csv"
fail_1769_nimi = "1769_norm.csv"

fail_822_path = os.path.join(andmete_kaust, fail_822_nimi)
fail_1769_path = os.path.join(andmete_kaust, fail_1769_nimi)

st.subheader("Peatus 822 (Zoo)")
andmed_822 = lae_ja_töötle_andmed(fail_822_path)
statistika_hilinemised(andmed_822, fail_822_nimi)

st.subheader("Peatus 1769 (Toompark)")
andmed_1769 = lae_ja_töötle_andmed(fail_1769_path)
statistika_hilinemised(andmed_1769, fail_1769_nimi)
st.markdown("---")
rita_analüüs()