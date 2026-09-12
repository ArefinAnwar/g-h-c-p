(function () {
  const SCRIPT = (window.HUMAN_EVAL && window.HUMAN_EVAL.scriptUrl) || "";

  const $ = (id) => document.getElementById(id);
  const gate = $("gate");
  const howto = $("howto");
  const task = $("task");
  const done = $("done");

  let itemsById = {};
  let assign = {};
  let queue = [];
  let ix = 0;
  let who = "";
  let pick = null;
  let readable = "";
  let t0 = 0;

  function jsonp(url) {
    return new Promise((resolve, reject) => {
      const cb = "he_" + Date.now();
      const t = setTimeout(() => {
        cleanup();
        reject(new Error("timeout"));
      }, 8000);
      function cleanup() {
        clearTimeout(t);
        delete window[cb];
        if (s.parentNode) s.parentNode.removeChild(s);
      }
      window[cb] = (data) => {
        cleanup();
        resolve(data);
      };
      const s = document.createElement("script");
      s.src = url + (url.indexOf("?") >= 0 ? "&" : "?") + "callback=" + cb;
      s.onerror = () => {
        cleanup();
        reject(new Error("script"));
      };
      document.body.appendChild(s);
    });
  }

  async function remoteDone(w) {
    if (!SCRIPT) return [];
    try {
      const data = await jsonp(SCRIPT + "?who=" + encodeURIComponent(w));
      return (data && data.done) || [];
    } catch (e) {
      return [];
    }
  }

  function saveRow(rec) {
    if (!SCRIPT) return;
    const q = new URLSearchParams({
      write: "1",
      who: rec.who,
      graph_id: String(rec.graph_id),
      gitqa_id: rec.gitqa_id || "",
      nodes: (rec.nodes || []).join("-"),
      readable: rec.readable || "",
      ms: String(rec.ms || ""),
    });
    jsonp(SCRIPT + "?" + q.toString()).catch(() => {
      $("save-msg").textContent = "Saved on this device (sheet unreachable).";
    });
  }

  function hashWho(w) {
    let h = 70;
    for (let i = 0; i < w.length; i++) h = (h * 31 + w.charCodeAt(i)) >>> 0;
    return h || 1;
  }

  function queueFor(w) {
    const a = assign[w];
    if (!a) return [];
    const ids = a.shared.concat(a.own);
    const rng = function (seed) {
      let s = seed;
      return function () {
        s = (s * 1664525 + 1013904223) % 4294967296;
        return s / 4294967296;
      };
    };
    const r = rng(hashWho(w));
    const shuf = ids.slice();
    for (let i = shuf.length - 1; i > 0; i--) {
      const j = Math.floor(r() * (i + 1));
      const tmp = shuf[i];
      shuf[i] = shuf[j];
      shuf[j] = tmp;
    }
    return shuf;
  }

  function showTask() {
    const gid = queue[ix];
    const it = itemsById[gid];
    pick = null;
    readable = "";
    t0 = Date.now();
    $("prog-label").textContent = ix + 1 + " / " + queue.length;
    $("bar").style.width = (100 * ix) / queue.length + "%";
    $("img").src = it.image;
    $("img").alt = "graph " + it.gitqa_id;
    $("opts").innerHTML = "";
    it.options.forEach((o) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = String.fromCharCode(65 + o.id) + ".  " + o.label;
      b.onclick = () => {
        pick = o;
        [...$("opts").children].forEach((x) => x.classList.remove("on"));
        b.classList.add("on");
        maybeEnable();
      };
      $("opts").appendChild(b);
    });
    [...$("read").querySelectorAll("button")].forEach((b) => {
      b.classList.remove("on");
    });
    $("next").disabled = true;
    $("save-msg").textContent = "";
  }

  function maybeEnable() {
    $("next").disabled = !(pick && readable);
  }

  $("read").onclick = (ev) => {
    const b = ev.target.closest("button");
    if (!b) return;
    readable = b.getAttribute("data-v");
    [...$("read").querySelectorAll("button")].forEach((x) => x.classList.remove("on"));
    b.classList.add("on");
    maybeEnable();
  };

  $("next").onclick = () => {
    if (!pick || !readable) return;
    $("next").disabled = true;
    const it = itemsById[queue[ix]];
    saveRow({
      who: who,
      graph_id: it.graph_id,
      gitqa_id: it.gitqa_id,
      nodes: pick.nodes,
      readable: readable,
      ms: Date.now() - t0,
    });
    ix += 1;
    if (ix >= queue.length) {
      $("bar").style.width = "100%";
      task.classList.add("hidden");
      done.classList.remove("hidden");
      $("done-msg").textContent =
        "Thanks. You finished " + queue.length + " graphs as " + who + ".";
      return;
    }
    showTask();
  };

  $("start").onclick = async () => {
    who = $("who").value.trim().toLowerCase();
    $("gate-err").classList.add("hidden");
    const [itemPack, asg] = await Promise.all([
      fetch("items.json").then((r) => r.json()),
      fetch("assignments.json").then((r) => r.json()),
    ]);
    assign = asg;
    if (!assign[who]) {
      $("gate-err").textContent = "Unknown code — use the private code from your email.";
      $("gate-err").classList.remove("hidden");
      return;
    }
    itemPack.items.forEach((it) => {
      itemsById[it.graph_id] = it;
    });
    const all = queueFor(who);
    // Progress lives on the server only: re-read it on every visit.
    const doneIds = new Set(await remoteDone(who));
    queue = all.filter((id) => !doneIds.has(id));
    gate.classList.add("hidden");
    if (!queue.length) {
      done.classList.remove("hidden");
      $("done-msg").textContent = "Nothing left on this code. Thanks.";
      return;
    }
    $("resume-msg").textContent =
      doneIds.size > 0
        ? "Welcome back — " + doneIds.size + " of " + all.length + " done, " + queue.length + " to go."
        : "You have " + all.length + " drawings to rate.";
    howto.classList.remove("hidden");
  };

  $("begin").onclick = () => {
    howto.classList.add("hidden");
    task.classList.remove("hidden");
    showTask();
  };

  $("rehow").onclick = () => {
    task.classList.add("hidden");
    howto.classList.remove("hidden");
  };

  const q = new URLSearchParams(location.search).get("who");
  if (q) $("who").value = q.replace(/^\//, "");
})();
