# remora-ha Remora custom component for Home Assistant
### Remora
Remora is a IoT/DIY solution using a dedicated hardware and software to:
- get electrical consumption information via the ***TeleInfo***
- manage heating via the ***Fil Pilote***  

Link: https://github.com/hallard/remora_soft

### PyRemora
This is a simple Python library to handle the [Remora](https://github.com/hallard/remora_soft "Remora") API.  
The main objective is to include it into [Home Assistant](https://www.home-assistant.io/ "Home Assistant") components to manage heaters using the ***Fil Pilote*** technique and fetch ***TeleInfo*** information.  

Link: https://github.com/FreeTHX/pyremora

### Remora in Home Assistant
This component provides:
- ```sensor``` over TeleInfo  
A sensor for each ***TeleInfo*** header can be configured to fetch ***TeleInfo*** value.  
See ```SENSOR_TYPES``` in ```sensor.py``` to get the list of supported headers.
- ```climate``` to manage water heater via ***Relais***  
Use it to switch on/off the heater and set the preset mode.  
- ```climate``` to manage heater via ***Fil Pilote***  
Setup a climate entity for each ***Fil Pilote***.  

Note : A mapping between ```hvac_mode``` and ```preset_mode``` has been implemented as follow :
```python
REMORA_PRESET_MODES_TO_HVAC_MODE = {
    remora.FpMode.Arrêt.name: HVAC_MODE_OFF,
    remora.FpMode.HorsGel.name: HVAC_MODE_COOL,
    remora.FpMode.Eco.name: HVAC_MODE_HEAT_COOL,
    remora.FpMode.Confort.name: HVAC_MODE_HEAT
}
```

### HASS Integration
Copy the custom_components folder to get it install under '/config/custom_components/remora/'.  
Edit your configuration.yaml file.

```YAML
# Remora
remora:
  host: 'Your Remora device hostname or IP address'

sensor:
  - platform: remora
  # scan_interval: xx (in sec, default 30)
    resources:
      # Add a list of valid TeleInfo headers
      # Check valid list with SENSOR_TYPES in sensor.py
      - IINST
      - ADCO
      - BASE
      - PAPP

climate:
  - platform: remora
    filpilote:
      # List of FilPilote index you want to manage
      # name is optional to set a friendly_name 
      # temp_sensor is optional for temperature sensor display
      - fp: 1
        name: 'Kitchen'
        temp_sensor: 'sensor.temperature_158d000XXXXXXX'
      - fp: 2
      - fp: 3
      - fp: 4
      - fp: 5
    relais: True
```

### Demo
![Example](https://user-images.githubusercontent.com/16355105/209246279-c3783768-7a41-495d-bedc-c5fcc68ca5c5.png)


### Energy Integration
You can add sensors like **BASE**, **HCHC**, **HCHP** or others **Index** on the Energy Dashboard.  
![Add Index to Energy Dashboard](https://user-images.githubusercontent.com/16355105/209245053-dfb6d78a-b246-46bf-8f89-b68840e11f78.png)  
  
This will give you the following energy consuption chart.  
![Energy Chart](https://user-images.githubusercontent.com/16355105/209245317-1ecf4e18-1a4d-48e8-99ae-317d921359b6.png)