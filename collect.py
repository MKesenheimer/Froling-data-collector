#!/usr/bin/env python3
import requests
import argparse
import time
import sys
import os
import datetime
#from tabulate import tabulate
from enum import Enum

__prog_name__ = 'Froling data collector'
__version__ = 0.1

class Status(Enum):
    LOGIN_FAILED = 1,
    SUCCESS = 0

def login(cfg):
    print("[+] Logging in...")
    url = "https://connect-api.froeling.com:443/app/v1.0/resources/loginNew"
    headers = {"Content-Type": "application/json", "Connection": "close", "Accept": "*/*", "User-Agent": "Froeling PROD/2107.1 (com.froeling.connect-ios; build:2107.1.01; iOS 15.2.1) Alamofire/4.8.1", "Accept-Language": "en", "Accept-Encoding": "gzip, deflate"}
    data={"deviceId": cfg.deviceID, "osType": "IOS", "password": cfg.password, "pushToken": "", "userName": cfg.username}
    response = requests.post(url, headers=headers, json=data)
    bearer = response.headers['Authorization']

    f = open("bearer.txt", "w")
    f.write(bearer)
    f.close()
    if len(bearer) == 0:
        print("[-] Login failed.")
        return Status.LOGIN_FAILED
    else:
        print("[+] Login succeeded.")
        return Status.SUCCESS


def getFacilityDetails(cfg):
    try:
        f = open("bearer.txt", "r")
        bearer = f.read()
        f.close()
    except:
        return Status.LOGIN_FAILED, [], []

    url = "https://connect-api.froeling.com:443/app/v1.0/resources/facility/getFacilityDetails/41641"
    headers = {"Connection": "close", "Accept": "*/*", "User-Agent": "Froeling PROD/2107.1 (com.froeling.connect-ios; build:2107.1.01; iOS 15.2.1) Alamofire/4.8.1", "Accept-Language": "en", "Accept-Encoding": "gzip, deflate", 'Authorization': bearer}
    response = requests.get(url, headers=headers)

    if "security check failed" in str(response.content) or len(str(response.content)) == 0:
        return Status.LOGIN_FAILED, [], []

    #print("response = {}".format(response.content))
    data = response.json()

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
    istTemp = data['userMenus'][0]['listView'][0]
    kgCounter = data['userMenus'][5]['listView'][1]
    vorlaufBeiMinus10 = data['userMenus'][1]['topView'][3]['parameter']
    vorlaufBeiPlus10 = data['userMenus'][1]['topView'][4]['parameter']
    aktuellerVorlauf = data['userMenus'][1]['listView'][0]
    outAirTemp = data['userMenus'][1]['listView'][2]
    warmwasserIst = data['userMenus'][2]['topView'][0]['parameter']
    warmwasserSoll = data['userMenus'][2]['topView'][1]['parameter']
    kollektorTemp = data['userMenus'][4]['topView'][1]['parameter']
    kollektorPumpe = data['userMenus'][4]['topView'][0]['parameter']
    #print(kollektorPumpe)

    # Header
    header = ["Datum/Uhrzeit","Boiler Ist [{}]".format(istTemp['unitLabel']),
        "HK Vorlauf bei -10°C [{}]".format(vorlaufBeiMinus10['unitLabel']),
        "HK Vorlauf bei +10°C [{}]".format(vorlaufBeiMinus10['unitLabel']),
        "HK Vorlauf ist [{}]".format(aktuellerVorlauf['unitLabel']),
        "Aussentemperatur [{}]".format(outAirTemp['unitLabel']),
        "Warmwasser Ist [{}]".format(warmwasserIst['unitLabel']),
        "Warmwasser Soll [{}]".format(warmwasserSoll['unitLabel']),
        "Kollektor [{}]".format(kollektorTemp['unitLabel']),
        "Kollektorpumpe [{}]".format(kollektorPumpe['unitLabel']),
        "Pelletverbrauch [{}]".format(kgCounter['unitLabel'])]

    now = datetime.datetime.now()
    values = [now.strftime("%Y-%m-%d %H:%M:%S"),
            istTemp['valueText'], 
            vorlaufBeiMinus10['valueText'],
            vorlaufBeiPlus10['valueText'],
            aktuellerVorlauf['valueText'],
            outAirTemp['valueText'],
            warmwasserIst['valueText'],
            warmwasserSoll['valueText'],
            kollektorTemp['valueText'],
            kollektorPumpe['valueText'],
            kgCounter['valueText']]

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

    parser.add_argument('-i', '--intervall',
        action='store',
        metavar='<intervall>',
        dest='intervall',
        type=int,
        help='The time intervall to poll the data.',
        default=60)

    cfg = parser.parse_args()
    cfg.prog_name = __prog_name__

    print("[+] Collecting data...")
    status, header, data = getFacilityDetails(cfg)
    print(",".join(header))

    while True:
        if status == Status.LOGIN_FAILED:
            login(cfg)
        status, header, data = getFacilityDetails(cfg)
        #collectedData += [data]
        #print(tabulate([data],headers=header))
        print(",".join(data))

        # write data to file
        if os.path.isfile('data.csv'):
            f = open("data.csv", 'a')
            f.write(",".join(data))
            f.write("\n")
            f.close()
        else:
            f = open("data.csv", 'w')
            f.write(",".join(header))
            f.write("\n")
            f.write(",".join(data))
            f.write("\n")
            f.close()

        time.sleep(cfg.intervall)




if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Exiting...')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
