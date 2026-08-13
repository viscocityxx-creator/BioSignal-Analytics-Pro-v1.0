
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)

def generate_pdf_report(result, ecg_plot_path, spectrum_plot_path, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        spaceAfter=12,
    )
    small = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
    )

    story = []
    story.append(Paragraph("BioSignal Analytics Pro v1.0", title_style))
    story.append(Paragraph("ECG Analysis Report", styles["Heading2"]))
    story.append(Spacer(1, 10))

    summary_rows = [
        ["Metric", "Result"],
        ["File", result["filename"]],
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
        ["Signal quality", result["signal_quality"]["rating"]],
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
    story.append(table)
    story.append(Spacer(1, 14))

    issues = result["signal_quality"].get("issues", [])
    if issues:
        story.append(Paragraph("Quality Notes", styles["Heading3"]))
        for issue in issues:
            story.append(Paragraph(f"- {issue}", styles["BodyText"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("ECG Signal", styles["Heading3"]))
    story.append(Image(ecg_plot_path, width=7.0*inch, height=3.0*inch))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Frequency Spectrum", styles["Heading3"]))
    story.append(Image(spectrum_plot_path, width=7.0*inch, height=3.0*inch))
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "<b>Disclaimer:</b> This software is an educational portfolio project and is not "
        "a validated clinical diagnostic device. Results must not be used for medical decisions.",
        small
    ))

    doc.build(story)

def _fmt(value, suffix=""):
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}{suffix}"
    except Exception:
        return str(value)
