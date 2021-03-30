import schedule, json, time, datetime, requests

baseurl = "https://production.somtoday.nl"

school_name = None
username = None
password = None

access_token = None
refresh_token = None
endpoint = None
access_header = None
student_id = None
school_uuid = None

nieuweCijfers = None
nieuweAfspaken = None
fetchedAfspraken = None 
updateCijfers = None

vakken = None
docenten = None

fetch_dagen = 3
sync_interval = 3 # in minutes

mention_prefix =  None
webhook_url =  None

def scheduleTime(time):
    date = str(datetime.date.today())
    somtime = {
            "08:30": date + "T08:30",
            "09:20": date + "T09:20",
            "10:10": date + "T10:10",
            "11:20": date + "T11:20",
            "12:10": date + "T12:10",
            "13:30": date + "T13:30",
            "14:30": date + "T14:30",
            "15:20": date + "T15:20",
            "17:00": date + "T17:00",
    }
    return somtime.get(time)


def createEmbeds(afspraak):
    embed = {}
    embed["color"] = 29439
    if "cijfer_id" in afspraak:
        embed["title"] = "Nieuw Cijfer!"
        embed["description"] = """ Resultaat:  {}\nTelt Mee:  {}\nVak:  {}\nBeschijving:  {}""".format(
                afspraak.get("resultaat"),
                afspraak.get("telt mee"),
                afspraak.get("vak"),
                afspraak.get("beschrijving"))
    elif "afsprakenId" in afspraak:
        embed["title"] = "Volgende Les!"
        embed["description"] = """ Lesuur:  {}\nVak:  {}\nLokaal:  {}\nDocent:  {}""".format(
                    afspraak.get("begindatumtijd").split("T")[1],
                    afspraak.get("vak"),
                    afspraak.get("lokaal"),
                    afspraak.get("docent"))
    else:
        embed["title"] = "Lessen voor {}".format(afspraak["title"])
        embed["description"] = afspraak["lessen"]
    embed["footer"] = {"text": "Send on: {}".format(datetime.datetime.now().strftime("%H:%M"))}
    return embed

def intoFile(data, path):
    with open(path, "w+") as temp:
        json.dump(data, temp, indent=4)
        temp.close()

def getFile(path):
    with open(path, "r") as temp:
        data = json.loads(temp.read())
        temp.close()
    return data

def load():
    global school_name, username, password, vakken, docenten, mention_prefix, webhook_url
    somtodaysettings = getFile(path="config/somtodaysettings.json")
    school_name = somtodaysettings["school_name"]
    username = somtodaysettings["username"]
    password = somtodaysettings["password"]

    vakken = getFile(path="config/extra/subjects.json")
    docenten = getFile(path="config/extra/teachers.json")

    discordSettings = getFile(path="config/settingsdiscord.json")
    mention_prefix = discordSettings["discord_webhook"]["mention_prefix"]
    webhook_url = discordSettings["discord_webhook"]["webhook_url"]

def get_school_uuid():
    global school_uuid
    org_request = requests.get("https://servers.somtoday.nl/organisaties.json")
    org_list = json.loads(org_request.text)

    for org in org_list[0]["instellingen"]:
        if org["naam"] == school_name:
            school_uuid = org["uuid"]
            break

