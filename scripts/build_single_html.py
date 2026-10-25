"""Bundle this project's static explorer into one offline HTML file."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit, unquote

def build_single_html(entry: Path, output: Path) -> Path:
    entry, output = Path(entry).resolve(), Path(output).resolve()
    if entry == output:
        raise ValueError("Output cannot overwrite the source entry")
    if output.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("Output must be an HTML file")
    root = entry.parent
    text = entry.read_text(encoding="utf-8-sig")
    scripts = []

    def attribute(tag: str, name: str) -> str | None:
        found = re.search(r"\b" + name + r"""\s*=\s*(['"])(.*?)\1""", tag, re.I | re.S)
        return found.group(2) if found else None

    def read_asset(source: str) -> str:
        url = urlsplit(source)
        if url.scheme or url.netloc:
            raise ValueError("Only local assets can be embedded")
        asset = (root / unquote(url.path)).resolve()
        if root not in asset.parents or asset == output:
            raise ValueError("Asset must stay inside the entry directory")
        return asset.read_text(encoding="utf-8-sig")

    def replace_link(match):
        tag = match.group(0)
        if attribute(tag, "rel") != "stylesheet":
            return tag
        source = attribute(tag, "href")
        if not source:
            raise ValueError("Stylesheet has no href")
        css = read_asset(source)
        if re.search(r"</style", css, re.I):
            raise ValueError("Unexpected style terminator in stylesheet")
        return "<style>\n" + css + "\n</style>"

    def replace_script(match):
        source = attribute(match.group("attrs"), "src")
        if source is None:
            return match.group(0)
        javascript = read_asset(source)
        # HTML parsing ends script elements before JavaScript parses its strings.
        javascript = re.sub(r"</script", lambda _: r"<\/script", javascript, flags=re.I)
        scripts.append("<script>\n" + javascript + "\n</script>")
        return ""

    text = re.sub(r"<link\b[^>]*>", replace_link, text, flags=re.I)
    text = re.sub(r"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>",
                  replace_script, text, flags=re.I | re.S)
    # Scripts execute in source order only after the page DOM exists.
    closing = re.search(r"</body\s*>", text, re.I)
    if closing is None:
        raise ValueError("Entry is missing a closing body element")
    text = text[:closing.start()] + "\n".join(scripts) + "\n" + text[closing.start():]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    return output

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", type=Path, default=Path("website/local.html"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = build_single_html(args.entry, args.output)
    print(f"Single HTML written: {output} ({output.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
