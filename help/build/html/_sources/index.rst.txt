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

* :ref:`Kopioi lähdeaineistoa tietokantaan`
* :ref:`Kaavamääräyksen päivitys joukolle kaavakohteita`


Kopioi lähdeaineistoa tietokantaan
..................................

Kopiointi lähdekarttatasosta yleiskaavan tietokantaan onnistuu seuraavin vaihein:

#. Valitse lähdekarttataso sekä kohdekaavakohdetaulu ja kohdekentät haluamillesi lähdekarttatason kentille. Kun jätät lähdekenttää vastaavan kohdekentän arvon tyhjäksi, niin ko. lähdekentän arvoja ei kopioida kohdetauluun, mutta esim. kaavan nimi ja numero huomioidaan silti myöhemmin. Kun jätät kohdekentän valitsematta, niin sille ei kopioida lähdetaulusta arvoa, mutta voit myöhemmin halutessasi asettaa sille joka tapauksessa oletusarvon. Klikkaa Seuraava-painiketta, kun olet asettanut haluamillesi lähdekarttatason kentille kohdetaulun kentän.
#. Valitse lähdekarttatason attribuuttitaulusta tietokantaan kopioitavat kohteet ja klikkaa sitten Seuraava-painiketta. Voit halutessasi sulkea lähdekarttatason attribuuttitaulun valittuasi kopioitavat kohteet.
#. Valitse tarvittaessa oletusarvot pakollisille kohdetaulujen kentille ja mahdollisesti muita kopiointiasetuksia, kuten tehdäänkö kaavamääräysotsikkoa vastaava kaavamääräys, jos sitä ei jo ole. Klikkaa Aja-painiketta aloittaaksesi lähdekarttatason kohteiden kopioinnin yleiskaavan tietokantaan.

.. Voit halutessasi tarkistaa ajamisen seurauksena tehtävän kopion aiheuttamat muutokset tietokantaan "Näytä ajolla tehtävät muutokset"-painikkeella.


Kaavamääräyksen päivitys joukolle kaavakohteita
................................................

Tällä ominaisuudella käyttäjä voi päivittää kaavamääräyksen kerralla halutulle joukolle kaavakohteita. Kaavamääräys, joka kohteille päivitetään valitaan "Valitse kaavamääräys"-kohdasta. Myös kaavamääräyksen otsikon, tekstin ja kuvauksen voi päivittää tämän dialogin kautta.

Asetuksella "Poista kaavakohteilta vanhat kaavamääräykset" poistetaan valituilla kaavakohteilla jo olevat kaavamääräykset. Käyttäjä valitsee päivitettävät kaavakohteet "Valitse päivitettävät aluekohteet"-, "Valitse päivitettävät täydentävät aluekohteet"-, "Valitse päivitettävät viivamaiset kohteet"- ja "Valitse päivitettävät pistemäiset kohteet"-painikkeiden kautta avatuvien karttatasojen attribuuttitaulujen kautta. Käyttäjä voi myös valita kohteet jo ennen "Kaavamääräyksen päivitys joukolle kaavakohteita"-dialogin avaamista, mutta ko. kohteiden valinta pitää varmistaa avaamalla haluamansa karttatasojen attribuuttitailut em. mainituilla painikkeilla ennen "Tee päivitykset"-painikkeen painamista.

Jos kaavakohteille on asetettu yleiskaava ja yleiskaavalle numero, niin käyttötarkoituksen lyhenne koitetaan huomioida aluevarausten kaavamääräysten päivityksessä.

Teknisesti ei ole aina mahdollista visualisoida kaavakohteita suoraan kaavamääräys-taulun kaavamääräyksen perusteella ainakin siksi, että kaavakohteeseen voi liittyä useita kaavamääräyksiä ja siksi QGIS-työtilassa kaavakohteiden visualisointityyli on valittu kaavakohde-taulujen kayttotarkoitus_lyhenne-kentän perusteella, johon muiden kuin käyttötarkoitusalueiden tapauksessa, on tallennettu lyhenteen sijaan kaavamääräys-taulussa olevan kaavakohteeseen liittyvän kaavamääräyksen otsikko. Jos kaavakohteeseen liittyy useita kaavamääräyksiä, niin käyttäjä voi "Päivitä käyttötarkoitus vaikka kohteella olisi useita kaavamääräyksiä"-asetuksella valita miten tässä tilanteessa toimitaan. Kaavakohteiden käyttötarkoituksen (kenttä kayttotarkoitus_lyhenne) arvo päivitetään myös (ja samalla päivitetään kaavakohteiden kaavamaaraysotsikko-kentän arvo), kun "Päivitä käyttötarkoitus vaikka kohteella olisi useita kaavamääräyksiä"-asetus on valittu, vaikka kohteella olisi useita kaavamääräyksiä päivityksen jälkeen. Jos ko. asetus ei ole käytössä, niin valittu kaavamääräys lisätään kohteelle, mutta käyttötarkoitukseen ei tehdä muutoksia, jos kohteella on useita kaavamääräyksiä päivityksen jälkeen. Jos kuitenkin asetus "Poista kaavakohteilta vanhat kaavamääräykset" on käytössä, niin "Päivitä käyttötarkoitus vaikka kohteella olisi useita kaavamääräyksiä"-asetuksella ei ole vaikutusta.

Jos et valitse kaavamääräystä ja jätät "Poista kaavakohteilta vanhat kaavamääräykset"-asetuksen valituksi, niin valitsemiltasi kaavakohteilta poistetaan kaavamääräykset, mutta ei lisätä uusia. Jos myös asetus "Päivitä käyttötarkoitus vaikka kohteella olisi useita kaavamääräyksiä" on valittu, niin myös käyttötarkoituksen (kenttä kayttotarkoitus_lyhenne) arvo poistetaan myös (ja samalla poistetaan myös kaavakohteiden kaavamaaraysotsikko-kentän arvo).


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

