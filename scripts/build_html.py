"""
Macro War Room — single-file HTML builder
Transforms the React source (src/App.jsx + src/index.css) into a self-contained,
build-free public index.html that GitHub Pages serves directly (nihon-dashboard
style). React / ReactDOM / Recharts / Babel load from CDN; data.json + analysis.json
are fetched at runtime, so DAILY DATA UPDATES NEED NO REBUILD — this only needs to
run when you change the UI in src/App.jsx.

Run:  python scripts/build_html.py      (writes ./index.html)
"""

import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP  = (ROOT / "src" / "App.jsx").read_text(encoding="utf-8")
CSS  = (ROOT / "src" / "index.css").read_text(encoding="utf-8")

# ── Turn ES-module App.jsx into browser-global code ──────────────────────────
def must_replace(text, old, new, label):
    if old not in text:
        sys.exit(f"[build_html] FAILED — could not find {label} in src/App.jsx. "
                 f"Did the source change shape? Update scripts/build_html.py.")
    return text.replace(old, new, 1)

# React + hooks come from the global `React` (UMD), not an import.
APP = must_replace(
    APP,
    'import React, { useState, useEffect, useRef } from "react";',
    'const { useState, useEffect, useRef } = React;',
    "the React import")

# Recharts components come from the global `Recharts` (UMD).
APP = must_replace(APP, 'import {\n', 'const {\n', "the recharts import opener")
APP = must_replace(APP, '} from "recharts";', '} = Recharts;', "the recharts import closer")

# No bundler → no import.meta.env; data lives next to index.html at the site root.
APP = must_replace(APP, '`${import.meta.env.BASE_URL}data.json`', "'./data.json'", "the data.json fetch path")
APP = must_replace(APP, '`${import.meta.env.BASE_URL}analysis.json`', "'./analysis.json'", "the analysis.json fetch path")

# No ES-module export; App is just a function in the script scope.
APP = must_replace(APP, 'export default function App(){', 'function App(){', "the App export")

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<link rel="icon" type="image/svg+xml" href="./favicon.svg" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Macro War Room</title>
<!-- ───────────────────────────────────────────────────────────────────────
     GENERATED FILE — do not edit by hand.
     Edit src/App.jsx (and src/index.css), then run:  python scripts/build_html.py
     Daily market/analysis data is fetched at runtime from ./data.json +
     ./analysis.json (refreshed by the GitHub Actions workflow), so a data
     update never requires regenerating this file.
─────────────────────────────────────────────────────────────────────────── -->
<style>
{CSS}
</style>
<script crossorigin src="https://unpkg.com/react@18.3.1/umd/react.production.min.js"></script>
<script crossorigin src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js"></script>
<!-- prop-types is a peer dependency of the Recharts UMD build -->
<script crossorigin src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>
<script crossorigin src="https://unpkg.com/recharts@2.12.7/umd/Recharts.js"></script>
<script src="https://unpkg.com/@babel/standalone@7.24.7/babel.min.js"></script>
</head>
<body>
<div id="root"></div>
<script type="text/babel" data-presets="react">
{APP}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
</script>
</body>
</html>
"""

out = ROOT / "index.html"
out.write_text(HTML, encoding="utf-8")
print(f"[build_html] wrote {out}  ({len(HTML):,} bytes)")
