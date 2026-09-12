const GOLD = {"0":[0,1,16,22,15,11,19],"1":[0,2,17,4],"2":[0,1,12,20,4,2],"3":[0,1,22,17,7,6],"4":[0,1,3],"5":[0,1,16,4,24],"6":[0,2,3],"7":[0,1,5,20,2,9,14,15,16,19,18],"8":[0,1,19,2],"9":[0,2,3],"10":[0,2,3],"11":[0,2,3],"12":[0,1,2],"13":[0,1,3],"14":[0,2,15,8],"15":[0,1,5,20,2],"16":[0,1,2],"17":[0,1,7,20,25,13],"18":[0,3,13,14],"19":[0,1,4],"20":[0,1,16,4,24],"21":[0,1,23,13],"22":[0,1,12,20,4,2],"23":[0,2,3],"24":[0,1,8,13],"25":[0,1,4],"26":[0,1,6,4],"27":[0,2,13,3],"28":[0,1,7,20,25,13],"29":[0,2,14],"30":[0,1,23,13],"31":[0,1,15,11,2,12,14,10,20],"32":[0,2,6],"33":[0,1,17,2,4,9,14],"34":[0,1,16,8,13,23,12,7],"35":[0,1,2],"36":[0,2,10],"37":[0,1,4,2,11],"38":[0,2,11],"39":[0,3,18],"40":[0,1,18,5,3],"41":[0,2,4],"42":[0,2,6],"43":[0,3,24,16,17],"44":[0,1,12],"45":[0,2,10,20,8,18,24],"46":[0,1,13,5],"47":[0,1,2,25],"48":[0,1,17],"49":[0,2,17,4],"50":[0,1,13,5],"51":[0,3,18],"52":[0,1,10,19],"53":[0,1,19,2],"54":[0,3,14],"55":[0,1,3,22,8,14,9,15,5],"56":[0,3,11,4],"57":[0,2,15,8],"58":[0,2,19,13,21],"59":[0,1,5,19,2],"60":[0,3,7,21],"61":[0,1,10,19],"62":[0,1,15,25,17,4],"63":[0,1,15,8,2],"64":[0,1,15,11,2],"65":[0,1,12,3],"66":[0,1,5,3],"67":[0,2,6,10],"68":[0,1,25,24,18],"69":[0,1,15,11,2]};

function sheet_() {
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheets()[0];
  if (sh.getLastRow() === 0) {
    sh.appendRow([
      "ts", "who", "graph_id", "gitqa_id", "choice_nodes", "readable", "correct", "ms",
    ]);
  }
  return sh;
}

function parseNodes_(s) {
  if (Object.prototype.toString.call(s) === "[object Array]") return s.map(Number);
  if (!s) return [];
  return String(s).split(/[-,]/).map(Number).filter(function (x) { return !isNaN(x); });
}

function norm_(nodes) {
  var n = parseNodes_(nodes);
  if (n.length >= 2 && n[0] === n[n.length - 1]) n = n.slice(0, -1);
  if (n.length < 3) return "";
  function rot(seq) {
    var i = seq.indexOf(Math.min.apply(null, seq));
    return seq.slice(i).concat(seq.slice(0, i)).join(",");
  }
  var a = rot(n);
  var b = rot(n.slice().reverse());
  return a < b ? a : b;
}

function doneFor_(who) {
  var sh = sheet_();
  var vals = sh.getDataRange().getValues();
  var out = [];
  for (var i = 1; i < vals.length; i++) {
    if (String(vals[i][1]) === String(who) && vals[i][2] !== "") {
      out.push(Number(vals[i][2]));
    }
  }
  return out;
}

function jsonp_(e, obj) {
  var body = JSON.stringify(obj);
  var cb = e && e.parameter && e.parameter.callback;
  if (cb) {
    return ContentService.createTextOutput(cb + "(" + body + ")")
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return ContentService.createTextOutput(body).setMimeType(ContentService.MimeType.JSON);
}

function writeRow_(row) {
  var who = String(row.who || "").trim();
  var gid = Number(row.graph_id);
  var nodes = parseNodes_(row.nodes);
  var gold = GOLD[String(gid)] || [];
  var correct = norm_(nodes) === norm_(gold) ? 1 : 0;
  sheet_().appendRow([
    new Date().toISOString(),
    who,
    gid,
    row.gitqa_id || "",
    nodes.join("-"),
    row.readable || "",
    correct,
    row.ms || "",
  ]);
  return { ok: true, correct: correct, done: doneFor_(who) };
}

function doGet(e) {
  e = e || { parameter: {} };
  if (String(e.parameter.write || "") === "1") {
    return jsonp_(e, writeRow_({
      who: e.parameter.who,
      graph_id: e.parameter.graph_id,
      gitqa_id: e.parameter.gitqa_id,
      nodes: e.parameter.nodes,
      readable: e.parameter.readable,
      ms: e.parameter.ms,
    }));
  }
  var who = (e.parameter.who || "").trim();
  if (!who) return jsonp_(e, { ok: false, error: "missing who" });
  var done = doneFor_(who);
  return jsonp_(e, { ok: true, who: who, done: done, n: done.length });
}

function doPost(e) {
  var raw = (e.postData && e.postData.contents) || "{}";
  return jsonp_(e, writeRow_(JSON.parse(raw)));
}
