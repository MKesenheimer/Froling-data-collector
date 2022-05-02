var payload = msg.payload;
var debug = [];

// consumptions
var c1 = [];

// temperatures
var t1 = [];
var t2 = [];
var t3 = [];
var t4 = [];
var t5 = [];
var t6 = [];
var t7 = [];

// pumps
var p1 = [];
var p2 = [];
var p3 = [];

// powers
var P1 = [];
var P2 = [];

// Momentanleistung der Solaranlage in kW
var leistungSolar = 0;
// Momentanverlustleistung bzw. Heizlast des gesamten Hauses
var leistungVerlust = 0;

// Energie, die nötig ist, 1 Liter Wasser um 1K zu erwärmen [Wh / l K]
var pEnergiedichte = 1.16;

var maxvalues = 504; // one week if one datapoint every 20min
var min = Math.max(0, payload.length - maxvalues);
//debug.push({"min": min});

for (let i = min; i < payload.length; i++) {
  var timestamp = Date.parse(payload[i]["Datum/Uhrzeit"]);
  
  // extract the consumption per day
  // derivative of moving average
  var t = 24;
  var d = 7; // time window: seven day
  var twindow = 60 * 60 * 1000 * t * d; // 1000ms = 1s
  var prev = timestamp - twindow;
  index = 0;
  for (let j = i; j >= 0; j--) {
    var prevtimestamp = Date.parse(payload[j]["Datum/Uhrzeit"]);
    if (prevtimestamp < prev) {
        index = j;
        break;
    }
  }
  
  //debug.push({"timestamp":timestamp,"prevtimestamp":prevtimestamp, "index":i, "previous index":index});
  
  var prevconsumption = parseInt(payload[index]["Pelletverbrauch [kg]"]) + parseInt(payload[index]["Pelletverbrauch [t]"]) * 1000;
  var nowconsumption = parseInt(payload[i]["Pelletverbrauch [kg]"]) + parseInt(payload[i]["Pelletverbrauch [t]"]) * 1000;
  var consumptionPerTime = (nowconsumption - prevconsumption) / d;
  
  var kgpelletverbrauch = {"x":timestamp, "y":(consumptionPerTime)};
  var boilerIst = {"x":timestamp, "y":parseInt(payload[i]["Boiler Ist [°C]"])};
  var hkvorlaufIst = {"x":timestamp, "y":parseInt(payload[i]["HK Vorlauf ist [°C]"])};
  var aussentemp = {"x":timestamp, "y":parseInt(payload[i]["Aussentemperatur [°C]"])};
  var warmwasserIst = {"x":timestamp, "y":parseInt(payload[i]["Warmwasser Ist [°C]"])};
  var pufferFuehlerOben = {"x":timestamp, "y":parseInt(payload[i]["Puffer Fuehler oben [°C]"])};
  var pufferFuehlerUnten = {"x":timestamp, "y":parseInt(payload[i]["Puffer Fuehler unten [°C]"])};
  var kollektorIst = {"x":timestamp, "y":parseInt(payload[i]["Kollektor [°C]"])};
  var kollektorPumpe = {"x":timestamp, "y":parseInt(payload[i]["Kollektor Pumpe [%]"])};
  var pufferPumpe = {"x":timestamp, "y":parseInt(payload[i]["Puffer Pumpe [%]"])};
  var heizkreisPumpe = {"x":timestamp, "y":parseInt(payload[i]["HK Pumpe [%]"])};
  
  // Abschätzung der Leistung der Solaranlage
  // Hinweis: die maximale Fördermenge wurde aus dem Datenblatt der Pumpe Grundfos UPM3 25-75 geschätzt.
  // Bruttokollektorfläche ~9.78m^2, 2 * 30 Röhren (HP 30 Sunex)
  // Außerdem wurde dieser Faktor aus dem Wärmeverlust des Hauses  abgeschätzt.
  // Ohne übermäßigem Wasserverbrauch (kein Warmwasser, nur Heizung) braucht das Haus bei 0°C Aussentemperatur ungefähr 1.9kW an Leistung, um die Innentemperatur konstant zu halten.
  // Die Leistung der Solaranlage muss nun 1.9kW betragen, wenn sich die Temperatur des Puffers nicht ändert.
  // Also kann der Faktor so gewählt werden, dass die Momentanleistung der Solaranlage 1.9kW beträgt, wenn die Aussentemperatur 0°C beträgt und die Puffertemperatur konstant ist.
  var literProStunde = 400 * parseInt(payload[i]["Kollektor Pumpe [%]"]) / 100; // Fördermenge der Pumpe, [l / h]
  var deltaT1 = parseInt(payload[i]["Kollektor [°C]"]) - parseInt(payload[i]["Puffer Fuehler unten [°C]"]);
  leistungSolar = parseInt(pEnergiedichte * literProStunde * deltaT1 * 10) / 10;
  var powerSolar = {"x":timestamp, "y":leistungSolar};
  
  c1.push(kgpelletverbrauch);
  
  t1.push(boilerIst);
  t2.push(hkvorlaufIst);
  t3.push(aussentemp);
  t4.push(warmwasserIst);
  t5.push(pufferFuehlerOben);
  t6.push(pufferFuehlerUnten);
  t7.push(kollektorIst);
  
  p1.push(kollektorPumpe);
  p2.push(pufferPumpe);
  p3.push(heizkreisPumpe);
  
  P1.push(powerSolar);
}

