const GOLD = {"0":[0,1,16,22,15,11,19],"1":[0,2,17,4],"2":[0,1,12,20,4,2],"3":[0,1,22,17,7,6],"4":[0,1,3],"5":[0,1,16,4,24],"6":[0,2,3],"7":[0,1,5,20,2,9,14,15,16,19,18],"8":[0,1,19,2],"9":[0,2,3],"10":[0,2,3],"11":[0,2,3],"12":[0,1,2],"13":[0,1,3],"14":[0,2,15,8],"15":[0,1,5,20,2],"16":[0,1,2],"17":[0,1,7,20,25,13],"18":[0,3,13,14],"19":[0,1,4],"20":[0,1,16,4,24],"21":[0,1,23,13],"22":[0,1,12,20,4,2],"23":[0,2,3],"24":[0,1,8,13],"25":[0,1,4],"26":[0,1,6,4],"27":[0,2,13,3],"28":[0,1,7,20,25,13],"29":[0,2,14],"30":[0,1,23,13],"31":[0,1,15,11,2,12,14,10,20],"32":[0,2,6],"33":[0,1,17,2,4,9,14],"34":[0,1,16,8,13,23,12,7],"35":[0,1,2],"36":[0,2,10],"37":[0,1,4,2,11],"38":[0,2,11],"39":[0,3,18],"40":[0,1,18,5,3],"41":[0,2,4],"42":[0,2,6],"43":[0,3,24,16,17],"44":[0,1,12],"45":[0,2,10,20,8,18,24],"46":[0,1,13,5],"47":[0,1,2,25],"48":[0,1,17],"49":[0,2,17,4],"50":[0,1,13,5],"51":[0,3,18],"52":[0,1,10,19],"53":[0,1,19,2],"54":[0,3,14],"55":[0,1,3,22,8,14,9,15,5],"56":[0,3,11,4],"57":[0,2,15,8],"58":[0,2,19,13,21],"59":[0,1,5,19,2],"60":[0,3,7,21],"61":[0,1,10,19],"62":[0,1,15,25,17,4],"63":[0,1,15,8,2],"64":[0,1,15,11,2],"65":[0,1,12,3],"66":[0,1,5,3],"67":[0,2,6,10],"68":[0,1,25,24,18],"69":[0,1,15,11,2]};

function bindSheet() {
  var ss = SpreadsheetApp.getActive();
  if (!ss) throw new Error("Open this script from the Sheet: Extensions → Apps Script");
  PropertiesService.getScriptProperties().setProperty("SS_ID", ss.getId());
}

function sheet_() {
  var id = PropertiesService.getScriptProperties().getProperty("SS_ID");
  var ss = id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActive();
  if (!ss) throw new Error("Run bindSheet once in the Apps Script editor");
  var sh = ss.getSheets()[0];
  if (sh.getLastRow() === 0) {
    sh.appendRow([
      "ts", "who", "graph_id", "gitqa_id", "choice_nodes", "readable", "correct", "ms",
    ]);
  }
  // Keep node lists as text: Sheets turns "0-1-3" into the date 2000-1-3 otherwise.
  sh.getRange("E:E").setNumberFormat("@");
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

function stats_() {
  var vals = sheet_().getDataRange().getValues();
  var rows = [];
  for (var i = 1; i < vals.length; i++) {
    if (vals[i][1] === "" && vals[i][2] === "") continue;
    rows.push({
      ts: String(vals[i][0] || ""),
      who: String(vals[i][1] || ""),
      graph_id: Number(vals[i][2]),
      gitqa_id: String(vals[i][3] || ""),
      choice_nodes: String(vals[i][4] || "").replace(/^'/, ""),
      readable: String(vals[i][5] || ""),
      correct: Number(vals[i][6] || 0),
      ms: Number(vals[i][7] || 0)
    });
  }
  return rows;
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
    "'" + nodes.join("-"),
    row.readable || "",
    correct,
    row.ms || "",
  ]);
  return { ok: true, correct: correct, done: doneFor_(who) };
}

function rowFrom_(e) {
  var p = (e && e.parameter) || {};
  if (p.who) return p;
  var raw = (e.postData && e.postData.contents) || "";
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch (err) {
    return p;
  }
}

function doGet(e) {
  try {
    e = e || { parameter: {} };
    if (String(e.parameter.ping || "") === "1") {
      return jsonp_(e, { ok: true, ping: true });
    }
    if (String(e.parameter.stats || "") === "1") {
      var rows = stats_();
      return jsonp_(e, { ok: true, n: rows.length, rows: rows });
    }
    if (String(e.parameter.write || "") === "1") {
      return jsonp_(e, writeRow_(rowFrom_(e)));
    }
    var who = (e.parameter.who || "").trim();
    if (!who) return jsonp_(e, { ok: false, error: "missing who" });
    var done = doneFor_(who);
    return jsonp_(e, { ok: true, who: who, done: done, n: done.length });
  } catch (err) {
    return jsonp_(e, { ok: false, error: String(err) });
  }
}

function doPost(e) {
  try {
    return jsonp_(e, writeRow_(rowFrom_(e)));
  } catch (err) {
    return jsonp_(e, { ok: false, error: String(err) });
  }
}

function testWrite() {
  bindSheet();
  writeRow_({
    who: "test",
    graph_id: 0,
    gitqa_id: "manual",
    nodes: "0-1-3",
    readable: "yes",
    ms: 1,
  });
}
