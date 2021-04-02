import schedule, json, datetime, time, requests

# Leerling stuff:
schoolNaam = None
leerlingNummer = None
wachtwoord = None

# School ids
studentId = None
schooluuid = None

# Docenten / Vakken:
vakken = None
docenten = None

# Api stuff:
baseUrl = "https://production.somtoday.nl"
accessToken = None
refreshToken = None
accesHeader = None
endpoint = None

# Settings:
CheckDagen = 5      # Dagen
minTussenCheck = 5  # Minutes

def getFile(path):
    try:
        with open(path, "r") as file:
            data = json.loads(file.read())
            file.close()
    except:
        intoFile(data=[],path=path)
        data = getFile(path=path)
    return data


def intoFile(data, path):
    with open(path, "w+") as file:
        json.dump(obj=data, fp=file, indent=4)
        file.close()


def loadSettings():
    global schoolNaam, leerlingNummer, wachtwoord
    # Load Settings:
    settings = getFile(path="config/settings.json")["somtoday"]
    schoolNaam, leerlingNummer, wachtwoord = settings["schoolNaam"], settings["leerlingNummer"], settings["wachtwoord"]


def finduuid():
    global baseUrl, schoolNaam, schooluuid
    allschooluuids = requests.get("https://servers.somtoday.nl/organisaties.json")
    if allschooluuids.status_code < 400:
        try:
            allschooluuids = json.loads(allschooluuids.text)
            for school in allschooluuids[0]["instellingen"]:
                if school["naam"] == schoolNaam:
                    schooluuid = school["uuid"]
                    break
        except:
            print("Geen response of error in school uuids!")
    else:
        print("Error met uuids Code: {}".format(allschooluuids.status_code))


def auth():
    global accessToken, accesHeader, endpoint, refreshToken, baseUrl, leerlingNummer, wachtwoord
    isAuth = accessToken is not None
    data = {
        "grant_type": "password",
        "username": schooluuid + "\\" + leerlingNummer,
        "password": wachtwoord,
        "scope": "openid"
    }
    accesHeaders = {
        "Authorization": "Basic RDUwRTBDMDYtMzJEMS00QjQxLUExMzctQTlBODUwQzg5MkMyOnZEZFdkS3dQTmFQQ3loQ0RoYUNuTmV5ZHlMeFNHTkpY", 
        "Accept": "application/json"
    }
    tokenRequest = None
    if accessToken == None:
        tokenRequest = requests.post(
            baseUrl + "/oauth2/token", data=data, headers=accesHeaders
        )
        if tokenRequest.status_code == 500:
            print("Niet kunnen autoriseren! Code: 500")
            quit()
        elif tokenRequest.status_code == 200:
            print("successful ingelog! Code: 200")
            tokenRequestJson = tokenRequest.json()
            accessToken = tokenRequestJson["access_token"]
            refreshToken = tokenRequestJson["refresh_token"]
            endpoint = tokenRequestJson["somtoday_api_url"]
            accesHeader = {"Authorization": "Bearer " +
                accessToken, "Accept": "application/json"}
            isAuth = True
        else:
            isAuth = False
        
    if accessToken != None and not isAuth:
        print("Token vernieuwen.. ")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refreshToken
        }
        refreshRequest = requests.post(
            baseUrl + "/oauth2/token", data=data, headers=accesHeaders
        )
        if refreshRequest.status_code == 200:
            print("successful refreshtoken Code: 200")
            refreshRequestJson = refreshRequest.json()
            accessToken = refreshRequestJson["access_token"]
            refreshToken = refreshRequestJson["refresh_token"]
            accesHeader = {
                "Authorization": "Bearer " + accessToken, 
                "Accept": "application/json"}
            endpoint = refreshRequestJson["somtoday_api_url"]
            isAuth = True
        else:
            print("Niet gelukt met refreshtoken! Code: {}".format(refreshRequest.status_code))
    
    if isAuth == False and tokenRequest is not None:
        print("Niet kunnen authoriseren! Zijn je inlog gegevens goed? Code: {} Reden: {}".format(tokenRequest.status_code, tokenRequest.reason))


