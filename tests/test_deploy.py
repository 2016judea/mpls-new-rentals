"""outputDirectory "." served api/_full/full.json.gz as /api/%5Ffull/... (200) until 2026-10-19:
the whole paid feed, to anyone. Only public/ is served statically now; the bundle reaches api/data.js
through includeFiles and nothing else."""
import importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_only_public_is_served_statically_and_the_bundle_only_reaches_the_function():
    spec = importlib.util.spec_from_file_location("deploy", ROOT / "scripts/deploy.py")
    dp = importlib.util.module_from_spec(spec); spec.loader.exec_module(dp)
    rels = [str(r) for r, _ in dp.collect()]
    vj = json.loads((ROOT / "site/vercel.json").read_text())
    assert vj["outputDirectory"] == "public"
    assert {"/api/_full/:path*", "/api/%5Ffull/:path*", "/api/%5ffull/:path*"} <= {r["source"] for r in vj["redirects"]}
    assert "public/index.html" in rels and "api/_full/full.json.gz" in rels
    assert not [r for r in rels if r.startswith("public/") and ("_full" in r or r.startswith("public/api"))]
    assert all(r.startswith(("public/", "api/")) or r in ("vercel.json", "offer.json") for r in rels)
    assert '"outputDirectory": "public"' in (ROOT / "scripts/deploy.py").read_text()