def Auth():
    global access_token, endpoint, refresh_token, baseurl, access_token, access_header
    is_authenticated = access_token is not None
    data = {"grant_type": "password",
            "username": school_uuid + "\\" + username,
            "password": password,
            "scope": "openid"}
    acces_headers = {
        "Authorization": "Basic RDUwRTBDMDYtMzJEMS00QjQxLUExMzctQTlBODUwQzg5MkMyOnZEZFdkS3dQTmFQQ3loQ0RoYUNuTmV5ZHlMeFNHTkpY", "Accept": "application/json"}
    token_request = None
    if access_token == None:
        token_request = requests.post(
            baseurl + "/oauth2/token", data=data, headers=acces_headers)
        if token_request.status_code == 500:
            print("Unable to authenticate! Are the servers down?! Response: 500")
            quit()
        elif token_request.status_code == 200:
            print("Successfully logged in!")
            token_json = json.loads(token_request.text)

            access_token = token_json["access_token"]
            refresh_token = token_json["refresh_token"]
            endpoint = token_json["somtoday_api_url"]
            access_header = {"Authorization": "Bearer " +
                             access_token, "Accept": "application/json"}
            is_authenticated = True
        else:
            is_authenticated = False
    if refresh_token != None and not is_authenticated:
        print("Refreshing the token..")
        data = {"grant_type": "refresh_token",
                "refresh_token": refresh_token}
        refresh_request = requests.post(
            baseurl + "/oauth2/token", data=data, headers=acces_headers)
        token_json = json.loads(refresh_request.text)

        access_token = token_json["access_token"]
        refresh_token = token_json["refresh_token"]
        endpoint = token_json["somtoday_api_url"]
        access_header = {"Authorization": "Bearer " +
                         access_token, "Accept": "application/json"}
        is_authenticated = True
    if is_authenticated == False and token_request is not None:
        print("Unable to authenticate! Are your credentials right? {} {}".format(token_request.status_code, token_request.reason))

def get_student_id():
    global student_id, access_header, endpoint
    students_request = requests.get(endpoint + "/rest/v1/leerlingen", headers=access_header)
    students_json = json.loads(students_request.text)
    student_id = students_json["items"][0]["links"][0]["id"]
 

def getAfspraken():
    global access_token, student_id, endpoint, fetch_dagen, nieuweAfspaken

    beginDate = datetime.date.today()
    eindDate = datetime.date.today() + datetime.timedelta(days=int(fetch_dagen))
    afsprakenHeader = {
        "Authorization": "Bearer " + access_token, 
        "Accept": "application/json"}
    afsprakenParams = {
        "begindatum": beginDate,
        "einddatum": eindDate}
    afspraken_url = endpoint + "/rest/v1/afspraken"
    afspraken_request = requests.get(afspraken_url, headers=afsprakenHeader, params=afsprakenParams)
    if "code" in afspraken_request.json():
        if afspraken_request.json()["code"] == 404:
            print(afspraken_request.json())

    if "code" not in afspraken_request.json():
            nieuweAfspaken = json.loads(afspraken_request.text)
            intoFile(data=nieuweAfspaken, path="data/somtoday_afspraken.json")
    else:
        print("error in afspraken krijgen")
        intoFile(data=afspraken_request.text, path="data/crashafspraken.json")

    
def getCijfers():
    global endpoint, access_token, student_id, nieuweCijfers, updateCijfers
    cijfer_header = {"Authorization": "Bearer " +
                        access_token, "Accept": "application/json"}
    cijfer_url = endpoint + "/rest/v1/resultaten/huidigVoorLeerling/" + str(student_id) + "?"
    cijfer_request = requests.get(cijfer_url, headers=cijfer_header)
    if "code" in cijfer_request.json():
        if cijfer_request.json()["code"] == 404:
            print(cijfer_request.json())
    elif "code" not in cijfer_request.json():
        cijfer_json = json.loads(cijfer_request.text)
        cijfers = []
        for cijfer in cijfer_json["items"]:
            if cijfer["type"] == "Toetskolom":
                if "weging" in cijfer:
                    weight = cijfer["weging"]
                elif "examenWeging" in cijfer:
                    weight = str(cijfer["examenWeging"]) + " SE"
                else:
                    weight = None
                description = cijfer["omschrijving"] if "omschrijving" in cijfer else None
                cijfers.append({"cijfer_id": cijfer["links"][0]["id"],"resultaat": cijfer["resultaat"], "telt mee": weight,
                                        "beschrijving": description, "vak":cijfer["vak"]["afkorting"]})

        oudeCijfers = getFile("data/somtoday_cijfers.json")
        intoFile(path="data/somtoday_cijfers.json", data=cijfers)

        updateCijfers = []
        for grade in cijfers:
            if grade not in oudeCijfers:
                updateCijfers.append(grade)
        nieuweCijfers = cijfers
    else:
        print("Error met cijfers!")
        intoFile(data=cijfer_request.text, path="data/crashcijfers.json")
    

