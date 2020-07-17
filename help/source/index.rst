.. Yleiskaava documentation master file, created by
   sphinx-quickstart on Sun Feb 12 17:11:03 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tervetuloa Yleiskaava-työkalun dokumentaatioon!
===============================================

Contents:

.. toctree::
   :maxdepth: 2

Toiminnot
=========

* Kopioi lähdeaineistoa tietokantaan


Kopioi lähdeaineistoa tietokantaan
..................................

Kopiointi lähdekarttatasosta yleiskaavan tietokantaan onnistuu seuraavin vaihein:

#. Valitse lähdekarttataso sekä kohdekaavakohdetaulu ja kohdekentät haluamillesi lähdekarttatason kentille. Kun jätät lähdekenttää vastaavan kohdekentän arvon tyhjäksi, niin ko. lähdekentän arvoja ei kopioida kohdetauluun, mutta esim. kaavan nimi ja numero huomioidaan silti myöhemmin. Kun jätät kohdekentän valitsematta, niin sille ei kopioida lähdetaulusta arvoa, mutta voit myöhemmin halutessasi asettaa sille joka tapauksessa oletusarvon. Klikkaa Seuraava-painiketta, kun olet asettanut haluamillesi lähdekarttatason kentille kohdetaulun kentän.
#. Valitse lähdekarttatason attribuuttitaulusta tietokantaan kopioitavat kohteet ja klikkaa sitten Seuraava-painiketta. Voit halutessasi sulkea lähdekarttatason attribuuttitaulun valittuasi kopioitavat kohteet.
#. Valitse tarvittaessa oletusarvot pakollisille kohdetaulujen kentille ja mahdollisesti muita kopiointiasetuksia, kuten tehdäänkö kaavamääräysotsikkoa vastaava kaavamääräys, jos sitä ei jo ole. Klikkaa Aja-painiketta aloittaaksesi lähdekarttatason kohteiden kopioinnin yleiskaavan tietokantaan.

.. Voit halutessasi tarkistaa ajamisen seurauksena tehtävän kopion aiheuttamat muutokset tietokantaan "Näytä ajolla tehtävät muutokset"-painikkeella.


Kaaavamääräyksen päivitys joukolle kaavakohteita
................................................

Tällä ominaisuudella käyttäjä voi päivittää kaavamääräyksen kerralla halutulle joukolle kaavakohteita. Myös kaavakohteiden käyttötarkoituslyhenteen (kenttä kayttotarkoitus_lyhenne) arvo voidaan päivittää käyttäjän niin halutessa (samalla päivitetään kaavakohteiden kaavamaaraysotsikko-kentän arvo). Jos kaavakohteille on asetettu yleiskaava ja yleiskaavalle numero, niin käyttötarkoituksen lyhenne koitetaan huomioida kaavakohteiden kaavamääräysten päivityksessä.

Teknisesti ei ole aina mahdollista visualisoida kaavakohteita suoraan kaavamääräys-taulun kaavamääräyksen perusteella ainakin siksi, että kaavakohteeseen voi liittyä useita kaavamääräyksiä. QGIS-työtilassa kaavakohteiden visualisointityyli on valittu kaavakohde-taulujen kayttotarkoitus_lyhenne-kentän perusteella, johon muiden kuin käyttötarkoitusalueiden tapauksessa, on tallennettu lyhenteen sijaan kaavamääräys-taulussa olevan kaavakohteeseen liittyvän kaavamääräyksen otsikko. Jos kaavakohteeseen liittyy useita kaavamääräyksiä, niin käyttäjältä varmistetaan, että tehdäänkö kayttotarkoitus_lyhenne-kentän arvon päivitys.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