def findStudentId():
    global studentId, accesHeader, endpoint
    studentRequest = requests.get(
        endpoint + "/rest/v1/leerlingen", headers=accesHeader
    )
    if studentRequest.status_code < 400:
        studentRequestJson = studentRequest.json()
        studentId = studentRequestJson["items"][0]["links"][0]["id"]
    else:
        print("Fout in Student id krijgen! Code: {}".format(studentRequest.status_code))


def findAfspraken():
    global accessToken, endpoint, CheckDagen
    Bdate = str(datetime.date.today())  # begindatum
    Edate = str(datetime.date.today() + datetime.timedelta(days=int(CheckDagen))) # EindDatum
    afsprakenheader = {
        "Authorization": "Bearer " + accessToken, 
        "Accept": "application/json"
    }
    afsprakenParams = {
        "begindatum": Bdate,
        "einddatum": Edate
    }
    afsprakenRequest = requests.get(
        endpoint + "/rest/v1/afspraken", headers=afsprakenheader, params=afsprakenParams
    )
    if afsprakenRequest.status_code < 400:
        intoFile(data=afsprakenRequest.json(), path="data/afspraken.json")
    else:
        print("Er ging iets fout in afspraken! Code: {}".format(afsprakenRequest.json()))


def findcijfers():
    global endpoint, accessToken, studentId
    cijferHeader = {
        "Authorization": "Bearer " + accessToken, 
        "Accept": "application/json"
    }
    cijferRequest = requests.get(
        endpoint + "/rest/v1/resultaten/huidigVoorLeerling/" + str(studentId), headers=cijferHeader)
    if cijferRequest.status_code < 400:
        cijfers = []
        for listcijfer in cijferRequest.json()["items"]:
            cijfer = {}
            if "id" in listcijfer["links"][0]:
                cijfer["cijferId"] = listcijfer["links"][0]["id"]

            if "weging" in listcijfer:
                cijfer["telt mee"] = listcijfer["weging"]

            elif "examenWeging" in listcijfer:
                cijfer["telt mee"] = str(listcijfer["examenWeging"]) + " SE"

            if "omschrijving" in listcijfer:
                cijfer["omschrijving"] = listcijfer["omschrijving"]
            
            if "resultaat" in listcijfer:
                cijfer["resultaat"] = listcijfer["resultaat"]
            
            if "vak" in listcijfer:
                cijfer["vak"] = listcijfer["vak"]["afkorting"]

            if "weging" in listcijfer:
                cijfers.append(cijfer)
        intoFile(data=cijfers, path="data/cijfers.json")
    else:
        print("Error met Cijfers! Code: {}".format(cijferRequest.status_code))


def fetchAfspraken():
    afspraken = getFile(path="data/afspraken.json")
    docenten, vakken = getFile(path="config/docenten.json"), getFile(path="config/vakken.json")
    FetchedAfspraken = []
    for afspraak in afspraken["items"]:
        les = {}
        if "id" in afspraak["links"][0]:
            les["afspraakid"] = afspraak["links"][0]["id"]

        if "locatie" in afspraak:
            les["locatie"] = afspraak["locatie"]

        if "titel" in afspraak:
            les["title"] = afspraak["titel"]  # Locatie - vak - docent

            titleList = les["title"].split(" - ")
            if titleList[len(titleList)-1] in docenten:
                les["docent"] = docenten[titleList[len(titleList)-1]]
            else:
                les["docent"] = titleList[len(titleList)-1]

            if titleList[len(titleList)-2] in vakken:
                les["vak"] = vakken[titleList[len(titleList)-2]]
            else:
                les["vak"] = titleList[len(titleList)-2]

        if "beginLesuur" in afspraak:
            les["Buur"] = afspraak["beginLesuur"]
        
        if "eindLesuur" in afspraak:
            les["Euur"] = afspraak["eindLesuur"]

        if "beginDatumTijd" in afspraak:
            if afspraak["beginDatumTijd"][len(afspraak["beginDatumTijd"])-4] == "1": 
                les["Btijd"] = afspraak["beginDatumTijd"].removesuffix(":00.000+01:00")
            else:
                les["Btijd"] = afspraak["beginDatumTijd"].removesuffix(":00.000+02:00")
            
        if "eindDatumTijd" in afspraak:
            if afspraak["eindDatumTijd"][len(afspraak["eindDatumTijd"])-4] == "1": 
                les["Etijd"] = afspraak["eindDatumTijd"].removesuffix(":00.000+01:00")
            else:
                les["Etijd"] = afspraak["eindDatumTijd"].removesuffix(":00.000+02:00")

        FetchedAfspraken.append(les)
    intoFile(data=FetchedAfspraken, path="data/fetchedafspraken.json")
    