def sortAfspraken():
    global nieuweAfspaken, fetchedAfspraken
    fetchedAfspraken = []
    if nieuweAfspaken != "" or None:
        for afspraak in nieuweAfspaken["items"]:
            if afspraak["titel"] != "Beweegmoment":
                afsprakenId = afspraak["links"][0]["id"]
                if "locatie" in afspraak:
                    locatie = afspraak["locatie"]
                else:
                    locatie = None

                title = afspraak["titel"]
                listTitle = title.split(" - ")

                if len(listTitle) != 1:
                    if locatie == None:
                        locatie = listTitle[0]
                    
                    vak = listTitle[1]
                    if len(vak) > 9:
                        vak = "nlt"
                    if vak in vakken:
                        vak = vakken.get(vak)
                    
                    docent = listTitle[len(listTitle)-1]
                    if docent in docenten:
                        docent = docenten.get(docent)
                else:
                    vak, docent, locatie = afspraak["titel"], afspraak["titel"], afspraak["titel"]
                
                if "beginLesuur" in afspraak:
                    tijdLesUur = afspraak["beginLesuur"]
                else:
                    tijdLesUur = None
                
                if "eindLesuur" in afspraak:
                    tijdEndLes = afspraak["eindLesuur"]
                else:
                    tijdEndLes = None
                
                if "beginDatumTijd" in afspraak:
                    Datum = afspraak["beginDatumTijd"]
                    if Datum[len(Datum)-4] == "1": 
                        beginDatum = afspraak["beginDatumTijd"].removesuffix(":00.000+01:00")
                    else:
                        beginDatum = afspraak["beginDatumTijd"].removesuffix(":00.000+02:00")
                if "eindDatumTijd" in afspraak:
                    Datum = afspraak["eindDatumTijd"]
                    if Datum[len(Datum)-4] == "1": 
                        eindDatum = afspraak["eindDatumTijd"].removesuffix(":00.000+01:00")
                    else:
                        eindDatum = afspraak["eindDatumTijd"].removesuffix(":00.000+02:00")
            
                afsprakenJson = {
                    "vak": vak,
                    "lokaal": locatie,
                    "docent": docent,
                    "beginlesuur": tijdLesUur,
                    "eindlesuur": tijdEndLes,
                    "begindatumtijd": beginDatum,
                    "einddatumtijd": eindDatum,
                    "afsprakenId": afsprakenId
                }
                fetchedAfspraken.append(afsprakenJson)

        if fetchedAfspraken != []:
            intoFile(data=fetchedAfspraken, path="data/fetched_afspraken.json")

def getles(requestedTime):
    global fetchedAfspraken

    komendeles = []
    temp = []
    lesuur = scheduleTime(time=str(requestedTime))
    if lesuur != None or "None":
        if fetchedAfspraken != None:
            for afspraak in fetchedAfspraken:
                if afspraak["begindatumtijd"] == lesuur:
                    komendeles.append(afspraak)      
    else:
        print("error met tijd")
    return komendeles

