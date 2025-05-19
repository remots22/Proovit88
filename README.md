# Proovit88
Otsustasin esmalt laadida alla Eesti GTFS andmestiku ning seda uurida. Kavatsen esmalt teha lihtsama graafiku GTFS andmete põhjal. Andmestik on saadaval: "http://www.peatus.ee/gtfs/" ning juhend: "https://developers.google.com/transit/gtfs/reference/",

Leidsin stops.txt failist vastavad peatused:
| stop_id | stop_code | stop_name | stop_lat    | stop_lon    | zone_id | alias | stop_area | stop_desc | lest_x     | lest_y    | zone_name | authority   |
|---------|-----------|-----------|-------------|-------------|---------|-------|-----------|-----------|------------|-----------|-----------|-------------|
| 822     | 00702-1   | Zoo       | 59.42621424 | 24.65888954 | 822     |       | Haabersti |           | 6587778.16 | 537400.97 | Harju1    | Tallinna TA |
| 1769    | 10902-1   | Toompark  | 59.43682472 | 24.73332737 | 1769    |       | Kesklinn  |           | 6589004.00 | 541613.25 | Harju1    | Tallinna TA |

routes.txt põhjal sõidavad Zoo ja Toompargi vahel järgmised liinid:
| route_id | agency_id | route_short_name | route_long_name              | route_type | route_color | competent_authority | route_desc |
|----------|-----------|------------------|------------------------------|------------|-------------|---------------------|------------|
| xxxx     | 56        | 21               | Balti jaam - Landi           | 3          | de2c42      | Tallinna TA         |            |
| xxxx     | 56        | 21B              | Balti jaam - Kakumäe         | 3          | de2c42      | Tallinna TA         |            |
| xxxx     | 56        | 41               | Balti jaam - Landi           | 3          | de2c42      | Tallinna TA         |            |
| xxxx     | 56        | 41B              | Balti jaam - Kakumäe         | 3          | de2c42      | Tallinna TA         |            |
| xxxx     | 56        | 8                | Väike-Õismäe - Äigrumäe      | 3          | de2c42      | Tallinna TA         |            |
| xxxx     | 56        | 92               | ÖÖ Balti jaam - Väike-Õismäe | 3          | de2c42      | Tallinna TA         |            |

Selle põhjal
# Allikad
Ühistranspordiregistri avaandmed
Ajaline kaetus: 28.05.2018; Uuenemissagedus: iga päev  
Litsents: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/ee/deed.et)  
URL: https://avaandmed.eesti.ee/datasets/uhistranspordiregistri-avaandmed

Google Transit GTFS Schedule
Viimane uuendus: 21.12.2022  
URL: https://developers.google.com/transit/gtfs/reference/