var msg1 = {payload:""};
var msg2 = {payload:""};
var msg3 = {payload:""};

msg1.payload = [{"series":"Pelletverbrauch [kg]", 
                "data":[c1], 
                "labels": "Pelletverbrauch [kg]"}];
                
msg2.payload = [{"series":["Boiler Ist [°C]", "HK Vorlauf ist [°C]", "Aussentemperatur [°C]", "Warmwasser Ist [°C]", "Puffer Fuehler oben [°C]", "Puffer Fuehler unten [°C]", "Kollektor [°C]"], 
                "data":[t1, t2, t3, t4, t5, t6, t7], 
                "labels": ["Boiler Ist [°C]", "HK Vorlauf ist [°C]", "Aussentemperatur [°C]", "Warmwasser Ist [°C]", "Puffer Fuehler oben [°C]", "Puffer Fuehler unten [°C]", "Kollektor [°C]"]}];

msg3.payload = [{"series":["Kollektor Pumpe [%]", "Puffer Pumpe [%]", "HK Pumpe [%]"], 
                "data":[p1, p2, p3], 
                "labels": ["Kollektor Pumpe [%]", "Puffer Pumpe [%]", "HK Pumpe [%]"]}];

// Momentanwerte
pufferLadezustand = parseInt(payload[payload.length - 1]["Puffer Ladezustand [%]"]);
systemStatus = payload[payload.length - 1]["Status"]
pelletzaehler = nowconsumption;

// Langzeitmittelwert Verbrauch
var start = Date.parse("2021-11-01");
var now = Date.parse(payload[payload.length - 1]["Datum/Uhrzeit"]);
var days = parseInt((now - start) / 1000 / 24 / 60 / 60);
var longrun = parseInt(pelletzaehler / days * 10) / 10;

// Abschätzung der Verlustleistung bzw. Heizlast des Hauses
// Puffervolumen, das ist der Teil des Wassers im Heizkreis, aus dem die Wärme entnommen wird
var gesamtVolumen = 1000;
// Temperaturabfall pro Stunde (3 * 20min = 1h)
var deltaT2proh = 0;
if (payload.length >= 4) {
  deltaT2proh = parseInt(payload[payload.length - 1]["Puffer Fuehler oben [°C]"]) - parseInt(payload[payload.length - 4]["Puffer Fuehler oben [°C]"]);
}
// Da wir nur die Puffertemperatur zur Verfügung stehen haben und die Puffertemperatur aus der Summe aller Leistungen entsteht, 
// die ins System eingebracht werden, muss die Verlustleistung um die eingebrachten Leistungen korrigiert werden.
// TODO: Heizleistung muss auch noch abgezogen werden.
leistungVerlust = parseInt((pEnergiedichte * gesamtVolumen * deltaT2proh - leistungSolar) * 10) / 10;

// DEBUG
debug.push(days);

var msg4 = {payload:pufferLadezustand};
var msg5 = {payload:systemStatus};
var msg6 = {payload:pelletzaehler};
var msg7 = {payload:longrun};
var msg8 = {payload:leistungSolar};
var msg9 = {payload:leistungVerlust};

return [msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8, msg9];
