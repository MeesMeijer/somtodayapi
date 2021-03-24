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

VolgendeLes = None 
nieuweCijfers = None
nieuweAfspaken = None
fetchedAfspraken = None 
updateCijfers = None

vakken = None
docenten = None

fetch_dagen = 3
sync_interval = 2 # in minutes

mention_prefix =  None
webhook_url =  None

def scheduleTime(time):
    date = datetime.datetime.now().strftime("%Y-%m-%d") 
    somtime = {
            "08:30": date + "T08:30:00.000+01:00",
            "09:20": date + "T09:20:00.000+01:00",
            "10:10": date + "T10:10:00.000+01:00",
            "11:20": date + "T11:20:00.000+01:00",
            "12:10": date + "T12:10:00.000+01:00",
            "13:30": date + "T13:30:00.000+01:00",
            "14:30": date + "T14:30:00.000+01:00",
            "15:20": date + "T15:20:00.000+01:00",
            "17:00": date + "T17:00:00.000+01:00",
    }
    return somtime.get(time)

def createEmbeds(x):
    embed = {}
    embed["color"] = 29439
    if "cijfer_id" in x:
        embed["title"] = "Nieuw Cijfer!"
        embed["description"] = """ Resultaat:  {}\nTelt Mee:  {}\nVak:  {}\nBeschijving:  {}""".format(
                x.get("resultaat"),
                x.get("telt mee"),
                x.get("vak"),
                x.get("beschrijving"))
    elif "afspraken_id" in x:
        embed["title"] = "Volgende Les!"
        embed["description"] = """ Lesuur:  {}\nVak:  {}\nLokaal:  {}\nDocent:  {}""".format(
                    x.get("begin_tijd").split("T")[1][0:5],
                    x.get("vak"),
                    x.get("lokaal"),
                    x.get("docent"))
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
    data = getFile(path="config2/somtoday_credentials.json")
    school_name = data["school_name"]
    username = data["username"]
    password = data["password"]

    vakken = getFile(path="config2/extra/subjects.json")
    docenten = getFile(path="config2/extra/teachers.json")

    discordSettings = getFile(path="config2/discord_not.json")
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
    students_request = requests.get(
        endpoint + "/rest/v1/leerlingen", headers=access_header)
    students_json = json.loads(students_request.text)
    student_id = students_json["items"][0]["links"][0]["id"]
   
    


def getAfspraken():
    global access_token, student_id, endpoint, fetch_dagen, nieuweAfspaken

    begin_date = datetime.datetime.now().strftime("%Y-%m-%d")
    eind_date = str(datetime.datetime.now().strftime("%Y-%m-")) + str(int(begin_date.split("-")[2]) + int(fetch_dagen))
    afspraken_header = {
        "Authorization": "Bearer " + access_token, 
        "Accept": "application/json",
    }

    afspraken_params = {
        "begindatum": begin_date,
        "einddatum": eind_date
    }

    afspraken_url = endpoint + "/rest/v1/afspraken?" + str(student_id)
    afspraken_request = requests.get(afspraken_url, headers=afspraken_header, params=afspraken_params)
    afspraken_json = json.loads(afspraken_request.text)
    nieuweAfspaken = afspraken_json
        
    intoFile(data=afspraken_json, path="data2/somtoday_afspraken.json")
    

def getCijfers():
    global endpoint, access_token, student_id, nieuweCijfers, updateCijfers
    
    cijfer_header = {"Authorization": "Bearer " +
                        access_token, "Accept": "application/json"}
    cijfer_url = endpoint + "/rest/v1/resultaten/huidigVoorLeerling/" + str(student_id)
    cijfer_request = requests.get(cijfer_url, headers=cijfer_header)
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

    oudeCijfers = getFile("data2/somtoday_cijfers.json")
    intoFile(path="data2/somtoday_cijfers.json", data=cijfers)

    updateCijfers = []
    for grade in cijfers:
        if grade not in oudeCijfers:
            updateCijfers.append(grade)
    nieuweCijfers = cijfers

