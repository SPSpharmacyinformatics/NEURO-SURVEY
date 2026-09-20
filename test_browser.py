#!/usr/bin/env python3
"""Browser-level usability tests: emulates a real person on the live site.

Uses Playwright + headless Chromium. Every interaction a human would perform —
clicking radios, typing usernames, watching the digit span, hunting symbols —
is performed for real against https://neuro.sps.dpdns.org.

Run: python3 test_browser.py
"""
import random
import re
import sys
import time

from playwright.sync_api import sync_playwright, expect

BASE = "https://neuro.sps.dpdns.org"
USER = f"human_{int(time.time()) % 1000000}"
ART = "/home/sabarinath/projects/NEURO-SURVEY/test-artifacts"
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{detail}]" if detail and not cond else ""))


def human_pause(a=150, b=450):
    time.sleep(random.uniform(a, b) / 1000)


def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                                  locale="en-US")
        page = ctx.new_page()
        page.set_default_timeout(15000)

        # ---------- 0. landing ----------
        page.goto(BASE)
        expect(page.locator("h1")).to_contain_text("Brain Circus")
        check("landing page renders", True)
        page.screenshot(path=f"{ART}/01_landing.png")

        # ---------- 1. registration ----------
        page.get_by_role("link", name=re.compile("log in|nft name", re.I)).first.click()
        page.fill("input[name='username']", USER)
        human_pause()
        page.get_by_role("button", name=re.compile("Mint my nft name|That's me")).click()
        expect(page.locator(".topbar")).to_contain_text("shelf")
        check("registration + topbar shows nft name shelf", True)
        page.screenshot(path=f"{ART}/02_registered.png")

        # ---------- 2. clinical screen, full human walk ----------
        page.get_by_role("link", name=re.compile("Buckle up|Grand Tour", re.I)).first.click()
        expect(page.locator("h1")).to_contain_text("Grand Tour")
        page.fill("input[name='age']", "27")
        page.select_option("select[name='gender']", "Female")
        page.get_by_role("button", name=re.compile("All aboard")).click()

        # AuDHD persona via REAL clicks
        def click_radio(name, value):
            page.check(f"input[name='{name}'][value='{value}']")
            human_pause()

        for i, v in enumerate([2, 2, 2, 2, 2, 2, 2, 0, 0]):      # PHQ-9 moderate
            click_radio(f"phq9_{i}", v)
        page.get_by_role("button", name=re.compile("Next stop")).click()
        for i, v in enumerate([2, 2, 2, 2, 1, 2, 1]):            # GAD-7 moderate
            click_radio(f"gad7_{i}", v)
        page.get_by_role("button", name=re.compile("Next stop")).click()
        for i, v in enumerate([4, 4, 4, 4, 3, 3]):               # ASRS positive
            click_radio(f"asrs_{i}", v)
        page.get_by_role("button", name=re.compile("Next stop")).click()
        aq_vals = ["0", "0", "3", "0", "0", "3", "0", "3", "0", "0"]  # AQ-10 positive
        for i, v in enumerate(aq_vals):
            click_radio(f"aq10_{i}", v)
        page.get_by_role("button", name=re.compile("Next stop")).click()
        for i in range(13):
            click_radio(f"mdq_{i}", "No")
        page.get_by_role("button", name=re.compile("Next stop")).click()
        for i in range(5):
            click_radio(f"pcptsd5_{i}", "No")
        page.get_by_role("button", name=re.compile("Next stop")).click()
        for i in range(50):
            click_radio(f"big5_{i}", "1" if i < 10 else "2")
        page.get_by_role("button", name=re.compile("Next stop")).click()
        for i in range(25):
            click_radio(f"pid5_{i}", "1")
        page.get_by_role("button", name=re.compile("Open my results")).click()

        expect(page.locator("h1")).to_contain_text("Treasure Map")
        body = page.content()
        check("screen: AuDHD flags visible",
              "Attention &amp; Hyperactivity" in body and "Autism Spectrum" in body)
        check("screen: masking-to-mood flag fires",
              "Mood &amp; Depression" in body)  # PHQ-9=14 intentionally crosses 10
        page.screenshot(path=f"{ART}/03_screen_results.png", full_page=True)

        # ---------- 3. IQ test, fully interactive ----------
        page.goto(f"{BASE}/iq")
        page.get_by_role("link", name=re.compile("Enter the arena")).click()
        expect(page.locator("#stage .opt").first).to_be_visible(timeout=10000)
        check("iq: first question visible", True)

        # answer static items: pick the correct option (data-ok) like a sharp test-taker
        for q in range(16):
            page.wait_for_selector("#stage .opt", timeout=10000)
            opts = page.locator("#stage .opt")
            human_pause(200, 600)
            correct_clicked = False
            for j in range(opts.count()):
                if opts.nth(j).get_attribute("data-ok") == "true":
                    opts.nth(j).click()
                    correct_clicked = True
                    break
            if not correct_clicked:
                opts.first.click()
        check("iq: 16 static items answered", q == 15)

        # digit span: watch the box, type what we saw
        digits_seen = ""
        deadline = time.time() + 20
        while time.time() < deadline:
            if page.locator("#dans").count() > 0:
                break
            txt = page.locator("#dbox").text_content() or ""
            if txt.strip().isdigit():
                digits_seen += txt.strip()
            time.sleep(0.2)
        page.fill("#dans", digits_seen)
        page.click("#dok")
        check("iq: digit span round 1 typed", len(digits_seen) >= 3, digits_seen)

        # fail fast through remaining stages (2 mistakes end the game)
        for _ in range(2):
            try:
                page.wait_for_selector("#dans", timeout=15000)
                page.fill("#dans", "999")
                page.click("#dok")
            except Exception:
                break
            if page.locator("#stimer").count() > 0:
                break

        # symbol safari: click every triangle that appears
        try:
            page.wait_for_selector("#stimer", timeout=10000)
            deadline = time.time() + 70
            while time.time() < deadline and page.locator("#stimer").count() > 0:
                for tri in page.locator("#sfield span", has_text="▲").all():
                    try:
                        tri.click(timeout=300)
                    except Exception:
                        pass  # glyph despawned mid-click; grab the next one
                time.sleep(0.1)
            found = re.search(r"found:\s*(\d+)", page.content())
            check("iq: symbol safari played", found and int(found.group(1)) > 5,
                  found.group(1) if found else "0")
        except Exception as e:
            check("iq: symbol safari played", False, str(e)[:80])

        # results form
        page.wait_for_selector("#done:not(.hidden)", timeout=15000)
        page.fill("#done input[name='age']", "27")
        page.screenshot(path=f"{ART}/04_iq_done.png")
        page.get_by_role("button", name=re.compile("Compute My Score")).click()
        expect(page.locator("h1")).to_contain_text(re.compile(r"\d"))
        iq_score = page.locator("h1").first.text_content()
        check("iq: score page reached", iq_score.strip().isdigit(), iq_score)
        page.screenshot(path=f"{ART}/05_iq_result.png")

        # ---------- 4. EQ test ----------
        page.goto(f"{BASE}/eq")
        page.get_by_role("link", name=re.compile("Start detecting")).click()
        for i in range(40):
            page.check(f"input[name='eq_{i}'][value='{random.choice([1, 2, 3])}']")
        page.get_by_role("button", name=re.compile("Reveal my empathy")).click()
        expect(page.locator("h1")).to_contain_text(re.compile(r"\d+ / \d+"))
        check("eq: result reached", True)
        page.screenshot(path=f"{ART}/06_eq_result.png")

        # ---------- 5. quick map with real slider nudging ----------
        page.goto(f"{BASE}/quick-map")
        page.fill("input[name='name']", USER)
        page.fill("input[name='age']", "27")
        page.select_option("select[name='gender']", "Female")
        page.check("input[name='consent']")
        page.get_by_role("button", name=re.compile("rabbit hole")).click()
        sliders = page.locator("input[type='range']")
        n = sliders.count()
        for i in range(n):
            sl = sliders.nth(i)
            sl.click()
            target = random.choice([1, 2, 3, 5, 6, 7])
            cur = int(sl.input_value())
            for _ in range(abs(target - cur)):
                sl.press("ArrowRight" if target > cur else "ArrowLeft")
                time.sleep(0.03)
        page.get_by_role("button", name=re.compile("Reveal my wiggles")).click()
        expect(page.locator(".result-title")).to_be_visible()
        check("quick map: radar result reached", True)
        page.screenshot(path=f"{ART}/07_quickmap_result.png", full_page=True)

        # ---------- 6. dashboard aggregates everything ----------
        page.goto(f"{BASE}/dashboard")
        expect(page.locator("h1").first).to_contain_text(USER)
        body = page.content()
        check("dash: IQ section", "IQ" in body)
        check("dash: EQ section", "EQ" in body)
        check("dash: clinical screen section", "Clinical Screen" in body)
        check("dash: quick map radar", "mapRadar" in body)
        check("dash: insights fired", page.locator(".sticker").count() >= 1)
        page.screenshot(path=f"{ART}/08_dashboard.png", full_page=True)

        # ---------- 7. persistence across logout/login ----------
        page.get_by_role("link", name=re.compile("log out")).click()
        page.wait_for_url(f"{BASE}/")
        page.goto(f"{BASE}/dashboard", wait_until="domcontentloaded")
        check("logout gates dashboard", "/login" in page.url)
        page.fill("input[name='username']", USER)
        page.get_by_role("button", name=re.compile("That's me")).click()
        page.goto(f"{BASE}/dashboard")
        expect(page.locator("h1").first).to_contain_text(USER)
        body = page.content()
        check("history persists after re-login",
              "attempt(s)" in body and "Clinical Screen" in body)

        # ---------- 8. mobile viewport sanity ----------
        mctx = browser.new_context(viewport={"width": 390, "height": 844},
                                   is_mobile=True, has_touch=True)
        mp = mctx.new_page()
        mp.goto(f"{BASE}/")
        mp.screenshot(path=f"{ART}/09_mobile_home.png")
        check("mobile: home renders", "Brain Circus" in mp.content())
        mp.goto(f"{BASE}/iq/test")
        mp.wait_for_selector("#stage .opt", timeout=10000)
        mp.screenshot(path=f"{ART}/10_mobile_iq.png")
        check("mobile: iq test playable", mp.locator("#stage .opt").count() > 0)
        mctx.close()

        browser.close()


error = None
try:
    run()
except Exception:
    import traceback
    error = traceback.format_exc()
    traceback.print_exc()
finally:
    print("\n" + "=" * 60)
    fails = [r for r in results if not r[1]]
    print(f"TOTAL: {len(results)} | PASS: {len(results) - len(fails)} | FAIL: {len(fails)}")
    for name, _, detail in fails:
        print(f"  ✗ {name} {detail}")
    if error:
        sys.exit(2)
    sys.exit(1 if fails else 0)
