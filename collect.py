#!/usr/bin/env python3
import requests
import argparse
import time
import sys
import os
import datetime
#from tabulate import tabulate
from enum import Enum
from paho.mqtt import client as mqtt

__prog_name__ = 'Froling data collector'
__version__ = 0.3

# globals
outputdir = "."
client = None

# Energie, die nötig ist, 1 Liter Wasser um 1K zu erwärmen [Wh / l K]
pEnergiedichte = 1.16
# Puffervolumen, das ist der Teil des Wassers im Heizkreis, aus dem die Wärme entnommen wird
gesamtVolumen = 1000

# Energiedichte von Pellets in Wh/kg
pPelletsEnergiedichte = 4800

# MQTT
QOS = 1

def log(message):
    global outputdir
    now = datetime.datetime.now()
    date_time = now.strftime("%d.%m.%Y %H:%M:%S: ")
    message = date_time + message
    print(message)
    # write message to file
    f = open(outputdir + "/collection.log", 'a')
    f.write(message)
    f.write("\n")
    f.close()

class Status(Enum):
    ERROR = 2,
    LOGIN_FAILED = 1,
    SUCCESS = 0

def login(cfg):
    global outputdir
    log("[+] Logging in...")
    url = "https://connect-api.froeling.com:443/app/v1.0/resources/loginNew"
    headers = {"Content-Type": "application/json", "Connection": "close", "Accept": "*/*", "User-Agent": "Froeling PROD/2107.1 (com.froeling.connect-ios; build:2107.1.01; iOS 15.2.1) Alamofire/4.8.1", "Accept-Language": "en", "Accept-Encoding": "gzip, deflate"}
    data={"deviceId": cfg.deviceID, "osType": "IOS", "password": cfg.password, "pushToken": "", "userName": cfg.username}
    response = requests.post(url, headers=headers, json=data)
    bearer = response.headers['Authorization']

    f = open(outputdir + "/bearer.txt", "w")
    f.write(bearer)
    f.close()
    if len(bearer) == 0:
        log("[-] Login failed.")
        return Status.LOGIN_FAILED
    else:
        log("[+] Login succeeded.")
        return Status.SUCCESS

def mqttConnect(cfg):
    global client
    client = mqtt.Client()
    client.username_pw_set(cfg.mqttusername, cfg.mqttpassword)
    client.will_set("/froling/status", "connection failure", qos=QOS, retain=False)
    mip, mport = cfg.mqttbroker.split(":")
    client.connect(mip, int(mport))
    client.loop_start()

def mqttDisconnect():
    global client
    try:
        client.disconnect()
    except:
        pass

def publishMessage(topic, value):
    global client
    info = client.publish(topic, value, qos=QOS)
    info.wait_for_publish()