def sortAfspraken():
    global nieuweAfspaken, fetchedAfspraken
    fetchedAfspraken = []
    for afspraak in nieuweAfspaken["items"]:
        afspraken_id = afspraak["links"][0]["id"]
        title = afspraak["titel"]
        if "beginLesuur" in afspraak:
            beginLesuur = afspraak["beginLesuur"]
            eindLesuur = afspraak["eindLesuur"]
        else:
            beginLesuur = "None"
            eindLesuur = "None"
        begin_tijd = afspraak["beginDatumTijd"]
        eind_tijd = afspraak["eindDatumTijd"]
        title_list = title.split(" - ")
        if title_list != ['Beweegmoment']:
            if title_list == ["bijles nederlands"]:
                vak = "bijles Nederlands"
            else:
                vak = title_list[1]
                if vak[0:4] == "ah4f":
                    vak = vak[4:len(vak)]
                elif vak[0:3] == "ah4":
                    vak = vak[3:(len(vak)-1)]
                if vak in vakken:
                    vak = vakken.get(vak)
            
            lokaal = title_list[0]
            docent = title_list[len(title_list) -1]
            if docent in docenten:
                docent = docenten.get(docent)

            afsprakenJson = {
                "beginLesuur": beginLesuur,
                "datum": begin_tijd.split("T")[0],
                "afspraken_id": afspraken_id,
                "docent": docent,
                "lokaal": lokaal,
                "vak": vak,
                "eindLesuur": eindLesuur,
                "begin_tijd": begin_tijd, 
                "eind_tijd": eind_tijd
            }
            fetchedAfspraken.append(afsprakenJson)

    if fetchedAfspraken != []:
        intoFile(data=fetchedAfspraken, path="data2/fetched_afspraken.json")

def getlessen(requestedTime):
    global fetchedAfspraken
    komendeles = []
    komendelessen = []
    lesuur = scheduleTime(time=str(requestedTime))
    if lesuur != None or "None":
        for afspraak in fetchedAfspraken:
            datum = afspraak["datum"]
            begin_tijd = afspraak["begin_tijd"]

            if begin_tijd == lesuur:
                komendeles.append(afspraak)

            if begin_tijd == datum:
                komendelessen.append(afspraak)
    else:
        print("error met tijd")
    
    return [komendeles, komendelessen]
    
def discord(requestedTime):
    global mention_prefix, webhook_url, updateCijfers

    def sendDiscord(embeds):
        data = json.dumps({
                    "embeds": embeds})
        print("data: " + str(data))

        json_header = {"Content-Type": "application/json"}

        response = requests.post(webhook_url, data=data, headers=json_header)
        if not response.ok:
            print("Failed to execute discord wehook!")
            print(response.status_code)
            print(response.reason)
            print(response.text)

    #afspraken = getlessen(requestedTime)[1]
    #embeds.append(createEmbed(afspraken))

    listEmbeds = []
    afspraak = getlessen(requestedTime)[0]
    print("\nAfspraken: " + str(afspraak))
    if afspraak != [] or None:
        for les in afspraak:
            listEmbeds.append(createEmbeds(les))
        
    print("Nieuwe Cijfers:" + str(updateCijfers))
    if updateCijfers != [] or None:
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


def updateSomtoday(requestedTime):
    try: 
        Auth()
    except:
        time.sleep(1)
        try:
            Auth()
        except:
            print("Error Auth")

    try:
        getAfspraken()
        sortAfspraken()
    except:
        time.sleep(1)
        try:
            getAfspraken()
            sortAfspraken()
        except:
            print("error afspraken")

    try:
        getCijfers()
    except:
        time.sleep(1)
        try:
            getCijfers()
        except:
            print("error cijfer")
            
    try: 
        discord(requestedTime)
    except:
        print("error discord")


load()
get_school_uuid()

Auth()
get_student_id()

schedule.every().day.at("08:20").do(updateSomtoday, requestedTime="08:30")
schedule.every().day.at("09:10").do(updateSomtoday, requestedTime="09:20")
schedule.every().day.at("10:00").do(updateSomtoday, requestedTime="10:10")
schedule.every().day.at("11:10").do(updateSomtoday, requestedTime="11:20")
schedule.every().day.at("12:00").do(updateSomtoday, requestedTime="12:10")
schedule.every().day.at("13:20").do(updateSomtoday, requestedTime="13:30")
schedule.every().day.at("14:20").do(updateSomtoday, requestedTime="14:30")
schedule.every().day.at("15:10").do(updateSomtoday, requestedTime="15:20")
schedule.every().day.at("16:50").do(updateSomtoday, requestedTime="17:00")
schedule.every(sync_interval).minutes.do(updateSomtoday, requestedTime="cijfer")


print("updating every hour")
while True:
    schedule.run_pending()
    time.sleep(1)
