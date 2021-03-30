# somtodayapi
Dit Programma gebruikt de Somtoday Api om Afspraken en Cijfers op te halen.

## Instalatie
```bash
pip install schedule requests
```

## De Nodige infromatie:

1. Maak folders data en config aan
2. In config maak deze bestanden:

    ## settingsdiscord.json: 
    ```json
    {
        "discord_webhook": {
              "name": "", 
              "username": "", 
              "avatar_url": "",
              "mention_prefix": "<@ YOur mentions>",
              "webhook_url": "Your Webhook url"
          }
    }
    ```

    ## somtodaysettings.json:
    ```json
    {
        "school_name": "",
        "username": "",
        "password": ""
    }
    ```
    
    Hierna maak in config, een folder extra aan: 
    Hierin maak je de bestanden:
    
    ## subjects.json
    ```json
    {
        "shortname vak": "lange naam vak"
       
    } Als je dit niet wilt, laat dan file leeg met {}
    ```
    
    ## teachers.json:
    ```json
    {
        "afkorting": "Naam docent"
    } Als je dit niet wilt, laat dan leeg met {}
    ```
    
## Problemen 
Ik ben nog veel aan het veranderen binnen dit programmer, als je het gebruikt, check dan of je de nieuwst versie hebt!
