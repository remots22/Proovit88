import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os

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