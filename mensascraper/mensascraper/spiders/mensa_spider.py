from copyreg import add_extension

import scrapy

class MensaSpider(scrapy.Spider):
    name = "mensaspider"

    start_urls = [
        "https://www.imensa.de/index.html"
    ]

    def parse(self, response):
        # Auf der Startseite sind alle 16 Bundesländer verlinkt.
        bundeslaender = response.css(".primary::attr(href)").getall()
        yield from response.follow_all(bundeslaender, callback=self.parse_bundeslaender)


    def parse_bundeslaender(self, response):
        # Allgemeiner Aufbau von imensa.de: Bundesländer -> Städte -> Mensen

        # ".category" als Indikator auf Ebene der Mensen
        # Ist dieser nicht vorhanden handelt es sich NICHT um einen Stadtstaat
        # Es wird daher zunächst über alle Städte iteriert
        if response.css(".category").get() is None:
            staedte = response.css(".primary::attr(href)").getall()
            yield from response.follow_all(staedte, callback=self.parse_staedte)

        # Berücksichtigung der Stadtstaaten
        # Hier abweichender Aufbau: Bundesländer -> Mensen
        # Es kann also direkt über die Mensen iteriert werden
        else:
            mensen = response.css(".primary::attr(href)").getall()
            yield from response.follow_all(mensen, callback=self.parse_mensen)

    def parse_staedte(self, response):
        # Auf Stadtebene werden die einzelnen Mensen verlinkt.
        mensen = response.css(".primary::attr(href)").getall()
        yield from response.follow_all(mensen, callback=self.parse_mensen)

    def parse_mensen(self, response):
        # Hier liegt die gesuchte Information der Mensen
        #Speisepläne werden nach Aufgabenstellung nicht berücksichtigt

        name = response.css("h1.aw-title-header-title::text").get()

        # Falls keine vollständige Adresse hinterlegt ist, setzen wir Platzhalter,
        # damit der Scraper nicht mit einem IndexError abbricht.
        adresse = response.css("a.panel-body::text").getall()
        if len(adresse) != 2:
            strasse = "-"
            plz_stadt = "-"
        else:
            strasse = adresse[0]
            plz_stadt = adresse[1]

        # Manche Mensen habe keine Bewertung
        # In diesem Fall werden Platzhalter "-" gesetzt
        if response.css("div.aw-ratings-average::text").get() is None:
            sterne = "-"
            bewertungen = "-"
        else:
            sterne = response.css("div.aw-ratings-average::text").get()
            bewertungen = response.css("div.aw-ratings-count::text").get()

        yield {
            "Name" : name,
            "Straße" : strasse,
            "PLZ/Stadt" : plz_stadt,
            "Sterne" : sterne,
            "Bewertungen" : bewertungen,
        }