def getFacilityDetails(cfg):
    global outputdir
    try:
        f = open(outputdir + "/bearer.txt", "r")
        bearer = f.read()
        f.close()
    except:
        return Status.LOGIN_FAILED, [], []

    url = "https://connect-api.froeling.com:443/app/v1.0/resources/facility/getFacilityDetails/41641"
    headers = {"Connection": "close", "Accept": "*/*", "User-Agent": "Froeling PROD/2107.1 (com.froeling.connect-ios; build:2107.1.01; iOS 15.2.1) Alamofire/4.8.1", "Accept-Language": "en", "Accept-Encoding": "gzip, deflate", 'Authorization': bearer}
    
    try:
      response = requests.get(url, headers=headers)
    except:
      return Status.ERROR, [], []

    if "security check failed" in str(response.content) or len(str(response.content)) == 0:
        return Status.LOGIN_FAILED, [], []

    #log("response = {}".format(response.content))
    try:
      data = response.json()
    except:
      return Status.ERROR, [], []

    # TODO: Diese Zuordnung ist individuell für die Anlage.
    # TODO: Die Zuordnung sollte dynamisch geschehen, ggf. mit einer Schleife alle Keys durchgehen
    # und die Zuordnung dynamisch erzeugen.
    # Boiler
    istTemp = data['userMenus'][0]['topView'][0]
    betriebsstunden = data['userMenus'][0]['topView'][1]
    brennerstarts = data['userMenus'][0]['topView'][2]
    stundenSeitWartung = data['userMenus'][0]['topView'][3]
    teillastStunden = data['userMenus'][0]['topView'][4]
    fernschalten = data['userMenus'][0]['topView'][5]
    boilerState = data['userMenus'][0]['topView'][6]
    betriebsArt = data['userMenus'][0]['topView'][7]
    kesselEinAus = data['userMenus'][0]['topView'][8]
    facilityState = data['userMenus'][0]['topView'][9]
    betriebsArtKessel = data['userMenus'][0]['topView'][10]
    
    # Heizkreis
    hkEditierbar = data['userMenus'][1]['topView'][0]
    pumpeAktiv = data['userMenus'][1]['topView'][1]
    betriebsart = data['userMenus'][1]['topView'][2]
    vorlaufBeiMinus10 = data['userMenus'][1]['topView'][3]
    vorlaufBeiPlus10 = data['userMenus'][1]['topView'][4]
    componentName = data['userMenus'][1]['topView'][5]

    # Warmwasser
    istTemp = data['userMenus'][2]['topView'][0]
    sollTemp = data['userMenus'][2]['topView'][1]
    pumpeAktiv = data['userMenus'][2]['topView'][2]
    betriebsart = data['userMenus'][2]['topView'][3]
    componentName = data['userMenus'][2]['topView'][4]

    # Puffer
    bufferSensorAmount = data['userMenus'][3]['topView'][0]
    Ladezustand = data['userMenus'][3]['topView'][1]
    Ladezustand_diskret = data['userMenus'][3]['topView'][2]
    pumpeAnsteuerung = data['userMenus'][3]['topView'][3]
    componentName = data['userMenus'][3]['topView'][4]
    fuehlerOben = data['userMenus'][3]['topView'][5]
    fuehlerUnten = data['userMenus'][3]['topView'][6]

    # Kollektor
    kollektorPumpe = data['userMenus'][4]['topView'][0]
    kollektorTemp = data['userMenus'][4]['topView'][1]

    # Pelletlage
    Restbestand = data['userMenus'][5]['topView'][0]
    zaehlerRest = data['userMenus'][5]['topView'][1]
    
    # Zirkulationspumpe
    drehzahlPumpe = data['userMenus'][6]['topView'][0]
    ruecklaufTempIst = data['userMenus'][6]['topView'][1]
    ruecklaufTempAbschalten = data['userMenus'][6]['topView'][2]

    # relevante Grössen
    #facilityState = data['userMenus'][0]['topView'][9]['parameter']
    boilerState = data['userMenus'][0]['topView'][6]['parameter']
    boilerIstTemp = data['userMenus'][0]['listView'][0]
    kesselEinAus = data['userMenus'][0]['topView'][8]['parameter']
    kgCounter = data['userMenus'][5]['listView'][1]
    tCounter = data['userMenus'][5]['listView'][2]
    vorlaufBeiMinus10 = data['userMenus'][1]['topView'][3]['parameter']
    vorlaufBeiPlus10 = data['userMenus'][1]['topView'][4]['parameter']
    aktuellerVorlauf = data['userMenus'][1]['listView'][0]
    hkpumpeAktiv = data['userMenus'][1]['topView'][1]['parameter']
    outAirTemp = data['userMenus'][1]['listView'][2]
    warmwasserIst = data['userMenus'][2]['topView'][0]['parameter']
    warmwasserSoll = data['userMenus'][2]['topView'][1]['parameter']
    pufferLadezustand = data['userMenus'][3]['topView'][1]['parameter']
    pufferPumpeAnsteuerung = data['userMenus'][3]['topView'][3]['parameter']
    pufferfuehlerOben = data['userMenus'][3]['topView'][5]['parameter']
    pufferfuehlerUnten = data['userMenus'][3]['topView'][6]['parameter']
    kollektorTemp = data['userMenus'][4]['topView'][1]['parameter']
    kollektorPumpe = data['userMenus'][4]['topView'][0]['parameter']
    #log(kollektorPumpe)

    # Header
    header = ["Datum/Uhrzeit",
        "Status",
        "Boiler Ist [{}]".format(boilerIstTemp['unitLabel']),
        #"Boiler An/Aus",
        "HK Vorlauf bei -10°C [{}]".format(vorlaufBeiMinus10['unitLabel']),
        "HK Vorlauf bei +10°C [{}]".format(vorlaufBeiMinus10['unitLabel']),
        "HK Vorlauf ist [{}]".format(aktuellerVorlauf['unitLabel']),
        "HK Pumpe [%]",
        "Aussentemperatur [{}]".format(outAirTemp['unitLabel']),
        "Warmwasser Ist [{}]".format(warmwasserIst['unitLabel']),
        "Warmwasser Soll [{}]".format(warmwasserSoll['unitLabel']),
        "Puffer Fuehler oben [{}]".format(pufferfuehlerOben['unitLabel']),
        "Puffer Fuehler unten [{}]".format(pufferfuehlerUnten['unitLabel']),
        "Puffer Ladezustand [{}]".format(pufferLadezustand['unitLabel']),
        "Puffer Pumpe [%]".format(pufferPumpeAnsteuerung['unitLabel']),
        "Kollektor [{}]".format(kollektorTemp['unitLabel']),
        "Kollektor Pumpe [{}]".format(kollektorPumpe['unitLabel']),
        "Pelletverbrauch [{}]".format(kgCounter['unitLabel']),
        "Pelletverbrauch [{}]".format(tCounter['unitLabel'])]

    now = datetime.datetime.now()
    values = [now.strftime("%Y-%m-%d %H:%M:%S"),
            boilerState['valueText'],
            boilerIstTemp['valueText'],
            #kesselEinAus['valueText'],
            vorlaufBeiMinus10['valueText'],
            vorlaufBeiPlus10['valueText'],
            aktuellerVorlauf['valueText'],
            str(int(hkpumpeAktiv['valueText']) * 100),
            outAirTemp['valueText'],
            warmwasserIst['valueText'],
            warmwasserSoll['valueText'],
            pufferfuehlerOben['valueText'],
            pufferfuehlerUnten['valueText'],
            pufferLadezustand['valueText'],
            pufferPumpeAnsteuerung['valueText'],
            kollektorTemp['valueText'],
            kollektorPumpe['valueText'],
            kgCounter['valueText'],
            tCounter['valueText']]

    # derived values
    # Fördermenge der Pumpe, [l / h]
    literProStunde = 400 * float(kollektorPumpe['valueText']) / 100
    deltaT1 = float(kollektorTemp['valueText']) - float(pufferfuehlerUnten['valueText'])
    leistungSolar = pEnergiedichte * literProStunde * deltaT1
    # TODO: erzeugte Energie der Solaranlage berechnen

    # verbrauchte Energie des Kessels
    pelletZaehler = kgCounter['valueText'] + tCounter['valueText'] * 1000
    # verbrauchte Energie des Kessels in Wh
    energieKessel = pPelletsEnergiedichte * pelletZaehler

    # publish all values
    mqttConnect(cfg)
    publishMessage("/froling/boilerState", boilerState['valueText'])
    publishMessage("/froling/boilerIstTemp", boilerIstTemp['valueText'])
    publishMessage("/froling/vorlaufBeiMinus10", vorlaufBeiMinus10['valueText'])
    publishMessage("/froling/vorlaufBeiPlus10", vorlaufBeiPlus10['valueText'])
    publishMessage("/froling/aktuellerVorlauf", aktuellerVorlauf['valueText'])
    publishMessage("/froling/hkpumpeAktiv", str(int(hkpumpeAktiv['valueText']) * 100))
    publishMessage("/froling/outAirTemp", outAirTemp['valueText'])
    publishMessage("/froling/warmwasserIst", warmwasserIst['valueText'])
    publishMessage("/froling/pufferfuehlerOben", pufferfuehlerOben['valueText'])
    publishMessage("/froling/pufferfuehlerUnten", pufferfuehlerUnten['valueText'])
    publishMessage("/froling/pufferLadezustand", pufferLadezustand['valueText'])
    publishMessage("/froling/pufferPumpeAnsteuerung", pufferPumpeAnsteuerung['valueText'])
    publishMessage("/froling/kollektorTemp", kollektorTemp['valueText'])
    publishMessage("/froling/kollektorPumpe", kollektorPumpe['valueText'])
    publishMessage("/froling/leistungSolar", leistungSolar)
    publishMessage("/froling/pelletZaehler", pelletZaehler)
    publishMessage("/froling/energieKessel", energieKessel)
    mqttDisconnect()

    return Status.SUCCESS, header, values


