/* The Brain Circus — on-device journey (trends), intervention log and the
   shareable side-by-side comparison. Everything is computed in this browser;
   the only thing that ever leaves is the code the user chooses to show. */
(function () {
    "use strict";

    var METRICS = window.NEURO_METRICS || [];
    var HKEY = "neuro_history_v1";
    var LKEY = "neuro_log_v1";
    var COLORS = ["#ff5da2", "#4ecdc4", "#a78bfa", "#f39c12", "#2ecc71", "#e74c3c",
                  "#3498db", "#e67e22", "#1abc9c", "#9b59b6"];

    function readJSON(k, def) {
        try { var v = JSON.parse(localStorage.getItem(k)); return v == null ? def : v; }
        catch (e) { return def; }
    }
    function writeJSON(k, v) {
        try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {}
    }
    function b64url(bytes) {
        var s = "";
        for (var i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
        return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    }
    function unb64url(str) {
        str = str.replace(/-/g, "+").replace(/_/g, "/");
        while (str.length % 4) str += "=";
        var raw = atob(str), out = [];
        for (var i = 0; i < raw.length; i++) out.push(raw.charCodeAt(i));
        return out;
    }
    function pct(v, max) { return Math.max(0, Math.min(100, Math.round((v || 0) / max * 100))); }

    function encode(vals) {
        return "n1" + b64url(METRICS.map(function (m) { return pct(vals[m.key], m.max); }));
    }
    function decode(code) {
        if (!code || code.slice(0, 2) !== "n1") return null;
        var bytes;
        try { bytes = unb64url(code.slice(2)); } catch (e) { return null; }
        if (bytes.length !== METRICS.length) return null;
        var out = {};
        METRICS.forEach(function (m, i) { out[m.key] = Math.round(bytes[i] * m.max / 100); });
        return out;
    }
    function compareUrl(code) {
        return location.origin + "/compare?a=" + encodeURIComponent(code);
    }

    /* ---------------- intervention log ---------------- */
    function interventions() { return readJSON(LKEY, []); }
    function addIntervention(text) {
        var list = interventions();
        list.push({ ts: Date.now(), text: String(text || "").trim() });
        writeJSON(LKEY, list);
        return list;
    }
    function renderInterventions(host) {
        if (!host) return;
        var list = interventions();
        if (!list.length) { host.innerHTML = "<p class='muted tiny'>No notes yet. Log things like starting a medication, a sleep change, or therapy starting/stopping — then watch whether your lines move.</p>"; return; }
        host.innerHTML = "<ul class='quest-list'>" + list.map(function (it) {
            return "<li><span class='mono tiny'>" + new Date(it.ts).toLocaleDateString() + "</span> " +
                   esc(it.text) + "</li>";
        }).join("") + "</ul>";
    }
    function esc(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }

    /* ---------------- trend chart ---------------- */
    function clinicalMetrics() {
        return METRICS.filter(function (m) { return m.group === "Clinical"; });
    }
    function renderChart(canvas, hist) {
        if (!canvas || typeof Chart === "undefined" || hist.length < 2) return;
        var ms = clinicalMetrics();
        var labels = hist.map(function (h) { return new Date(h.ts).toLocaleDateString(); });
        var ivs = interventions();
        var plugin = {
            id: "neuroInterventions",
            afterDraw: function (chart) {
                if (!ivs.length) return;
                var x = chart.scales.x, area = chart.chartArea, ctx = chart.ctx;
                ctx.save();
                ivs.forEach(function (it) {
                    var idx = 0, best = Infinity;
                    hist.forEach(function (h, i) {
                        var dd = Math.abs(h.ts - it.ts);
                        if (dd < best) { best = dd; idx = i; }
                    });
                    if (best > 1000 * 60 * 60 * 24 * 45) return;
                    var px = x.getPixelForValue(idx);
                    ctx.beginPath();
                    ctx.setLineDash([4, 4]);
                    ctx.strokeStyle = "#8a93a5";
                    ctx.moveTo(px, area.top);
                    ctx.lineTo(px, area.bottom);
                    ctx.stroke();
                });
                ctx.restore();
            }
        };
        new Chart(canvas, {
            type: "line",
            data: {
                labels: labels,
                datasets: ms.map(function (m, i) {
                    return {
                        label: m.label,
                        data: hist.map(function (h) { return pct(h.v[m.key], m.max); }),
                        borderColor: COLORS[i % COLORS.length],
                        backgroundColor: COLORS[i % COLORS.length],
                        tension: 0.25, spanGaps: true
                    };
                })
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100, title: { display: true, text: "% of scale" } }
                },
                plugins: { legend: { position: "bottom" } }
            },
            plugins: [plugin]
        });
    }

    /* ---------------- results page ---------------- */
    window.NeuroJourney = {
        encode: encode, decode: decode, compareUrl: compareUrl,
        initResults: function () {
            var snap = window.NEURO_SNAPSHOT;
            if (!snap) return;
            var hist = readJSON(HKEY, []);
            var sig = JSON.stringify(snap);
            var last = hist[hist.length - 1];
            if (last && last.sig === sig && Date.now() - last.ts < 120000) {
                last.ts = Date.now();
            } else {
                hist.push({ ts: Date.now(), v: snap, sig: sig });
            }
            if (hist.length > 200) hist = hist.slice(-200);
            writeJSON(HKEY, hist);

            var countEl = document.getElementById("journey-count");
            if (countEl) countEl.textContent = hist.length;

            renderChart(document.getElementById("journey-chart"), hist);
            renderInterventions(document.getElementById("journey-log"));

            var logForm = document.getElementById("journey-log-form");
            if (logForm) logForm.addEventListener("submit", function (e) {
                e.preventDefault();
                var inp = document.getElementById("journey-log-input");
                if (inp && inp.value.trim()) { addIntervention(inp.value); inp.value = ""; renderInterventions(document.getElementById("journey-log")); }
            });

            var clearBtn = document.getElementById("journey-clear");
            if (clearBtn) clearBtn.addEventListener("click", function () {
                if (!confirm("Erase your locally stored check-in history and notes on this device?")) return;
                try { localStorage.removeItem(HKEY); localStorage.removeItem(LKEY); } catch (e) {}
                location.reload();
            });

            var code = encode(snap);
            var codeInput = document.getElementById("journey-code");
            if (codeInput) codeInput.value = code;
            var qrHost = document.getElementById("journey-qr");
            if (qrHost && typeof qrcode !== "undefined") {
                try {
                    var q = qrcode(0, "M");
                    q.addData(compareUrl(code));
                    q.make();
                    qrHost.innerHTML = q.createSvgTag({ cellSize: 4, margin: 2 });
                } catch (e) { qrHost.textContent = "(QR unavailable — use the code)"; }
            }
            var copyBtn = document.getElementById("journey-copy");
            if (copyBtn) copyBtn.addEventListener("click", function () {
                var c = compareUrl(code);
                if (navigator.clipboard) navigator.clipboard.writeText(c);
                copyBtn.textContent = "copied ✓";
            });
        },

        /* ---------------- compare page ---------------- */
        initCompare: function () {
            var aEl = document.getElementById("cmp-a");
            var bEl = document.getElementById("cmp-b");
            var out = document.getElementById("cmp-out");
            var params = new URLSearchParams(location.search);
            if (params.get("a") && aEl) aEl.value = params.get("a");
            if (params.get("b") && bEl) bEl.value = params.get("b");

            function normCode(s) {
                s = (s || "").trim();
                var m = s.match(/[?&]a=([^&]+)/);
                if (m) s = decodeURIComponent(m[1]);
                return s;
            }
            function draw() {
                var a = decode(normCode(aEl && aEl.value));
                var b = decode(normCode(bEl && bEl.value));
                if (!a) { out.innerHTML = "<p class='muted'>Paste the first code (or scan their QR) to begin.</p>"; return; }
                var rows = METRICS.map(function (m) {
                    var pa = pct(a[m.key], m.max);
                    var pb = b ? pct(b[m.key], m.max) : null;
                    var barB = pb == null ? "" :
                        "<div class='cmp-bar'><div style='width:" + pb + "%; background:" + "#4ecdc4" + "'></div></div><span class='tiny mono'>" + pb + "%</span>";
                    return "<tr><th>" + esc(m.label) + "<div class='tiny muted'>" + esc(m.group) + "</div></th>" +
                        "<td><div class='cmp-bar'><div style='width:" + pa + "%; background:" + "#ff5da2" + "'></div></div><span class='tiny mono'>" + pa + "%</span></td>" +
                        "<td>" + barB + "</td></tr>";
                }).join("");
                out.innerHTML =
                    "<table class='cmp-table'><thead><tr><th>Measure</th><th>Person A</th><th>Person B</th></tr></thead><tbody>" +
                    rows + "</tbody></table>" +
                    (b ? "" : "<p class='muted tiny'>Add the second person's code to see them side by side.</p>") +
                    "<p class='muted tiny'>These are self-reported scale percentages, not a diagnosis or a compatibility score. Differences are conversation starters, not verdicts.</p>";
            }
            if (aEl) aEl.addEventListener("input", draw);
            if (bEl) bEl.addEventListener("input", draw);
            draw();
        }
    };
})();