def fullday(dag):
    global fetchedAfspraken
    lessen = []
    temp = []
    if dag == "morgen":
        date = str(datetime.date.today() + datetime.timedelta(days=1))
    elif dag == "vandaag":
        date = str(datetime.date.today())

    for afspraak in fetchedAfspraken:
        if afspraak.get("begindatumtijd").split("T")[0] == date:
            vak = afspraak["vak"]
            les = afspraak["beginlesuur"]
            lokaal = afspraak["lokaal"]
            tijd = afspraak["begindatumtijd"].split("T")[1]
            temp.append("{} , lesuur: {} / {}\n , Vak: {}\n , Lokaal: {}\n\n".format(
                les, les, tijd, vak, lokaal))
    temp.sort()
    for les in temp:
        leslist = les.split(" , ")
        lessen.append(" ".join(leslist[1:]))
    if dag == "morgen":
        title = "Lessen voor morgen!"
    elif dag == "vandaag":
        title = "Lessen voor vandaag!"
    return {"title": title , "lessen": " ".join(lessen)}

def discord(requestedTime):
    global mention_prefix, webhook_url, updateCijfers
    def sendDiscord(embeds):
        data = json.dumps({
                    "embeds": embeds})
        json_header = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, data=data, headers=json_header)
        if not response.ok:
            print("Failed to execute discord wehook!")
            print(response.status_code)
            print(response.reason)
            print(response.text)

    if updateCijfers != None or []:
        listEmbeds = []
        if requestedTime == "morgen":
            afspraken = fullday("morgen")
            listEmbeds.append(createEmbeds(afspraken))
        elif requestedTime == "vandaag":
            afspraken = fullday("vandaag")
            listEmbeds.append(createEmbeds(afspraken))

        
        afspraak = getles(requestedTime)
        #print("\nAfspraken: " + str(afspraak))
        if afspraak != [] or None:
            for les in afspraak:
                listEmbeds.append(createEmbeds(les))


        #print("Nieuwe Cijfers:" + str(updateCijfers))
        if updateCijfers != None and []:
            for cijfer in updateCijfers:
                listEmbeds.append(createEmbeds(cijfer))
            updateCijfers = None 

        #print("list embeds: " + str(listEmbeds))
        if listEmbeds != []:
            sendDiscord(listEmbeds)
            # for x in listEmbeds:
            #     print("send: " + str(x))
            #     sendDiscord(x)
        else:
            print("Geen les of  nieuwe cijfers! \nCheck On: {}".format(datetime.datetime.now().strftime("%H:%M")))
    else:
        print("Geen les of  nieuwe cijfers! \nCheck On: {}".format(datetime.datetime.now().strftime("%H:%M")))


def updateSomtoday(requestedTime):
    Auth()
    getAfspraken()
    sortAfspraken()
    getCijfers()
    discord(requestedTime)

def updateCijfer():
    Auth()
    getCijfers()
    discord("cijfer")

def test():
    Auth()
    print("2")
    getAfspraken()
    print("3")
    sortAfspraken()
    print("4")
    getCijfers()
    print("5")
    discord("vandaag")
    print("6")


load()
get_school_uuid()

Auth()
get_student_id()

#test()
schedule.every().day.at("08:20").do(updateSomtoday, requestedTime="08:30")
schedule.every().day.at("09:10").do(updateSomtoday, requestedTime="09:20")
schedule.every().day.at("10:00").do(updateSomtoday, requestedTime="10:10")
schedule.every().day.at("11:10").do(updateSomtoday, requestedTime="11:20")
schedule.every().day.at("12:00").do(updateSomtoday, requestedTime="12:10")
schedule.every().day.at("13:20").do(updateSomtoday, requestedTime="13:30")
schedule.every().day.at("14:20").do(updateSomtoday, requestedTime="14:30")
schedule.every().day.at("15:10").do(updateSomtoday, requestedTime="15:20")
schedule.every().day.at("16:50").do(updateSomtoday, requestedTime="17:00")
schedule.every().day.at("22:30").do(updateSomtoday, requestedTime="morgen")
schedule.every().day.at("07:00").do(updateSomtoday, requestedTime="vandaag")
schedule.every(sync_interval).minutes.do(updateCijfer)

print("Running!")
while True:
    schedule.run_pending()
    time.sleep(0.2)
