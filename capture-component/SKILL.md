---
name: capture-component
description: Capture a cropped PNG (or scroll GIF) of a Storybook component story for PR screenshots, via browser-harness CDP clip. Use when asked to screenshot/gif a component, a Storybook story, or produce PR visuals from a running Storybook.
---

# capture-component

Crop is done **at capture time** with CDP `Page.captureScreenshot` `clip` (element bbox), not ffmpeg. ffmpeg only stitches GIF frames.

## Prereqs
- Storybook running: `pnpm --filter <fe-pkg> storybook` → `http://localhost:6007`.
- `browser-harness` on `$PATH` (drives the user's Chrome via CDP).
- `ffmpeg` only if making a GIF.

## Rules
- **Never write captures into the repo.** Output to `~/Desktop/<name>-captures/` (or ask).
- Story URL = isolated preview: `http://localhost:6007/iframe.html?id=<kebab-title>--<kebab-export>&viewMode=story` (e.g. title `Components/Lupo/ProgressQueue` + export `Scrolling` → `components-lupo-progressqueue--scrolling`).
- Target the component by an **exact** selector (`section[aria-label="..."]`, a unique class). Generic `section`/`button`/`ul` also match Storybook chrome.
- `cdp()` takes params as **kwargs**, not a dict: `cdp('Page.captureScreenshot', format='png', clip=clip)`.
- `clip` from `getBoundingClientRect()`, pad ~2px (rounded corners), `scale:2` (crisp on retina ≈ 4× output).

## Still (PNG)
```bash
browser-harness <<'PY'
import base64, os, json, time
out = os.path.expanduser('~/Desktop/CAP-captures'); os.makedirs(out, exist_ok=True)
sel = 'button.bg-primary-solid'   # exact selector for the component
new_tab('http://localhost:6007/iframe.html?id=STORY-ID&viewMode=story'); wait_for_load(); time.sleep(0.5)
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
new_tab('http://localhost:6007/iframe.html?id=STORY-ID&viewMode=story'); wait_for_load(); time.sleep(0.6)
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
