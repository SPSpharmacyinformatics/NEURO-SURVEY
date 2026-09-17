/* The Brain Circus — client-side UX helpers.
   Nothing here sends data anywhere: drafts and preferences live only in
   this browser's localStorage. */
(function () {
    "use strict";

    /* ---------------- low-sensory ("calm") mode ---------------- */
    var CALM_KEY = "neuro_calm";

    function calmWanted() {
        try {
            var stored = localStorage.getItem(CALM_KEY);
            if (stored === "1") return true;
            if (stored === "0") return false;
        } catch (e) { /* private mode / storage blocked */ }
        return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    }

    function calmApply(on) {
        document.documentElement.classList.toggle("calm", !!on);
        var b = document.getElementById("calm-toggle");
        if (b) {
            b.textContent = on ? "🔇 calm mode: on" : "🎈 calm mode: off";
            b.setAttribute("aria-pressed", on ? "true" : "false");
        }
    }

    window.NeuroCalm = {
        isOn: function () { return document.documentElement.classList.contains("calm"); },
        set: function (on) {
            try { localStorage.setItem(CALM_KEY, on ? "1" : "0"); } catch (e) {}
            calmApply(on);
        },
        toggle: function () { this.set(!this.isOn()); },
        init: function () { calmApply(calmWanted()); }
    };
    window.NeuroCalm.init();
    window.addEventListener("DOMContentLoaded", function () { calmApply(NeuroCalm.isOn()); });

    /* ---------------- screen draft (localStorage only) ---------------- */
    var KEY = "neuro_screen_draft_v1";

    function read() {
        try { return JSON.parse(localStorage.getItem(KEY)) || null; } catch (e) { return null; }
    }
    function write(d) {
        try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {}
    }
    function clear() {
        try { localStorage.removeItem(KEY); } catch (e) {}
    }
    function capture(form) {
        var out = {}, i, el;
        for (i = 0; i < form.elements.length; i++) {
            el = form.elements[i];
            if (!el.name || el.disabled) continue;
            if (el.type === "radio") { if (el.checked) out[el.name] = el.value; }
            else if (el.type === "checkbox") { if (el.checked) (out[el.name] = out[el.name] || []).push(el.value); }
            else out[el.name] = el.value;
        }
        return out;
    }
    function apply(form, data) {
        if (!data) return;
        var i, el;
        for (i = 0; i < form.elements.length; i++) {
            el = form.elements[i];
            if (!el.name || !(el.name in data)) continue;
            if (el.type === "radio") el.checked = String(data[el.name]) === String(el.value);
            else if (el.type === "checkbox") el.checked = (data[el.name] || []).indexOf(el.value) >= 0;
            else el.value = data[el.name];
        }
    }
    function blank() { var d = read() || {}; d.sections = d.sections || {}; return d; }

    window.NeuroDraft = {
        read: read, write: write, clear: clear, capture: capture, apply: apply,
        saveSection: function (idx, form) {
            var d = blank(); d.sections[idx] = capture(form); d.idx = idx; d.ts = Date.now(); write(d);
        },
        saveIdentity: function (form) {
            var d = blank(); d.identity = capture(form); d.ts = Date.now(); write(d);
        },
        savedCount: function () {
            var d = read(); return d && d.sections ? Object.keys(d.sections).length : 0;
        },
        firstMissing: function (total) {
            var d = read();
            if (!d || !d.sections) return 0;
            for (var i = 0; i < total; i++) { if (!d.sections[i]) return i; }
            return total;
        }
    };
})();