def makeEmbed(afspraak): # {les: {les}} or {cijfer: {cijfer}}
    embed = {}
    embed["color"] = 29439
    if "les" in afspraak:
        embed["title"] = "Volgende Les!"
        embed["description"] = """ Lesuur:  {}\nVak:  {}\nLokaal:  {}\nDocent:  {}""".format(
            afspraak["les"]["Btijd"].split("T")[1], afspraak["les"]["vak"], afspraak["les"]["locatie"], afspraak["les"]["docent"])
    elif "cijfer" in afspraak:
        embed["title"] = "Nieuw Cijfer!"
        embed["description"] = """ Resultaat:  {}\nTelt Mee:  {}\nVak:  {}\nBeschijving:  {}""".format(
            afspraak["cijfer"]["resultaat"], afspraak["cijfer"]["telt mee"], afspraak["cijfer"]["vak"], afspraak["cijfer"]["omschrijving"])
    else:
        embed["title"] = afspraak["title"]
        embed["description"] = afspraak["description"]
    embed["footer"] = {"text": "Send on: {}".format(datetime.datetime.now().strftime("%H:%M"))}
    return embed


def sendWebhook(embeds):
    settings = getFile(path="config/settings.json")["webhook"]
    postData = json.dumps({"embeds": embeds})
    postHeader = {"Content-Type": "application/json"}
    postRequest = requests.post(settings["webhookUrl"], data=postData, headers=postHeader)
    if not postRequest.ok:
        print("Iets ging fout met de Webhook!")
        print("Status Code: {}".format(postRequest.status_code))
        print("Reden: {}".format(postRequest.reason))
        print("Response: {}".format(postRequest.text))


def checkles(Rtijd):
    # Vernieuw jsonfiles:
    auth()
    findAfspraken()
    fetchAfspraken()

    # Check for Les:
    afspraken = getFile(path="data/fetchedafspraken.json")
    date = str(datetime.date.today())
    lessen = []
    for afspraak in afspraken:
        if date + "T" + Rtijd == afspraak["Btijd"]:
            lessen.append(afspraak)
    
    embeds = []
    if lessen != []:
        for les in lessen:
            embeds.append(makeEmbed({ "les" : les }))
    
    if embeds == []:
        print("Geen Les Om {}!".format(Rtijd))
    else:
        sendWebhook(embeds)
    
    print("Checked On {}\n".format(datetime.datetime.now().strftime("%H:%M")))


def checkcijfers():
    global studentId
    auth()
    oudeCijfers = getFile(path="data/cijfers.json")
    findcijfers()
    nieuweCijfers = getFile(path="data/cijfers.json")
    
    cijfers = []
    for cijfer in nieuweCijfers:
        if cijfer not in oudeCijfers:
            cijfers.append(cijfer)
    
    embeds = []
    if cijfers != []:
        for cijfer in cijfers:
            embeds.append(makeEmbed({"cijfer": cijfer }))
    
    if embeds != []:
        sendWebhook(embeds)
    else:
        print("Geen Nieuwe Cijfers!")
    
    print("Checked On {}\n".format(datetime.datetime.now().strftime("%H:%M")))


# Moet altijd eerst gebeuren!
loadSettings()
finduuid()
auth()
findStudentId()

schedule.every().day.at("08:20").do(checkles, Rtijd="08:30")
schedule.every().day.at("09:10").do(checkles, Rtijd="09:20")
schedule.every().day.at("10:00").do(checkles, Rtijd="10:10")
schedule.every().day.at("11:10").do(checkles, Rtijd="11:20")
schedule.every().day.at("12:00").do(checkles, Rtijd="12:10")
schedule.every().day.at("13:20").do(checkles, Rtijd="13:30")
schedule.every().day.at("14:20").do(checkles, Rtijd="14:30")
schedule.every().day.at("15:10").do(checkles, Rtijd="15:20")
schedule.every().day.at("16:50").do(checkles, Rtijd="17:00")
schedule.every(int(minTussenCheck)).minutes.do(checkcijfers)

print("Checking The somtoday Api's ")
while True:
    schedule.run_pending()
    time.sleep(0.5)