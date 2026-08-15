from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image


def generate_pdf_report(result, ecg_plot_path, spectrum_plot_path, rr_plot_path, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=18, leading=22, spaceAfter=12)
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8.5, leading=11)

    story = [
        Paragraph("BioSignal Analytics Pro v2.0", title_style),
        Paragraph("Adaptive ECG Analysis Report", styles["Heading2"]),
        Spacer(1, 10),
    ]

    detector = result.get("adaptive_detection", {})
    source = result.get("input_metadata", {})
    quality = result["signal_quality"]

    summary_rows = [
        ["Metric", "Result"],
        ["File", result["filename"]],
        ["Source format", source.get("source_format", "N/A").upper()],
        ["Mapped columns", f'{source.get("time_column", "?")} -> Time_s; {source.get("signal_column", "?")} -> ECG_mV'],
        ["Samples", str(result["samples"])],
        ["Sampling frequency", f'{result["sampling_frequency_hz"]:.2f} Hz'],
        ["Recording duration", f'{result["duration_s"]:.2f} s'],
        ["Detected beats", str(result["detected_beats"])],
        ["Average BPM", _fmt(result.get("average_bpm"))],
        ["Minimum BPM", _fmt(result.get("minimum_bpm"))],
        ["Maximum BPM", _fmt(result.get("maximum_bpm"))],
        ["Mean RR interval", _fmt(result.get("mean_rr_s"), " s")],
        ["SDNN", _fmt(result.get("sdnn_ms"), " ms")],
        ["RMSSD", _fmt(result.get("rmssd_ms"), " ms")],
        ["Dominant frequency", _fmt(result.get("dominant_frequency_hz"), " Hz")],
        ["Signal quality", f'{quality["rating"]} ({quality["score"]:.0f}/100)'],
    ]
    table = Table(summary_rows, colWidths=[2.3*inch, 3.4*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E8EDF3")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#AAB2BD")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.extend([table, Spacer(1, 14)])

    story.append(Paragraph("Adaptive Detection Metadata", styles["Heading3"]))
    adaptive_rows = [
        ["Estimated R-R interval", _fmt(detector.get("estimated_rr_s"), " s")],
        ["Derived minimum peak distance", _fmt(detector.get("derived_min_distance_s"), " s")],
        ["Derived prominence", _fmt(detector.get("derived_prominence"))],
        ["Candidate peaks", str(detector.get("candidate_count", "N/A"))],
        ["Detection method", str(detector.get("method", "N/A"))],
    ]
    adaptive_table = Table(adaptive_rows, colWidths=[2.6*inch, 3.1*inch])
    adaptive_table.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#CBD5E1")), ("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.extend([adaptive_table, Spacer(1, 12)])

    if quality.get("issues"):
        story.append(Paragraph("Quality Notes", styles["Heading3"]))
        for issue in quality["issues"]:
            story.append(Paragraph(f"- {issue}", styles["BodyText"]))
        story.append(Spacer(1, 8))

    for heading, path in [
        ("ECG Signal", ecg_plot_path),
        ("Beat-to-Beat Trend", rr_plot_path),
        ("Frequency Spectrum", spectrum_plot_path),
    ]:
        story.append(Paragraph(heading, styles["Heading3"]))
        story.append(Image(path, width=7.0*inch, height=3.0*inch))
        story.append(Spacer(1, 12))

    story.append(Paragraph(
        "<b>Disclaimer:</b> This software is an educational engineering portfolio project. "
        "Its adaptive thresholds, signal-quality scores, and derived metrics are not clinically validated and must not be used for medical decisions.",
        small,
    ))
    doc.build(story)


def _fmt(value, suffix=""):
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}{suffix}"
    except Exception:
        return str(value)
