"""PDF generation produces a valid, populated document."""
from survey.deterministic import build_report
from survey.pdf import build_pdf


def _bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def test_single_site_pdf(one_bundle, tmp_path):
    out = tmp_path / "report.pdf"
    path = build_pdf(build_report(one_bundle), out)
    data = _bytes(path)
    assert data[:4] == b"%PDF"
    assert len(data) > 3000  # not an empty shell
    try:
        from pypdf import PdfReader
    except ImportError:
        return
    reader = PdfReader(str(out))
    assert len(reader.pages) >= 1
    text = "".join((p.extract_text() or "") for p in reader.pages)
    assert one_bundle.site.id in text
    assert "Scorecard" in text
    assert "To be verified" in text
    assert "Site Assessment" in text


def test_multi_site_pdf(bundles, tmp_path):
    reports = [build_report(b) for b in bundles[:3]]
    out = tmp_path / "multi.pdf"
    build_pdf(reports, out)
    data = _bytes(out)
    assert data[:4] == b"%PDF"
    try:
        from pypdf import PdfReader
    except ImportError:
        return
    assert len(PdfReader(str(out)).pages) >= 3


def test_nogo_site_pdf_renders(gated_bundle, tmp_path):
    out = tmp_path / "nogo.pdf"
    build_pdf(build_report(gated_bundle), out)
    assert _bytes(out)[:4] == b"%PDF"
