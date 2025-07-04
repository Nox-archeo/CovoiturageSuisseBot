import json
import os

def create_cities_json():
    """Crée le fichier cities.json avec la liste des communes"""
    print("📝 Création du fichier cities.json...")
    
    # Liste complète des communes suisses
    raw_data = """GDEKT	GDEBZNR	GDENR	GDENAME	GDENAMK	GDEBZNA	GDEKTNA	GDEMUTDAT
ZH	101	1	Aeugst am Albis	Aeugst am Albis	Bezirk Affoltern	Zürich	15.11.1976
ZH	101	2	Affoltern am Albis	Affoltern am Albis	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	3	Bonstetten	Bonstetten	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	4	Hausen am Albis	Hausen am Albis	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	5	Hedingen	Hedingen	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	6	Kappel am Albis	Kappel am Albis	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	7	Knonau	Knonau	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	8	Maschwanden	Maschwanden	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	9	Mettmenstetten	Mettmenstetten	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	10	Obfelden	Obfelden	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	11	Ottenbach	Ottenbach	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	12	Rifferswil	Rifferswil	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	13	Stallikon	Stallikon	Bezirk Affoltern	Zürich	01.01.1960
ZH	101	14	Wettswil am Albis	Wettswil am Albis	Bezirk Affoltern	Zürich	15.11.1976
ZH	102	21	Adlikon	Adlikon	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	22	Benken (ZH)	Benken (ZH)	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	23	Berg am Irchel	Berg am Irchel	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	24	Buch am Irchel	Buch am Irchel	Bezirk Andelfingen	Zürich	01.01.2013
ZH	102	25	Dachsen	Dachsen	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	26	Dorf	Dorf	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	27	Feuerthalen	Feuerthalen	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	28	Flaach	Flaach	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	29	Flurlingen	Flurlingen	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	30	Andelfingen	Andelfingen	Bezirk Andelfingen	Zürich	01.01.1970
ZH	102	31	Henggart	Henggart	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	32	Humlikon	Humlikon	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	33	Kleinandelfingen	Kleinandelfingen	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	34	Laufen-Uhwiesen	Laufen-Uhwiesen	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	35	Marthalen	Marthalen	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	36	Oberstammheim	Oberstammheim	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	37	Ossingen	Ossingen	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	38	Rheinau	Rheinau	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	39	Thalheim an der Thur	Thalheim an der Thur	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	40	Trüllikon	Trüllikon	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	41	Truttikon	Truttikon	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	42	Unterstammheim	Unterstammheim	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	43	Volken	Volken	Bezirk Andelfingen	Zürich	01.01.1960
ZH	102	44	Waltalingen	Waltalingen	Bezirk Andelfingen	Zürich	01.01.1960
ZH	103	51	Bachenbülach	Bachenbülach	Bezirk Bülach	Zürich	01.01.1960
ZH	103	52	Bassersdorf	Bassersdorf	Bezirk Bülach	Zürich	01.01.1960
ZH	103	53	Bülach	Bülach	Bezirk Bülach	Zürich	01.01.1960
ZH	103	54	Dietlikon	Dietlikon	Bezirk Bülach	Zürich	01.01.1960
ZH	103	55	Eglisau	Eglisau	Bezirk Bülach	Zürich	01.01.1960
ZH	103	56	Embrach	Embrach	Bezirk Bülach	Zürich	01.01.1960
ZH	103	57	Freienstein-Teufen	Freienstein-Teufen	Bezirk Bülach	Zürich	01.01.1960
ZH	103	58	Glattfelden	Glattfelden	Bezirk Bülach	Zürich	01.01.1960
ZH	103	59	Hochfelden	Hochfelden	Bezirk Bülach	Zürich	01.01.1960
ZH	103	60	Höri	Höri	Bezirk Bülach	Zürich	01.01.1960
ZH	103	61	Hüntwangen	Hüntwangen	Bezirk Bülach	Zürich	01.01.1960
ZH	103	62	Kloten	Kloten	Bezirk Bülach	Zürich	01.01.1960
ZH	103	63	Lufingen	Lufingen	Bezirk Bülach	Zürich	01.01.1960
ZH	103	64	Nürensdorf	Nürensdorf	Bezirk Bülach	Zürich	01.01.1960
ZH	103	65	Oberembrach	Oberembrach	Bezirk Bülach	Zürich	01.01.1960
ZH	103	66	Opfikon	Opfikon	Bezirk Bülach	Zürich	01.01.1960
ZH	103	67	Rafz	Rafz	Bezirk Bülach	Zürich	01.01.1960
ZH	103	68	Rorbas	Rorbas	Bezirk Bülach	Zürich	01.01.1960
ZH	103	69	Wallisellen	Wallisellen	Bezirk Bülach	Zürich	01.01.1960
ZH	103	70	Wasterkingen	Wasterkingen	Bezirk Bülach	Zürich	01.01.1960
ZH	103	71	Wil (ZH)	Wil (ZH)	Bezirk Bülach	Zürich	01.01.1960
ZH	103	72	Winkel	Winkel	Bezirk Bülach	Zürich	01.01.1960
ZH	104	81	Bachs	Bachs	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	82	Boppelsen	Boppelsen	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	83	Buchs (ZH)	Buchs (ZH)	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	84	Dällikon	Dällikon	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	85	Dänikon	Dänikon	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	86	Dielsdorf	Dielsdorf	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	87	Hüttikon	Hüttikon	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	88	Neerach	Neerach	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	89	Niederglatt	Niederglatt	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	90	Niederhasli	Niederhasli	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	91	Niederweningen	Niederweningen	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	92	Oberglatt	Oberglatt	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	93	Oberweningen	Oberweningen	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	94	Otelfingen	Otelfingen	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	95	Regensberg	Regensberg	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	96	Regensdorf	Regensdorf	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	97	Rümlang	Rümlang	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	98	Schleinikon	Schleinikon	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	99	Schöfflisdorf	Schöfflisdorf	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	100	Stadel	Stadel	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	101	Steinmaur	Steinmaur	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	104	102	Weiach	Weiach	Bezirk Dielsdorf	Zürich	01.01.1960
ZH	105	111	Bäretswil	Bäretswil	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	112	Bubikon	Bubikon	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	113	Dürnten	Dürnten	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	114	Fischenthal	Fischenthal	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	115	Gossau (ZH)	Gossau (ZH)	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	116	Grüningen	Grüningen	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	117	Hinwil	Hinwil	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	118	Rüti (ZH)	Rüti (ZH)	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	119	Seegräben	Seegräben	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	120	Wald (ZH)	Wald (ZH)	Bezirk Hinwil	Zürich	01.01.1960
ZH	105	121	Wetzikon (ZH)	Wetzikon (ZH)	Bezirk Hinwil	Zürich	01.01.1960
ZH	106	131	Adliswil	Adliswil	Bezirk Horgen	Zürich	01.01.1960
ZH	106	132	Hirzel	Hirzel	Bezirk Horgen	Zürich	01.01.1960
ZH	106	133	Horgen	Horgen	Bezirk Horgen	Zürich	01.01.1960
ZH	106	134	Hütten	Hütten	Bezirk Horgen	Zürich	01.01.1960
ZH	106	135	Kilchberg (ZH)	Kilchberg (ZH)	Bezirk Horgen	Zürich	01.01.1960
ZH	106	136	Langnau am Albis	Langnau am Albis	Bezirk Horgen	Zürich	01.01.1960
ZH	106	137	Oberrieden	Oberrieden	Bezirk Horgen	Zürich	01.01.1960
ZH	106	138	Richterswil	Richterswil	Bezirk Horgen	Zürich	01.01.1960
ZH	106	139	Rüschlikon	Rüschlikon	Bezirk Horgen	Zürich	01.01.1960
ZH	106	140	Schönenberg (ZH)	Schönenberg (ZH)	Bezirk Horgen	Zürich	01.01.1960
ZH	106	141	Thalwil	Thalwil	Bezirk Horgen	Zürich	01.01.1960
ZH	106	142	Wädenswil	Wädenswil	Bezirk Horgen	Zürich	01.01.1960
ZH	107	151	Erlenbach (ZH)	Erlenbach (ZH)	Bezirk Meilen	Zürich	01.01.1960
ZH	107	152	Herrliberg	Herrliberg	Bezirk Meilen	Zürich	01.01.1960
ZH	107	153	Hombrechtikon	Hombrechtikon	Bezirk Meilen	Zürich	01.01.1960
ZH	107	154	Küsnacht (ZH)	Küsnacht (ZH)	Bezirk Meilen	Zürich	01.01.1960
ZH	107	155	Männedorf	Männedorf	Bezirk Meilen	Zürich	01.01.1960
ZH	107	156	Meilen	Meilen	Bezirk Meilen	Zürich	01.01.1960
ZH	107	157	Oetwil am See	Oetwil am See	Bezirk Meilen	Zürich	01.01.1960
ZH	107	158	Stäfa	Stäfa	Bezirk Meilen	Zürich	01.01.1960
ZH	107	159	Uetikon am See	Uetikon am See	Bezirk Meilen	Zürich	10.03.1977
ZH	107	160	Zumikon	Zumikon	Bezirk Meilen	Zürich	01.01.1960
ZH	107	161	Zollikon	Zollikon	Bezirk Meilen	Zürich	01.01.1986
ZH	108	171	Bauma	Bauma	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	172	Fehraltorf	Fehraltorf	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	173	Hittnau	Hittnau	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	174	Illnau-Effretikon	Illnau-Effretikon	Bezirk Pfäffikon	Zürich	16.03.1974
ZH	108	175	Kyburg	Kyburg	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	176	Lindau	Lindau	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	177	Pfäffikon	Pfäffikon	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	178	Russikon	Russikon	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	179	Sternenberg	Sternenberg	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	180	Weisslingen	Weisslingen	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	181	Wila	Wila	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	108	182	Wildberg	Wildberg	Bezirk Pfäffikon	Zürich	01.01.1960
ZH	109	191	Dübendorf	Dübendorf	Bezirk Uster	Zürich	01.01.1960
ZH	109	192	Egg	Egg	Bezirk Uster	Zürich	01.01.1960
ZH	109	193	Fällanden	Fällanden	Bezirk Uster	Zürich	01.01.1960
ZH	109	194	Greifensee	Greifensee	Bezirk Uster	Zürich	01.01.1960
ZH	109	195	Maur	Maur	Bezirk Uster	Zürich	01.01.1960
ZH	109	196	Mönchaltorf	Mönchaltorf	Bezirk Uster	Zürich	01.01.1960
ZH	109	197	Schwerzenbach	Schwerzenbach	Bezirk Uster	Zürich	01.01.1960
ZH	109	198	Uster	Uster	Bezirk Uster	Zürich	01.01.1960
ZH	109	199	Volketswil	Volketswil	Bezirk Uster	Zürich	01.01.1960
ZH	109	200	Wangen-Brüttisellen	Wangen-Brüttisellen	Bezirk Uster	Zürich	01.01.1976
ZH	110	211	Altikon	Altikon	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	213	Brütten	Brütten	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	214	Dägerlen	Dägerlen	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	215	Dättlikon	Dättlikon	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	216	Dinhard	Dinhard	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	217	Elgg	Elgg	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	218	Ellikon an der Thur	Ellikon an der Thur	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	219	Elsau	Elsau	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	220	Hagenbuch	Hagenbuch	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	221	Hettlingen	Hettlingen	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	222	Hofstetten (ZH)	Hofstetten (ZH)	Bezirk Winterthur	Zürich	01.01.2003
ZH	110	223	Neftenbach	Neftenbach	Bezirk Winterthur	Zürich	01.01.2013
ZH	110	224	Pfungen	Pfungen	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	225	Rickenbach (ZH)	Rickenbach (ZH)	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	226	Schlatt (ZH)	Schlatt (ZH)	Bezirk Winterthur	Zürich	01.01.1999
ZH	110	227	Seuzach	Seuzach	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	228	Turbenthal	Turbenthal	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	230	Winterthur	Winterthur	Bezirk Winterthur	Zürich	01.01.1960
ZH	110	231	Zell (ZH)	Zell (ZH)	Bezirk Winterthur	Zürich	01.01.1960
ZH	111	241	Aesch (ZH)	Aesch (ZH)	Bezirk Dietikon	Zürich	01.01.2003
ZH	111	242	Birmensdorf (ZH)	Birmensdorf (ZH)	Bezirk Dietikon	Zürich	01.01.1990
ZH	111	243	Dietikon	Dietikon	Bezirk Dietikon	Zürich	01.01.1990
ZH	111	244	Geroldswil	Geroldswil	Bezirk Dietikon	Zürich	01.01.1990
ZH	111	245	Oberengstringen	Oberengstringen	Bezirk Dietikon	Zürich	01.01.1990
ZH	111	246	Oetwil an der Limmat	Oetwil an der Limmat	Bezirk Dietikon	Zürich	01.01.1990
ZH	111	247	Schlieren	Schlieren	Bezirk Dietikon	Zürich	01.01.1990
ZH	111	248	Uitikon	Uitikon	Bezirk Dietikon	Zürich	01.01.1990
ZH	111	249	Unterengstringen	Unterengstringen	Bezirk Dietikon	Zürich	01.01.1990
ZH	111	250	Urdorf	Urdorf	Bezirk Dietikon	Zürich	01.01.1990
ZH	111	251	Weiningen (ZH)	Weiningen (ZH)	Bezirk Dietikon	Zürich	01.01.1990
ZH	112	261	Zürich	Zürich	Bezirk Zürich	Zürich	01.01.1990
ZH	110	298	Wiesendangen	Wiesendangen	Bezirk Winterthur	Zürich	01.01.2014
BE	243	301	Aarberg	Aarberg	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	302	Bargen (BE)	Bargen (BE)	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	303	Grossaffoltern	Grossaffoltern	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	304	Kallnach	Kallnach	Verwaltungskreis Seeland	Bern / Berne	01.01.2013
BE	243	305	Kappelen	Kappelen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	306	Lyss	Lyss	Verwaltungskreis Seeland	Bern / Berne	01.01.2011
BE	246	307	Meikirch	Meikirch	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	243	309	Radelfingen	Radelfingen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	310	Rapperswil (BE)	Rapperswil (BE)	Verwaltungskreis Seeland	Bern / Berne	01.01.2013
BE	243	311	Schüpfen	Schüpfen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	312	Seedorf (BE)	Seedorf (BE)	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	244	321	Aarwangen	Aarwangen	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	322	Auswil	Auswil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	323	Bannwil	Bannwil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	324	Bleienbach	Bleienbach	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	325	Busswil bei Melchnau	Busswil bei Melchnau	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	326	Gondiswil	Gondiswil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	329	Langenthal	Langenthal	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	331	Lotzwil	Lotzwil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	332	Madiswil	Madiswil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2011
BE	244	333	Melchnau	Melchnau	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	334	Obersteckholz	Obersteckholz	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	335	Oeschenbach	Oeschenbach	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	336	Reisiswil	Reisiswil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	337	Roggwil (BE)	Roggwil (BE)	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	338	Rohrbach	Rohrbach	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	339	Rohrbachgraben	Rohrbachgraben	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	340	Rütschelen	Rütschelen	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	341	Schwarzhäusern	Schwarzhäusern	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	342	Thunstetten	Thunstetten	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	344	Ursenbach	Ursenbach	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	345	Wynau	Wynau	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	246	351	Bern	Bern	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	352	Bolligen	Bolligen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	353	Bremgarten bei Bern	Bremgarten bei Bern	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	354	Kirchlindach	Kirchlindach	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	355	Köniz	Köniz	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	356	Muri bei Bern	Muri bei Bern	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	357	Oberbalm	Oberbalm	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	358	Stettlen	Stettlen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	359	Vechigen	Vechigen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	360	Wohlen bei Bern	Wohlen bei Bern	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	361	Zollikofen	Zollikofen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	362	Ittigen	Ittigen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	363	Ostermundigen	Ostermundigen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	242	371	Biel/Bienne	Biel/Bienne	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	372	Evilard	Evilard	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	243	381	Arch	Arch	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	382	Büetigen	Büetigen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	383	Büren an der Aare	Büren an der Aare	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	385	Diessbach bei Büren	Diessbach bei Büren	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	386	Dotzigen	Dotzigen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	242	387	Lengnau (BE)	Lengnau (BE)	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	243	388	Leuzigen	Leuzigen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	389	Meienried	Meienried	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	242	390	Meinisberg	Meinisberg	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	243	391	Oberwil bei Büren	Oberwil bei Büren	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	242	392	Pieterlen	Pieterlen	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	243	393	Rüti bei Büren	Rüti bei Büren	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	394	Wengi	Wengi	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	245	401	Aefligen	Aefligen	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	402	Alchenstorf	Alchenstorf	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	246	403	Bäriswil	Bäriswil	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	245	404	Burgdorf	Burgdorf	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	405	Ersigen	Ersigen	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	406	Hasle bei Burgdorf	Hasle bei Burgdorf	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	407	Heimiswil	Heimiswil	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	408	Hellsau	Hellsau	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	409	Hindelbank	Hindelbank	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	410	Höchstetten	Höchstetten	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	411	Kernenried	Kernenried	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	412	Kirchberg (BE)	Kirchberg (BE)	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	413	Koppigen	Koppigen	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	414	Krauchthal	Krauchthal	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	415	Lyssach	Lyssach	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	416	Mötschwil	Mötschwil	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	417	Niederösch	Niederösch	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	418	Oberburg	Oberburg	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	419	Oberösch	Oberösch	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	420	Rüdtligen-Alchenflüh	Rüdtligen-Alchenflüh	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	421	Rumendingen	Rumendingen	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	422	Rüti bei Lyssach	Rüti bei Lyssach	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	423	Willadingen	Willadingen	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	424	Wynigen	Wynigen	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	241	431	Corgémont	Corgémont	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	432	Cormoret	Cormoret	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	433	Cortébert	Cortébert	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	434	Courtelary	Courtelary	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	435	La Ferrière	La Ferrière	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	436	La Heutte	La Heutte	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	437	Mont-Tramelan	Mont-Tramelan	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	438	Orvin	Orvin	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	439	Péry	Péry	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	441	Renan (BE)	Renan (BE)	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	442	Romont (BE)	Romont (BE)	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	443	Saint-Imier	Saint-Imier	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	444	Sonceboz-Sombeval	Sonceboz-Sombeval	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	445	Sonvilier	Sonvilier	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	446	Tramelan	Tramelan	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	448	Villeret	Villeret	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	449	Sauge	Sauge	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2014
BE	243	491	Brüttelen	Brüttelen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	492	Erlach	Erlach	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	493	Finsterhennen	Finsterhennen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	494	Gals	Gals	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	495	Gampelen	Gampelen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	496	Ins	Ins	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	497	Lüscherz	Lüscherz	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	498	Müntschemier	Müntschemier	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	499	Siselen	Siselen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	500	Treiten	Treiten	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	501	Tschugg	Tschugg	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	502	Vinelz	Vinelz	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	532	Bangerten	Bangerten	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	245	533	Bätterkinden	Bätterkinden	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	246	535	Deisswil bei Münchenbuchsee	Deisswil b. Münchenbuch.	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	536	Diemerswil	Diemerswil	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	538	Fraubrunnen	Fraubrunnen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2014
BE	246	540	Jegenstorf	Jegenstorf	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2014
BE	246	541	Iffwil	Iffwil	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	543	Mattstetten	Mattstetten	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	544	Moosseedorf	Moosseedorf	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	546	Münchenbuchsee	Münchenbuchsee	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	551	Urtenen-Schönbühl	Urtenen-Schönbühl	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	245	552	Utzenstorf	Utzenstorf	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	246	553	Wiggiswil	Wiggiswil	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	245	554	Wiler bei Utzenstorf	Wiler bei Utzenstorf	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	556	Zielebach	Zielebach	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	246	557	Zuzwil (BE)	Zuzwil (BE)	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	249	561	Adelboden	Adelboden	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	562	Aeschi bei Spiez	Aeschi bei Spiez	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	563	Frutigen	Frutigen	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	564	Kandergrund	Kandergrund	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	565	Kandersteg	Kandersteg	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	566	Krattigen	Krattigen	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	567	Reichenbach im Kandertal	Reichenbach im Kandertal	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	250	571	Beatenberg	Beatenberg	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	572	Bönigen	Bönigen	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	573	Brienz (BE)	Brienz (BE)	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	574	Brienzwiler	Brienzwiler	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	575	Därligen	Därligen	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	576	Grindelwald	Grindelwald	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	577	Gsteigwiler	Gsteigwiler	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	578	Gündlischwand	Gündlischwand	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	579	Habkern	Habkern	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	580	Hofstetten bei Brienz	Hofstetten bei Brienz	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	581	Interlaken	Interlaken	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	582	Iseltwald	Iseltwald	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	584	Lauterbrunnen	Lauterbrunnen	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	585	Leissigen	Leissigen	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	586	Lütschental	Lütschental	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	587	Matten bei Interlaken	Matten bei Interlaken	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	588	Niederried bei Interlaken	Niederried b. Interlaken	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	589	Oberried am Brienzersee	Oberried am Brienzersee	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	590	Ringgenberg (BE)	Ringgenberg (BE)	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	591	Saxeten	Saxeten	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	592	Schwanden bei Brienz	Schwanden bei Brienz	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	593	Unterseen	Unterseen	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	594	Wilderswil	Wilderswil	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	246	602	Arni (BE)	Arni (BE)	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	603	Biglen	Biglen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	605	Bowil	Bowil	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	606	Brenzikofen	Brenzikofen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	607	Freimettigen	Freimettigen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	608	Grosshöchstetten	Grosshöchstetten	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	609	Häutligen	Häutligen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	610	Herbligen	Herbligen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	611	Kiesen	Kiesen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	612	Konolfingen	Konolfingen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	613	Landiswil	Landiswil	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	614	Linden	Linden	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	615	Mirchel	Mirchel	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	616	Münsingen	Münsingen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2013
BE	246	617	Niederhünigen	Niederhünigen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	619	Oberdiessbach	Oberdiessbach	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2014
BE	246	620	Oberthal	Oberthal	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	622	Oppligen	Oppligen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	623	Rubigen	Rubigen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	624	Schlosswil	Schlosswil	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	625	Tägertschi	Tägertschi	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	626	Walkringen	Walkringen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	627	Worb	Worb	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	628	Zäziwil	Zäziwil	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	629	Oberhünigen	Oberhünigen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	630	Allmendingen	Allmendingen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	632	Wichtrach	Wichtrach	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	661	Clavaleyres	Clavaleyres	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	662	Ferenbalm	Ferenbalm	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	663	Frauenkappelen	Frauenkappelen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	664	Golaten	Golaten	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	665	Gurbrü	Gurbrü	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	666	Kriechenwil	Kriechenwil	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	667	Laupen	Laupen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	668	Mühleberg	Mühleberg	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	669	Münchenwiler	Münchenwiler	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	670	Neuenegg	Neuenegg	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	671	Wileroltigen	Wileroltigen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	241	681	Belprahon	Belprahon	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	682	Bévilard	Bévilard	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	683	Champoz	Champoz	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	684	Châtelat	Châtelat	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	687	Corcelles (BE)	Corcelles (BE)	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	690	Court	Court	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	691	Crémines	Crémines	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	692	Eschert	Eschert	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	694	Grandval	Grandval	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	696	Loveresse	Loveresse	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	697	Malleray	Malleray	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	699	Monible	Monible	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	700	Moutier	Moutier	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	701	Perrefitte	Perrefitte	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	702	Pontenet	Pontenet	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	703	Reconvilier	Reconvilier	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	704	Roches (BE)	Roches (BE)	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	706	Saicourt	Saicourt	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	707	Saules (BE)	Saules (BE)	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	708	Schelten	Schelten	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	709	Seehof	Seehof	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	710	Sornetan	Sornetan	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	711	Sorvilier	Sorvilier	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	712	Souboz	Souboz	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	713	Tavannes	Tavannes	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	715	Rebévelier	Rebévelier	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	723	La Neuveville	La Neuveville	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	724	Nods	Nods	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2010
BE	241	726	Plateau de Diesse	Plateau de Diesse	Arrondissement administratif Jura bernois	Bern / Berne	01.01.2014
BE	242	731	Aegerten	Aegerten	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	732	Bellmund	Bellmund	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	733	Brügg	Brügg	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	243	734	Bühl	Bühl	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	735	Epsach	Epsach	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	736	Hagneck	Hagneck	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	737	Hermrigen	Hermrigen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	738	Jens	Jens	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	242	739	Ipsach	Ipsach	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	740	Ligerz	Ligerz	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	243	741	Merzligen	Merzligen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	242	742	Mörigen	Mörigen	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	743	Nidau	Nidau	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	744	Orpund	Orpund	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	745	Port	Port	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	746	Safnern	Safnern	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	747	Scheuren	Scheuren	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	242	748	Schwadernau	Schwadernau	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	243	749	Studen (BE)	Studen (BE)	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	242	750	Sutz-Lattrigen	Sutz-Lattrigen	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	243	751	Täuffelen	Täuffelen	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	754	Walperswil	Walperswil	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	243	755	Worben	Worben	Verwaltungskreis Seeland	Bern / Berne	01.01.2010
BE	242	756	Twann-Tüscherz	Twann-Tüscherz	Verwaltungskreis Biel/Bienne	Bern / Berne	01.01.2010
BE	249	761	Därstetten	Därstetten	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	762	Diemtigen	Diemtigen	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	763	Erlenbach im Simmental	Erlenbach im Simmental	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	766	Oberwil im Simmental	Oberwil im Simmental	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	247	767	Reutigen	Reutigen	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	249	768	Spiez	Spiez	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	249	769	Wimmis	Wimmis	Verwaltungskreis Frutigen-Niedersimmental	Bern / Berne	01.01.2010
BE	247	770	Stocken-Höfen	Stocken-Höfen	Verwaltungskreis Thun	Bern / Berne	01.01.2014
BE	250	782	Guttannen	Guttannen	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	783	Hasliberg	Hasliberg	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	784	Innertkirchen	Innertkirchen	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2014
BE	250	785	Meiringen	Meiringen	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	250	786	Schattenhalb	Schattenhalb	Verwaltungskreis Interlaken-Oberhasli	Bern / Berne	01.01.2010
BE	248	791	Boltigen	Boltigen	Verwaltungskreis Obersimmental-Saanen	Bern / Berne	01.01.2010
BE	248	792	Lenk	Lenk	Verwaltungskreis Obersimmental-Saanen	Bern / Berne	01.01.2010
BE	248	793	St. Stephan	St. Stephan	Verwaltungskreis Obersimmental-Saanen	Bern / Berne	01.01.2010
BE	248	794	Zweisimmen	Zweisimmen	Verwaltungskreis Obersimmental-Saanen	Bern / Berne	01.01.2010
BE	248	841	Gsteig	Gsteig	Verwaltungskreis Obersimmental-Saanen	Bern / Berne	01.01.2010
BE	248	842	Lauenen	Lauenen	Verwaltungskreis Obersimmental-Saanen	Bern / Berne	01.01.2010
BE	248	843	Saanen	Saanen	Verwaltungskreis Obersimmental-Saanen	Bern / Berne	01.01.2010
BE	246	852	Guggisberg	Guggisberg	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	853	Rüschegg	Rüschegg	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	855	Schwarzenburg	Schwarzenburg	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2011
BE	246	861	Belp	Belp	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2012
BE	247	863	Burgistein	Burgistein	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	246	865	Gelterfingen	Gelterfingen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	866	Gerzensee	Gerzensee	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	247	867	Gurzelen	Gurzelen	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	246	868	Jaberg	Jaberg	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	869	Kaufdorf	Kaufdorf	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	870	Kehrsatz	Kehrsatz	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	872	Kirchdorf (BE)	Kirchdorf (BE)	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	873	Kirchenthurnen	Kirchenthurnen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	874	Lohnstorf	Lohnstorf	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	875	Mühledorf (BE)	Mühledorf (BE)	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	876	Mühlethurnen	Mühlethurnen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	877	Niedermuhlern	Niedermuhlern	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	878	Noflen	Noflen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	879	Riggisberg	Riggisberg	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	880	Rüeggisberg	Rüeggisberg	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	246	881	Rümligen	Rümligen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	247	883	Seftigen	Seftigen	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	246	884	Toffen	Toffen	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	247	885	Uttigen	Uttigen	Verwaltungskreis Thun	Bern / Berne	01.01.2014
BE	247	886	Wattenwil	Wattenwil	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	246	888	Wald (BE)	Wald (BE)	Verwaltungskreis Bern-Mittelland	Bern / Berne	01.01.2010
BE	245	901	Eggiwil	Eggiwil	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	902	Langnau im Emmental	Langnau im Emmental	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	903	Lauperswil	Lauperswil	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	904	Röthenbach im Emmental	Röthenbach im Emmental	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	905	Rüderswil	Rüderswil	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	906	Schangnau	Schangnau	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	907	Signau	Signau	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	908	Trub	Trub	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	909	Trubschachen	Trubschachen	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	247	921	Amsoldingen	Amsoldingen	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	922	Blumenstein	Blumenstein	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	923	Buchholterberg	Buchholterberg	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	924	Eriz	Eriz	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	925	Fahrni	Fahrni	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	927	Heiligenschwendi	Heiligenschwendi	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	928	Heimberg	Heimberg	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	929	Hilterfingen	Hilterfingen	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	931	Homberg	Homberg	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	932	Horrenbach-Buchen	Horrenbach-Buchen	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	934	Oberhofen am Thunersee	Oberhofen am Thunersee	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	935	Oberlangenegg	Oberlangenegg	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	936	Pohlern	Pohlern	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	937	Schwendibach	Schwendibach	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	938	Sigriswil	Sigriswil	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	939	Steffisburg	Steffisburg	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	940	Teuffenthal (BE)	Teuffenthal (BE)	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	941	Thierachern	Thierachern	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	942	Thun	Thun	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	943	Uebeschi	Uebeschi	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	944	Uetendorf	Uetendorf	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	945	Unterlangenegg	Unterlangenegg	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	946	Wachseldorn	Wachseldorn	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	947	Zwieselberg	Zwieselberg	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	247	948	Forst-Längenbühl	Forst-Längenbühl	Verwaltungskreis Thun	Bern / Berne	01.01.2010
BE	245	951	Affoltern im Emmental	Affoltern im Emmental	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	952	Dürrenroth	Dürrenroth	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	244	953	Eriswil	Eriswil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	954	Huttwil	Huttwil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	245	955	Lützelflüh	Lützelflüh	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	956	Rüegsau	Rüegsau	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	957	Sumiswald	Sumiswald	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	245	958	Trachselwald	Trachselwald	Verwaltungskreis Emmental	Bern / Berne	01.01.2010
BE	244	959	Walterswil (BE)	Walterswil (BE)	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	960	Wyssachen	Wyssachen	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	971	Attiswil	Attiswil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	972	Berken	Berken	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	973	Bettenhausen	Bettenhausen	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2011
BE	244	975	Farnern	Farnern	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	976	Graben	Graben	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	977	Heimenhausen	Heimenhausen	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	978	Hermiswil	Hermiswil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	979	Herzogenbuchsee	Herzogenbuchsee	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	980	Inkwil	Inkwil	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	981	Niederbipp	Niederbipp	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	982	Niederönz	Niederönz	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	983	Oberbipp	Oberbipp	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	985	Ochlenberg	Ochlenberg	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	987	Rumisberg	Rumisberg	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	988	Seeberg	Seeberg	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	989	Thörigen	Thörigen	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	990	Walliswil bei Niederbipp	Walliswil bei Niederbipp	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	991	Walliswil bei Wangen	Walliswil bei Wangen	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	992	Wangen an der Aare	Wangen an der Aare	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	993	Wangenried	Wangenried	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	995	Wiedlisbach	Wiedlisbach	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
BE	244	996	Wolfisberg	Wolfisberg	Verwaltungskreis Oberaargau	Bern / Berne	01.01.2010
LU	316	1001	Doppleschwand	Doppleschwand	Wahlkreis Entlebuch	Luzern	01.01.2013
LU	316	1002	Entlebuch	Entlebuch	Wahlkreis Entlebuch	Luzern	01.01.2013
LU	316	1004	Flühli	Flühli	Wahlkreis Entlebuch	Luzern	01.01.2013
LU	316	1005	Hasle (LU)	Hasle (LU)	Wahlkreis Entlebuch	Luzern	01.01.2013
LU	316	1007	Romoos	Romoos	Wahlkreis Entlebuch	Luzern	01.01.2013
LU	316	1008	Schüpfheim	Schüpfheim	Wahlkreis Entlebuch	Luzern	01.01.2013
LU	316	1009	Werthenstein	Werthenstein	Wahlkreis Entlebuch	Luzern	01.01.2013
LU	316	1010	Escholzmatt-Marbach	Escholzmatt-Marbach	Wahlkreis Entlebuch	Luzern	01.01.2013
LU	313	1021	Aesch (LU)	Aesch (LU)	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1022	Altwis	Altwis	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1023	Ballwil	Ballwil	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1024	Emmen	Emmen	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1025	Ermensee	Ermensee	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1026	Eschenbach (LU)	Eschenbach (LU)	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1030	Hitzkirch	Hitzkirch	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1031	Hochdorf	Hochdorf	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1032	Hohenrain	Hohenrain	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1033	Inwil	Inwil	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1037	Rain	Rain	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1039	Römerswil	Römerswil	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1040	Rothenburg	Rothenburg	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	313	1041	Schongau	Schongau	Wahlkreis Hochdorf	Luzern	01.01.2013
LU	312	1051	Adligenswil	Adligenswil	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1052	Buchrain	Buchrain	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1053	Dierikon	Dierikon	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1054	Ebikon	Ebikon	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1055	Gisikon	Gisikon	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1056	Greppen	Greppen	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1057	Honau	Honau	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1058	Horw	Horw	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1059	Kriens	Kriens	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	311	1061	Luzern	Luzern	Wahlkreis Luzern-Stadt	Luzern	01.01.2013
LU	312	1062	Malters	Malters	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1063	Meggen	Meggen	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1064	Meierskappel	Meierskappel	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1065	Root	Root	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1066	Schwarzenberg	Schwarzenberg	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1067	Udligenswil	Udligenswil	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1068	Vitznau	Vitznau	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	312	1069	Weggis	Weggis	Wahlkreis Luzern-Land	Luzern	01.01.2013
LU	314	1081	Beromünster	Beromünster	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1082	Büron	Büron	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1083	Buttisholz	Buttisholz	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1084	Eich	Eich	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1085	Geuensee	Geuensee	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1086	Grosswangen	Grosswangen	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1088	Hildisrieden	Hildisrieden	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1089	Knutwil	Knutwil	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1091	Mauensee	Mauensee	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1093	Neuenkirch	Neuenkirch	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1094	Nottwil	Nottwil	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1095	Oberkirch	Oberkirch	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1097	Rickenbach (LU)	Rickenbach (LU)	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1098	Ruswil	Ruswil	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1099	Schenkon	Schenkon	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1100	Schlierbach	Schlierbach	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1102	Sempach	Sempach	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1103	Sursee	Sursee	Wahlkreis Sursee	Luzern	01.01.2013
LU	314	1104	Triengen	Triengen	Wahlkreis Sursee	Luzern	01.01.2013
LU	316	1107	Wolhusen	Wolhusen	Wahlkreis Entlebuch	Luzern	01.01.2013
LU	315	1121	Alberswil	Alberswil	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1122	Altbüron	Altbüron	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1123	Altishofen	Altishofen	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1125	Dagmersellen	Dagmersellen	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1126	Ebersecken	Ebersecken	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1127	Egolzwil	Egolzwil	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1128	Ettiswil	Ettiswil	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1129	Fischbach	Fischbach	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1130	Gettnau	Gettnau	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1131	Grossdietwil	Grossdietwil	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1132	Hergiswil bei Willisau	Hergiswil bei Willisau	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1135	Luthern	Luthern	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1136	Menznau	Menznau	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1137	Nebikon	Nebikon	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1139	Pfaffnau	Pfaffnau	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1140	Reiden	Reiden	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1142	Roggliswil	Roggliswil	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1143	Schötz	Schötz	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1145	Ufhusen	Ufhusen	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1146	Wauwil	Wauwil	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1147	Wikon	Wikon	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1150	Zell (LU)	Zell (LU)	Wahlkreis Willisau	Luzern	01.01.2013
LU	315	1151	Willisau	Willisau	Wahlkreis Willisau	Luzern	01.01.2013
UR	400	1201	Altdorf (UR)	Altdorf (UR)	Kanton Uri	Uri	01.01.1960
UR	400	1202	Andermatt	Andermatt	Kanton Uri	Uri	01.01.1960
UR	400	1203	Attinghausen	Attinghausen	Kanton Uri	Uri	01.01.1960
UR	400	1204	Bauen	Bauen	Kanton Uri	Uri	01.01.1960
UR	400	1205	Bürglen (UR)	Bürglen (UR)	Kanton Uri	Uri	01.01.1960
UR	400	1206	Erstfeld	Erstfeld	Kanton Uri	Uri	01.01.1960
UR	400	1207	Flüelen	Flüelen	Kanton Uri	Uri	01.01.1960
UR	400	1208	Göschenen	Göschenen	Kanton Uri	Uri	01.01.1960
UR	400	1209	Gurtnellen	Gurtnellen	Kanton Uri	Uri	01.01.1960
UR	400	1210	Hospental	Hospental	Kanton Uri	Uri	01.01.1960
UR	400	1211	Isenthal	Isenthal	Kanton Uri	Uri	01.01.1960
UR	400	1212	Realp	Realp	Kanton Uri	Uri	01.01.1960
UR	400	1213	Schattdorf	Schattdorf	Kanton Uri	Uri	01.01.1960
UR	400	1214	Seedorf (UR)	Seedorf (UR)	Kanton Uri	Uri	01.01.1960
UR	400	1215	Seelisberg	Seelisberg	Kanton Uri	Uri	01.01.1960
UR	400	1216	Silenen	Silenen	Kanton Uri	Uri	01.01.1960
UR	400	1217	Sisikon	Sisikon	Kanton Uri	Uri	01.01.1960
UR	400	1218	Spiringen	Spiringen	Kanton Uri	Uri	01.01.1960
UR	400	1219	Unterschächen	Unterschächen	Kanton Uri	Uri	01.01.1960
UR	400	1220	Wassen	Wassen	Kanton Uri	Uri	01.01.1960
SZ	501	1301	Einsiedeln	Einsiedeln	Bezirk Einsiedeln	Schwyz	01.01.1960
SZ	502	1311	Gersau	Gersau	Bezirk Gersau	Schwyz	01.01.1960
SZ	503	1321	Feusisberg	Feusisberg	Bezirk Höfe	Schwyz	01.01.1960
SZ	503	1322	Freienbach	Freienbach	Bezirk Höfe	Schwyz	01.01.1960
SZ	503	1323	Wollerau	Wollerau	Bezirk Höfe	Schwyz	01.01.1960
SZ	504	1331	Küssnacht (SZ)	Küssnacht (SZ)	Bezirk Küssnacht (SZ)	Schwyz	01.01.2004
SZ	505	1341	Altendorf	Altendorf	Bezirk March	Schwyz	01.01.1960
SZ	505	1342	Galgenen	Galgenen	Bezirk March	Schwyz	01.01.1960
SZ	505	1343	Innerthal	Innerthal	Bezirk March	Schwyz	01.01.1960
SZ	505	1344	Lachen	Lachen	Bezirk March	Schwyz	01.01.1960
SZ	505	1345	Reichenburg	Reichenburg	Bezirk March	Schwyz	01.01.1960
SZ	505	1346	Schübelbach	Schübelbach	Bezirk March	Schwyz	01.01.1960
SZ	505	1347	Tuggen	Tuggen	Bezirk March	Schwyz	01.01.1960
SZ	505	1348	Vorderthal	Vorderthal	Bezirk March	Schwyz	01.01.1960
SZ	505	1349	Wangen (SZ)	Wangen (SZ)	Bezirk March	Schwyz	01.01.1960
SZ	506	1361	Alpthal	Alpthal	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1362	Arth	Arth	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1363	Illgau	Illgau	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1364	Ingenbohl	Ingenbohl	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1365	Lauerz	Lauerz	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1366	Morschach	Morschach	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1367	Muotathal	Muotathal	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1368	Oberiberg	Oberiberg	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1369	Riemenstalden	Riemenstalden	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1370	Rothenthurm	Rothenthurm	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1371	Sattel	Sattel	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1372	Schwyz	Schwyz	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1373	Steinen	Steinen	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1374	Steinerberg	Steinerberg	Bezirk Schwyz	Schwyz	01.01.1960
SZ	506	1375	Unteriberg	Unteriberg	Bezirk Schwyz	Schwyz	01.01.1960
OW	600	1401	Alpnach	Alpnach	Kanton Obwalden	Obwalden	01.01.1960
OW	600	1402	Engelberg	Engelberg	Kanton Obwalden	Obwalden	01.01.1960
OW	600	1403	Giswil	Giswil	Kanton Obwalden	Obwalden	01.01.1960
OW	600	1404	Kerns	Kerns	Kanton Obwalden	Obwalden	01.01.1960
OW	600	1405	Lungern	Lungern	Kanton Obwalden	Obwalden	01.01.1960
OW	600	1406	Sachseln	Sachseln	Kanton Obwalden	Obwalden	01.01.1960
OW	600	1407	Sarnen	Sarnen	Kanton Obwalden	Obwalden	01.01.1960
NW	700	1501	Beckenried	Beckenried	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1502	Buochs	Buochs	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1503	Dallenwil	Dallenwil	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1504	Emmetten	Emmetten	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1505	Ennetbürgen	Ennetbürgen	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1506	Ennetmoos	Ennetmoos	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1507	Hergiswil (NW)	Hergiswil (NW)	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1508	Oberdorf (NW)	Oberdorf (NW)	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1509	Stans	Stans	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1510	Stansstad	Stansstad	Kanton Nidwalden	Nidwalden	01.01.1960
NW	700	1511	Wolfenschiessen	Wolfenschiessen	Kanton Nidwalden	Nidwalden	01.01.1960
GL	800	1630	Glarus Nord	Glarus Nord	Kanton Glarus	Glarus	01.01.2011
GL	800	1631	Glarus Süd	Glarus Süd	Kanton Glarus	Glarus	01.01.2011
GL	800	1632	Glarus	Glarus	Kanton Glarus	Glarus	01.01.2011
ZG	900	1701	Baar	Baar	Kanton Zug	Zug	01.01.1960
ZG	900	1702	Cham	Cham	Kanton Zug	Zug	01.01.1960
ZG	900	1703	Hünenberg	Hünenberg	Kanton Zug	Zug	01.01.1960
ZG	900	1704	Menzingen	Menzingen	Kanton Zug	Zug	01.01.1960
ZG	900	1705	Neuheim	Neuheim	Kanton Zug	Zug	01.01.1960
ZG	900	1706	Oberägeri	Oberägeri	Kanton Zug	Zug	01.01.1960
ZG	900	1707	Risch	Risch	Kanton Zug	Zug	01.01.1960
ZG	900	1708	Steinhausen	Steinhausen	Kanton Zug	Zug	01.01.1960
ZG	900	1709	Unterägeri	Unterägeri	Kanton Zug	Zug	01.01.1960
ZG	900	1710	Walchwil	Walchwil	Kanton Zug	Zug	01.01.1960
ZG	900	1711	Zug	Zug	Kanton Zug	Zug	01.01.1960
FR	1001	2004	Bussy (FR)	Bussy (FR)	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2005	Châbles	Châbles	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2008	Châtillon (FR)	Châtillon (FR)	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2009	Cheiry	Cheiry	District de la Broye	Fribourg / Freiburg	01.01.2005
FR	1001	2010	Cheyres	Cheyres	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2011	Cugy (FR)	Cugy (FR)	District de la Broye	Fribourg / Freiburg	01.01.2005
FR	1001	2013	Domdidier	Domdidier	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2014	Dompierre (FR)	Dompierre (FR)	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2015	Estavayer-le-Lac	Estavayer-le-Lac	District de la Broye	Fribourg / Freiburg	01.01.2012
FR	1001	2016	Fétigny	Fétigny	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2022	Gletterens	Gletterens	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2024	Léchelles	Léchelles	District de la Broye	Fribourg / Freiburg	01.09.1994
FR	1001	2025	Lully (FR)	Lully (FR)	District de la Broye	Fribourg / Freiburg	01.01.2006
FR	1001	2027	Ménières	Ménières	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2029	Montagny (FR)	Montagny (FR)	District de la Broye	Fribourg / Freiburg	01.01.2004
FR	1001	2033	Morens (FR)	Morens (FR)	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2034	Murist	Murist	District de la Broye	Fribourg / Freiburg	01.01.1992
FR	1001	2035	Nuvilly	Nuvilly	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2038	Prévondavaux	Prévondavaux	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2039	Rueyres-les-Prés	Rueyres-les-Prés	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2040	Russy	Russy	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2041	Saint-Aubin (FR)	Saint-Aubin (FR)	District de la Broye	Fribourg / Freiburg	01.01.1991
FR	1001	2043	Sévaz	Sévaz	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2044	Surpierre	Surpierre	District de la Broye	Fribourg / Freiburg	01.01.2005
FR	1001	2045	Vallon	Vallon	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2047	Villeneuve (FR)	Villeneuve (FR)	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2049	Vuissens	Vuissens	District de la Broye	Fribourg / Freiburg	01.01.1960
FR	1001	2050	Les Montets	Les Montets	District de la Broye	Fribourg / Freiburg	01.01.2004
FR	1001	2051	Delley-Portalban	Delley-Portalban	District de la Broye	Fribourg / Freiburg	01.01.2005
FR	1001	2052	Vernay	Vernay	District de la Broye	Fribourg / Freiburg	01.01.2006
FR	1002	2061	Auboranges	Auboranges	District de la Glâne	Fribourg / Freiburg	01.01.1960
FR	1002	2063	Billens-Hennens	Billens-Hennens	District de la Glâne	Fribourg / Freiburg	01.01.1998
FR	1002	2066	Chapelle (Glâne)	Chapelle (Glâne)	District de la Glâne	Fribourg / Freiburg	01.01.1960
FR	1002	2067	Le Châtelard	Le Châtelard	District de la Glâne	Fribourg / Freiburg	01.01.1960
FR	1002	2068	Châtonnaye	Châtonnaye	District de la Glâne	Fribourg / Freiburg	01.01.1960
FR	1002	2072	Ecublens (FR)	Ecublens (FR)	District de la Glâne	Fribourg / Freiburg	01.03.1969
FR	1002	2079	Grangettes	Grangettes	District de la Glâne	Fribourg / Freiburg	01.01.1960
FR	1002	2086	Massonnens	Massonnens	District de la Glâne	Fribourg / Freiburg	01.01.1960
FR	1002	2087	Mézières (FR)	Mézières (FR)	District de la Glâne	Fribourg / Freiburg	01.01.2004
FR	1002	2089	Montet (Glâne)	Montet (Glâne)	District de la Glâne	Fribourg / Freiburg	01.01.1960
FR	1002	2096	Romont (FR)	Romont (FR)	District de la Glâne	Fribourg / Freiburg	01.01.1981
FR	1002	2097	Rue	Rue	District de la Glâne	Fribourg / Freiburg	01.01.2001
FR	1002	2099	Siviriez	Siviriez	District de la Glâne	Fribourg / Freiburg	01.01.2004
FR	1002	2102	Ursy	Ursy	District de la Glâne	Fribourg / Freiburg	01.01.2012
FR	1002	2111	Villaz-Saint-Pierre	Villaz-Saint-Pierre	District de la Glâne	Fribourg / Freiburg	01.01.1978
FR	1002	2113	Vuisternens-devant-Romont	Vuisternens-dev-Romont	District de la Glâne	Fribourg / Freiburg	01.01.2004
FR	1002	2114	Villorsonnens	Villorsonnens	District de la Glâne	Fribourg / Freiburg	01.01.2001
FR	1002	2115	Torny	Torny	District de la Glâne	Fribourg / Freiburg	01.01.2004
FR	1002	2116	La Folliaz	La Folliaz	District de la Glâne	Fribourg / Freiburg	01.01.2005
FR	1003	2121	Haut-Intyamon	Haut-Intyamon	District de la Gruyère	Fribourg / Freiburg	01.01.2002
FR	1003	2122	Pont-en-Ogoz	Pont-en-Ogoz	District de la Gruyère	Fribourg / Freiburg	01.01.2003
FR	1003	2123	Botterens	Botterens	District de la Gruyère	Fribourg / Freiburg	01.01.2006
FR	1003	2124	Broc	Broc	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2125	Bulle	Bulle	District de la Gruyère	Fribourg / Freiburg	01.01.2006
FR	1003	2128	Châtel-sur-Montsalvens	Châtel-sur-Montsalvens	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2129	Corbières	Corbières	District de la Gruyère	Fribourg / Freiburg	01.01.2011
FR	1003	2130	Crésuz	Crésuz	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2131	Echarlens	Echarlens	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2134	Grandvillard	Grandvillard	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2135	Gruyères	Gruyères	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2137	Hauteville	Hauteville	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2138	Jaun	Jaun	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2140	Marsens	Marsens	District de la Gruyère	Fribourg / Freiburg	01.01.2001
FR	1003	2143	Morlon	Morlon	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2145	Le Pâquier (FR)	Le Pâquier (FR)	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2147	Pont-la-Ville	Pont-la-Ville	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2148	Riaz	Riaz	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2149	La Roche	La Roche	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2152	Sâles	Sâles	District de la Gruyère	Fribourg / Freiburg	01.01.2001
FR	1003	2153	Sorens	Sorens	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2155	Vaulruz	Vaulruz	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2160	Vuadens	Vuadens	District de la Gruyère	Fribourg / Freiburg	01.01.1960
FR	1003	2162	Bas-Intyamon	Bas-Intyamon	District de la Gruyère	Fribourg / Freiburg	01.01.2004
FR	1003	2163	Val-de-Charmey	Val-de-Charmey	District de la Gruyère	Fribourg / Freiburg	01.01.2014
FR	1004	2171	Arconciel	Arconciel	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2172	Autafond	Autafond	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2173	Autigny	Autigny	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2174	Avry	Avry	District de la Sarine	Fribourg / Freiburg	01.01.2001
FR	1004	2175	Belfaux	Belfaux	District de la Sarine	Fribourg / Freiburg	01.01.1977
FR	1004	2177	Chénens	Chénens	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2179	Chésopelloz	Chésopelloz	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2183	Corminboeuf	Corminboeuf	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2184	Corpataux-Magnedens	Corpataux-Magnedens	District de la Sarine	Fribourg / Freiburg	01.01.1999
FR	1004	2185	Corserey	Corserey	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2186	Cottens (FR)	Cottens (FR)	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2189	Ependes (FR)	Ependes (FR)	District de la Sarine	Fribourg / Freiburg	01.01.1977
FR	1004	2192	Farvagny	Farvagny	District de la Sarine	Fribourg / Freiburg	01.01.1996
FR	1004	2194	Ferpicloz	Ferpicloz	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2196	Fribourg	Fribourg	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2197	Givisiez	Givisiez	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2198	Granges-Paccot	Granges-Paccot	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2200	Grolley	Grolley	District de la Sarine	Fribourg / Freiburg	01.01.2000
FR	1004	2206	Marly	Marly	District de la Sarine	Fribourg / Freiburg	01.01.1976
FR	1004	2208	Matran	Matran	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2211	Neyruz (FR)	Neyruz (FR)	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2213	Noréaz	Noréaz	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2216	Pierrafortscha	Pierrafortscha	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2217	Ponthaux	Ponthaux	District de la Sarine	Fribourg / Freiburg	01.01.1981
FR	1004	2220	Le Mouret	Le Mouret	District de la Sarine	Fribourg / Freiburg	01.01.2003
FR	1004	2221	Prez-vers-Noréaz	Prez-vers-Noréaz	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2222	Rossens (FR)	Rossens (FR)	District de la Sarine	Fribourg / Freiburg	01.06.1972
FR	1004	2223	Le Glèbe	Le Glèbe	District de la Sarine	Fribourg / Freiburg	01.01.2003
FR	1004	2225	Senèdes	Senèdes	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2226	Treyvaux	Treyvaux	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2228	Villars-sur-Glâne	Villars-sur-Glâne	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2230	Villarsel-sur-Marly	Villarsel-sur-Marly	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2231	Vuisternens-en-Ogoz	Vuisternens-en-Ogoz	District de la Sarine	Fribourg / Freiburg	01.01.1960
FR	1004	2233	Hauterive (FR)	Hauterive (FR)	District de la Sarine	Fribourg / Freiburg	01.01.2001
FR	1004	2234	La Brillaz	La Brillaz	District de la Sarine	Fribourg / Freiburg	01.01.2001
FR	1004	2235	La Sonnaz	La Sonnaz	District de la Sarine	Fribourg / Freiburg	01.01.2004
FR	1005	2243	Barberêche	Barberêche	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2250	Courgevaux	Courgevaux	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2251	Courlevon	Courlevon	Bezirk See / District du Lac	Fribourg / Freiburg	15.02.1974
FR	1005	2254	Courtepin	Courtepin	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.2003
FR	1005	2257	Cressier (FR)	Cressier (FR)	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2258	Fräschels	Fräschels	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2259	Galmiz	Galmiz	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2260	Gempenach	Gempenach	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2261	Greng	Greng	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2262	Gurmels	Gurmels	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.2005
FR	1005	2264	Jeuss	Jeuss	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2265	Kerzers	Kerzers	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2266	Kleinbösingen	Kleinbösingen	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2270	Lurtigen	Lurtigen	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2271	Meyriez	Meyriez	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2272	Misery-Courtion	Misery-Courtion	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1997
FR	1005	2274	Muntelier	Muntelier	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2275	Murten	Murten	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.2013
FR	1005	2276	Ried bei Kerzers	Ried bei Kerzers	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.2006
FR	1005	2277	Salvenach	Salvenach	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2278	Ulmiz	Ulmiz	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1005	2279	Villarepos	Villarepos	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1983
FR	1005	2280	Bas-Vully	Bas-Vully	Bezirk See / District du Lac	Fribourg / Freiburg	24.05.1977
FR	1005	2281	Haut-Vully	Haut-Vully	Bezirk See / District du Lac	Fribourg / Freiburg	24.05.1977
FR	1005	2283	Wallenried	Wallenried	Bezirk See / District du Lac	Fribourg / Freiburg	01.01.1960
FR	1006	2291	Alterswil	Alterswil	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2292	Brünisried	Brünisried	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2293	Düdingen	Düdingen	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2294	Giffers	Giffers	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2295	Bösingen	Bösingen	Bezirk Sense	Fribourg / Freiburg	01.01.1962
FR	1006	2296	Heitenried	Heitenried	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2298	Oberschrot	Oberschrot	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2299	Plaffeien	Plaffeien	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2300	Plasselb	Plasselb	Bezirk Sense	Fribourg / Freiburg	01.01.1971
FR	1006	2301	Rechthalten	Rechthalten	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2302	St. Antoni	St. Antoni	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2303	St. Silvester	St. Silvester	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2304	St. Ursen	St. Ursen	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2305	Schmitten (FR)	Schmitten (FR)	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2306	Tafers	Tafers	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2307	Tentlingen	Tentlingen	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2308	Ueberstorf	Ueberstorf	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1006	2309	Wünnewil-Flamatt	Wünnewil-Flamatt	Bezirk Sense	Fribourg / Freiburg	01.01.1974
FR	1006	2310	Zumholz	Zumholz	Bezirk Sense	Fribourg / Freiburg	01.01.1960
FR	1007	2321	Attalens	Attalens	District de la Veveyse	Fribourg / Freiburg	01.01.1960
FR	1007	2323	Bossonnens	Bossonnens	District de la Veveyse	Fribourg / Freiburg	01.01.1960
FR	1007	2325	Châtel-Saint-Denis	Châtel-Saint-Denis	District de la Veveyse	Fribourg / Freiburg	01.01.1960
FR	1007	2328	Granges (Veveyse)	Granges (Veveyse)	District de la Veveyse	Fribourg / Freiburg	01.01.1960
FR	1007	2333	Remaufens	Remaufens	District de la Veveyse	Fribourg / Freiburg	01.01.1960
FR	1007	2335	Saint-Martin (FR)	Saint-Martin (FR)	District de la Veveyse	Fribourg / Freiburg	01.01.2004
FR	1007	2336	Semsales	Semsales	District de la Veveyse	Fribourg / Freiburg	01.01.1968
FR	1007	2337	Le Flon	Le Flon	District de la Veveyse	Fribourg / Freiburg	01.01.2004
FR	1007	2338	La Verrerie	La Verrerie	District de la Veveyse	Fribourg / Freiburg	01.01.2004
SO	1101	2401	Egerkingen	Egerkingen	Bezirk Gäu	Solothurn	01.01.1991
SO	1101	2402	Härkingen	Härkingen	Bezirk Gäu	Solothurn	01.01.1991
SO	1101	2403	Kestenholz	Kestenholz	Bezirk Gäu	Solothurn	01.01.1991
SO	1101	2404	Neuendorf	Neuendorf	Bezirk Gäu	Solothurn	01.01.1991
SO	1101	2405	Niederbuchsiten	Niederbuchsiten	Bezirk Gäu	Solothurn	01.01.1991
SO	1101	2406	Oberbuchsiten	Oberbuchsiten	Bezirk Gäu	Solothurn	01.01.1991
SO	1101	2407	Oensingen	Oensingen	Bezirk Gäu	Solothurn	01.01.1991
SO	1101	2408	Wolfwil	Wolfwil	Bezirk Gäu	Solothurn	01.01.1991
SO	1102	2421	Aedermannsdorf	Aedermannsdorf	Bezirk Thal	Solothurn	01.01.1991
SO	1102	2422	Balsthal	Balsthal	Bezirk Thal	Solothurn	01.01.1991
SO	1102	2423	Gänsbrunnen	Gänsbrunnen	Bezirk Thal	Solothurn	01.01.1991
SO	1102	2424	Herbetswil	Herbetswil	Bezirk Thal	Solothurn	01.01.1991
SO	1102	2425	Holderbank (SO)	Holderbank (SO)	Bezirk Thal	Solothurn	01.01.1991
SO	1102	2426	Laupersdorf	Laupersdorf	Bezirk Thal	Solothurn	01.01.1991
SO	1102	2427	Matzendorf	Matzendorf	Bezirk Thal	Solothurn	01.01.1991
SO	1102	2428	Mümliswil-Ramiswil	Mümliswil-Ramiswil	Bezirk Thal	Solothurn	01.01.1991
SO	1102	2429	Welschenrohr	Welschenrohr	Bezirk Thal	Solothurn	01.01.1991
SO	1103	2445	Biezwil	Biezwil	Bezirk Bucheggberg	Solothurn	01.01.1960
SO	1103	2455	Lüterkofen-Ichertswil	Lüterkofen-Ichertswil	Bezirk Bucheggberg	Solothurn	01.01.1961
SO	1103	2456	Lüterswil-Gächliwil	Lüterswil-Gächliwil	Bezirk Bucheggberg	Solothurn	01.01.1995
SO	1103	2457	Messen	Messen	Bezirk Bucheggberg	Solothurn	01.01.2010
SO	1103	2461	Schnottwil	Schnottwil	Bezirk Bucheggberg	Solothurn	01.01.1960
SO	1103	2463	Unterramsern	Unterramsern	Bezirk Bucheggberg	Solothurn	01.01.1960
SO	1103	2464	Lüsslingen-Nennigkofen	Lüsslingen-Nennigkofen	Bezirk Bucheggberg	Solothurn	01.01.2013
SO	1103	2465	Buchegg	Buchegg	Bezirk Bucheggberg	Solothurn	01.01.2014
SO	1104	2471	Bättwil	Bättwil	Bezirk Dorneck	Solothurn	01.01.1960
SO	1104	2472	Büren (SO)	Büren (SO)	Bezirk Dorneck	Solothurn	01.01.1960
SO	1104	2473	Dornach	Dornach	Bezirk Dorneck	Solothurn	01.01.1960
SO	1104	2474	Gempen	Gempen	Bezirk Dorneck	Solothurn	01.01.1960
SO	1104	2475	Hochwald	Hochwald	Bezirk Dorneck	Solothurn	01.01.1960
SO	1104	2476	Hofstetten-Flüh	Hofstetten-Flüh	Bezirk Dorneck	Solothurn	01.01.1986
SO	1104	2477	Metzerlen-Mariastein	Metzerlen-Mariastein	Bezirk Dorneck	Solothurn	01.01.2004
SO	1104	2478	Nuglar-St. Pantaleon	Nuglar-St. Pantaleon	Bezirk Dorneck	Solothurn	01.01.1960
SO	1104	2479	Rodersdorf	Rodersdorf	Bezirk Dorneck	Solothurn	01.01.1960
SO	1104	2480	Seewen	Seewen	Bezirk Dorneck	Solothurn	01.01.1960
SO	1104	2481	Witterswil	Witterswil	Bezirk Dorneck	Solothurn	01.01.1960
SO	1105	2491	Hauenstein-Ifenthal	Hauenstein-Ifenthal	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2492	Kienberg	Kienberg	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2493	Lostorf	Lostorf	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2495	Niedergösgen	Niedergösgen	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2497	Obergösgen	Obergösgen	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2498	Rohr (SO)	Rohr (SO)	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2499	Stüsslingen	Stüsslingen	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2500	Trimbach	Trimbach	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2501	Winznau	Winznau	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2502	Wisen (SO)	Wisen (SO)	Bezirk Gösgen	Solothurn	01.01.1960
SO	1105	2503	Erlinsbach (SO)	Erlinsbach (SO)	Bezirk Gösgen	Solothurn	01.01.2006
SO	1106	2511	Aeschi (SO)	Aeschi (SO)	Bezirk Wasseramt	Solothurn	01.01.2012
SO	1106	2513	Biberist	Biberist	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2514	Bolken	Bolken	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2516	Deitingen	Deitingen	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2517	Derendingen	Derendingen	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2518	Etziken	Etziken	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2519	Gerlafingen	Gerlafingen	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2520	Halten	Halten	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2523	Horriwil	Horriwil	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2524	Hüniken	Hüniken	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2525	Kriegstetten	Kriegstetten	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2526	Lohn-Ammannsegg	Lohn-Ammannsegg	Bezirk Wasseramt	Solothurn	01.01.1993
SO	1106	2527	Luterbach	Luterbach	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2528	Obergerlafingen	Obergerlafingen	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2529	Oekingen	Oekingen	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2530	Recherswil	Recherswil	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2532	Subingen	Subingen	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2534	Zuchwil	Zuchwil	Bezirk Wasseramt	Solothurn	01.01.1991
SO	1106	2535	Drei Höfe	Drei Höfe	Bezirk Wasseramt	Solothurn	01.01.2013
SO	1107	2541	Balm bei Günsberg	Balm bei Günsberg	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2542	Bellach	Bellach	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2543	Bettlach	Bettlach	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2544	Feldbrunnen-St. Niklaus	Feldbrunnen-St. Niklaus	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2545	Flumenthal	Flumenthal	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2546	Grenchen	Grenchen	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2547	Günsberg	Günsberg	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2548	Hubersdorf	Hubersdorf	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2549	Kammersrohr	Kammersrohr	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2550	Langendorf	Langendorf	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2551	Lommiswil	Lommiswil	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2553	Oberdorf (SO)	Oberdorf (SO)	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2554	Riedholz	Riedholz	Bezirk Lebern	Solothurn	01.01.2011
SO	1107	2555	Rüttenen	Rüttenen	Bezirk Lebern	Solothurn	01.01.1960
SO	1107	2556	Selzach	Selzach	Bezirk Lebern	Solothurn	01.01.1960
SO	1108	2571	Boningen	Boningen	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2572	Däniken	Däniken	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2573	Dulliken	Dulliken	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2574	Eppenberg-Wöschnau	Eppenberg-Wöschnau	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2575	Fulenbach	Fulenbach	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2576	Gretzenbach	Gretzenbach	Bezirk Olten	Solothurn	01.01.1973
SO	1108	2578	Gunzgen	Gunzgen	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2579	Hägendorf	Hägendorf	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2580	Kappel (SO)	Kappel (SO)	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2581	Olten	Olten	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2582	Rickenbach (SO)	Rickenbach (SO)	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2583	Schönenwerd	Schönenwerd	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2584	Starrkirch-Wil	Starrkirch-Wil	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2585	Walterswil (SO)	Walterswil (SO)	Bezirk Olten	Solothurn	01.01.1960
SO	1108	2586	Wangen bei Olten	Wangen bei Olten	Bezirk Olten	Solothurn	01.01.1960
SO	1109	2601	Solothurn	Solothurn	Bezirk Solothurn	Solothurn	01.01.1960
SO	1110	2611	Bärschwil	Bärschwil	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2612	Beinwil (SO)	Beinwil (SO)	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2613	Breitenbach	Breitenbach	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2614	Büsserach	Büsserach	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2615	Erschwil	Erschwil	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2616	Fehren	Fehren	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2617	Grindel	Grindel	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2618	Himmelried	Himmelried	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2619	Kleinlützel	Kleinlützel	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2620	Meltingen	Meltingen	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2621	Nunningen	Nunningen	Bezirk Thierstein	Solothurn	01.01.1960
SO	1110	2622	Zullwil	Zullwil	Bezirk Thierstein	Solothurn	01.01.1960
BS	1200	2701	Basel	Basel	Kanton Basel-Stadt	Basel-Stadt	01.01.1960
BS	1200	2702	Bettingen	Bettingen	Kanton Basel-Stadt	Basel-Stadt	01.01.1960
BS	1200	2703	Riehen	Riehen	Kanton Basel-Stadt	Basel-Stadt	01.01.1960
BL	1301	2761	Aesch (BL)	Aesch (BL)	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2762	Allschwil	Allschwil	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2763	Arlesheim	Arlesheim	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2764	Biel-Benken	Biel-Benken	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2765	Binningen	Binningen	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2766	Birsfelden	Birsfelden	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2767	Bottmingen	Bottmingen	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2768	Ettingen	Ettingen	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2769	Münchenstein	Münchenstein	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2770	Muttenz	Muttenz	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2771	Oberwil (BL)	Oberwil (BL)	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2772	Pfeffingen	Pfeffingen	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2773	Reinach (BL)	Reinach (BL)	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2774	Schönenbuch	Schönenbuch	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1301	2775	Therwil	Therwil	Bezirk Arlesheim	Basel-Landschaft	01.01.1994
BL	1302	2781	Blauen	Blauen	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2782	Brislach	Brislach	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2783	Burg im Leimental	Burg im Leimental	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2784	Dittingen	Dittingen	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2785	Duggingen	Duggingen	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2786	Grellingen	Grellingen	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2787	Laufen	Laufen	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2788	Liesberg	Liesberg	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2789	Nenzlingen	Nenzlingen	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2790	Roggenburg	Roggenburg	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2791	Röschenz	Röschenz	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2792	Wahlen	Wahlen	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1302	2793	Zwingen	Zwingen	Bezirk Laufen	Basel-Landschaft	01.01.1994
BL	1303	2821	Arisdorf	Arisdorf	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2822	Augst	Augst	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2823	Bubendorf	Bubendorf	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2824	Frenkendorf	Frenkendorf	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2825	Füllinsdorf	Füllinsdorf	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2826	Giebenach	Giebenach	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2827	Hersberg	Hersberg	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2828	Lausen	Lausen	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2829	Liestal	Liestal	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2830	Lupsingen	Lupsingen	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2831	Pratteln	Pratteln	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2832	Ramlinsburg	Ramlinsburg	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2833	Seltisberg	Seltisberg	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1303	2834	Ziefen	Ziefen	Bezirk Liestal	Basel-Landschaft	01.01.1994
BL	1304	2841	Anwil	Anwil	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2842	Böckten	Böckten	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2843	Buckten	Buckten	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2844	Buus	Buus	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2845	Diepflingen	Diepflingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2846	Gelterkinden	Gelterkinden	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2847	Häfelfingen	Häfelfingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2848	Hemmiken	Hemmiken	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2849	Itingen	Itingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2850	Känerkinden	Känerkinden	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2851	Kilchberg (BL)	Kilchberg (BL)	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2852	Läufelfingen	Läufelfingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2853	Maisprach	Maisprach	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2854	Nusshof	Nusshof	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2855	Oltingen	Oltingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2856	Ormalingen	Ormalingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2857	Rickenbach (BL)	Rickenbach (BL)	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2858	Rothenfluh	Rothenfluh	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2859	Rümlingen	Rümlingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2860	Rünenberg	Rünenberg	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2861	Sissach	Sissach	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2862	Tecknau	Tecknau	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2863	Tenniken	Tenniken	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2864	Thürnen	Thürnen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2865	Wenslingen	Wenslingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2866	Wintersingen	Wintersingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2867	Wittinsburg	Wittinsburg	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2868	Zeglingen	Zeglingen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1304	2869	Zunzgen	Zunzgen	Bezirk Sissach	Basel-Landschaft	01.01.1994
BL	1305	2881	Arboldswil	Arboldswil	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2882	Bennwil	Bennwil	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2883	Bretzwil	Bretzwil	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2884	Diegten	Diegten	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2885	Eptingen	Eptingen	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2886	Hölstein	Hölstein	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2887	Lampenberg	Lampenberg	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2888	Langenbruck	Langenbruck	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2889	Lauwil	Lauwil	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2890	Liedertswil	Liedertswil	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2891	Niederdorf	Niederdorf	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2892	Oberdorf (BL)	Oberdorf (BL)	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2893	Reigoldswil	Reigoldswil	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2894	Titterten	Titterten	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
BL	1305	2895	Waldenburg	Waldenburg	Bezirk Waldenburg	Basel-Landschaft	01.01.1994
SH	1401	2901	Gächlingen	Gächlingen	Bezirk Oberklettgau	Schaffhausen	01.01.1960
SH	1401	2903	Löhningen	Löhningen	Bezirk Oberklettgau	Schaffhausen	01.01.1960
SH	1401	2904	Neunkirch	Neunkirch	Bezirk Oberklettgau	Schaffhausen	01.01.1960
SH	1402	2914	Büttenhardt	Büttenhardt	Bezirk Reiat	Schaffhausen	01.01.1960
SH	1402	2915	Dörflingen	Dörflingen	Bezirk Reiat	Schaffhausen	01.01.1960
SH	1402	2917	Lohn (SH)	Lohn (SH)	Bezirk Reiat	Schaffhausen	01.01.1960
SH	1402	2919	Stetten (SH)	Stetten (SH)	Bezirk Reiat	Schaffhausen	01.01.1960
SH	1402	2920	Thayngen	Thayngen	Bezirk Reiat	Schaffhausen	01.01.2009
SH	1403	2931	Bargen (SH)	Bargen (SH)	Bezirk Schaffhausen	Schaffhausen	01.01.1960
SH	1403	2932	Beringen	Beringen	Bezirk Schaffhausen	Schaffhausen	01.01.2013
SH	1403	2933	Buchberg	Buchberg	Bezirk Schaffhausen	Schaffhausen	01.01.1960
SH	1403	2936	Merishausen	Merishausen	Bezirk Schaffhausen	Schaffhausen	01.01.1960
SH	1403	2937	Neuhausen am Rheinfall	Neuhausen am Rheinfall	Bezirk Schaffhausen	Schaffhausen	01.01.1960
SH	1403	2938	Rüdlingen	Rüdlingen	Bezirk Schaffhausen	Schaffhausen	01.01.1960
SH	1403	2939	Schaffhausen	Schaffhausen	Bezirk Schaffhausen	Schaffhausen	01.01.2009
SH	1404	2951	Beggingen	Beggingen	Bezirk Schleitheim	Schaffhausen	01.01.1960
SH	1404	2952	Schleitheim	Schleitheim	Bezirk Schleitheim	Schaffhausen	01.01.1960
SH	1404	2953	Siblingen	Siblingen	Bezirk Schleitheim	Schaffhausen	01.01.1960
SH	1405	2961	Buch (SH)	Buch (SH)	Bezirk Stein	Schaffhausen	01.01.1960
SH	1405	2962	Hemishofen	Hemishofen	Bezirk Stein	Schaffhausen	01.01.1960
SH	1405	2963	Ramsen	Ramsen	Bezirk Stein	Schaffhausen	01.01.1960
SH	1405	2964	Stein am Rhein	Stein am Rhein	Bezirk Stein	Schaffhausen	01.01.1960
SH	1406	2971	Hallau	Hallau	Bezirk Unterklettgau	Schaffhausen	01.01.1960
SH	1406	2972	Oberhallau	Oberhallau	Bezirk Unterklettgau	Schaffhausen	01.01.1960
SH	1406	2973	Trasadingen	Trasadingen	Bezirk Unterklettgau	Schaffhausen	01.01.1960
SH	1406	2974	Wilchingen	Wilchingen	Bezirk Unterklettgau	Schaffhausen	01.01.2005
AR	1501	3001	Herisau	Herisau	Bezirk Hinterland	Appenzell Ausserrhoden	01.01.1960
AR	1501	3002	Hundwil	Hundwil	Bezirk Hinterland	Appenzell Ausserrhoden	01.01.1960
AR	1501	3003	Schönengrund	Schönengrund	Bezirk Hinterland	Appenzell Ausserrhoden	01.01.1960
AR	1501	3004	Schwellbrunn	Schwellbrunn	Bezirk Hinterland	Appenzell Ausserrhoden	01.01.1960
AR	1501	3005	Stein (AR)	Stein (AR)	Bezirk Hinterland	Appenzell Ausserrhoden	01.01.1960
AR	1501	3006	Urnäsch	Urnäsch	Bezirk Hinterland	Appenzell Ausserrhoden	01.01.1960
AR	1501	3007	Waldstatt	Waldstatt	Bezirk Hinterland	Appenzell Ausserrhoden	01.01.1960
AR	1502	3021	Bühler	Bühler	Bezirk Mittelland	Appenzell Ausserrhoden	01.01.1960
AR	1502	3022	Gais	Gais	Bezirk Mittelland	Appenzell Ausserrhoden	01.01.1960
AR	1502	3023	Speicher	Speicher	Bezirk Mittelland	Appenzell Ausserrhoden	01.01.1960
AR	1502	3024	Teufen (AR)	Teufen (AR)	Bezirk Mittelland	Appenzell Ausserrhoden	01.01.1960
AR	1502	3025	Trogen	Trogen	Bezirk Mittelland	Appenzell Ausserrhoden	01.01.1960
AR	1503	3031	Grub (AR)	Grub (AR)	Bezirk Vorderland	Appenzell Ausserrhoden	01.01.1960
AR	1503	3032	Heiden	Heiden	Bezirk Vorderland	Appenzell Ausserrhoden	01.01.1960
AR	1503	3033	Lutzenberg	Lutzenberg	Bezirk Vorderland	Appenzell Ausserrhoden	01.01.1960
AR	1503	3034	Rehetobel	Rehetobel	Bezirk Vorderland	Appenzell Ausserrhoden	01.01.1960
AR	1503	3035	Reute (AR)	Reute (AR)	Bezirk Vorderland	Appenzell Ausserrhoden	01.01.1960
AR	1503	3036	Wald (AR)	Wald (AR)	Bezirk Vorderland	Appenzell Ausserrhoden	01.01.1960
AR	1503	3037	Walzenhausen	Walzenhausen	Bezirk Vorderland	Appenzell Ausserrhoden	01.01.1960
AR	1503	3038	Wolfhalden	Wolfhalden	Bezirk Vorderland	Appenzell Ausserrhoden	01.01.1960
AI	1600	3101	Appenzell	Appenzell	Kanton Appenzell Innerrhoden	Appenzell Innerrhoden	01.01.1997
AI	1600	3102	Gonten	Gonten	Kanton Appenzell Innerrhoden	Appenzell Innerrhoden	01.01.1997
AI	1600	3103	Rüte	Rüte	Kanton Appenzell Innerrhoden	Appenzell Innerrhoden	01.01.1997
AI	1600	3104	Schlatt-Haslen	Schlatt-Haslen	Kanton Appenzell Innerrhoden	Appenzell Innerrhoden	01.01.1997
AI	1600	3105	Schwende	Schwende	Kanton Appenzell Innerrhoden	Appenzell Innerrhoden	01.01.1997
AI	1600	3111	Oberegg	Oberegg	Kanton Appenzell Innerrhoden	Appenzell Innerrhoden	01.01.1997
SG	1721	3201	Häggenschwil	Häggenschwil	Wahlkreis St. Gallen	St. Gallen	01.01.2003
SG	1721	3202	Muolen	Muolen	Wahlkreis St. Gallen	St. Gallen	01.01.2003
SG	1721	3203	St. Gallen	St. Gallen	Wahlkreis St. Gallen	St. Gallen	01.01.2003
SG	1721	3204	Wittenbach	Wittenbach	Wahlkreis St. Gallen	St. Gallen	01.01.2003
SG	1722	3211	Berg (SG)	Berg (SG)	Wahlkreis Rorschach	St. Gallen	01.01.2003
SG	1721	3212	Eggersriet	Eggersriet	Wahlkreis St. Gallen	St. Gallen	01.01.2003
SG	1722	3213	Goldach	Goldach	Wahlkreis Rorschach	St. Gallen	01.01.2003
SG	1722	3214	Mörschwil	Mörschwil	Wahlkreis Rorschach	St. Gallen	01.01.2003
SG	1722	3215	Rorschach	Rorschach	Wahlkreis Rorschach	St. Gallen	01.01.2003
SG	1722	3216	Rorschacherberg	Rorschacherberg	Wahlkreis Rorschach	St. Gallen	01.01.2003
SG	1722	3217	Steinach	Steinach	Wahlkreis Rorschach	St. Gallen	01.01.2003
SG	1722	3218	Tübach	Tübach	Wahlkreis Rorschach	St. Gallen	01.01.2003
SG	1722	3219	Untereggen	Untereggen	Wahlkreis Rorschach	St. Gallen	01.01.2003
SG	1723	3231	Au (SG)	Au (SG)	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3232	Balgach	Balgach	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3233	Berneck	Berneck	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3234	Diepoldsau	Diepoldsau	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3235	Rheineck	Rheineck	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3236	St. Margrethen	St. Margrethen	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1722	3237	Thal	Thal	Wahlkreis Rorschach	St. Gallen	01.01.2003
SG	1723	3238	Widnau	Widnau	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3251	Altstätten	Altstätten	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3252	Eichberg	Eichberg	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3253	Marbach (SG)	Marbach (SG)	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3254	Oberriet (SG)	Oberriet (SG)	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3255	Rebstein	Rebstein	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1723	3256	Rüthi (SG)	Rüthi (SG)	Wahlkreis Rheintal	St. Gallen	01.01.2003
SG	1724	3271	Buchs (SG)	Buchs (SG)	Wahlkreis Werdenberg	St. Gallen	01.01.2003
SG	1724	3272	Gams	Gams	Wahlkreis Werdenberg	St. Gallen	01.01.2003
SG	1724	3273	Grabs	Grabs	Wahlkreis Werdenberg	St. Gallen	01.01.2003
SG	1724	3274	Sennwald	Sennwald	Wahlkreis Werdenberg	St. Gallen	01.01.2003
SG	1724	3275	Sevelen	Sevelen	Wahlkreis Werdenberg	St. Gallen	01.01.2003
SG	1724	3276	Wartau	Wartau	Wahlkreis Werdenberg	St. Gallen	01.01.2003
SG	1725	3291	Bad Ragaz	Bad Ragaz	Wahlkreis Sarganserland	St. Gallen	01.01.2003
SG	1725	3292	Flums	Flums	Wahlkreis Sarganserland	St. Gallen	01.01.2003
SG	1725	3293	Mels	Mels	Wahlkreis Sarganserland	St. Gallen	01.01.2003
SG	1725	3294	Pfäfers	Pfäfers	Wahlkreis Sarganserland	St. Gallen	01.01.2003
SG	1725	3295	Quarten	Quarten	Wahlkreis Sarganserland	St. Gallen	01.01.2003
SG	1725	3296	Sargans	Sargans	Wahlkreis Sarganserland	St. Gallen	01.01.2003
SG	1725	3297	Vilters-Wangs	Vilters-Wangs	Wahlkreis Sarganserland	St. Gallen	01.01.2003
SG	1725	3298	Walenstadt	Walenstadt	Wahlkreis Sarganserland	St. Gallen	01.01.2003
SG	1726	3311	Amden	Amden	Wahlkreis See-Gaster	St. Gallen	01.01.2003
SG	1726	3312	Benken (SG)	Benken (SG)	Wahlkreis See-Gaster	St. Gallen	01.01.2003
SG	1726	3313	Kaltbrunn	Kaltbrunn	Wahlkreis See-Gaster	St. Gallen	01.01.2003
SG	1726	3315	Schänis	Schänis	Wahlkreis See-Gaster	St. Gallen	01.01.2003
SG	1726	3316	Weesen	Weesen	Wahlkreis See-Gaster	St. Gallen	01.01.2003
SG	1726	3338	Schmerikon	Schmerikon	Wahlkreis See-Gaster	St. Gallen	01.01.2003
SG	1726	3339	Uznach	Uznach	Wahlkreis See-Gaster	St. Gallen	01.01.2003
SG	1726	3340	Rapperswil-Jona	Rapperswil-Jona	Wahlkreis See-Gaster	St. Gallen	01.01.2007
SG	1726	3341	Gommiswald	Gommiswald	Wahlkreis See-Gaster	St. Gallen	01.01.2013
SG	1726	3342	Eschenbach (SG)	Eschenbach (SG)	Wahlkreis See-Gaster	St. Gallen	01.01.2013
SG	1727	3352	Ebnat-Kappel	Ebnat-Kappel	Wahlkreis Toggenburg	St. Gallen	01.01.2003
SG	1727	3359	Wildhaus-Alt St. Johann	Wildhaus-Alt St. Johann	Wahlkreis Toggenburg	St. Gallen	01.01.2010
SG	1727	3360	Nesslau	Nesslau	Wahlkreis Toggenburg	St. Gallen	01.01.2013
SG	1727	3372	Hemberg	Hemberg	Wahlkreis Toggenburg	St. Gallen	01.01.2003
SG	1727	3374	Lichtensteig	Lichtensteig	Wahlkreis Toggenburg	St. Gallen	01.01.2003
SG	1727	3375	Oberhelfenschwil	Oberhelfenschwil	Wahlkreis Toggenburg	St. Gallen	01.01.2003
SG	1727	3378	Neckertal	Neckertal	Wahlkreis Toggenburg	St. Gallen	01.01.2009
SG	1727	3379	Wattwil	Wattwil	Wahlkreis Toggenburg	St. Gallen	01.01.2013
SG	1727	3392	Kirchberg (SG)	Kirchberg (SG)	Wahlkreis Toggenburg	St. Gallen	01.01.2003
SG	1727	3393	Lütisburg	Lütisburg	Wahlkreis Toggenburg	St. Gallen	01.01.2003
SG	1727	3394	Mosnang	Mosnang	Wahlkreis Toggenburg	St. Gallen	01.01.2003
SG	1727	3395	Bütschwil-Ganterschwil	Bütschwil-Ganterschwil	Wahlkreis Toggenburg	St. Gallen	01.01.2013
SG	1728	3401	Degersheim	Degersheim	Wahlkreis Wil	St. Gallen	01.01.2003
SG	1728	3402	Flawil	Flawil	Wahlkreis Wil	St. Gallen	01.01.2003
SG	1728	3405	Jonschwil	Jonschwil	Wahlkreis Wil	St. Gallen	01.01.2003
SG	1728	3407	Oberuzwil	Oberuzwil	Wahlkreis Wil	St. Gallen	01.01.2003
SG	1728	3408	Uzwil	Uzwil	Wahlkreis Wil	St. Gallen	01.01.2003
SG	1728	3422	Niederbüren	Niederbüren	Wahlkreis Wil	St. Gallen	01.01.2003
SG	1728	3423	Niederhelfenschwil	Niederhelfenschwil	Wahlkreis Wil	St. Gallen	01.01.2003
SG	1728	3424	Oberbüren	Oberbüren	Wahlkreis Wil	St. Gallen	01.01.2003
SG	1728	3426	Zuzwil (SG)	Zuzwil (SG)	Wahlkreis Wil	St. Gallen	01.01.2003
SG	1728	3427	Wil (SG)	Wil (SG)	Wahlkreis Wil	St. Gallen	01.01.2013
SG	1721	3441	Andwil (SG)	Andwil (SG)	Wahlkreis St. Gallen	St. Gallen	01.01.2003
SG	1721	3442	Gaiserwald	Gaiserwald	Wahlkreis St. Gallen	St. Gallen	01.01.2003
SG	1721	3443	Gossau (SG)	Gossau (SG)	Wahlkreis St. Gallen	St. Gallen	01.01.2003
SG	1721	3444	Waldkirch	Waldkirch	Wahlkreis St. Gallen	St. Gallen	01.01.2003
GR	1821	3501	Alvaschein	Alvaschein	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3502	Mon	Mon	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3503	Mutten	Mutten	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3504	Stierva	Stierva	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3505	Tiefencastel	Tiefencastel	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3506	Vaz/Obervaz	Vaz/Obervaz	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3511	Alvaneu	Alvaneu	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3512	Brienz/Brinzauls	Brienz/Brinzauls	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3513	Lantsch/Lenz	Lantsch/Lenz	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3514	Schmitten (GR)	Schmitten (GR)	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3515	Surava	Surava	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3521	Bergün/Bravuogn	Bergün/Bravuogn	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3522	Filisur	Filisur	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3531	Bivio	Bivio	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3532	Cunter	Cunter	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3533	Marmorera	Marmorera	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3534	Mulegns	Mulegns	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3536	Riom-Parsonz	Riom-Parsonz	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3538	Salouf	Salouf	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3539	Savognin	Savognin	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3540	Sur	Sur	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1821	3541	Tinizong-Rona	Tinizong-Rona	Bezirk Albula	Graubünden / Grigioni / Grischun	01.01.2001
GR	1822	3551	Brusio	Brusio	Distretto di Bernina	Graubünden / Grigioni / Grischun	01.01.2001
GR	1822	3561	Poschiavo	Poschiavo	Distretto di Bernina	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3572	Falera	Falera	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3575	Laax	Laax	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3581	Sagogn	Sagogn	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3582	Schluein	Schluein	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3598	St. Martin	St. Martin	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3603	Vals	Vals	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3611	Andiast	Andiast	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3612	Obersaxen	Obersaxen	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3616	Waltensburg/Vuorz	Waltensburg/Vuorz	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3617	Mundaun	Mundaun	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2009
GR	1831	3618	Lumnezia	Lumnezia	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2013
GR	1831	3619	Ilanz/Glion	Ilanz/Glion	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2014
GR	1823	3631	Almens	Almens	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3633	Fürstenau	Fürstenau	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3634	Paspels	Paspels	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3635	Pratval	Pratval	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3636	Rodels	Rodels	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3637	Rothenbrunnen	Rothenbrunnen	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3638	Scharans	Scharans	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3640	Sils im Domleschg	Sils im Domleschg	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3661	Cazis	Cazis	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2010
GR	1823	3662	Flerden	Flerden	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3663	Masein	Masein	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3668	Thusis	Thusis	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3669	Tschappina	Tschappina	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3670	Urmein	Urmein	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3671	Tomils	Tomils	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2009
GR	1831	3672	Safiental	Safiental	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2013
GR	1823	3681	Avers	Avers	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3691	Hinterrhein	Hinterrhein	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3693	Nufenen	Nufenen	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3694	Splügen	Splügen	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2006
GR	1823	3695	Sufers	Sufers	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3701	Andeer	Andeer	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2009
GR	1823	3703	Casti-Wergenstein	Casti-Wergenstein	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3705	Donat	Donat	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2003
GR	1823	3707	Lohn (GR)	Lohn (GR)	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3708	Mathon	Mathon	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3711	Rongellen	Rongellen	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3712	Zillis-Reischen	Zillis-Reischen	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2001
GR	1823	3713	Ferrera	Ferrera	Bezirk Hinterrhein	Graubünden / Grigioni / Grischun	01.01.2008
GR	1824	3721	Bonaduz	Bonaduz	Bezirk Imboden	Graubünden / Grigioni / Grischun	01.01.2001
GR	1824	3722	Domat/Ems	Domat/Ems	Bezirk Imboden	Graubünden / Grigioni / Grischun	01.01.2001
GR	1824	3723	Rhäzüns	Rhäzüns	Bezirk Imboden	Graubünden / Grigioni / Grischun	01.01.2001
GR	1824	3731	Felsberg	Felsberg	Bezirk Imboden	Graubünden / Grigioni / Grischun	01.01.2001
GR	1824	3732	Flims	Flims	Bezirk Imboden	Graubünden / Grigioni / Grischun	01.01.2001
GR	1824	3733	Tamins	Tamins	Bezirk Imboden	Graubünden / Grigioni / Grischun	01.01.2001
GR	1824	3734	Trin	Trin	Bezirk Imboden	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3741	Ardez	Ardez	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3742	Guarda	Guarda	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3743	Lavin	Lavin	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3744	Susch	Susch	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3745	Tarasp	Tarasp	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3746	Zernez	Zernez	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3752	Samnaun	Samnaun	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3761	Ftan	Ftan	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3762	Scuol	Scuol	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3763	Sent	Sent	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3764	Valsot	Valsot	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2013
GR	1827	3781	Bever	Bever	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3782	Celerina/Schlarigna	Celerina/Schlarigna	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3783	Madulain	Madulain	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3784	Pontresina	Pontresina	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3785	La Punt-Chamues-ch	La Punt-Chamues-ch	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3786	Samedan	Samedan	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3787	St. Moritz	St. Moritz	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3788	S-chanf	S-chanf	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3789	Sils im Engadin/Segl	Sils im Engadin/Segl	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3790	Silvaplana	Silvaplana	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3791	Zuoz	Zuoz	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2001
GR	1827	3792	Bregaglia	Bregaglia	Bezirk Maloja / Distretto di Maloggia	Graubünden / Grigioni / Grischun	01.01.2010
GR	1828	3801	Arvigo	Arvigo	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3803	Braggio	Braggio	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3804	Buseno	Buseno	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3805	Castaneda	Castaneda	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3806	Cauco	Cauco	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3808	Rossa	Rossa	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3810	Santa Maria in Calanca	Santa Maria in Calanca	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3811	Selma	Selma	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3821	Lostallo	Lostallo	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3822	Mesocco	Mesocco	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3823	Soazza	Soazza	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3831	Cama	Cama	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3832	Grono	Grono	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3833	Leggia	Leggia	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3834	Roveredo (GR)	Roveredo (GR)	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3835	San Vittore	San Vittore	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1828	3836	Verdabbio	Verdabbio	Distretto di Moesa	Graubünden / Grigioni / Grischun	01.01.2001
GR	1825	3847	Val Müstair	Val Müstair	Bezirk Inn	Graubünden / Grigioni / Grischun	01.01.2009
GR	1830	3851	Davos	Davos	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2009
GR	1830	3861	Fideris	Fideris	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1830	3862	Furna	Furna	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1830	3863	Jenaz	Jenaz	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1830	3871	Klosters-Serneus	Klosters-Serneus	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1830	3881	Conters im Prättigau	Conters im Prättigau	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1830	3882	Küblis	Küblis	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1830	3883	Saas	Saas	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1830	3891	Luzein	Luzein	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1830	3893	St. Antönien	St. Antönien	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2007
GR	1829	3901	Chur	Chur	Bezirk Plessur	Graubünden / Grigioni / Grischun	01.01.2001
GR	1829	3911	Churwalden	Churwalden	Bezirk Plessur	Graubünden / Grigioni / Grischun	01.01.2010
GR	1829	3921	Arosa	Arosa	Bezirk Plessur	Graubünden / Grigioni / Grischun	01.01.2013
GR	1829	3926	Maladers	Maladers	Bezirk Plessur	Graubünden / Grigioni / Grischun	01.01.2001
GR	1829	3932	Tschiertschen-Praden	Tschiertschen-Praden	Bezirk Plessur	Graubünden / Grigioni / Grischun	01.01.2009
GR	1826	3941	Haldenstein	Haldenstein	Bezirk Landquart	Graubünden / Grigioni / Grischun	01.01.2001
GR	1826	3945	Trimmis	Trimmis	Bezirk Landquart	Graubünden / Grigioni / Grischun	01.01.2008
GR	1826	3946	Untervaz	Untervaz	Bezirk Landquart	Graubünden / Grigioni / Grischun	01.01.2001
GR	1826	3947	Zizers	Zizers	Bezirk Landquart	Graubünden / Grigioni / Grischun	01.01.2001
GR	1826	3951	Fläsch	Fläsch	Bezirk Landquart	Graubünden / Grigioni / Grischun	01.01.2001
GR	1826	3952	Jenins	Jenins	Bezirk Landquart	Graubünden / Grigioni / Grischun	01.01.2001
GR	1826	3953	Maienfeld	Maienfeld	Bezirk Landquart	Graubünden / Grigioni / Grischun	01.01.2001
GR	1826	3954	Malans	Malans	Bezirk Landquart	Graubünden / Grigioni / Grischun	01.01.2001
GR	1826	3955	Landquart	Landquart	Bezirk Landquart	Graubünden / Grigioni / Grischun	01.01.2012
GR	1830	3961	Grüsch	Grüsch	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2011
GR	1830	3962	Schiers	Schiers	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1830	3972	Seewis im Prättigau	Seewis im Prättigau	Bezirk Prättigau-Davos	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3981	Breil/Brigels	Breil/Brigels	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3982	Disentis/Mustér	Disentis/Mustér	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3983	Medel (Lucmagn)	Medel (Lucmagn)	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3985	Sumvitg	Sumvitg	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3986	Tujetsch	Tujetsch	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2001
GR	1831	3987	Trun	Trun	Bezirk Surselva	Graubünden / Grigioni / Grischun	01.01.2012
AG	1901	4001	Aarau	Aarau	Bezirk Aarau	Aargau	01.01.2010
AG	1901	4002	Biberstein	Biberstein	Bezirk Aarau	Aargau	01.01.1960
AG	1901	4003	Buchs (AG)	Buchs (AG)	Bezirk Aarau	Aargau	01.01.1960
AG	1901	4004	Densbüren	Densbüren	Bezirk Aarau	Aargau	01.01.1960
AG	1901	4005	Erlinsbach (AG)	Erlinsbach (AG)	Bezirk Aarau	Aargau	01.01.2006
AG	1901	4006	Gränichen	Gränichen	Bezirk Aarau	Aargau	01.01.1960
AG	1901	4007	Hirschthal	Hirschthal	Bezirk Aarau	Aargau	01.01.1960
AG	1901	4008	Küttigen	Küttigen	Bezirk Aarau	Aargau	01.01.1960
AG	1901	4009	Muhen	Muhen	Bezirk Aarau	Aargau	01.01.1960
AG	1901	4010	Oberentfelden	Oberentfelden	Bezirk Aarau	Aargau	01.01.1960
AG	1901	4012	Suhr	Suhr	Bezirk Aarau	Aargau	01.01.1960
AG	1901	4013	Unterentfelden	Unterentfelden	Bezirk Aarau	Aargau	01.01.1960
AG	1902	4021	Baden	Baden	Bezirk Baden	Aargau	01.01.1962
AG	1902	4022	Bellikon	Bellikon	Bezirk Baden	Aargau	01.01.1960
AG	1902	4023	Bergdietikon	Bergdietikon	Bezirk Baden	Aargau	01.01.1960
AG	1902	4024	Birmenstorf (AG)	Birmenstorf (AG)	Bezirk Baden	Aargau	01.01.1960
AG	1902	4026	Ennetbaden	Ennetbaden	Bezirk Baden	Aargau	01.01.1960
AG	1902	4027	Fislisbach	Fislisbach	Bezirk Baden	Aargau	01.01.1960
AG	1902	4028	Freienwil	Freienwil	Bezirk Baden	Aargau	01.01.1960
AG	1902	4029	Gebenstorf	Gebenstorf	Bezirk Baden	Aargau	01.01.1960
AG	1902	4030	Killwangen	Killwangen	Bezirk Baden	Aargau	01.01.1960
AG	1902	4031	Künten	Künten	Bezirk Baden	Aargau	01.01.1960
AG	1902	4032	Mägenwil	Mägenwil	Bezirk Baden	Aargau	01.01.1960
AG	1902	4033	Mellingen	Mellingen	Bezirk Baden	Aargau	01.01.1960
AG	1902	4034	Neuenhof	Neuenhof	Bezirk Baden	Aargau	01.01.1960
AG	1902	4035	Niederrohrdorf	Niederrohrdorf	Bezirk Baden	Aargau	01.01.1960
AG	1902	4037	Oberrohrdorf	Oberrohrdorf	Bezirk Baden	Aargau	01.01.1960
AG	1902	4038	Obersiggenthal	Obersiggenthal	Bezirk Baden	Aargau	01.01.1960
AG	1902	4039	Remetschwil	Remetschwil	Bezirk Baden	Aargau	01.01.1960
AG	1902	4040	Spreitenbach	Spreitenbach	Bezirk Baden	Aargau	01.01.1960
AG	1902	4041	Stetten (AG)	Stetten (AG)	Bezirk Baden	Aargau	01.01.1960
AG	1902	4042	Turgi	Turgi	Bezirk Baden	Aargau	01.01.1960
AG	1902	4044	Untersiggenthal	Untersiggenthal	Bezirk Baden	Aargau	01.01.1960
AG	1902	4045	Wettingen	Wettingen	Bezirk Baden	Aargau	01.01.1960
AG	1902	4046	Wohlenschwil	Wohlenschwil	Bezirk Baden	Aargau	01.01.1960
AG	1902	4047	Würenlingen	Würenlingen	Bezirk Baden	Aargau	01.01.1960
AG	1902	4048	Würenlos	Würenlos	Bezirk Baden	Aargau	01.01.1960
AG	1902	4049	Ehrendingen	Ehrendingen	Bezirk Baden	Aargau	01.01.2006
AG	1903	4061	Arni (AG)	Arni (AG)	Bezirk Bremgarten	Aargau	01.01.1983
AG	1903	4062	Berikon	Berikon	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4063	Bremgarten (AG)	Bremgarten (AG)	Bezirk Bremgarten	Aargau	01.01.2014
AG	1903	4064	Büttikon	Büttikon	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4065	Dottikon	Dottikon	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4066	Eggenwil	Eggenwil	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4067	Fischbach-Göslikon	Fischbach-Göslikon	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4068	Hägglingen	Hägglingen	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4071	Jonen	Jonen	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4072	Niederwil (AG)	Niederwil (AG)	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4073	Oberlunkhofen	Oberlunkhofen	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4074	Oberwil-Lieli	Oberwil-Lieli	Bezirk Bremgarten	Aargau	01.01.1984
AG	1903	4075	Rudolfstetten-Friedlisberg	Rudolfstetten-Friedlisb.	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4076	Sarmenstorf	Sarmenstorf	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4077	Tägerig	Tägerig	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4078	Uezwil	Uezwil	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4079	Unterlunkhofen	Unterlunkhofen	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4080	Villmergen	Villmergen	Bezirk Bremgarten	Aargau	01.01.2010
AG	1903	4081	Widen	Widen	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4082	Wohlen (AG)	Wohlen (AG)	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4083	Zufikon	Zufikon	Bezirk Bremgarten	Aargau	01.01.1960
AG	1903	4084	Islisberg	Islisberg	Bezirk Bremgarten	Aargau	01.01.1983
AG	1904	4091	Auenstein	Auenstein	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4092	Birr	Birr	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4093	Birrhard	Birrhard	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4094	Bözen	Bözen	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4095	Brugg	Brugg	Bezirk Brugg	Aargau	01.01.2010
AG	1904	4096	Effingen	Effingen	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4097	Elfingen	Elfingen	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4099	Habsburg	Habsburg	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4100	Hausen (AG)	Hausen (AG)	Bezirk Brugg	Aargau	01.01.2003
AG	1904	4104	Lupfig	Lupfig	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4105	Mandach	Mandach	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4106	Mönthal	Mönthal	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4107	Mülligen	Mülligen	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4110	Remigen	Remigen	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4111	Riniken	Riniken	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4112	Rüfenach	Rüfenach	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4113	Scherz	Scherz	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4114	Schinznach-Bad	Schinznach-Bad	Bezirk Brugg	Aargau	01.01.2003
AG	1904	4117	Thalheim (AG)	Thalheim (AG)	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4120	Veltheim (AG)	Veltheim (AG)	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4121	Villigen	Villigen	Bezirk Brugg	Aargau	01.01.2006
AG	1904	4122	Villnachern	Villnachern	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4123	Windisch	Windisch	Bezirk Brugg	Aargau	01.01.1960
AG	1904	4124	Bözberg	Bözberg	Bezirk Brugg	Aargau	01.01.2013
AG	1904	4125	Schinznach	Schinznach	Bezirk Brugg	Aargau	01.01.2014
AG	1905	4131	Beinwil am See	Beinwil am See	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4132	Birrwil	Birrwil	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4133	Burg (AG)	Burg (AG)	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4134	Dürrenäsch	Dürrenäsch	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4135	Gontenschwil	Gontenschwil	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4136	Holziken	Holziken	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4137	Leimbach (AG)	Leimbach (AG)	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4138	Leutwil	Leutwil	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4139	Menziken	Menziken	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4140	Oberkulm	Oberkulm	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4141	Reinach (AG)	Reinach (AG)	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4142	Schlossrued	Schlossrued	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4143	Schmiedrued	Schmiedrued	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4144	Schöftland	Schöftland	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4145	Teufenthal (AG)	Teufenthal (AG)	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4146	Unterkulm	Unterkulm	Bezirk Kulm	Aargau	01.01.1960
AG	1905	4147	Zetzwil	Zetzwil	Bezirk Kulm	Aargau	01.01.1960
AG	1906	4161	Eiken	Eiken	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4163	Frick	Frick	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4164	Gansingen	Gansingen	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4165	Gipf-Oberfrick	Gipf-Oberfrick	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4166	Herznach	Herznach	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4167	Hornussen	Hornussen	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4169	Kaisten	Kaisten	Bezirk Laufenburg	Aargau	01.01.2010
AG	1906	4170	Laufenburg	Laufenburg	Bezirk Laufenburg	Aargau	01.01.2010
AG	1906	4172	Münchwilen (AG)	Münchwilen (AG)	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4173	Oberhof	Oberhof	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4175	Oeschgen	Oeschgen	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4176	Schwaderloch	Schwaderloch	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4177	Sisseln	Sisseln	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4179	Ueken	Ueken	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4181	Wittnau	Wittnau	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4182	Wölflinswil	Wölflinswil	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4183	Zeihen	Zeihen	Bezirk Laufenburg	Aargau	01.01.1960
AG	1906	4184	Mettauertal	Mettauertal	Bezirk Laufenburg	Aargau	01.01.2010
AG	1907	4191	Ammerswil	Ammerswil	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4192	Boniswil	Boniswil	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4193	Brunegg	Brunegg	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4194	Dintikon	Dintikon	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4195	Egliswil	Egliswil	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4196	Fahrwangen	Fahrwangen	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4197	Hallwil	Hallwil	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4198	Hendschiken	Hendschiken	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4199	Holderbank (AG)	Holderbank (AG)	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4200	Hunzenschwil	Hunzenschwil	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4201	Lenzburg	Lenzburg	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4202	Meisterschwanden	Meisterschwanden	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4203	Möriken-Wildegg	Möriken-Wildegg	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4204	Niederlenz	Niederlenz	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4205	Othmarsingen	Othmarsingen	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4206	Rupperswil	Rupperswil	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4207	Schafisheim	Schafisheim	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4208	Seengen	Seengen	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4209	Seon	Seon	Bezirk Lenzburg	Aargau	01.01.1960
AG	1907	4210	Staufen	Staufen	Bezirk Lenzburg	Aargau	01.01.1960
AG	1908	4221	Abtwil	Abtwil	Bezirk Muri	Aargau	01.01.1960
AG	1908	4222	Aristau	Aristau	Bezirk Muri	Aargau	01.01.1960
AG	1908	4223	Auw	Auw	Bezirk Muri	Aargau	01.01.1960
AG	1908	4224	Beinwil (Freiamt)	Beinwil (Freiamt)	Bezirk Muri	Aargau	01.01.1960
AG	1908	4226	Besenbüren	Besenbüren	Bezirk Muri	Aargau	01.01.1960
AG	1908	4227	Bettwil	Bettwil	Bezirk Muri	Aargau	01.01.1960
AG	1908	4228	Boswil	Boswil	Bezirk Muri	Aargau	01.01.1960
AG	1908	4229	Bünzen	Bünzen	Bezirk Muri	Aargau	01.01.1960
AG	1908	4230	Buttwil	Buttwil	Bezirk Muri	Aargau	01.01.1960
AG	1908	4231	Dietwil	Dietwil	Bezirk Muri	Aargau	01.01.1960
AG	1908	4232	Geltwil	Geltwil	Bezirk Muri	Aargau	01.01.1960
AG	1908	4233	Kallern	Kallern	Bezirk Muri	Aargau	01.01.1960
AG	1908	4234	Merenschwand	Merenschwand	Bezirk Muri	Aargau	01.01.2012
AG	1908	4235	Mühlau	Mühlau	Bezirk Muri	Aargau	01.01.1960
AG	1908	4236	Muri (AG)	Muri (AG)	Bezirk Muri	Aargau	01.01.1960
AG	1908	4237	Oberrüti	Oberrüti	Bezirk Muri	Aargau	01.01.1960
AG	1908	4238	Rottenschwil	Rottenschwil	Bezirk Muri	Aargau	01.01.1960
AG	1908	4239	Sins	Sins	Bezirk Muri	Aargau	01.01.1960
AG	1908	4240	Waltenschwil	Waltenschwil	Bezirk Muri	Aargau	01.01.1960
AG	1909	4251	Hellikon	Hellikon	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4252	Kaiseraugst	Kaiseraugst	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4253	Magden	Magden	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4254	Möhlin	Möhlin	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4255	Mumpf	Mumpf	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4256	Obermumpf	Obermumpf	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4257	Olsberg	Olsberg	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4258	Rheinfelden	Rheinfelden	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4259	Schupfart	Schupfart	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4260	Stein (AG)	Stein (AG)	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4261	Wallbach	Wallbach	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4262	Wegenstetten	Wegenstetten	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4263	Zeiningen	Zeiningen	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1909	4264	Zuzgen	Zuzgen	Bezirk Rheinfelden	Aargau	01.01.1960
AG	1910	4271	Aarburg	Aarburg	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4272	Attelwil	Attelwil	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4273	Bottenwil	Bottenwil	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4274	Brittnau	Brittnau	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4275	Kirchleerau	Kirchleerau	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4276	Kölliken	Kölliken	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4277	Moosleerau	Moosleerau	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4279	Murgenthal	Murgenthal	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4280	Oftringen	Oftringen	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4281	Reitnau	Reitnau	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4282	Rothrist	Rothrist	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4283	Safenwil	Safenwil	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4284	Staffelbach	Staffelbach	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4285	Strengelbach	Strengelbach	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4286	Uerkheim	Uerkheim	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4287	Vordemwald	Vordemwald	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4288	Wiliberg	Wiliberg	Bezirk Zofingen	Aargau	01.01.1960
AG	1910	4289	Zofingen	Zofingen	Bezirk Zofingen	Aargau	01.01.2002
AG	1911	4301	Baldingen	Baldingen	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4302	Böbikon	Böbikon	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4303	Böttstein	Böttstein	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4304	Döttingen	Döttingen	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4305	Endingen	Endingen	Bezirk Zurzach	Aargau	01.01.2014
AG	1911	4306	Fisibach	Fisibach	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4307	Full-Reuenthal	Full-Reuenthal	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4308	Kaiserstuhl	Kaiserstuhl	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4309	Klingnau	Klingnau	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4310	Koblenz	Koblenz	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4311	Leibstadt	Leibstadt	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4312	Lengnau (AG)	Lengnau (AG)	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4313	Leuggern	Leuggern	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4314	Mellikon	Mellikon	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4315	Rekingen (AG)	Rekingen (AG)	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4316	Rietheim	Rietheim	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4317	Rümikon	Rümikon	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4318	Schneisingen	Schneisingen	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4319	Siglistorf	Siglistorf	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4320	Tegerfelden	Tegerfelden	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4322	Wislikofen	Wislikofen	Bezirk Zurzach	Aargau	01.01.1960
AG	1911	4323	Bad Zurzach	Bad Zurzach	Bezirk Zurzach	Aargau	01.12.2006
TG	2011	4401	Arbon	Arbon	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4406	Dozwil	Dozwil	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4411	Egnach	Egnach	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4416	Hefenhofen	Hefenhofen	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4421	Horn	Horn	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4426	Kesswil	Kesswil	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4431	Roggwil (TG)	Roggwil (TG)	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4436	Romanshorn	Romanshorn	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4441	Salmsach	Salmsach	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4446	Sommeri	Sommeri	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4451	Uttwil	Uttwil	Bezirk Arbon	Thurgau	01.01.2011
TG	2011	4461	Amriswil	Amriswil	Bezirk Arbon	Thurgau	01.01.2011
TG	2015	4471	Bischofszell	Bischofszell	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4476	Erlen	Erlen	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4486	Hauptwil-Gottshaus	Hauptwil-Gottshaus	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4495	Hohentannen	Hohentannen	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4501	Kradolf-Schönenberg	Kradolf-Schönenberg	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4506	Sulgen	Sulgen	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4511	Zihlschlacht-Sitterdorf	Zihlschlacht-Sitterdorf	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2012	4536	Basadingen-Schlattingen	Basadingen-Schlattingen	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4545	Diessenhofen	Diessenhofen	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4546	Schlatt (TG)	Schlatt (TG)	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2014	4551	Aadorf	Aadorf	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2012	4561	Felben-Wellhausen	Felben-Wellhausen	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4566	Frauenfeld	Frauenfeld	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4571	Gachnang	Gachnang	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4590	Hüttlingen	Hüttlingen	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4591	Matzingen	Matzingen	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4601	Neunforn	Neunforn	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4606	Stettfurt	Stettfurt	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4611	Thundorf	Thundorf	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4616	Uesslingen-Buch	Uesslingen-Buch	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4621	Warth-Weiningen	Warth-Weiningen	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2013	4641	Altnau	Altnau	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4643	Bottighofen	Bottighofen	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4646	Ermatingen	Ermatingen	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4651	Gottlieben	Gottlieben	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4656	Güttingen	Güttingen	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4666	Kemmental	Kemmental	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4671	Kreuzlingen	Kreuzlingen	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4681	Langrickenbach	Langrickenbach	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4683	Lengwil	Lengwil	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4691	Münsterlingen	Münsterlingen	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4696	Tägerwilen	Tägerwilen	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4701	Wäldi	Wäldi	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2015	4711	Affeltrangen	Affeltrangen	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2014	4716	Bettwiesen	Bettwiesen	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4721	Bichelsee-Balterswil	Bichelsee-Balterswil	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4723	Braunau	Braunau	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4724	Eschlikon	Eschlikon	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4726	Fischingen	Fischingen	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4741	Lommis	Lommis	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4746	Münchwilen (TG)	Münchwilen (TG)	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4751	Rickenbach (TG)	Rickenbach (TG)	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2015	4756	Schönholzerswilen	Schönholzerswilen	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2014	4761	Sirnach	Sirnach	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4776	Tobel-Tägerschen	Tobel-Tägerschen	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4781	Wängi	Wängi	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2014	4786	Wilen (TG)	Wilen (TG)	Bezirk Münchwilen	Thurgau	01.01.2011
TG	2015	4791	Wuppenau	Wuppenau	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2012	4801	Berlingen	Berlingen	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4806	Eschenz	Eschenz	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4811	Herdern	Herdern	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4816	Homburg	Homburg	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4821	Hüttwilen	Hüttwilen	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4826	Mammern	Mammern	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4831	Müllheim	Müllheim	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4841	Pfyn	Pfyn	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2013	4846	Raperswilen	Raperswilen	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2013	4851	Salenstein	Salenstein	Bezirk Kreuzlingen	Thurgau	01.01.2011
TG	2012	4864	Steckborn	Steckborn	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2012	4871	Wagenhausen	Wagenhausen	Bezirk Frauenfeld	Thurgau	01.01.2011
TG	2015	4881	Amlikon-Bissegg	Amlikon-Bissegg	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4891	Berg (TG)	Berg (TG)	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4901	Birwinken	Birwinken	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4911	Bürglen (TG)	Bürglen (TG)	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4921	Bussnang	Bussnang	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4941	Märstetten	Märstetten	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4946	Weinfelden	Weinfelden	Bezirk Weinfelden	Thurgau	01.01.2011
TG	2015	4951	Wigoltingen	Wigoltingen	Bezirk Weinfelden	Thurgau	01.01.2011
TI	2101	5001	Arbedo-Castione	Arbedo-Castione	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5002	Bellinzona	Bellinzona	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5003	Cadenazzo	Cadenazzo	Distretto di Bellinzona	Ticino	13.03.2005
TI	2101	5004	Camorino	Camorino	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5005	Giubiasco	Giubiasco	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5006	Gnosca	Gnosca	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5007	Gorduno	Gorduno	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5008	Gudo	Gudo	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5009	Isone	Isone	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5010	Lumino	Lumino	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5012	Moleno	Moleno	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5013	Monte Carasso	Monte Carasso	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5014	Pianezzo	Pianezzo	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5015	Preonzo	Preonzo	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5017	Sant'Antonino	Sant'Antonino	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5018	Sant'Antonio	Sant'Antonio	Distretto di Bellinzona	Ticino	01.01.1960
TI	2101	5019	Sementina	Sementina	Distretto di Bellinzona	Ticino	01.01.1960
TI	2102	5048	Acquarossa	Acquarossa	Distretto di Blenio	Ticino	04.04.2004
TI	2102	5049	Blenio	Blenio	Distretto di Blenio	Ticino	22.10.2006
TI	2102	5050	Serravalle	Serravalle	Distretto di Blenio	Ticino	01.04.2012
TI	2103	5061	Airolo	Airolo	Distretto di Leventina	Ticino	01.01.1960
TI	2103	5063	Bedretto	Bedretto	Distretto di Leventina	Ticino	01.01.1960
TI	2103	5064	Bodio	Bodio	Distretto di Leventina	Ticino	01.01.1960
TI	2103	5071	Dalpe	Dalpe	Distretto di Leventina	Ticino	01.01.1960
TI	2103	5072	Faido	Faido	Distretto di Leventina	Ticino	01.04.2012
TI	2103	5073	Giornico	Giornico	Distretto di Leventina	Ticino	01.01.1960
TI	2103	5076	Personico	Personico	Distretto di Leventina	Ticino	01.01.1960
TI	2103	5077	Pollegio	Pollegio	Distretto di Leventina	Ticino	01.01.1960
TI	2103	5078	Prato (Leventina)	Prato (Leventina)	Distretto di Leventina	Ticino	01.01.1960
TI	2103	5079	Quinto	Quinto	Distretto di Leventina	Ticino	01.01.1960
TI	2103	5081	Sobrio	Sobrio	Distretto di Leventina	Ticino	01.01.1960
TI	2104	5091	Ascona	Ascona	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5095	Brione (Verzasca)	Brione (Verzasca)	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5096	Brione sopra Minusio	Brione sopra Minusio	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5097	Brissago	Brissago	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5102	Corippo	Corippo	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5105	Frasco	Frasco	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5108	Gordola	Gordola	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5109	Gresso	Gresso	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5112	Lavertezzo	Lavertezzo	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5113	Locarno	Locarno	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5115	Losone	Losone	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5117	Mergoscia	Mergoscia	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5118	Minusio	Minusio	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5119	Mosogno	Mosogno	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5120	Muralto	Muralto	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5121	Orselina	Orselina	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5125	Ronco sopra Ascona	Ronco sopra Ascona	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5129	Sonogno	Sonogno	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5131	Tenero-Contra	Tenero-Contra	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5132	Vergeletto	Vergeletto	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5135	Vogorno	Vogorno	Distretto di Locarno	Ticino	01.01.1960
TI	2104	5136	Onsernone	Onsernone	Distretto di Locarno	Ticino	01.01.1995
TI	2104	5137	Isorno	Isorno	Distretto di Locarno	Ticino	13.04.2001
TI	2104	5138	Cugnasco-Gerra	Cugnasco-Gerra	Distretto di Locarno	Ticino	20.04.2008
TI	2105	5141	Agno	Agno	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5143	Aranno	Aranno	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5144	Arogno	Arogno	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5146	Astano	Astano	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5148	Bedano	Bedano	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5149	Bedigliora	Bedigliora	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5151	Bioggio	Bioggio	Distretto di Lugano	Ticino	20.04.2008
TI	2105	5154	Bissone	Bissone	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5160	Brusino Arsizio	Brusino Arsizio	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5161	Cademario	Cademario	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5162	Cadempino	Cadempino	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5167	Canobbio	Canobbio	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5171	Caslano	Caslano	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5176	Comano	Comano	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5178	Croglio	Croglio	Distretto di Lugano	Ticino	04.04.1976
TI	2105	5180	Cureglia	Cureglia	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5181	Curio	Curio	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5186	Grancia	Grancia	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5187	Gravesano	Gravesano	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5189	Lamone	Lamone	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5192	Lugano	Lugano	Distretto di Lugano	Ticino	14.04.2013
TI	2105	5193	Magliaso	Magliaso	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5194	Manno	Manno	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5195	Maroggia	Maroggia	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5196	Massagno	Massagno	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5197	Melano	Melano	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5198	Melide	Melide	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5199	Mezzovico-Vira	Mezzovico-Vira	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5200	Miglieglia	Miglieglia	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5202	Monteggio	Monteggio	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5203	Morcote	Morcote	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5205	Muzzano	Muzzano	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5206	Neggio	Neggio	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5207	Novaggio	Novaggio	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5208	Origlio	Origlio	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5210	Paradiso	Paradiso	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5212	Ponte Capriasca	Ponte Capriasca	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5213	Ponte Tresa	Ponte Tresa	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5214	Porza	Porza	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5216	Pura	Pura	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5219	Rovio	Rovio	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5221	Savosa	Savosa	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5222	Sessa	Sessa	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5225	Sorengo	Sorengo	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5226	Capriasca	Capriasca	Distretto di Lugano	Ticino	20.04.2008
TI	2105	5227	Torricella-Taverne	Torricella-Taverne	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5230	Vernate	Vernate	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5231	Vezia	Vezia	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5233	Vico Morcote	Vico Morcote	Distretto di Lugano	Ticino	01.01.1960
TI	2105	5236	Collina d'Oro	Collina d'Oro	Distretto di Lugano	Ticino	01.04.2012
TI	2105	5237	Alto Malcantone	Alto Malcantone	Distretto di Lugano	Ticino	13.03.2005
TI	2105	5238	Monteceneri	Monteceneri	Distretto di Lugano	Ticino	21.11.2010
TI	2106	5242	Balerna	Balerna	Distretto di Mendrisio	Ticino	01.01.1960
TI	2106	5249	Castel San Pietro	Castel San Pietro	Distretto di Mendrisio	Ticino	04.04.2004
TI	2106	5250	Chiasso	Chiasso	Distretto di Mendrisio	Ticino	04.04.1976
TI	2106	5251	Coldrerio	Coldrerio	Distretto di Mendrisio	Ticino	01.01.1960
TI	2106	5254	Mendrisio	Mendrisio	Distretto di Mendrisio	Ticino	14.04.2013
TI	2106	5257	Morbio Inferiore	Morbio Inferiore	Distretto di Mendrisio	Ticino	01.01.1960
TI	2106	5260	Novazzano	Novazzano	Distretto di Mendrisio	Ticino	01.01.1960
TI	2106	5263	Riva San Vitale	Riva San Vitale	Distretto di Mendrisio	Ticino	01.01.1960
TI	2106	5266	Stabio	Stabio	Distretto di Mendrisio	Ticino	01.01.1960
TI	2106	5268	Vacallo	Vacallo	Distretto di Mendrisio	Ticino	01.01.1960
TI	2106	5269	Breggia	Breggia	Distretto di Mendrisio	Ticino	25.10.2009
TI	2107	5281	Biasca	Biasca	Distretto di Riviera	Ticino	01.01.1960
TI	2107	5282	Claro	Claro	Distretto di Riviera	Ticino	01.01.1960
TI	2107	5283	Cresciano	Cresciano	Distretto di Riviera	Ticino	01.01.1960
TI	2107	5284	Iragna	Iragna	Distretto di Riviera	Ticino	01.01.1960
TI	2107	5285	Lodrino	Lodrino	Distretto di Riviera	Ticino	01.01.1960
TI	2107	5286	Osogna	Osogna	Distretto di Riviera	Ticino	01.01.1960
TI	2108	5304	Bosco/Gurin	Bosco/Gurin	Distretto di Vallemaggia	Ticino	01.01.1960
TI	2108	5307	Campo (Vallemaggia)	Campo (Vallemaggia)	Distretto di Vallemaggia	Ticino	01.01.1960
TI	2108	5309	Cerentino	Cerentino	Distretto di Vallemaggia	Ticino	01.01.1960
TI	2108	5310	Cevio	Cevio	Distretto di Vallemaggia	Ticino	22.10.2006
TI	2108	5315	Linescio	Linescio	Distretto di Vallemaggia	Ticino	01.01.1960
TI	2108	5317	Maggia	Maggia	Distretto di Vallemaggia	Ticino	04.04.2004
TI	2108	5323	Lavizzara	Lavizzara	Distretto di Vallemaggia	Ticino	04.04.2004
TI	2108	5324	Avegno Gordevio	Avegno Gordevio	Distretto di Vallemaggia	Ticino	20.04.2008
TI	2104	5396	Terre di Pedemonte	Terre di Pedemonte	Distretto di Locarno	Ticino	14.04.2013
TI	2104	5397	Centovalli	Centovalli	Distretto di Locarno	Ticino	25.10.2009
TI	2104	5398	Gambarogno	Gambarogno	Distretto di Locarno	Ticino	25.04.2010
VD	2221	5401	Aigle	Aigle	District d'Aigle	Vaud	01.09.2006
VD	2221	5402	Bex	Bex	District d'Aigle	Vaud	01.09.2006
VD	2221	5403	Chessel	Chessel	District d'Aigle	Vaud	01.09.2006
VD	2221	5404	Corbeyrier	Corbeyrier	District d'Aigle	Vaud	01.09.2006
VD	2221	5405	Gryon	Gryon	District d'Aigle	Vaud	01.09.2006
VD	2221	5406	Lavey-Morcles	Lavey-Morcles	District d'Aigle	Vaud	01.09.2006
VD	2221	5407	Leysin	Leysin	District d'Aigle	Vaud	01.09.2006
VD	2221	5408	Noville	Noville	District d'Aigle	Vaud	01.09.2006
VD	2221	5409	Ollon	Ollon	District d'Aigle	Vaud	01.09.2006
VD	2221	5410	Ormont-Dessous	Ormont-Dessous	District d'Aigle	Vaud	01.09.2006
VD	2221	5411	Ormont-Dessus	Ormont-Dessus	District d'Aigle	Vaud	01.09.2006
VD	2221	5412	Rennaz	Rennaz	District d'Aigle	Vaud	01.09.2006
VD	2221	5413	Roche (VD)	Roche (VD)	District d'Aigle	Vaud	01.09.2006
VD	2221	5414	Villeneuve (VD)	Villeneuve (VD)	District d'Aigle	Vaud	01.09.2006
VD	2221	5415	Yvorne	Yvorne	District d'Aigle	Vaud	01.09.2006
VD	2227	5421	Apples	Apples	District de Morges	Vaud	01.09.2006
VD	2227	5422	Aubonne	Aubonne	District de Morges	Vaud	01.07.2011
VD	2227	5423	Ballens	Ballens	District de Morges	Vaud	01.09.2006
VD	2227	5424	Berolle	Berolle	District de Morges	Vaud	01.09.2006
VD	2227	5425	Bière	Bière	District de Morges	Vaud	01.09.2006
VD	2227	5426	Bougy-Villars	Bougy-Villars	District de Morges	Vaud	01.09.2006
VD	2227	5427	Féchy	Féchy	District de Morges	Vaud	01.09.2006
VD	2227	5428	Gimel	Gimel	District de Morges	Vaud	01.09.2006
VD	2228	5429	Longirod	Longirod	District de Nyon	Vaud	01.09.2006
VD	2228	5430	Marchissy	Marchissy	District de Nyon	Vaud	01.09.2006
VD	2227	5431	Mollens (VD)	Mollens (VD)	District de Morges	Vaud	01.09.2006
VD	2227	5432	Montherod	Montherod	District de Morges	Vaud	01.09.2006
VD	2228	5434	Saint-George	Saint-George	District de Nyon	Vaud	01.09.2006
VD	2227	5435	Saint-Livres	Saint-Livres	District de Morges	Vaud	01.09.2006
VD	2227	5436	Saint-Oyens	Saint-Oyens	District de Morges	Vaud	01.09.2006
VD	2227	5437	Saubraz	Saubraz	District de Morges	Vaud	01.09.2006
VD	2222	5451	Avenches	Avenches	District de la Broye-Vully	Vaud	01.07.2011
VD	2222	5456	Cudrefin	Cudrefin	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5458	Faoug	Faoug	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5464	Vully-les-Lacs	Vully-les-Lacs	District de la Broye-Vully	Vaud	01.07.2011
VD	2223	5471	Bettens	Bettens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5472	Bournens	Bournens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5473	Boussens	Boussens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2227	5474	La Chaux (Cossonay)	La Chaux (Cossonay)	District de Morges	Vaud	01.09.2006
VD	2227	5475	Chavannes-le-Veyron	Chavannes-le-Veyron	District de Morges	Vaud	01.09.2006
VD	2227	5476	Chevilly	Chevilly	District de Morges	Vaud	01.09.2006
VD	2227	5477	Cossonay	Cossonay	District de Morges	Vaud	01.09.2006
VD	2227	5478	Cottens (VD)	Cottens (VD)	District de Morges	Vaud	01.09.2006
VD	2227	5479	Cuarnens	Cuarnens	District de Morges	Vaud	01.09.2006
VD	2223	5480	Daillens	Daillens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2227	5481	Dizy	Dizy	District de Morges	Vaud	01.09.2006
VD	2227	5482	Eclépens	Eclépens	District de Morges	Vaud	01.09.2006
VD	2227	5483	Ferreyres	Ferreyres	District de Morges	Vaud	01.09.2006
VD	2227	5484	Gollion	Gollion	District de Morges	Vaud	01.09.2006
VD	2227	5485	Grancy	Grancy	District de Morges	Vaud	01.09.2006
VD	2227	5486	L'Isle	L'Isle	District de Morges	Vaud	01.09.2006
VD	2223	5487	Lussery-Villars	Lussery-Villars	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2227	5488	Mauraz	Mauraz	District de Morges	Vaud	01.09.2006
VD	2223	5489	Mex (VD)	Mex (VD)	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2227	5490	Moiry	Moiry	District de Morges	Vaud	01.09.2006
VD	2227	5491	Mont-la-Ville	Mont-la-Ville	District de Morges	Vaud	01.09.2006
VD	2227	5492	Montricher	Montricher	District de Morges	Vaud	01.09.2006
VD	2227	5493	Orny	Orny	District de Morges	Vaud	01.09.2006
VD	2227	5494	Pampigny	Pampigny	District de Morges	Vaud	01.09.2006
VD	2223	5495	Penthalaz	Penthalaz	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5496	Penthaz	Penthaz	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2227	5497	Pompaples	Pompaples	District de Morges	Vaud	01.09.2006
VD	2227	5498	La Sarraz	La Sarraz	District de Morges	Vaud	01.09.2006
VD	2227	5499	Senarclens	Senarclens	District de Morges	Vaud	01.09.2006
VD	2227	5500	Sévery	Sévery	District de Morges	Vaud	01.09.2006
VD	2223	5501	Sullens	Sullens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5503	Vufflens-la-Ville	Vufflens-la-Ville	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5511	Assens	Assens	District du Gros-de-Vaud	Vaud	01.01.2009
VD	2223	5512	Bercher	Bercher	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5513	Bioley-Orjulaz	Bioley-Orjulaz	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5514	Bottens	Bottens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5515	Bretigny-sur-Morrens	Bretigny-sur-Morrens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5516	Cugy (VD)	Cugy (VD)	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5518	Echallens	Echallens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5520	Essertines-sur-Yverdon	Essertines-sur-Yverdon	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5521	Etagnières	Etagnières	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5522	Fey	Fey	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5523	Froideville	Froideville	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5527	Morrens (VD)	Morrens (VD)	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5529	Oulens-sous-Echallens	Oulens-sous-Echallens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5530	Pailly	Pailly	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5531	Penthéréaz	Penthéréaz	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5533	Poliez-Pittet	Poliez-Pittet	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5534	Rueyres	Rueyres	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5535	Saint-Barthélemy (VD)	Saint-Barthélemy (VD)	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5537	Villars-le-Terroir	Villars-le-Terroir	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5539	Vuarrens	Vuarrens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2223	5540	Montilliez	Montilliez	District du Gros-de-Vaud	Vaud	01.07.2011
VD	2223	5541	Goumoëns	Goumoëns	District du Gros-de-Vaud	Vaud	01.07.2011
VD	2224	5551	Bonvillars	Bonvillars	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5552	Bullet	Bullet	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5553	Champagne	Champagne	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5554	Concise	Concise	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5555	Corcelles-près-Concise	Corcelles-près-Concise	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5556	Fiez	Fiez	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5557	Fontaines-sur-Grandson	Fontaines-sur-Grandson	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5559	Giez	Giez	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5560	Grandevent	Grandevent	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5561	Grandson	Grandson	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5562	Mauborget	Mauborget	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5563	Mutrux	Mutrux	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5564	Novalles	Novalles	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5565	Onnens (VD)	Onnens (VD)	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5566	Provence	Provence	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5568	Sainte-Croix	Sainte-Croix	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5571	Tévenon	Tévenon	District du Jura-Nord vaudois	Vaud	01.07.2011
VD	2226	5581	Belmont-sur-Lausanne	Belmont-sur-Lausanne	District de Lavaux-Oron	Vaud	01.09.2006
VD	2225	5582	Cheseaux-sur-Lausanne	Cheseaux-sur-Lausanne	District de Lausanne	Vaud	01.09.2006
VD	2229	5583	Crissier	Crissier	District de l'Ouest lausannois	Vaud	01.09.2006
VD	2225	5584	Epalinges	Epalinges	District de Lausanne	Vaud	01.09.2006
VD	2225	5585	Jouxtens-Mézery	Jouxtens-Mézery	District de Lausanne	Vaud	01.09.2006
VD	2225	5586	Lausanne	Lausanne	District de Lausanne	Vaud	01.09.2006
VD	2225	5587	Le Mont-sur-Lausanne	Le Mont-sur-Lausanne	District de Lausanne	Vaud	01.09.2006
VD	2226	5588	Paudex	Paudex	District de Lavaux-Oron	Vaud	01.09.2006
VD	2229	5589	Prilly	Prilly	District de l'Ouest lausannois	Vaud	01.09.2006
VD	2226	5590	Pully	Pully	District de Lavaux-Oron	Vaud	01.09.2006
VD	2229	5591	Renens (VD)	Renens (VD)	District de l'Ouest lausannois	Vaud	01.09.2006
VD	2225	5592	Romanel-sur-Lausanne	Romanel-sur-Lausanne	District de Lausanne	Vaud	01.09.2006
VD	2226	5601	Chexbres	Chexbres	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5604	Forel (Lavaux)	Forel (Lavaux)	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5606	Lutry	Lutry	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5607	Puidoux	Puidoux	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5609	Rivaz	Rivaz	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5610	Saint-Saphorin (Lavaux)	Saint-Saphorin (Lavaux)	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5611	Savigny	Savigny	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5613	Bourg-en-Lavaux	Bourg-en-Lavaux	District de Lavaux-Oron	Vaud	01.07.2011
VD	2227	5621	Aclens	Aclens	District de Morges	Vaud	01.09.2006
VD	2227	5622	Bremblens	Bremblens	District de Morges	Vaud	01.09.2006
VD	2227	5623	Buchillon	Buchillon	District de Morges	Vaud	01.09.2006
VD	2229	5624	Bussigny	Bussigny	District de l'Ouest lausannois	Vaud	01.05.2014
VD	2227	5625	Bussy-Chardonney	Bussy-Chardonney	District de Morges	Vaud	01.09.2006
VD	2229	5627	Chavannes-près-Renens	Chavannes-près-Renens	District de l'Ouest lausannois	Vaud	01.09.2006
VD	2227	5628	Chigny	Chigny	District de Morges	Vaud	01.09.2006
VD	2227	5629	Clarmont	Clarmont	District de Morges	Vaud	01.09.2006
VD	2227	5631	Denens	Denens	District de Morges	Vaud	01.09.2006
VD	2227	5632	Denges	Denges	District de Morges	Vaud	01.09.2006
VD	2227	5633	Echandens	Echandens	District de Morges	Vaud	01.09.2006
VD	2227	5634	Echichens	Echichens	District de Morges	Vaud	01.07.2011
VD	2229	5635	Ecublens (VD)	Ecublens (VD)	District de l'Ouest lausannois	Vaud	01.09.2006
VD	2227	5636	Etoy	Etoy	District de Morges	Vaud	01.09.2006
VD	2227	5637	Lavigny	Lavigny	District de Morges	Vaud	01.09.2006
VD	2227	5638	Lonay	Lonay	District de Morges	Vaud	01.09.2006
VD	2227	5639	Lully (VD)	Lully (VD)	District de Morges	Vaud	01.09.2006
VD	2227	5640	Lussy-sur-Morges	Lussy-sur-Morges	District de Morges	Vaud	01.09.2006
VD	2227	5642	Morges	Morges	District de Morges	Vaud	01.09.2006
VD	2227	5643	Préverenges	Préverenges	District de Morges	Vaud	01.09.2006
VD	2227	5644	Reverolle	Reverolle	District de Morges	Vaud	01.09.2006
VD	2227	5645	Romanel-sur-Morges	Romanel-sur-Morges	District de Morges	Vaud	01.09.2006
VD	2227	5646	Saint-Prex	Saint-Prex	District de Morges	Vaud	01.09.2006
VD	2229	5648	Saint-Sulpice (VD)	Saint-Sulpice (VD)	District de l'Ouest lausannois	Vaud	01.09.2006
VD	2227	5649	Tolochenaz	Tolochenaz	District de Morges	Vaud	01.09.2006
VD	2227	5650	Vaux-sur-Morges	Vaux-sur-Morges	District de Morges	Vaud	01.09.2006
VD	2229	5651	Villars-Sainte-Croix	Villars-Sainte-Croix	District de l'Ouest lausannois	Vaud	01.09.2006
VD	2227	5652	Villars-sous-Yens	Villars-sous-Yens	District de Morges	Vaud	01.09.2006
VD	2227	5653	Vufflens-le-Château	Vufflens-le-Château	District de Morges	Vaud	01.09.2006
VD	2227	5654	Vullierens	Vullierens	District de Morges	Vaud	01.09.2006
VD	2227	5655	Yens	Yens	District de Morges	Vaud	01.09.2006
VD	2223	5661	Boulens	Boulens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2222	5662	Brenles	Brenles	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5663	Bussy-sur-Moudon	Bussy-sur-Moudon	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5665	Chavannes-sur-Moudon	Chavannes-sur-Moudon	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5666	Chesalles-sur-Moudon	Chesalles-sur-Moudon	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5668	Cremin	Cremin	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5669	Curtilles	Curtilles	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5671	Dompierre (VD)	Dompierre (VD)	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5672	Forel-sur-Lucens	Forel-sur-Lucens	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5673	Hermenches	Hermenches	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5674	Lovatens	Lovatens	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5675	Lucens	Lucens	District de la Broye-Vully	Vaud	01.07.2011
VD	2222	5678	Moudon	Moudon	District de la Broye-Vully	Vaud	01.09.2006
VD	2223	5680	Ogens	Ogens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2222	5683	Prévonloup	Prévonloup	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5684	Rossenges	Rossenges	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5686	Sarzens	Sarzens	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5688	Syens	Syens	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5690	Villars-le-Comte	Villars-le-Comte	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5692	Vucherens	Vucherens	District de la Broye-Vully	Vaud	01.09.2006
VD	2223	5693	Montanaire	Montanaire	District du Gros-de-Vaud	Vaud	01.01.2013
VD	2228	5701	Arnex-sur-Nyon	Arnex-sur-Nyon	District de Nyon	Vaud	01.09.2006
VD	2228	5702	Arzier-Le Muids	Arzier-Le Muids	District de Nyon	Vaud	01.05.2014
VD	2228	5703	Bassins	Bassins	District de Nyon	Vaud	01.09.2006
VD	2228	5704	Begnins	Begnins	District de Nyon	Vaud	01.09.2006
VD	2228	5705	Bogis-Bossey	Bogis-Bossey	District de Nyon	Vaud	01.09.2006
VD	2228	5706	Borex	Borex	District de Nyon	Vaud	01.09.2006
VD	2228	5707	Chavannes-de-Bogis	Chavannes-de-Bogis	District de Nyon	Vaud	01.09.2006
VD	2228	5708	Chavannes-des-Bois	Chavannes-des-Bois	District de Nyon	Vaud	01.09.2006
VD	2228	5709	Chéserex	Chéserex	District de Nyon	Vaud	01.09.2006
VD	2228	5710	Coinsins	Coinsins	District de Nyon	Vaud	01.09.2006
VD	2228	5711	Commugny	Commugny	District de Nyon	Vaud	01.09.2006
VD	2228	5712	Coppet	Coppet	District de Nyon	Vaud	01.09.2006
VD	2228	5713	Crans-près-Céligny	Crans-près-Céligny	District de Nyon	Vaud	01.09.2006
VD	2228	5714	Crassier	Crassier	District de Nyon	Vaud	01.09.2006
VD	2228	5715	Duillier	Duillier	District de Nyon	Vaud	01.09.2006
VD	2228	5716	Eysins	Eysins	District de Nyon	Vaud	01.09.2006
VD	2228	5717	Founex	Founex	District de Nyon	Vaud	01.09.2006
VD	2228	5718	Genolier	Genolier	District de Nyon	Vaud	01.09.2006
VD	2228	5719	Gingins	Gingins	District de Nyon	Vaud	01.09.2006
VD	2228	5720	Givrins	Givrins	District de Nyon	Vaud	01.09.2006
VD	2228	5721	Gland	Gland	District de Nyon	Vaud	01.09.2006
VD	2228	5722	Grens	Grens	District de Nyon	Vaud	01.09.2006
VD	2228	5723	Mies	Mies	District de Nyon	Vaud	01.09.2006
VD	2228	5724	Nyon	Nyon	District de Nyon	Vaud	01.09.2006
VD	2228	5725	Prangins	Prangins	District de Nyon	Vaud	01.09.2006
VD	2228	5726	La Rippe	La Rippe	District de Nyon	Vaud	01.09.2006
VD	2228	5727	Saint-Cergue	Saint-Cergue	District de Nyon	Vaud	01.09.2006
VD	2228	5728	Signy-Avenex	Signy-Avenex	District de Nyon	Vaud	01.09.2006
VD	2228	5729	Tannay	Tannay	District de Nyon	Vaud	01.09.2006
VD	2228	5730	Trélex	Trélex	District de Nyon	Vaud	01.09.2006
VD	2228	5731	Le Vaud	Le Vaud	District de Nyon	Vaud	01.09.2006
VD	2228	5732	Vich	Vich	District de Nyon	Vaud	01.09.2006
VD	2224	5741	L'Abergement	L'Abergement	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5742	Agiez	Agiez	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5743	Arnex-sur-Orbe	Arnex-sur-Orbe	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5744	Ballaigues	Ballaigues	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5745	Baulmes	Baulmes	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5746	Bavois	Bavois	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5747	Bofflens	Bofflens	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5748	Bretonnières	Bretonnières	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5749	Chavornay	Chavornay	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5750	Les Clées	Les Clées	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5751	Corcelles-sur-Chavornay	Corcelles-sur-Chavornay	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5752	Croy	Croy	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5754	Juriens	Juriens	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5755	Lignerolle	Lignerolle	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5756	Montcherand	Montcherand	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5757	Orbe	Orbe	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5758	La Praz	La Praz	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5759	Premier	Premier	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5760	Rances	Rances	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5761	Romainmôtier-Envy	Romainmôtier-Envy	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5762	Sergey	Sergey	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5763	Valeyres-sous-Rances	Valeyres-sous-Rances	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5764	Vallorbe	Vallorbe	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5765	Vaulion	Vaulion	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5766	Vuiteboeuf	Vuiteboeuf	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2222	5782	Carrouge (VD)	Carrouge (VD)	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5785	Corcelles-le-Jorat	Corcelles-le-Jorat	District de la Broye-Vully	Vaud	01.09.2006
VD	2226	5788	Essertes	Essertes	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5789	Ferlens (VD)	Ferlens (VD)	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5790	Maracon	Maracon	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5791	Mézières (VD)	Mézières (VD)	District de Lavaux-Oron	Vaud	01.09.2006
VD	2226	5792	Montpreveyres	Montpreveyres	District de Lavaux-Oron	Vaud	01.09.2006
VD	2222	5798	Ropraz	Ropraz	District de la Broye-Vully	Vaud	01.09.2006
VD	2226	5799	Servion	Servion	District de Lavaux-Oron	Vaud	01.01.2012
VD	2222	5803	Vulliens	Vulliens	District de la Broye-Vully	Vaud	01.09.2006
VD	2223	5804	Jorat-Menthue	Jorat-Menthue	District du Gros-de-Vaud	Vaud	01.07.2011
VD	2226	5805	Oron	Oron	District de Lavaux-Oron	Vaud	01.01.2012
VD	2222	5812	Champtauroz	Champtauroz	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5813	Chevroux	Chevroux	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5816	Corcelles-près-Payerne	Corcelles-près-Payerne	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5817	Grandcour	Grandcour	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5819	Henniez	Henniez	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5821	Missy	Missy	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5822	Payerne	Payerne	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5827	Trey	Trey	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5828	Treytorrens (Payerne)	Treytorrens (Payerne)	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5830	Villarzel	Villarzel	District de la Broye-Vully	Vaud	01.09.2006
VD	2222	5831	Valbroye	Valbroye	District de la Broye-Vully	Vaud	01.07.2011
VD	2230	5841	Château-d'Oex	Château-d'Oex	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5842	Rossinière	Rossinière	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5843	Rougemont	Rougemont	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2227	5851	Allaman	Allaman	District de Morges	Vaud	01.09.2006
VD	2228	5852	Bursinel	Bursinel	District de Nyon	Vaud	01.09.2006
VD	2228	5853	Bursins	Bursins	District de Nyon	Vaud	01.09.2006
VD	2228	5854	Burtigny	Burtigny	District de Nyon	Vaud	01.09.2006
VD	2228	5855	Dully	Dully	District de Nyon	Vaud	01.09.2006
VD	2228	5856	Essertines-sur-Rolle	Essertines-sur-Rolle	District de Nyon	Vaud	01.09.2006
VD	2228	5857	Gilly	Gilly	District de Nyon	Vaud	01.09.2006
VD	2228	5858	Luins	Luins	District de Nyon	Vaud	01.09.2006
VD	2228	5859	Mont-sur-Rolle	Mont-sur-Rolle	District de Nyon	Vaud	01.09.2006
VD	2228	5860	Perroy	Perroy	District de Nyon	Vaud	01.09.2006
VD	2228	5861	Rolle	Rolle	District de Nyon	Vaud	01.09.2006
VD	2228	5862	Tartegnin	Tartegnin	District de Nyon	Vaud	01.09.2006
VD	2228	5863	Vinzel	Vinzel	District de Nyon	Vaud	01.09.2006
VD	2224	5871	L'Abbaye	L'Abbaye	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5872	Le Chenit	Le Chenit	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5873	Le Lieu	Le Lieu	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2230	5881	Blonay	Blonay	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5882	Chardonne	Chardonne	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5883	Corseaux	Corseaux	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5884	Corsier-sur-Vevey	Corsier-sur-Vevey	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5885	Jongny	Jongny	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5886	Montreux	Montreux	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5888	Saint-Légier-La Chiésaz	Saint-Légier-La Chiésaz	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5889	La Tour-de-Peilz	La Tour-de-Peilz	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5890	Vevey	Vevey	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2230	5891	Veytaux	Veytaux	District de la Riviera-Pays-d'Enhaut	Vaud	01.09.2006
VD	2224	5902	Belmont-sur-Yverdon	Belmont-sur-Yverdon	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5903	Bioley-Magnoux	Bioley-Magnoux	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5904	Chamblon	Chamblon	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5905	Champvent	Champvent	District du Jura-Nord vaudois	Vaud	01.01.2012
VD	2224	5907	Chavannes-le-Chêne	Chavannes-le-Chêne	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5908	Chêne-Pâquier	Chêne-Pâquier	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5909	Cheseaux-Noréaz	Cheseaux-Noréaz	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5910	Cronay	Cronay	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5911	Cuarny	Cuarny	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5912	Démoret	Démoret	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5913	Donneloye	Donneloye	District du Jura-Nord vaudois	Vaud	01.01.2012
VD	2224	5914	Ependes (VD)	Ependes (VD)	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5915	Essert-Pittet	Essert-Pittet	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5919	Mathod	Mathod	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5921	Molondin	Molondin	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5922	Montagny-près-Yverdon	Montagny-près-Yverdon	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2223	5923	Oppens	Oppens	District du Gros-de-Vaud	Vaud	01.09.2006
VD	2224	5924	Orges	Orges	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5925	Orzens	Orzens	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5926	Pomy	Pomy	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5928	Rovray	Rovray	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5929	Suchy	Suchy	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5930	Suscévaz	Suscévaz	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5931	Treycovagnes	Treycovagnes	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5932	Ursins	Ursins	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5933	Valeyres-sous-Montagny	Valeyres-sous-Montagny	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5934	Valeyres-sous-Ursins	Valeyres-sous-Ursins	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5935	Villars-Epeney	Villars-Epeney	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5937	Vugelles-La Mothe	Vugelles-La Mothe	District du Jura-Nord vaudois	Vaud	01.09.2006
VD	2224	5938	Yverdon-les-Bains	Yverdon-les-Bains	District du Jura-Nord vaudois	Vaud	01.07.2011
VD	2224	5939	Yvonand	Yvonand	District du Jura-Nord vaudois	Vaud	01.09.2006
VS	2301	6002	Brig-Glis	Brig-Glis	Bezirk Brig	Valais / Wallis	01.10.1972
VS	2301	6004	Eggerberg	Eggerberg	Bezirk Brig	Valais / Wallis	01.01.1960
VS	2301	6007	Naters	Naters	Bezirk Brig	Valais / Wallis	01.01.2013
VS	2301	6008	Ried-Brig	Ried-Brig	Bezirk Brig	Valais / Wallis	01.01.1994
VS	2301	6009	Simplon	Simplon	Bezirk Brig	Valais / Wallis	01.01.1960
VS	2301	6010	Termen	Termen	Bezirk Brig	Valais / Wallis	01.01.1960
VS	2301	6011	Zwischbergen	Zwischbergen	Bezirk Brig	Valais / Wallis	01.01.1960
VS	2302	6021	Ardon	Ardon	District de Conthey	Valais / Wallis	01.01.1960
VS	2302	6022	Chamoson	Chamoson	District de Conthey	Valais / Wallis	01.01.1960
VS	2302	6023	Conthey	Conthey	District de Conthey	Valais / Wallis	01.01.1960
VS	2302	6024	Nendaz	Nendaz	District de Conthey	Valais / Wallis	01.01.1960
VS	2302	6025	Vétroz	Vétroz	District de Conthey	Valais / Wallis	01.01.1960
VS	2303	6031	Bagnes	Bagnes	District d'Entremont	Valais / Wallis	01.01.1960
VS	2303	6032	Bourg-Saint-Pierre	Bourg-Saint-Pierre	District d'Entremont	Valais / Wallis	01.01.1960
VS	2303	6033	Liddes	Liddes	District d'Entremont	Valais / Wallis	01.01.1960
VS	2303	6034	Orsières	Orsières	District d'Entremont	Valais / Wallis	01.01.1960
VS	2303	6035	Sembrancher	Sembrancher	District d'Entremont	Valais / Wallis	01.01.1960
VS	2303	6036	Vollèges	Vollèges	District d'Entremont	Valais / Wallis	01.01.1960
VS	2304	6052	Bellwald	Bellwald	Bezirk Goms	Valais / Wallis	01.01.1960
VS	2304	6054	Binn	Binn	Bezirk Goms	Valais / Wallis	01.01.1960
VS	2304	6055	Blitzingen	Blitzingen	Bezirk Goms	Valais / Wallis	01.01.1960
VS	2304	6056	Ernen	Ernen	Bezirk Goms	Valais / Wallis	01.10.2004
VS	2304	6057	Fiesch	Fiesch	Bezirk Goms	Valais / Wallis	01.01.1960
VS	2304	6058	Fieschertal	Fieschertal	Bezirk Goms	Valais / Wallis	01.01.1960
VS	2304	6061	Lax	Lax	Bezirk Goms	Valais / Wallis	01.01.1960
VS	2304	6064	Niederwald	Niederwald	Bezirk Goms	Valais / Wallis	01.01.1960
VS	2304	6073	Grafschaft	Grafschaft	Bezirk Goms	Valais / Wallis	01.10.2000
VS	2304	6074	Münster-Geschinen	Münster-Geschinen	Bezirk Goms	Valais / Wallis	01.10.2004
VS	2304	6075	Reckingen-Gluringen	Reckingen-Gluringen	Bezirk Goms	Valais / Wallis	01.10.2004
VS	2304	6076	Obergoms	Obergoms	Bezirk Goms	Valais / Wallis	01.01.2009
VS	2305	6081	Les Agettes	Les Agettes	District d'Hérens	Valais / Wallis	01.01.1965
VS	2305	6082	Ayent	Ayent	District d'Hérens	Valais / Wallis	01.01.1960
VS	2305	6083	Evolène	Evolène	District d'Hérens	Valais / Wallis	01.01.1960
VS	2305	6084	Hérémence	Hérémence	District d'Hérens	Valais / Wallis	01.01.1960
VS	2305	6087	Saint-Martin (VS)	Saint-Martin (VS)	District d'Hérens	Valais / Wallis	01.01.1960
VS	2305	6089	Vex	Vex	District d'Hérens	Valais / Wallis	01.01.1960
VS	2305	6090	Mont-Noble	Mont-Noble	District d'Hérens	Valais / Wallis	01.01.2011
VS	2306	6101	Agarn	Agarn	Bezirk Leuk	Valais / Wallis	01.01.1960
VS	2306	6102	Albinen	Albinen	Bezirk Leuk	Valais / Wallis	01.01.1960
VS	2306	6104	Ergisch	Ergisch	Bezirk Leuk	Valais / Wallis	01.01.1960
VS	2306	6109	Inden	Inden	Bezirk Leuk	Valais / Wallis	01.01.1960
VS	2306	6110	Leuk	Leuk	Bezirk Leuk	Valais / Wallis	01.01.2013
VS	2306	6111	Leukerbad	Leukerbad	Bezirk Leuk	Valais / Wallis	01.01.1960
VS	2306	6112	Oberems	Oberems	Bezirk Leuk	Valais / Wallis	01.01.1960
VS	2306	6113	Salgesch	Salgesch	Bezirk Leuk	Valais / Wallis	01.01.1960
VS	2306	6116	Varen	Varen	Bezirk Leuk	Valais / Wallis	01.01.1960
VS	2306	6117	Guttet-Feschel	Guttet-Feschel	Bezirk Leuk	Valais / Wallis	01.10.2000
VS	2306	6118	Gampel-Bratsch	Gampel-Bratsch	Bezirk Leuk	Valais / Wallis	01.01.2009
VS	2306	6119	Turtmann-Unterems	Turtmann-Unterems	Bezirk Leuk	Valais / Wallis	01.01.2013
VS	2307	6131	Bovernier	Bovernier	District de Martigny	Valais / Wallis	01.01.1960
VS	2307	6132	Charrat	Charrat	District de Martigny	Valais / Wallis	01.01.1960
VS	2307	6133	Fully	Fully	District de Martigny	Valais / Wallis	01.01.1960
VS	2307	6134	Isérables	Isérables	District de Martigny	Valais / Wallis	01.01.1960
VS	2307	6135	Leytron	Leytron	District de Martigny	Valais / Wallis	01.01.1960
VS	2307	6136	Martigny	Martigny	District de Martigny	Valais / Wallis	01.08.1964
VS	2307	6137	Martigny-Combe	Martigny-Combe	District de Martigny	Valais / Wallis	01.01.1960
VS	2307	6139	Riddes	Riddes	District de Martigny	Valais / Wallis	01.01.1960
VS	2307	6140	Saillon	Saillon	District de Martigny	Valais / Wallis	01.01.1960
VS	2307	6141	Saxon	Saxon	District de Martigny	Valais / Wallis	01.01.1960
VS	2307	6142	Trient	Trient	District de Martigny	Valais / Wallis	01.01.1960
VS	2308	6151	Champéry	Champéry	District de Monthey	Valais / Wallis	01.01.1960
VS	2308	6152	Collombey-Muraz	Collombey-Muraz	District de Monthey	Valais / Wallis	01.01.1960
VS	2308	6153	Monthey	Monthey	District de Monthey	Valais / Wallis	01.01.1960
VS	2308	6154	Port-Valais	Port-Valais	District de Monthey	Valais / Wallis	01.01.1960
VS	2308	6155	Saint-Gingolph	Saint-Gingolph	District de Monthey	Valais / Wallis	01.01.1960
VS	2308	6156	Troistorrents	Troistorrents	District de Monthey	Valais / Wallis	01.01.1960
VS	2308	6157	Val-d'Illiez	Val-d'Illiez	District de Monthey	Valais / Wallis	01.01.1960
VS	2308	6158	Vionnaz	Vionnaz	District de Monthey	Valais / Wallis	01.01.1960
VS	2308	6159	Vouvry	Vouvry	District de Monthey	Valais / Wallis	01.01.1960
VS	2309	6172	Bister	Bister	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6173	Bitsch	Bitsch	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6177	Grengiols	Grengiols	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6181	Riederalp	Riederalp	Bezirk Raron	Valais / Wallis	01.11.2003
VS	2309	6191	Ausserberg	Ausserberg	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6192	Blatten	Blatten	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6193	Bürchen	Bürchen	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6194	Eischoll	Eischoll	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6195	Ferden	Ferden	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6197	Kippel	Kippel	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6198	Niedergesteln	Niedergesteln	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6199	Raron	Raron	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6201	Unterbäch	Unterbäch	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6202	Wiler (Lötschen)	Wiler (Lötschen)	Bezirk Raron	Valais / Wallis	01.01.1960
VS	2309	6203	Mörel-Filet	Mörel-Filet	Bezirk Raron	Valais / Wallis	01.01.2009
VS	2309	6204	Steg-Hohtenn	Steg-Hohtenn	Bezirk Raron	Valais / Wallis	01.01.2009
VS	2309	6205	Bettmeralp	Bettmeralp	Bezirk Raron	Valais / Wallis	01.01.2014
VS	2310	6211	Collonges	Collonges	District de Saint-Maurice	Valais / Wallis	01.01.1960
VS	2310	6212	Dorénaz	Dorénaz	District de Saint-Maurice	Valais / Wallis	01.01.1960
VS	2310	6213	Evionnaz	Evionnaz	District de Saint-Maurice	Valais / Wallis	01.01.1960
VS	2310	6214	Finhaut	Finhaut	District de Saint-Maurice	Valais / Wallis	01.01.1960
VS	2310	6215	Massongex	Massongex	District de Saint-Maurice	Valais / Wallis	01.01.1960
VS	2310	6217	Saint-Maurice	Saint-Maurice	District de Saint-Maurice	Valais / Wallis	01.01.2013
VS	2310	6218	Salvan	Salvan	District de Saint-Maurice	Valais / Wallis	01.01.1960
VS	2310	6219	Vernayaz	Vernayaz	District de Saint-Maurice	Valais / Wallis	01.01.1960
VS	2310	6220	Vérossaz	Vérossaz	District de Saint-Maurice	Valais / Wallis	01.01.1960
VS	2311	6232	Chalais	Chalais	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6234	Chermignon	Chermignon	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6235	Chippis	Chippis	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6238	Grône	Grône	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6239	Icogne	Icogne	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6240	Lens	Lens	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6241	Miège	Miège	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6242	Mollens (VS)	Mollens (VS)	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6243	Montana	Montana	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6244	Randogne	Randogne	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6246	Saint-Léonard	Saint-Léonard	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6248	Sierre	Sierre	District de Sierre	Valais / Wallis	01.10.1972
VS	2311	6249	Venthône	Venthône	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6250	Veyras	Veyras	District de Sierre	Valais / Wallis	01.01.1960
VS	2311	6252	Anniviers	Anniviers	District de Sierre	Valais / Wallis	01.01.2009
VS	2312	6261	Arbaz	Arbaz	District de Sion	Valais / Wallis	01.01.1960
VS	2312	6263	Grimisuat	Grimisuat	District de Sion	Valais / Wallis	01.01.1960
VS	2312	6265	Savièse	Savièse	District de Sion	Valais / Wallis	01.01.1960
VS	2312	6266	Sion	Sion	District de Sion	Valais / Wallis	01.01.2013
VS	2312	6267	Veysonnaz	Veysonnaz	District de Sion	Valais / Wallis	01.01.1960
VS	2313	6281	Baltschieder	Baltschieder	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6282	Eisten	Eisten	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6283	Embd	Embd	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6285	Grächen	Grächen	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6286	Lalden	Lalden	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6287	Randa	Randa	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6288	Saas-Almagell	Saas-Almagell	Bezirk Visp	Valais / Wallis	01.01.2007
VS	2313	6289	Saas-Balen	Saas-Balen	Bezirk Visp	Valais / Wallis	01.01.2007
VS	2313	6290	Saas-Fee	Saas-Fee	Bezirk Visp	Valais / Wallis	01.01.2007
VS	2313	6291	Saas-Grund	Saas-Grund	Bezirk Visp	Valais / Wallis	01.01.2007
VS	2313	6292	St. Niklaus	St. Niklaus	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6293	Stalden (VS)	Stalden (VS)	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6294	Staldenried	Staldenried	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6295	Täsch	Täsch	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6296	Törbel	Törbel	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6297	Visp	Visp	Bezirk Visp	Valais / Wallis	01.10.1972
VS	2313	6298	Visperterminen	Visperterminen	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6299	Zeneggen	Zeneggen	Bezirk Visp	Valais / Wallis	01.01.1960
VS	2313	6300	Zermatt	Zermatt	Bezirk Visp	Valais / Wallis	01.01.1960
NE	2401	6402	Bevaix	Bevaix	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6404	Boudry	Boudry	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6405	Brot-Dessous	Brot-Dessous	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6407	Corcelles-Cormondrèche	Corcelles-Cormondrèche	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6408	Cortaillod	Cortaillod	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6409	Fresens	Fresens	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6410	Gorgier	Gorgier	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6411	Montalchez	Montalchez	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6412	Peseux	Peseux	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6413	Rochefort	Rochefort	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6414	Saint-Aubin-Sauges	Saint-Aubin-Sauges	District de Boudry	Neuchâtel	01.01.1960
NE	2401	6415	Vaumarcus	Vaumarcus	District de Boudry	Neuchâtel	01.01.1966
NE	2401	6416	Milvignes	Milvignes	District de Boudry	Neuchâtel	01.01.2013
NE	2402	6421	La Chaux-de-Fonds	La Chaux-de-Fonds	District de la Chaux-de-Fonds	Neuchâtel	01.01.1960
NE	2402	6422	Les Planchettes	Les Planchettes	District de la Chaux-de-Fonds	Neuchâtel	01.01.1960
NE	2402	6423	La Sagne	La Sagne	District de la Chaux-de-Fonds	Neuchâtel	01.01.1960
NE	2403	6431	Les Brenets	Les Brenets	District du Locle	Neuchâtel	01.01.1960
NE	2403	6432	La Brévine	La Brévine	District du Locle	Neuchâtel	01.01.1960
NE	2403	6433	Brot-Plamboz	Brot-Plamboz	District du Locle	Neuchâtel	01.01.1960
NE	2403	6434	Le Cerneux-Péquignot	Le Cerneux-Péquignot	District du Locle	Neuchâtel	01.01.1960
NE	2403	6435	La Chaux-du-Milieu	La Chaux-du-Milieu	District du Locle	Neuchâtel	01.01.1960
NE	2403	6436	Le Locle	Le Locle	District du Locle	Neuchâtel	01.01.1960
NE	2403	6437	Les Ponts-de-Martel	Les Ponts-de-Martel	District du Locle	Neuchâtel	01.01.1960
NE	2404	6451	Cornaux	Cornaux	District de Neuchâtel	Neuchâtel	01.01.1960
NE	2404	6452	Cressier (NE)	Cressier (NE)	District de Neuchâtel	Neuchâtel	01.01.1960
NE	2404	6453	Enges	Enges	District de Neuchâtel	Neuchâtel	01.01.1960
NE	2404	6454	Hauterive (NE)	Hauterive (NE)	District de Neuchâtel	Neuchâtel	01.01.2001
NE	2404	6455	Le Landeron	Le Landeron	District de Neuchâtel	Neuchâtel	01.01.1966
NE	2404	6456	Lignières	Lignières	District de Neuchâtel	Neuchâtel	01.01.1960
NE	2404	6458	Neuchâtel	Neuchâtel	District de Neuchâtel	Neuchâtel	01.01.1960
NE	2404	6459	Saint-Blaise	Saint-Blaise	District de Neuchâtel	Neuchâtel	01.01.1960
NE	2404	6461	La Tène	La Tène	District de Neuchâtel	Neuchâtel	01.01.2009
NE	2405	6485	Valangin	Valangin	District du Val-de-Ruz	Neuchâtel	01.01.1960
NE	2405	6487	Val-de-Ruz	Val-de-Ruz	District du Val-de-Ruz	Neuchâtel	01.01.2013
NE	2406	6504	La Côte-aux-Fées	La Côte-aux-Fées	District du Val-de-Travers	Neuchâtel	01.01.1960
NE	2406	6511	Les Verrières	Les Verrières	District du Val-de-Travers	Neuchâtel	01.01.1960
NE	2406	6512	Val-de-Travers	Val-de-Travers	District du Val-de-Travers	Neuchâtel	01.01.2009
GE	2500	6601	Aire-la-Ville	Aire-la-Ville	Canton de Genève	Genève	01.01.1960
GE	2500	6602	Anières	Anières	Canton de Genève	Genève	01.01.1960
GE	2500	6603	Avully	Avully	Canton de Genève	Genève	01.01.1960
GE	2500	6604	Avusy	Avusy	Canton de Genève	Genève	01.01.1960
GE	2500	6605	Bardonnex	Bardonnex	Canton de Genève	Genève	01.01.1960
GE	2500	6606	Bellevue	Bellevue	Canton de Genève	Genève	01.01.1960
GE	2500	6607	Bernex	Bernex	Canton de Genève	Genève	01.01.1960
GE	2500	6608	Carouge (GE)	Carouge (GE)	Canton de Genève	Genève	01.01.1960
GE	2500	6609	Cartigny	Cartigny	Canton de Genève	Genève	01.01.1960
GE	2500	6610	Céligny	Céligny	Canton de Genève	Genève	01.01.1960
GE	2500	6611	Chancy	Chancy	Canton de Genève	Genève	01.01.1960
GE	2500	6612	Chêne-Bougeries	Chêne-Bougeries	Canton de Genève	Genève	01.01.1960
GE	2500	6613	Chêne-Bourg	Chêne-Bourg	Canton de Genève	Genève	01.01.1960
GE	2500	6614	Choulex	Choulex	Canton de Genève	Genève	01.01.1960
GE	2500	6615	Collex-Bossy	Collex-Bossy	Canton de Genève	Genève	01.01.1960
GE	2500	6616	Collonge-Bellerive	Collonge-Bellerive	Canton de Genève	Genève	01.01.1960
GE	2500	6617	Cologny	Cologny	Canton de Genève	Genève	01.01.1960
GE	2500	6618	Confignon	Confignon	Canton de Genève	Genève	01.01.1960
GE	2500	6619	Corsier (GE)	Corsier (GE)	Canton de Genève	Genève	01.01.1960
GE	2500	6620	Dardagny	Dardagny	Canton de Genève	Genève	01.01.1960
GE	2500	6621	Genève	Genève	Canton de Genève	Genève	01.01.1960
GE	2500	6622	Genthod	Genthod	Canton de Genève	Genève	01.01.1960
GE	2500	6623	Le Grand-Saconnex	Le Grand-Saconnex	Canton de Genève	Genève	01.01.1960
GE	2500	6624	Gy	Gy	Canton de Genève	Genève	01.01.1960
GE	2500	6625	Hermance	Hermance	Canton de Genève	Genève	01.01.1960
GE	2500	6626	Jussy	Jussy	Canton de Genève	Genève	01.01.1960
GE	2500	6627	Laconnex	Laconnex	Canton de Genève	Genève	01.01.1960
GE	2500	6628	Lancy	Lancy	Canton de Genève	Genève	01.01.1960
GE	2500	6629	Meinier	Meinier	Canton de Genève	Genève	01.01.1960
GE	2500	6630	Meyrin	Meyrin	Canton de Genève	Genève	01.01.1960
GE	2500	6631	Onex	Onex	Canton de Genève	Genève	01.01.1960
GE	2500	6632	Perly-Certoux	Perly-Certoux	Canton de Genève	Genève	01.01.1960
GE	2500	6633	Plan-les-Ouates	Plan-les-Ouates	Canton de Genève	Genève	01.01.1960
GE	2500	6634	Pregny-Chambésy	Pregny-Chambésy	Canton de Genève	Genève	01.01.1960
GE	2500	6635	Presinge	Presinge	Canton de Genève	Genève	01.01.1960
GE	2500	6636	Puplinge	Puplinge	Canton de Genève	Genève	01.01.1960
GE	2500	6637	Russin	Russin	Canton de Genève	Genève	01.01.1960
GE	2500	6638	Satigny	Satigny	Canton de Genève	Genève	01.01.1960
GE	2500	6639	Soral	Soral	Canton de Genève	Genève	01.01.1960
GE	2500	6640	Thônex	Thônex	Canton de Genève	Genève	01.01.1960
GE	2500	6641	Troinex	Troinex	Canton de Genève	Genève	01.01.1960
GE	2500	6642	Vandoeuvres	Vandoeuvres	Canton de Genève	Genève	01.01.1960
GE	2500	6643	Vernier	Vernier	Canton de Genève	Genève	01.01.1960
GE	2500	6644	Versoix	Versoix	Canton de Genève	Genève	01.01.1960
GE	2500	6645	Veyrier	Veyrier	Canton de Genève	Genève	01.01.1960
JU	2601	6702	Boécourt	Boécourt	District de Delémont	Jura	01.01.1979
JU	2601	6703	Bourrignon	Bourrignon	District de Delémont	Jura	01.01.1979
JU	2601	6704	Châtillon (JU)	Châtillon (JU)	District de Delémont	Jura	01.01.1979
JU	2601	6705	Corban	Corban	District de Delémont	Jura	01.01.1979
JU	2601	6706	Courchapoix	Courchapoix	District de Delémont	Jura	01.01.1979
JU	2601	6708	Courrendlin	Courrendlin	District de Delémont	Jura	01.01.1979
JU	2601	6709	Courroux	Courroux	District de Delémont	Jura	01.01.1979
JU	2601	6710	Courtételle	Courtételle	District de Delémont	Jura	01.01.1979
JU	2601	6711	Delémont	Delémont	District de Delémont	Jura	01.01.1979
JU	2601	6712	Develier	Develier	District de Delémont	Jura	01.01.1979
JU	2601	6713	Ederswiler	Ederswiler	District de Delémont	Jura	01.01.1979
JU	2601	6715	Mervelier	Mervelier	District de Delémont	Jura	01.01.1979
JU	2601	6716	Mettembert	Mettembert	District de Delémont	Jura	01.01.1984
JU	2601	6718	Movelier	Movelier	District de Delémont	Jura	01.01.1979
JU	2601	6719	Pleigne	Pleigne	District de Delémont	Jura	01.01.1979
JU	2601	6720	Rebeuvelier	Rebeuvelier	District de Delémont	Jura	01.01.1979
JU	2601	6721	Rossemaison	Rossemaison	District de Delémont	Jura	01.01.1979
JU	2601	6722	Saulcy	Saulcy	District de Delémont	Jura	01.01.1979
JU	2601	6724	Soyhières	Soyhières	District de Delémont	Jura	01.01.1979
JU	2601	6728	Vellerat	Vellerat	District de Delémont	Jura	01.07.1996
JU	2601	6729	Haute-Sorne	Haute-Sorne	District de Delémont	Jura	01.01.2013
JU	2601	6730	Val Terbi	Val Terbi	District de Delémont	Jura	01.01.2013
JU	2602	6741	Le Bémont (JU)	Le Bémont (JU)	District des Franches-Montagnes	Jura	01.01.1979
JU	2602	6742	Les Bois	Les Bois	District des Franches-Montagnes	Jura	01.01.1979
JU	2602	6743	Les Breuleux	Les Breuleux	District des Franches-Montagnes	Jura	01.01.1979
JU	2602	6744	La Chaux-des-Breuleux	La Chaux-des-Breuleux	District des Franches-Montagnes	Jura	01.01.1979
JU	2602	6745	Les Enfers	Les Enfers	District des Franches-Montagnes	Jura	01.01.1979
JU	2602	6748	Les Genevez (JU)	Les Genevez (JU)	District des Franches-Montagnes	Jura	01.01.1979
JU	2602	6750	Lajoux (JU)	Lajoux (JU)	District des Franches-Montagnes	Jura	01.01.1979
JU	2602	6751	Montfaucon	Montfaucon	District des Franches-Montagnes	Jura	01.01.2009
JU	2602	6753	Muriaux	Muriaux	District des Franches-Montagnes	Jura	01.01.2009
JU	2602	6754	Le Noirmont	Le Noirmont	District des Franches-Montagnes	Jura	01.01.1979
JU	2602	6757	Saignelégier	Saignelégier	District des Franches-Montagnes	Jura	01.01.2009
JU	2602	6758	Saint-Brais	Saint-Brais	District des Franches-Montagnes	Jura	01.01.1979
JU	2602	6759	Soubey	Soubey	District des Franches-Montagnes	Jura	01.01.1979
JU	2603	6771	Alle	Alle	District de Porrentruy	Jura	01.01.1979
JU	2603	6773	Beurnevésin	Beurnevésin	District de Porrentruy	Jura	01.01.1979
JU	2603	6774	Boncourt	Boncourt	District de Porrentruy	Jura	01.01.1979
JU	2603	6775	Bonfol	Bonfol	District de Porrentruy	Jura	01.01.1979
JU	2603	6778	Bure	Bure	District de Porrentruy	Jura	01.01.1979
JU	2603	6781	Coeuve	Coeuve	District de Porrentruy	Jura	01.01.1979
JU	2603	6782	Cornol	Cornol	District de Porrentruy	Jura	01.01.1979
JU	2603	6783	Courchavon	Courchavon	District de Porrentruy	Jura	01.01.1979
JU	2603	6784	Courgenay	Courgenay	District de Porrentruy	Jura	01.01.1979
JU	2603	6785	Courtedoux	Courtedoux	District de Porrentruy	Jura	01.01.1979
JU	2603	6787	Damphreux	Damphreux	District de Porrentruy	Jura	01.01.1979
JU	2603	6789	Fahy	Fahy	District de Porrentruy	Jura	01.01.1979
JU	2603	6790	Fontenais	Fontenais	District de Porrentruy	Jura	01.01.2013
JU	2603	6792	Grandfontaine	Grandfontaine	District de Porrentruy	Jura	01.01.1979
JU	2603	6793	Lugnez	Lugnez	District de Porrentruy	Jura	01.01.1979
JU	2603	6800	Porrentruy	Porrentruy	District de Porrentruy	Jura	01.01.1979
JU	2603	6803	Rocourt	Rocourt	District de Porrentruy	Jura	01.01.1979
JU	2603	6806	Vendlincourt	Vendlincourt	District de Porrentruy	Jura	01.01.1979
JU	2603	6807	Basse-Allaine	Basse-Allaine	District de Porrentruy	Jura	01.01.2009
JU	2603	6808	Clos du Doubs	Clos du Doubs	District de Porrentruy	Jura	01.01.2009
JU	2603	6809	Haute-Ajoie	Haute-Ajoie	District de Porrentruy	Jura	01.01.2009
JU	2603	6810	La Baroche	La Baroche	District de Porrentruy	Jura	01.01.2009

101 4 Hausen am Albis Hausen am Albis Bezirk Affoltern Zürich"""  # Collez ici toute la liste que vous avez partagée
    
    cities = []
    
    # Traiter chaque ligne
    for line in raw_data.split('\n'):
        if not line.strip():
            continue
            
        parts = line.strip().split()
        if len(parts) >= 6:
            # Le NPA est le 3ème élément (index 2)
            # Le canton est le dernier élément
            # Le nom est tout ce qui est entre les deux
            zip_code = parts[2]
            canton = parts[-1]
            
            # Extraire le nom en excluant Bezirk/District/etc
            name_parts = []
            for part in parts[3:]:
                if part in ['Bezirk', 'District', 'Distretto']:
                    break
                name_parts.append(part)
            
            city_name = ' '.join(name_parts)
            
            cities.append({
                "zip": zip_code,
                "name": city_name,
                "canton": canton
            })
    
    # Sauvegarder en JSON
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 'cities.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"cities": cities}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(cities)} communes sauvegardées dans cities.json")

if __name__ == "__main__":
    create_cities_json()
