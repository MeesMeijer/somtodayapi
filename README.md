# Somtoday Api
Dit Programma gebruikt de Somtoday Api om Afspraken en Cijfers op te halen.

## Instalatie
```bash
pip install schedule requests
```

## De Nodige informatie:

1. Maak de folders data en config aan.
2. In config zet je de volgende bestanden:

    ## settings.json: 
    ```json
    {
        "webhook": {
              "webhookUrl": "Your Webhook url"
          },
        "somtoday": {
             "schoolNaam": "",
             "leerlingNummer": "",
             "wachtwoord": ""
        }
    }
    ```
    
    ## vakken.json
    ```json
    {
        "shortname vak": "lange naam vak"
       
    } Als je dit niet wilt, laat dan file leeg met {}
    ```
    
    ## docenten.json:
    ```json
    {
        "afkorting": "Naam docent"
    } Als je dit niet wilt, laat dan leeg met {}
    ```
    
## Problemen 
Ik ben nog veel aan het veranderen binnen dit programmer, als je het gebruikt, check dan of je de nieuwst versie hebt!
