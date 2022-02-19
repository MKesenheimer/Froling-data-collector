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

var maxvalues = 504; // one week if one datapoint every 20min
var min = Math.max(0, payload.length - maxvalues);
//debug.push({"min": min});


for (let i = min; i < payload.length; i++) {
  var timestamp = Date.parse(payload[i]["Datum/Uhrzeit"]);
  
  // extract the consumption per day
  // derivative of moving average
  var t = 24;
  var d = 7;
  var twindow = 60 * 60 * 1000 * t * d; // time window: one day
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

msg3.payload = [{"series":["Kollektor Pumpe [%]", "Puffer Pumpe [%]"], 
                "data":[p1, p2], 
                "labels": ["Kollektor Pumpe [%]", "Puffer Pumpe [%]"]}];

// Momentanwerte
pufferLadezustand = parseInt(payload[payload.length - 1]["Puffer Ladezustand [%]"]);
systemStatus = payload[payload.length - 1]["Status"]
pelletzaehler = nowconsumption;

var msg4 = {payload:pufferLadezustand};
var msg5 = {payload:systemStatus};
var msg6 = {payload:pelletzaehler + " kg"};

var msg_debug = {payload:debug}

return [msg1, msg2, msg3, msg4, msg5, msg6];