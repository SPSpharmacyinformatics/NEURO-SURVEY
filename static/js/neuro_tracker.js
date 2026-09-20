/* NeuroTracker — private, on-device daily check-in.
 *
 * Everything lives in localStorage under "neuro_tracker_v1". Nothing here is
 * ever sent to the server. See templates/tracker.html.
 */
window.NeuroTracker = (function () {
    "use strict";

    var KEY = "neuro_tracker_v1";
    var COLORS = ["#ff5da2", "#4ecdc4", "#a78bfa", "#ffd93d", "#f39c12",
                  "#2ecc71", "#2575fc", "#e74c3c", "#00b09b", "#795548"];
    var SCALE_FIELDS = [];
    var METRICS = [];
    var entries = [];
    var pendingScores = {};
    var touched = {};
    var chart = null;

    function pad(n) { return (n < 10 ? "0" : "") + n; }
    function today() {
        var d = new Date();
        return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
    }
    function $(id) { return document.getElementById(id); }
    function esc(s) {
        return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }
    function num(id, float) {
        var el = $(id);
        if (!el) return null;
        var v = el.value.trim();
        if (v === "") return null;
        var n = float ? parseFloat(v) : parseInt(v, 10);
        return isNaN(n) ? null : n;
    }

    /* ---------------- storage ---------------- */
    function read() {
        try {
            var raw = localStorage.getItem(KEY);
            var data = raw ? JSON.parse(raw) : [];
            return Array.isArray(data) ? data : [];
        } catch (e) { return []; }
    }
    function write(list) {
        try {
            localStorage.setItem(KEY, JSON.stringify(list));
            entries = list.slice();
            renderAll();
            return true;
        } catch (e) {
            setStatus("Couldn't save — browser storage may be full or blocked.");
            return false;
        }
    }
    function upsert(entry) {
        var list = read();
        var replaced = false;
        for (var i = 0; i < list.length; i++) {
            if (list[i].date === entry.date) { list[i] = entry; replaced = true; break; }
        }
        if (!replaced) list.push(entry);
        list.sort(function (a, b) { return a.date < b.date ? -1 : 1; });
        return write(list) ? (replaced ? "updated" : "saved") : null;
    }

    /* ---------------- form ---------------- */
    function buildForm() {
        var host = $("range-fields");
        if (!host) return;
        try { SCALE_FIELDS = JSON.parse(host.getAttribute("data-fields")); }
        catch (e) { SCALE_FIELDS = []; }
        var html = "";
        SCALE_FIELDS.forEach(function (f) {
            html += '<div class="q-item"><p>' + esc(f[1]) +
                    ' <span class="muted tiny">' + esc(f[2]) + "</span></p>" +
                    '<div style="display:flex;align-items:center;gap:12px">' +
                    '<input type="range" min="1" max="5" step="1" value="3" id="tr-' + f[0] +
                    '" class="tr-range" style="flex:1">' +
                    '<output id="out-' + f[0] + '" style="font-weight:800;width:1.5em">3</output>' +
                    "</div></div>";
        });
        host.innerHTML = html;
        SCALE_FIELDS.forEach(function (f) {
            var inp = $("tr-" + f[0]);
            inp.addEventListener("input", function () {
                $("out-" + f[0]).textContent = inp.value;
                touched[f[0]] = true;
            });
        });
        METRICS = SCALE_FIELDS.map(function (f) {
            return { key: f[0], label: f[1], max: 5 };
        }).concat([
            { key: "sleep_h", label: "Sleep hours", max: 12 },
            { key: "caffeine", label: "Caffeine", max: 10 }
        ]);

        var sel = $("score-select");
        var opts = "";
        (window.NEURO_LIB_METRICS || []).forEach(function (m) {
            opts += '<option value="' + esc(m.id) + '" data-max="' + m.max + '">' +
                    esc(m.label) + "</option>";
        });
        sel.innerHTML = opts || '<option value="">— none available —</option>';
        function syncPlaceholder() {
            var o = sel.options[sel.selectedIndex];
            $("score-val").placeholder = o && o.getAttribute("data-max")
                ? "0–" + o.getAttribute("data-max") : "score";
        }
        sel.addEventListener("change", syncPlaceholder);
        syncPlaceholder();
    }

    function addScore() {
        var sel = $("score-select");
        if (!sel || !sel.value) return;
        var o = sel.options[sel.selectedIndex];
        var max = parseInt(o.getAttribute("data-max"), 10) || 0;
        var v = num("score-val", false);
        if (v == null) { setStatus("Enter a score first."); return; }
        if (v < 0 || (max && v > max)) { setStatus("Score must be between 0 and " + max + "."); return; }
        pendingScores[sel.value] = { label: o.textContent, value: v, max: max };
        $("score-val").value = "";
        renderChips();
    }
    function renderChips() {
        var host = $("score-chips");
        var html = "";
        Object.keys(pendingScores).forEach(function (k) {
            var s = pendingScores[k];
            html += '<span class="badge info" style="margin:2px 4px 2px 0">' + esc(s.label) +
                    ": " + s.value + "/" + s.max +
                    ' <a href="#" data-remove="' + esc(k) + '" style="text-decoration:none">✕</a></span>';
        });
        host.innerHTML = html;
        host.querySelectorAll("[data-remove]").forEach(function (a) {
            a.addEventListener("click", function (e) {
                e.preventDefault();
                delete pendingScores[a.getAttribute("data-remove")];
                renderChips();
            });
        });
    }

    function loadIntoForm(e) {
        $("tr-date").value = e.date;
        touched = {};
        SCALE_FIELDS.forEach(function (f) {
            var inp = $("tr-" + f[0]);
            if (inp && e[f[0]] != null) {
                inp.value = e[f[0]];
                $("out-" + f[0]).textContent = e[f[0]];
                touched[f[0]] = true;
            }
        });
        ["sleep_h", "caffeine", "cycle"].forEach(function (k) {
            $("tr-" + k).value = e[k] == null ? "" : e[k];
        });
        $("tr-meds").checked = !!e.meds;
        $("tr-exercise").checked = !!e.exercise;
        $("tr-notes").value = e.notes || "";
        pendingScores = {};
        Object.keys(e.scores || {}).forEach(function (k) {
            pendingScores[k] = e.scores[k];
        });
        renderChips();
        $("form-heading").textContent = "Editing " + e.date;
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function saveForm() {
        var date = $("tr-date").value || today();
        var entry = { date: date, scores: {} };
        SCALE_FIELDS.forEach(function (f) {
            if (!touched[f[0]]) return;         /* untouched slider != "neutral 3" */
            var v = num("tr-" + f[0], false);
            if (v != null) entry[f[0]] = v;
        });
        ["sleep_h", "caffeine", "cycle"].forEach(function (k) {
            var v = num("tr-" + k, k === "sleep_h");
            if (v != null) entry[k] = v;
        });
        entry.meds = $("tr-meds").checked;
        entry.exercise = $("tr-exercise").checked;
        var notes = $("tr-notes").value.trim();
        if (notes) entry.notes = notes;
        Object.keys(pendingScores).forEach(function (k) { entry.scores[k] = pendingScores[k]; });

        var res = upsert(entry);
        if (res) {
            setStatus("Check-in " + res + " for " + date + " ✅");
            $("form-heading").textContent = "How was today?";
            $("tr-date").value = today();
            $("tr-notes").value = "";
            pendingScores = {};
            renderChips();
            touched = {};
            SCALE_FIELDS.forEach(function (f) {
                $("tr-" + f[0]).value = 3;
                $("out-" + f[0]).textContent = "3";
            });
        }
    }

    function setStatus(msg) {
        var el = $("tracker-status");
        if (el) el.textContent = msg;
    }

    /* ---------------- rendering ---------------- */
    function allMetrics() {
        var list = METRICS.slice();
        var seen = {};
        list.forEach(function (m) { seen[m.key] = true; });
        entries.forEach(function (e) {
            Object.keys(e.scores || {}).forEach(function (k) {
                if (!seen[k]) {
                    seen[k] = true;
                    list.push({ key: k, label: e.scores[k].label, max: e.scores[k].max || 0 });
                }
            });
        });
        return list;
    }

    function valueOf(e, key) {
        if (e.scores && e.scores[key]) return e.scores[key].value;
        return e[key] == null ? null : e[key];
    }

    function renderList() {
        var host = $("tracker-entries");
        $("tracker-count").textContent = entries.length;
        if (!entries.length) {
            host.innerHTML = '<p class="muted">No check-ins yet. Log today above 👆</p>';
            return;
        }
        var desc = entries.slice().reverse();
        var html = "";
        desc.forEach(function (e) {
            var bits = [];
            SCALE_FIELDS.forEach(function (f) {
                if (e[f[0]] != null) bits.push(esc(f[1]) + " " + e[f[0]] + "/5");
            });
            if (e.sleep_h != null) bits.push("sleep " + e.sleep_h + "h");
            if (e.caffeine != null) bits.push("caffeine " + e.caffeine);
            if (e.meds) bits.push("💊");
            if (e.exercise) bits.push("🏃");
            Object.keys(e.scores || {}).forEach(function (k) {
                var s = e.scores[k];
                bits.push(esc(s.label) + " " + s.value + (s.max ? "/" + s.max : ""));
            });
            html += '<div class="q-item"><div style="display:flex;justify-content:space-between;' +
                    'gap:8px;flex-wrap:wrap;align-items:center"><b>' + esc(e.date) + "</b>" +
                    '<span><button class="btn secondary small" data-edit="' + esc(e.date) +
                    '">edit</button> <button class="btn secondary small" data-del="' + esc(e.date) +
                    '">✕</button></span></div>' +
                    '<p class="muted tiny" style="margin:6px 0 0">' + bits.join(" · ") + "</p>" +
                    (e.notes ? '<p style="margin:6px 0 0">' + esc(e.notes) + "</p>" : "") +
                    "</div>";
        });
        host.innerHTML = html;
        host.querySelectorAll("[data-edit]").forEach(function (b) {
            b.addEventListener("click", function () {
                var d = b.getAttribute("data-edit");
                for (var i = 0; i < entries.length; i++) {
                    if (entries[i].date === d) { loadIntoForm(entries[i]); break; }
                }
            });
        });
        host.querySelectorAll("[data-del]").forEach(function (b) {
            b.addEventListener("click", function () {
                var d = b.getAttribute("data-del");
                if (!confirm("Delete the check-in for " + d + "?")) return;
                write(entries.filter(function (e) { return e.date !== d; }));
            });
        });
    }

    function renderChart() {
        var cv = $("tracker-chart");
        if (!cv || !window.Chart) return;
        var sorted = entries.slice().sort(function (a, b) { return a.date < b.date ? -1 : 1; });
        var metrics = allMetrics();
        var datasets = [];
        var i = 0;
        metrics.forEach(function (m) {
            if (!m.max) return;
            var pts = sorted.map(function (e) {
                var v = valueOf(e, m.key);
                return v == null ? null : Math.round(v / m.max * 1000) / 10;
            });
            if (pts.every(function (p) { return p == null; })) return;
            var color = COLORS[i % COLORS.length];
            datasets.push({
                label: m.label, data: pts, borderColor: color,
                backgroundColor: color, tension: 0.3, spanGaps: true,
                pointRadius: 3, borderWidth: 3, _metric: m
            });
            i++;
        });
        var calm = window.NeuroCalm && NeuroCalm.isOn();
        if (chart) chart.destroy();
        chart = new Chart(cv, {
            type: "line",
            data: { labels: sorted.map(function (e) { return e.date; }), datasets: datasets },
            options: {
                responsive: true, maintainAspectRatio: false,
                animation: calm ? false : undefined,
                interaction: { mode: "index", intersect: false },
                scales: {
                    y: { min: 0, max: 100, ticks: { color: "#1a1a2e", callback: function (v) { return v + "%"; } } },
                    x: { ticks: { color: "#1a1a2e", maxRotation: 60, minRotation: 0 } }
                },
                plugins: {
                    legend: { labels: { color: "#1a1a2e", boxWidth: 12 } },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                var m = ctx.dataset._metric;
                                var raw = sorted[ctx.dataIndex] ? valueOf(sorted[ctx.dataIndex], m.key) : null;
                                return m.label + ": " + (raw == null ? "—" : raw + " / " + m.max) +
                                       " (" + ctx.parsed.y + "%)";
                            }
                        }
                    }
                }
            }
        });
    }

    function pearson(pairs) {
        var n = pairs.length;
        if (n < 2) return null;
        var sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0;
        for (var i = 0; i < n; i++) {
            var x = pairs[i][0], y = pairs[i][1];
            sx += x; sy += y; sxx += x * x; syy += y * y; sxy += x * y;
        }
        var vx = sxx - sx * sx / n, vy = syy - sy * sy / n;
        var cov = sxy - sx * sy / n;
        if (vx <= 0 || vy <= 0) return null;
        return cov / Math.sqrt(vx * vy);
    }
    function strength(r) {
        var a = Math.abs(r);
        if (a >= 0.7) return "strong";
        if (a >= 0.4) return "moderate";
        if (a >= 0.2) return "weak";
        return "negligible";
    }
    function mean(arr) {
        if (!arr.length) return null;
        return arr.reduce(function (a, b) { return a + b; }, 0) / arr.length;
    }

    function buildTargetSelect() {
        var sel = $("corr-target");
        var prev = sel.value;
        var html = "";
        allMetrics().forEach(function (m) {
            html += '<option value="' + esc(m.key) + '">' + esc(m.label) + "</option>";
        });
        sel.innerHTML = html;
        if (prev) { sel.value = prev; }
        if (!sel.value && sel.options.length) sel.selectedIndex = 0;
    }

    function renderStats() {
        var sel = $("corr-target");
        var host = $("corr-results");
        var ghost = $("group-results");
        if (!sel || !entries.length) {
            host.innerHTML = '<p class="muted">Log a few check-ins to see patterns.</p>';
            ghost.innerHTML = "";
            return;
        }
        var target = sel.value;
        var metrics = allMetrics();
        var tmetric = null;
        metrics.forEach(function (m) { if (m.key === target) tmetric = m; });

        var rows = [];
        metrics.forEach(function (m) {
            if (m.key === target) return;
            var pairs = [];
            entries.forEach(function (e) {
                var x = valueOf(e, m.key), y = valueOf(e, target);
                if (x != null && y != null) pairs.push([x, y]);
            });
            if (pairs.length < 5) return;
            var r = pearson(pairs);
            if (r == null) return;
            rows.push({ metric: m, r: r, n: pairs.length });
        });
        rows.sort(function (a, b) { return Math.abs(b.r) - Math.abs(a.r); });

        if (!rows.length) {
            host.innerHTML = '<p class="muted">Not enough overlapping days yet — ' +
                "at least 5 shared check-ins are needed.</p>";
        } else {
            var html = '<p class="muted tiny">Against <b>' + esc(tmetric ? tmetric.label : target) +
                       '</b> (top ' + Math.min(rows.length, 8) + "):</p>";
            rows.slice(0, 8).forEach(function (row) {
                var verb = row.r >= 0 ? "rises with" : "moves opposite to";
                html += '<div class="card" style="margin:8px 0;padding:10px 14px"><b>' +
                        esc(row.metric.label) + '</b> ' + verb + " " +
                        esc(tmetric ? tmetric.label : target) + ". " +
                        '<span class="badge ' + (Math.abs(row.r) >= 0.7 ? "flag" : "info") + '">' +
                        strength(row.r) + " r=" + row.r.toFixed(2) + "</span>" +
                        '<span class="muted tiny"> · ' + row.n + " shared days</span></div>";
            });
        }

        /* group comparisons for meds / exercise */
        var ghtml = "";
        [["meds", "💊 Meds", "no meds"],
         ["exercise", "🏃 Moved", "no move"]].forEach(function (pair) {
            var yes = [], no = [];
            entries.forEach(function (e) {
                var y = valueOf(e, target);
                if (y == null) return;
                (e[pair[0]] ? yes : no).push(y);
            });
            if (yes.length >= 3 && no.length >= 3) {
                var my = mean(yes), mn = mean(no);
                var diff = my - mn;
                ghtml += '<p style="margin:8px 0"><b>' + pair[1] + ":</b> mean " +
                         (tmetric ? tmetric.label : target) + " <b>" + my.toFixed(2) + "</b> vs " +
                         pair[2] + " <b>" + mn.toFixed(2) + "</b> — " +
                         (diff >= 0 ? "+" : "") + diff.toFixed(2) +
                         ' <span class="muted tiny">(' + yes.length + " vs " + no.length + " days)</span></p>";
            }
        });
        ghost.innerHTML = ghtml || "";
    }

    function renderAll() {
        renderList();
        renderChart();
        buildTargetSelect();
        renderStats();
    }

    function exportJson() {
        var blob = new Blob([JSON.stringify(entries, null, 2)],
                            { type: "application/json" });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "neuro-checkins-" + today() + ".json";
        a.click();
        URL.revokeObjectURL(a.href);
    }
    function importJson(file) {
        var reader = new FileReader();
        reader.onload = function () {
            try {
                var incoming = JSON.parse(reader.result);
                if (!Array.isArray(incoming)) throw new Error("not a list");
                var list = read();
                incoming.forEach(function (e) {
                    if (!e || !e.date) return;
                    var found = false;
                    for (var i = 0; i < list.length; i++) {
                        if (list[i].date === e.date) { list[i] = e; found = true; break; }
                    }
                    if (!found) list.push(e);
                });
                list.sort(function (a, b) { return a.date < b.date ? -1 : 1; });
                write(list);
                setStatus("Imported " + incoming.length + " check-in(s).");
            } catch (err) {
                setStatus("That file didn't look like a NeuroTracker backup.");
            }
        };
        reader.readAsText(file);
    }

    function init() {
        if (!$("tracker-form")) return;
        SCALE_FIELDS = [];
        buildForm();
        entries = read();
        $("tr-date").value = today();
        $("tracker-save").addEventListener("click", saveForm);
        $("score-add").addEventListener("click", addScore);
        $("tr-export").addEventListener("click", exportJson);
        $("tr-import").addEventListener("change", function (e) {
            if (e.target.files && e.target.files[0]) importJson(e.target.files[0]);
            e.target.value = "";
        });
        $("tr-clear").addEventListener("click", function () {
            if (confirm("Erase ALL check-ins on this device? This cannot be undone.")) {
                write([]);
                setStatus("All check-ins erased.");
            }
        });
        $("corr-target").addEventListener("change", renderStats);
        buildTargetSelect();
        renderAll();
    }

    return { init: init, read: read };
})();
