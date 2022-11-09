import bs4 as bs
import requests
import re
from geojson import Point, Feature, FeatureCollection
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

clinicData = []
clinicFeatureCollection = None


def getSoup(url):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    }
    response = requests.get(url, headers=headers)
    soup = bs.BeautifulSoup(response.text, "lxml")
    return soup


def geocode(postal):
    url = f"https://developers.onemap.sg/commonapi/search?searchVal={postal}&returnGeom=Y&getAddrDetails=N&pageNum=1"
    response = requests.get(url)
    responseJSON = response.json()
    coordinates = Point(
        (
            float(responseJSON["results"][0]["LONGITUDE"]),
            float(responseJSON["results"][0]["LATITUDE"]),
        )
    )
    return coordinates


def scrape():
    baseUrl = "https://www.rafflesmedicalgroup.com/clinic/"
    location = "singapore"
    page = 1
    morePages = True
    while morePages == True:
        print(f"Page: {page}")
        soup = getSoup(f"{baseUrl}?_sft_clinic-location={location}&sf_paged={page}")
        clinics = soup.find_all("div", {"class": "clinic"})
        if len(clinics) == 0:
            morePages = False
            break
        for clinic in clinics:
            # print(clinic)
            clinicText = clinic.find_all("div", {"class": "fl-post-text"})[0]
            clinicNameDirty = clinicText.find_all("a", href=True)[0].text.strip()
            clinicName = re.sub("\s+", " ", clinicNameDirty)
            clinicUrl = clinicText.find_all("a", href=True)[0]["href"]
            clinicMeta = clinic.find_all("div", attrs={"class": "fl-post-meta"})[0]
            clinicAddress = clinicMeta.find_all("p")[0].text.strip()
            clinicPostalCode = clinicAddress[-6:]   
            clinicCoordinates = geocode(clinicPostalCode)
            clinicFooter = clinic.find_all("div", {"class": "rmg-post-footer"})[0]
            clinicServices = []
            for service in clinicFooter.find_all("li"):
                clinicServices.append(service.text)

            clinicData.append(
                Feature(
                    geometry=clinicCoordinates,
                    properties={
                        "clinicName": clinicName,
                        "clinicUrl": clinicUrl,
                        "clinicAddress": clinicAddress,
                        "clinicServices": clinicServices,
                    },
                )
            )
        page += 1
        # morePages = False
        # break
    return FeatureCollection(clinicData)


app = Flask(__name__)
CORS(app)


@app.get("/")
def index():
    return clinicFeatureCollection


if __name__ == "__main__":
    print("Running initialization code...")
    clinicFeatureCollection = scrape()
    print("Starting server...")
    app.run()