def main():
    parser = argparse.ArgumentParser(description='%s version %.2f' % (__prog_name__, __version__))
    parser.add_argument('-u', '--username',
        action='store',
        metavar='<username>',
        dest='username',
        help='The username to the Froling services.',
        default='')

    parser.add_argument('-p', '--password',
        action='store',
        metavar='<password>',
        dest='password',
        help='The password to the Froling services.',
        default='')

    parser.add_argument('-d', '--deviceID',
        action='store',
        metavar='<deviceID>',
        dest='deviceID',
        help='The device ID to use',
        default='')

    parser.add_argument('-o', '--output-dir',
        action='store',
        metavar='<outputdir>',
        dest='outputdir',
        help='The directory to store the data to.',
        default='.')

    parser.add_argument('-m', '--mqtt-broker',
        action='store',
        metavar='<mqtt-broker-ip:port>',
        dest='mqttbroker',
        help='The MQTT broker IP and port. Format: ip:port.',
        default='127.0.0.1:1883')

    parser.add_argument('-U', '--mqtt-username',
        action='store',
        metavar='<mqtt-username>',
        dest='mqttusername',
        help='The username to login to the MQTT broker.',
        default='')

    parser.add_argument('-P', '--mqtt-password',
        action='store',
        metavar='<mqtt-password>',
        dest='mqttpassword',
        help='The password to login to the MQTT broker.',
        default='')

    parser.add_argument('-i', '--intervall',
        action='store',
        metavar='<intervall>',
        dest='intervall',
        type=int,
        help='The time intervall in seconds to poll the data.',
        default=60)

    cfg = parser.parse_args()
    cfg.prog_name = __prog_name__

    global outputdir
    outputdir = cfg.outputdir

    pid = os.getpid()
    with open(outputdir + "/process.id", "w") as pidfile:  
        pidfile.write("{}".format(pid))

    # mqtt
    #mqttConnect(cfg)

    log("[+] Collecting data...")
    status, header, data = getFacilityDetails(cfg)
    #log(",".join(header))

    prevStatus = Status.SUCCESS
    while True:
        status, header, data = getFacilityDetails(cfg)
        if status == Status.LOGIN_FAILED:
            log("[-] Login failed. Trying again in 5s.")
            time.sleep(5)
            login(cfg)

        elif status != Status.ERROR:
            if prevStatus != Status.SUCCESS:
                log("[+] Continuing collecting data.")
        
            # write data to file
            if os.path.isfile(outputdir + "/data.csv"):
                f = open(outputdir + "/data.csv", 'a')
                f.write(",".join(data))
                f.write("\n")
                f.close()
            else:
                f = open(outputdir + "/data.csv", 'w')
                f.write(",".join(header))
                f.write("\n")
                f.write(",".join(data))
                f.write("\n")
                f.close()

            time.sleep(cfg.intervall)

        else:
            log("[-] General error occured. Trying again in 60s.")
            time.sleep(60)

        prevError = status



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log('[+] Exiting...')
        mqttDisconnect()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
