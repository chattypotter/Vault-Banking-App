#!/usr/bin/env python3
"""
build_app.py — connects the four standalone Vault tab pages into one
navigable mini-app.

What it does
------------
Each of the 4 uploaded HTML files already renders a bottom nav bar with
tabs: Spend / Save / Send / Track. Right now clicking those tabs does
nothing (or only re-renders a local "active" state) because each file
lives on its own with no link to the others.

This script:
  1. Reads the 4 source files.
  2. Renames/copies them to standard names: spend.html, save.html,
     send.html, track.html.
  3. Injects a small routing script into each page, right before
     </body>, that listens for clicks on any .nav-item and navigates
     to the matching page (spend.html / save.html / send.html /
     track.html). Clicking the tab you're already on does nothing.
  4. Writes the wired-up files into an output folder.
  5. Optionally starts a local web server and opens your browser to
     the Spend tab (pass --serve to do this).

Usage
-----
    python3 build_app.py                # just build the wired files
    python3 build_app.py --serve        # build, then serve + open browser
    python3 build_app.py --serve --port 8000

Folder layout expected (edit SOURCES below if yours differ):
    ./spendsection.html
    ./save-tab.html
    ./send-tab.html
    ./track-tab-improved.html
"""

import argparse
import http.server
import os
import re
import socketserver
import sys
import webbrowser

# ---------------------------------------------------------------------------
# Map each nav tab id -> (source file on disk, output file name)
# Edit the left-hand source filenames here if your files are named differently.
# ---------------------------------------------------------------------------
SOURCES = {
    "spend": "spendsection.html",
    "save": "save-tab.html",
    "send": "send-tab.html",
    "track": "track-tab-improved.html",
}

OUTPUT_NAMES = {
    "spend": "index.html",
    "save": "save.html",
    "send": "send.html",
    "track": "track.html",
}

OUTPUT_DIR = "vault_app"


def make_router_script(current_tab: str) -> str:
    """JS snippet that turns the bottom-nav tabs into page links."""
    routes_js = ", ".join(f'{tab}: "{name}"' for tab, name in OUTPUT_NAMES.items())
    return f"""
<script>
/* ---- injected by build_app.py: cross-page tab navigation ---- */
(function () {{
  var ROUTES = {{ {routes_js} }};
  var CURRENT_TAB = "{current_tab}";
  document.addEventListener("click", function (e) {{
    var item = e.target.closest(".nav-item");
    if (!item) return;
    var id = item.dataset.id;
    if (!id || !ROUTES[id] || id === CURRENT_TAB) return;
    window.location.href = ROUTES[id];
  }});
}})();
</script>
"""


def inject_router(html: str, current_tab: str) -> str:
    """Insert the router script just before the closing </body> tag."""
    script = make_router_script(current_tab)
    if "</body>" in html:
        return html.replace("</body>", script + "</body>", 1)
    # Fallback: just append if no </body> tag is found.
    return html + script


def build(source_dir: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    for tab, source_name in SOURCES.items():
        source_path = os.path.join(source_dir, source_name)
        if not os.path.isfile(source_path):
            print(f"  ! Skipping '{tab}': source file not found at {source_path}")
            continue

        with open(source_path, "r", encoding="utf-8") as f:
            html = f.read()

        wired_html = inject_router(html, current_tab=tab)

        output_path = os.path.join(output_dir, OUTPUT_NAMES[tab])
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(wired_html)

        print(f"  \u2713 {source_name} -> {output_path}  (tab: {tab})")

    print(f"\nDone. Wired files are in ./{output_dir}/")
    print(f"Open {os.path.join(output_dir, 'index.html')} in a browser to start,")
    print("or re-run this script with --serve to launch a local server.")


def serve(output_dir: str, port: int) -> None:
    os.chdir(output_dir)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # keep console output clean

    with socketserver.TCPServer(("", port), QuietHandler) as httpd:
        url = f"http://localhost:{port}/index.html"
        print(f"Serving Vault app at {url}  (Ctrl+C to stop)")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


def main():
    parser = argparse.ArgumentParser(description="Wire up the Vault tab pages.")
    parser.add_argument(
        "--source-dir", default=".", help="Folder containing the 4 source HTML files."
    )
    parser.add_argument(
        "--output-dir", default=OUTPUT_DIR, help="Folder to write the wired app into."
    )
    parser.add_argument(
        "--serve", action="store_true", help="Start a local server and open the app."
    )
    parser.add_argument("--port", type=int, default=8000, help="Port for --serve.")
    args = parser.parse_args()

    print("Building Vault app...")
    build(args.source_dir, args.output_dir)

    if args.serve:
        serve(args.output_dir, args.port)


if __name__ == "__main__":
    sys.exit(main())
