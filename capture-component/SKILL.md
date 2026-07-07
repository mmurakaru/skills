---
name: capture-component
description: Capture a cropped PNG (or scroll GIF) of any web app UI element for PR screenshots, via browser-harness CDP clip. Use when asked to screenshot/gif a component or element, or produce PR visuals from a running app at any URL.
---

# capture-component

Crop is done **at capture time** with CDP `Page.captureScreenshot` `clip` (element bbox), not ffmpeg. ffmpeg only stitches GIF frames.

## Prereqs
- The target rendered at any URL you can open (local dev server, preview deploy, or a live site).
- `browser-harness` on `$PATH` (drives the user's Chrome via CDP).
- `ffmpeg` only if making a GIF.

## Rules
- **Never write captures into the repo.** Output to `~/Desktop/<name>-captures/` (or ask).
- Point at any URL that renders the target in the state you want. If the tooling offers an isolated preview URL (the component alone, no app chrome), prefer it.
- Target the component by an **exact** selector (`section[aria-label="..."]`, a unique class). Generic `section`/`button`/`ul` may also match page chrome (toolbars, app nav, etc.).
- `cdp()` takes params as **kwargs**, not a dict: `cdp('Page.captureScreenshot', format='png', clip=clip)`.
- `clip` from `getBoundingClientRect()`, pad ~2px (rounded corners), `scale:2` (crisp on retina ≈ 4× output).

## Still (PNG)
```bash
browser-harness <<'PY'
import base64, os, json, time
out = os.path.expanduser('~/Desktop/CAP-captures'); os.makedirs(out, exist_ok=True)
sel = '.my-component'   # exact selector for the component
new_tab('<url>'); wait_for_load(); time.sleep(0.5)  # any URL that renders the component
b = json.loads(js("(()=>{const e=document.querySelector('%s');const r=e.getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,w:r.width,h:r.height});})()" % sel))
clip = {'x':b['x']-2,'y':b['y']-2,'width':b['w']+4,'height':b['h']+4,'scale':2}
shot = cdp('Page.captureScreenshot', format='png', clip=clip, captureBeyondViewport=True)
open(os.path.join(out,'NAME.png'),'wb').write(base64.b64decode(shot['data']))
PY
```

## Scroll GIF
- Capture N frames stepping the scroll container's `scrollTop` 0→max, clipping the wrapper each frame.
```bash
browser-harness <<'PY'
import base64, os, json, time
out = os.path.expanduser('~/Desktop/CAP-captures/frames'); os.makedirs(out, exist_ok=True)
sel = 'section[aria-label="..."]'          # wrapper to clip
new_tab('<url>'); wait_for_load(); time.sleep(0.6)  # any URL that renders the component
b = json.loads(js("(()=>{const s=document.querySelector('%s');const u=s.querySelector('ul');const r=s.getBoundingClientRect();return JSON.stringify({x:r.left,y:r.top,w:r.width,h:r.height,max:u.scrollHeight-u.clientHeight});})()" % sel))
clip = {'x':b['x']-2,'y':b['y']-2,'width':b['w']+4,'height':b['h']+4,'scale':2}
N = 12
for i in range(N):
    js("document.querySelector('%s ul').scrollTop=%d" % (sel, round(b['max']*i/(N-1)))); time.sleep(0.08)
    open(os.path.join(out,'frame_%02d.png'%i),'wb').write(base64.b64decode(cdp('Page.captureScreenshot', format='png', clip=clip, captureBeyondViewport=True)['data']))
PY
```
- Stitch (ping-pong loop + palette for clean colours):
```bash
cd ~/Desktop/CAP-captures
ffmpeg -y -framerate 9 -i frames/frame_%02d.png -filter_complex \
  "[0:v]split[a][b];[b]reverse[rb];[a][rb]concat=n=2:v=1:a=0,fps=9,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  NAME.gif
```

## Verify
- `Read` the PNG / first+last frame to confirm framing and that the scroll actually moved.

## PR note
- GitHub PR bodies need images **uploaded** (drag-drop or `gh`); you can't link local files. Leave `<img>` placeholders or hand the files to the user.
