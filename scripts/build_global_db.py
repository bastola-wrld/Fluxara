#!/usr/bin/env python3
"""
Build Global Facility Database
Generates the global facility dataset (95 facilities) and saves to JSON and CSV.
"""
import pandas as pd
import numpy as np
import json
import os

facilities_dir = "satellite_data/facilities"
os.makedirs(facilities_dir, exist_ok=True)

GLOBAL_FACILITIES = [
    # ── USA — Permian Basin ──────────────────────────────
    {"name":"Pioneer NR Spraberry",        "country":"USA","region":"Permian Basin","state":"TX","lat":31.85,"lon":-102.10,"ghg_tonnes":542000,"type":"Oil & Gas"},
    {"name":"ExxonMobil XTO Permian",      "country":"USA","region":"Permian Basin","state":"TX","lat":31.70,"lon":-102.20,"ghg_tonnes":498000,"type":"Oil & Gas"},
    {"name":"Chevron Permian",             "country":"USA","region":"Permian Basin","state":"TX","lat":32.20,"lon":-101.90,"ghg_tonnes":412000,"type":"Oil & Gas"},
    {"name":"ConocoPhillips Midland",      "country":"USA","region":"Permian Basin","state":"TX","lat":32.10,"lon":-102.50,"ghg_tonnes":398000,"type":"Oil & Gas"},
    {"name":"Occidental Delaware",         "country":"USA","region":"Permian Basin","state":"TX","lat":31.90,"lon":-102.30,"ghg_tonnes":367000,"type":"Oil & Gas"},
    {"name":"Diamondback Energy",          "country":"USA","region":"Permian Basin","state":"TX","lat":31.60,"lon":-102.40,"ghg_tonnes":289000,"type":"Oil & Gas"},
    {"name":"Devon Energy Permian",        "country":"USA","region":"Permian Basin","state":"TX","lat":31.40,"lon":-102.60,"ghg_tonnes":245000,"type":"Oil & Gas"},
    {"name":"Marathon Oil Permian",        "country":"USA","region":"Permian Basin","state":"TX","lat":31.30,"lon":-102.80,"ghg_tonnes":176000,"type":"Oil & Gas"},
    # ── USA — Appalachian ────────────────────────────────
    {"name":"EQT Corporation",             "country":"USA","region":"Appalachian","state":"PA","lat":40.20,"lon":-79.80,"ghg_tonnes":567000,"type":"Natural Gas"},
    {"name":"Range Resources",             "country":"USA","region":"Appalachian","state":"PA","lat":40.50,"lon":-80.20,"ghg_tonnes":423000,"type":"Natural Gas"},
    {"name":"Southwestern Energy",         "country":"USA","region":"Appalachian","state":"WV","lat":38.90,"lon":-81.50,"ghg_tonnes":389000,"type":"Natural Gas"},
    {"name":"CNX Resources",               "country":"USA","region":"Appalachian","state":"PA","lat":39.80,"lon":-80.10,"ghg_tonnes":312000,"type":"Natural Gas"},
    # ── USA — Gulf of Mexico ─────────────────────────────
    {"name":"Shell GoM",                   "country":"USA","region":"Gulf of Mexico","state":"LA","lat":28.50,"lon":-90.50,"ghg_tonnes":756000,"type":"Offshore Oil"},
    {"name":"BP GoM",                      "country":"USA","region":"Gulf of Mexico","state":"LA","lat":28.20,"lon":-89.80,"ghg_tonnes":634000,"type":"Offshore Oil"},
    {"name":"Chevron GoM",                 "country":"USA","region":"Gulf of Mexico","state":"LA","lat":27.80,"lon":-91.20,"ghg_tonnes":589000,"type":"Offshore Oil"},
    # ── USA — Refineries ─────────────────────────────────
    {"name":"ExxonMobil Baytown",          "country":"USA","region":"Texas Gulf","state":"TX","lat":29.73,"lon":-94.97,"ghg_tonnes":4200000,"type":"Refinery"},
    {"name":"Marathon Galveston Bay",      "country":"USA","region":"Texas Gulf","state":"TX","lat":29.37,"lon":-94.90,"ghg_tonnes":3800000,"type":"Refinery"},
    {"name":"Valero Port Arthur",          "country":"USA","region":"Texas Gulf","state":"TX","lat":29.90,"lon":-93.93,"ghg_tonnes":3200000,"type":"Refinery"},
    # ── USA — Power Plants ───────────────────────────────
    {"name":"W.A. Parish Power Plant",     "country":"USA","region":"Texas","state":"TX","lat":29.47,"lon":-95.68,"ghg_tonnes":8900000,"type":"Power Plant"},
    {"name":"Scherer Power Plant",         "country":"USA","region":"Georgia","state":"GA","lat":33.07,"lon":-83.93,"ghg_tonnes":8200000,"type":"Power Plant"},
    # ── RUSSIA ───────────────────────────────────────────
    {"name":"Gazprom Urengoy",             "country":"Russia","region":"West Siberia","state":"Yamalo","lat":65.96,"lon":78.37,"ghg_tonnes":12000000,"type":"Natural Gas"},
    {"name":"Gazprom Yamburg",             "country":"Russia","region":"West Siberia","state":"Yamalo","lat":67.99,"lon":75.02,"ghg_tonnes":9800000,"type":"Natural Gas"},
    {"name":"Rosneft Samotlor",            "country":"Russia","region":"West Siberia","state":"Khanty","lat":61.10,"lon":76.40,"ghg_tonnes":7600000,"type":"Oil & Gas"},
    {"name":"Rosneft Vankor",              "country":"Russia","region":"East Siberia","state":"Krasnoyarsk","lat":67.85,"lon":83.55,"ghg_tonnes":5400000,"type":"Oil & Gas"},
    {"name":"Lukoil Kogalym",              "country":"Russia","region":"West Siberia","state":"Khanty","lat":62.26,"lon":74.48,"ghg_tonnes":4200000,"type":"Oil & Gas"},
    {"name":"Novatek Yamal LNG",           "country":"Russia","region":"Arctic","state":"Yamalo","lat":72.78,"lon":68.72,"ghg_tonnes":3800000,"type":"LNG Terminal"},
    # ── SAUDI ARABIA ─────────────────────────────────────
    {"name":"Aramco Ghawar Field",         "country":"Saudi Arabia","region":"Eastern Province","state":"EP","lat":25.12,"lon":49.20,"ghg_tonnes":18000000,"type":"Oil & Gas"},
    {"name":"Aramco Abqaiq Plant",         "country":"Saudi Arabia","region":"Eastern Province","state":"EP","lat":26.00,"lon":49.67,"ghg_tonnes":8900000,"type":"Oil & Gas"},
    {"name":"Aramco Ras Tanura Refinery",  "country":"Saudi Arabia","region":"Eastern Province","state":"EP","lat":26.65,"lon":50.15,"ghg_tonnes":6700000,"type":"Refinery"},
    {"name":"Aramco Yanbu Refinery",       "country":"Saudi Arabia","region":"Yanbu","state":"Madinah","lat":24.08,"lon":38.05,"ghg_tonnes":4200000,"type":"Refinery"},
    # ── UAE ───────────────────────────────────────────────
    {"name":"ADNOC Bu Hasa",               "country":"UAE","region":"Abu Dhabi","state":"AD","lat":23.50,"lon":53.42,"ghg_tonnes":5600000,"type":"Oil & Gas"},
    {"name":"ADNOC Ruwais Refinery",       "country":"UAE","region":"Abu Dhabi","state":"AD","lat":24.11,"lon":52.73,"ghg_tonnes":4100000,"type":"Refinery"},
    {"name":"ADNOC Das Island",            "country":"UAE","region":"Offshore","state":"AD","lat":25.15,"lon":52.87,"ghg_tonnes":3200000,"type":"LNG Terminal"},
    # ── IRAN ──────────────────────────────────────────────
    {"name":"NIOC South Pars Gas",         "country":"Iran","region":"Persian Gulf","state":"Bushehr","lat":27.57,"lon":51.77,"ghg_tonnes":14000000,"type":"Natural Gas"},
    {"name":"NIOC Ahvaz Field",            "country":"Iran","region":"Khuzestan","state":"KH","lat":31.32,"lon":48.67,"ghg_tonnes":9200000,"type":"Oil & Gas"},
    {"name":"Abadan Refinery",             "country":"Iran","region":"Khuzestan","state":"KH","lat":30.34,"lon":48.28,"ghg_tonnes":5400000,"type":"Refinery"},
    # ── IRAQ ──────────────────────────────────────────────
    {"name":"Rumaila Oil Field",           "country":"Iraq","region":"Basra","state":"Basra","lat":30.20,"lon":47.35,"ghg_tonnes":11000000,"type":"Oil & Gas"},
    {"name":"West Qurna Field",            "country":"Iraq","region":"Basra","state":"Basra","lat":30.53,"lon":47.42,"ghg_tonnes":8700000,"type":"Oil & Gas"},
    {"name":"Kirkuk Oil Field",            "country":"Iraq","region":"Kirkuk","state":"Kirkuk","lat":35.47,"lon":44.39,"ghg_tonnes":6200000,"type":"Oil & Gas"},
    # ── KUWAIT ───────────────────────────────────────────
    {"name":"KOC Burgan Field",            "country":"Kuwait","region":"South Kuwait","state":"AH","lat":28.97,"lon":48.00,"ghg_tonnes":9800000,"type":"Oil & Gas"},
    {"name":"KNPC Mina Al Ahmadi",         "country":"Kuwait","region":"South Kuwait","state":"AH","lat":29.07,"lon":48.13,"ghg_tonnes":5600000,"type":"Refinery"},
    # ── NIGERIA ───────────────────────────────────────────
    {"name":"Shell Niger Delta",           "country":"Nigeria","region":"Niger Delta","state":"Rivers","lat":4.85,"lon":6.98,"ghg_tonnes":8900000,"type":"Oil & Gas"},
    {"name":"Chevron Nigeria OML 49",      "country":"Nigeria","region":"Niger Delta","state":"Delta","lat":5.30,"lon":5.48,"ghg_tonnes":6700000,"type":"Oil & Gas"},
    {"name":"NLNG Bonny Island",           "country":"Nigeria","region":"Niger Delta","state":"Rivers","lat":4.44,"lon":7.15,"ghg_tonnes":5200000,"type":"LNG Terminal"},
    {"name":"Total Nigeria OML 58",        "country":"Nigeria","region":"Niger Delta","state":"Rivers","lat":4.67,"lon":7.23,"ghg_tonnes":4100000,"type":"Oil & Gas"},
    # ── VENEZUELA ─────────────────────────────────────────
    {"name":"PDVSA Orinoco Belt",          "country":"Venezuela","region":"Orinoco","state":"Monagas","lat":8.80,"lon":-63.20,"ghg_tonnes":9200000,"type":"Oil & Gas"},
    {"name":"PDVSA Lagunillas",            "country":"Venezuela","region":"Maracaibo","state":"Zulia","lat":10.13,"lon":-71.25,"ghg_tonnes":6800000,"type":"Oil & Gas"},
    # ── CANADA ────────────────────────────────────────────
    {"name":"Suncor Oil Sands",            "country":"Canada","region":"Alberta","state":"AB","lat":57.00,"lon":-111.50,"ghg_tonnes":19000000,"type":"Oil Sands"},
    {"name":"CNRL Horizon",                "country":"Canada","region":"Alberta","state":"AB","lat":57.38,"lon":-111.73,"ghg_tonnes":14000000,"type":"Oil Sands"},
    {"name":"Imperial Kearl",              "country":"Canada","region":"Alberta","state":"AB","lat":57.28,"lon":-111.65,"ghg_tonnes":8900000,"type":"Oil Sands"},
    {"name":"Cenovus Foster Creek",        "country":"Canada","region":"Alberta","state":"AB","lat":54.75,"lon":-110.40,"ghg_tonnes":6700000,"type":"Oil Sands"},
    # ── AUSTRALIA ─────────────────────────────────────────
    {"name":"Woodside Pluto LNG",          "country":"Australia","region":"Pilbara","state":"WA","lat":-20.63,"lon":116.71,"ghg_tonnes":5600000,"type":"LNG Terminal"},
    {"name":"Chevron Gorgon LNG",          "country":"Australia","region":"Pilbara","state":"WA","lat":-21.74,"lon":114.17,"ghg_tonnes":7200000,"type":"LNG Terminal"},
    {"name":"Santos Darwin LNG",           "country":"Australia","region":"NT","state":"NT","lat":-12.47,"lon":130.85,"ghg_tonnes":3800000,"type":"LNG Terminal"},
    {"name":"BHP Olympic Dam",             "country":"Australia","region":"SA","state":"SA","lat":-30.44,"lon":136.89,"ghg_tonnes":2900000,"type":"Mining"},
    # ── CHINA ─────────────────────────────────────────────
    {"name":"Sinopec Shengli Field",       "country":"China","region":"Shandong","state":"SD","lat":37.47,"lon":118.47,"ghg_tonnes":8900000,"type":"Oil & Gas"},
    {"name":"CNPC Daqing Field",           "country":"China","region":"Heilongjiang","state":"HLJ","lat":46.60,"lon":125.00,"ghg_tonnes":7600000,"type":"Oil & Gas"},
    {"name":"CNOOC Bohai Bay",             "country":"China","region":"Bohai","state":"Offshore","lat":38.80,"lon":120.50,"ghg_tonnes":5400000,"type":"Offshore Oil"},
    {"name":"Datang Duolun Power",         "country":"China","region":"Inner Mongolia","state":"NMG","lat":42.19,"lon":116.47,"ghg_tonnes":12000000,"type":"Power Plant"},
    {"name":"Guodian Tuoketuo",            "country":"China","region":"Inner Mongolia","state":"NMG","lat":40.27,"lon":111.07,"ghg_tonnes":11000000,"type":"Power Plant"},
    # ── INDIA ─────────────────────────────────────────────
    {"name":"ONGC Mumbai High",            "country":"India","region":"Offshore","state":"MH","lat":19.07,"lon":71.28,"ghg_tonnes":5600000,"type":"Offshore Oil"},
    {"name":"Reliance Jamnagar Refinery",  "country":"India","region":"Gujarat","state":"GJ","lat":22.47,"lon":70.06,"ghg_tonnes":8900000,"type":"Refinery"},
    {"name":"NTPC Vindhyachal Power",      "country":"India","region":"MP","state":"MP","lat":24.11,"lon":82.67,"ghg_tonnes":14000000,"type":"Power Plant"},
    {"name":"NTPC Rihand Power",           "country":"India","region":"UP","state":"UP","lat":24.03,"lon":83.02,"ghg_tonnes":12000000,"type":"Power Plant"},
    # ── NORTH SEA ─────────────────────────────────────────
    {"name":"Equinor Johan Sverdrup",      "country":"Norway","region":"North Sea","state":"Offshore","lat":58.80,"lon":2.52,"ghg_tonnes":890000,"type":"Offshore Oil"},
    {"name":"Equinor Troll Field",         "country":"Norway","region":"North Sea","state":"Offshore","lat":60.64,"lon":3.72,"ghg_tonnes":1200000,"type":"Natural Gas"},
    {"name":"BP Schiehallion",             "country":"UK","region":"North Sea","state":"Offshore","lat":60.13,"lon":-3.95,"ghg_tonnes":760000,"type":"Offshore Oil"},
    {"name":"Shell Shearwater",            "country":"UK","region":"North Sea","state":"Offshore","lat":57.91,"lon":1.79,"ghg_tonnes":650000,"type":"Offshore Oil"},
    {"name":"Harbour Energy Clair",        "country":"UK","region":"North Sea","state":"Offshore","lat":60.55,"lon":-2.01,"ghg_tonnes":540000,"type":"Offshore Oil"},
    # ── UK — Onshore ──────────────────────────────────────
    {"name":"Drax Power Station",          "country":"UK","region":"Yorkshire","state":"ENG","lat":53.74,"lon":-1.02,"ghg_tonnes":3200000,"type":"Power Plant"},
    {"name":"Ratcliffe Power Station",     "country":"UK","region":"Midlands","state":"ENG","lat":52.87,"lon":-1.25,"ghg_tonnes":2800000,"type":"Power Plant"},
    {"name":"Grangemouth Refinery",        "country":"UK","region":"Scotland","state":"SCO","lat":56.01,"lon":-3.71,"ghg_tonnes":1900000,"type":"Refinery"},
    # ── GERMANY ───────────────────────────────────────────
    {"name":"RWE Neurath Power",           "country":"Germany","region":"NRW","state":"NRW","lat":50.95,"lon":6.57,"ghg_tonnes":28000000,"type":"Power Plant"},
    {"name":"RWE Niederaussem",            "country":"Germany","region":"NRW","state":"NRW","lat":50.95,"lon":6.65,"ghg_tonnes":24000000,"type":"Power Plant"},
    {"name":"BASF Ludwigshafen",           "country":"Germany","region":"Baden","state":"RP","lat":49.47,"lon":8.44,"ghg_tonnes":4200000,"type":"Chemical Plant"},
    # ── NETHERLANDS ───────────────────────────────────────
    {"name":"Shell Pernis Refinery",       "country":"Netherlands","region":"Rotterdam","state":"ZH","lat":51.88,"lon":4.37,"ghg_tonnes":7800000,"type":"Refinery"},
    {"name":"Groningen Gas Field",         "country":"Netherlands","region":"Groningen","state":"GR","lat":53.24,"lon":6.83,"ghg_tonnes":5600000,"type":"Natural Gas"},
    # ── BRAZIL ────────────────────────────────────────────
    {"name":"Petrobras Tupi Pre-salt",     "country":"Brazil","region":"Santos Basin","state":"RJ","lat":-23.56,"lon":-43.87,"ghg_tonnes":8900000,"type":"Offshore Oil"},
    {"name":"Petrobras Campos Basin",      "country":"Brazil","region":"Campos","state":"RJ","lat":-22.00,"lon":-40.50,"ghg_tonnes":7600000,"type":"Offshore Oil"},
    {"name":"Vale Carajas Mine",           "country":"Brazil","region":"Para","state":"PA","lat":-6.07,"lon":-50.17,"ghg_tonnes":5400000,"type":"Mining"},
    # ── KAZAKHSTAN ────────────────────────────────────────
    {"name":"Tengizchevroil",              "country":"Kazakhstan","region":"Atyrau","state":"ATY","lat":45.47,"lon":53.11,"ghg_tonnes":12000000,"type":"Oil & Gas"},
    {"name":"Karachaganak Field",          "country":"Kazakhstan","region":"WKO","state":"WKO","lat":51.58,"lon":53.62,"ghg_tonnes":8900000,"type":"Oil & Gas"},
    {"name":"Kashagan Field",              "country":"Kazakhstan","region":"Atyrau","state":"ATY","lat":45.52,"lon":52.08,"ghg_tonnes":7600000,"type":"Offshore Oil"},
    # ── MEXICO ────────────────────────────────────────────
    {"name":"Pemex Cantarell Field",       "country":"Mexico","region":"Gulf Mexico","state":"CAM","lat":19.65,"lon":-91.97,"ghg_tonnes":9800000,"type":"Offshore Oil"},
    {"name":"Pemex Ku-Maloob-Zaap",        "country":"Mexico","region":"Gulf Mexico","state":"CAM","lat":19.88,"lon":-91.75,"ghg_tonnes":7600000,"type":"Offshore Oil"},
    {"name":"Pemex Salina Cruz Refinery",  "country":"Mexico","region":"Oaxaca","state":"OAX","lat":16.18,"lon":-95.18,"ghg_tonnes":4200000,"type":"Refinery"},
    # ── ALGERIA ───────────────────────────────────────────
    {"name":"Sonatrach Hassi Messaoud",    "country":"Algeria","region":"Sahara","state":"OUA","lat":31.67,"lon":6.07,"ghg_tonnes":7800000,"type":"Oil & Gas"},
    {"name":"Sonatrach Hassi R'Mel",       "country":"Algeria","region":"Sahara","state":"LAG","lat":32.95,"lon":3.27,"ghg_tonnes":6700000,"type":"Natural Gas"},
    # ── QATAR ─────────────────────────────────────────────
    {"name":"QatarEnergy North Field",     "country":"Qatar","region":"Offshore","state":"QA","lat":25.90,"lon":51.95,"ghg_tonnes":21000000,"type":"Natural Gas"},
    {"name":"Ras Laffan LNG",              "country":"Qatar","region":"North Qatar","state":"QA","lat":25.90,"lon":51.57,"ghg_tonnes":8900000,"type":"LNG Terminal"},
    # ── INDONESIA ─────────────────────────────────────────
    {"name":"Pertamina Rokan Block",       "country":"Indonesia","region":"Sumatra","state":"Riau","lat":1.35,"lon":101.45,"ghg_tonnes":5600000,"type":"Oil & Gas"},
    {"name":"Bontang LNG",                 "country":"Indonesia","region":"Kalimantan","state":"EK","lat":0.13,"lon":117.48,"ghg_tonnes":4200000,"type":"LNG Terminal"},
    # ── SOUTH AFRICA ──────────────────────────────────────
    {"name":"Sasol Secunda",               "country":"South Africa","region":"Mpumalanga","state":"MP","lat":-26.53,"lon":29.18,"ghg_tonnes":56000000,"type":"Chemical Plant"},
    {"name":"Eskom Kendal Power",          "country":"South Africa","region":"Mpumalanga","state":"MP","lat":-26.09,"lon":29.14,"ghg_tonnes":38000000,"type":"Power Plant"},
    {"name":"Eskom Lethabo Power",         "country":"South Africa","region":"Free State","state":"FS","lat":-26.80,"lon":27.75,"ghg_tonnes":35000000,"type":"Power Plant"},
]

df_global = pd.DataFrame(GLOBAL_FACILITIES)
df_global["id"]           = range(1, len(df_global) + 1)
df_global["risk"]         = df_global["ghg_tonnes"].apply(
    lambda x: "high" if x > 5000000 else ("medium" if x > 1000000 else "low")
)
df_global["reported_t_yr"] = (df_global["ghg_tonnes"] / 1000).round(1)
df_global["operator"]      = df_global["name"].apply(lambda x: x.split()[0])
df_global["data_source"]  = "manual_unverified"

csv_path  = f"{facilities_dir}/global_facilities.csv"
json_path = f"{facilities_dir}/global_facilities.json"
df_global.to_csv(csv_path, index=False)
df_global.to_json(json_path, orient="records", indent=2)

print(f"✅ Global facility database built")
print(f"   Total    : {len(df_global)} facilities")
print(f"   Countries: {df_global['country'].nunique()}")
print(f"\n   By country:")
for c, n in df_global["country"].value_counts().items():
    print(f"     {c:20s} : {n}")
print(f"\n   By type:")
for t, n in df_global["type"].value_counts().items():
    print(f"     {t:20s} : {n}")
