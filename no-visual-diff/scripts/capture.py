# Capture one state: writes <OUT>.png (clipped) + <OUT>.styles.json (computed styles of the subtree).
# Run via: URL=<url> SEL='<selector>' OUT=<path> browser-harness < capture.py
# Optional: WAIT=<seconds> caps how long to wait for SEL to appear (default 30).
import base64, os, json, time

url = os.environ["URL"]; sel = os.environ["SEL"]; out = os.environ["OUT"]
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

new_tab(url); wait_for_load()
# SPAs render after the load event: poll for the target instead of guessing a sleep.
deadline = time.time() + float(os.environ.get("WAIT", "30"))
while not js("!!document.querySelector(%r)" % sel):
    if time.time() > deadline:
        raise SystemExit(f"selector never appeared within WAIT: {sel}")
    time.sleep(0.25)
js("document.fonts.ready.then(()=>true)")  # settle web fonts before the pixel pass
time.sleep(0.5)
# Freeze animations/transitions/caret so the pixel pass is honest.
js("const s=document.createElement('style');s.textContent='*{transition:none!important;animation:none!important;caret-color:transparent!important}';document.head.appendChild(s)")

data = json.loads(js("""(()=>{
  const root=document.querySelector(%r);
  const els=[root,...root.querySelectorAll('*')];
  const b=root.getBoundingClientRect();
  return JSON.stringify({box:{x:b.left,y:b.top,w:b.width,h:b.height},els:els.map((e,i)=>{
    const cs=getComputedStyle(e); const o={}; for(const p of cs) o[p]=cs.getPropertyValue(p);
    return {i, tag:e.tagName.toLowerCase(), styles:o};
  })});
})()""" % sel))

b = data["box"]
clip = {"x": b["x"] - 2, "y": b["y"] - 2, "width": b["w"] + 4, "height": b["h"] + 4, "scale": 2}
shot = cdp("Page.captureScreenshot", format="png", clip=clip, captureBeyondViewport=True)
open(out + ".png", "wb").write(base64.b64decode(shot["data"]))
open(out + ".styles.json", "w").write(json.dumps(data["els"]))
print(f"wrote {out}.png + {out}.styles.json ({len(data['els'])} elements)")
