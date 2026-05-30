"""
ActuarialFleet — generatore report PDF (ReportLab)
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import io

# ── PALETTE ──
C_BG      = colors.HexColor("#0D0F14")
C_CARD    = colors.HexColor("#13161D")
C_ACC     = colors.HexColor("#4F8EF7")
C_ACC2    = colors.HexColor("#7C5CFC")
C_OK      = colors.HexColor("#22C55E")
C_WARN    = colors.HexColor("#F59E0B")
C_ERR     = colors.HexColor("#EF4444")
C_TEXT    = colors.HexColor("#E8EAF0")
C_TEXT2   = colors.HexColor("#9BA3BC")
C_BORDER  = colors.HexColor("#2A2E3D")
C_WHITE   = colors.white

def fmt_e(v, d=0):
    if v is None:
        return "—"
    return f"€ {v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_n(v, d=0):
    if v is None:
        return "—"
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Normal"],
            fontSize=22, textColor=C_ACC, fontName="Helvetica-Bold",
            spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"],
            fontSize=11, textColor=C_TEXT2, spaceAfter=16),
        "section": ParagraphStyle("section", parent=base["Normal"],
            fontSize=13, textColor=C_ACC, fontName="Helvetica-Bold",
            spaceBefore=14, spaceAfter=8,
            borderPad=4),
        "body": ParagraphStyle("body", parent=base["Normal"],
            fontSize=9, textColor=C_TEXT2, spaceAfter=4),
        "value": ParagraphStyle("value", parent=base["Normal"],
            fontSize=16, textColor=C_TEXT, fontName="Helvetica-Bold",
            spaceAfter=2),
        "label": ParagraphStyle("label", parent=base["Normal"],
            fontSize=8, textColor=C_TEXT2, spaceAfter=0),
        "footer": ParagraphStyle("footer", parent=base["Normal"],
            fontSize=8, textColor=C_TEXT2, alignment=TA_CENTER),
    }

def _table_style(header_bg=C_ACC, alt=True):
    style = [
        ("BACKGROUND",    (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 8),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("TEXTCOLOR",     (0, 1), (-1, -1), C_TEXT2),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1),
            [colors.HexColor("#13161D"), colors.HexColor("#1A1E28")] if alt else [colors.HexColor("#13161D")]),
        ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    return TableStyle(style)

def _metric_table(items):
    """Riga di metriche affiancate: [(label, value, color), ...]"""
    n = len(items)
    col_w = (A4[0] - 4 * cm) / n
    data = [[Paragraph(f"<font color='#{c[1:]}' size='14'><b>{v}</b></font>"
                       f"<br/><font color='#9BA3BC' size='7'>{l}</font>",
                       getSampleStyleSheet()["Normal"])
             for l, v, c in items]]
    t = Table([data[0]], colWidths=[col_w] * n)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#13161D")),
        ("BOX",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID",    (0, 0), (-1, -1), 0.3, C_BORDER),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
    ]))
    return t

def genera_report(flotte_df, sinistri_df, calcoli: list) -> bytes:
    """Genera report PDF professionale e restituisce bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="ActuarialFleet — Report Attuariale",
    )
    S = _styles()
    story = []

    # ── COPERTINA ──
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("ActuarialFleet", S["title"]))
    story.append(Paragraph("Report Attuariale — Portafoglio Flotte RCA", S["subtitle"]))
    story.append(Paragraph(
        f"Generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}  ·  "
        f"{len(flotte_df)} flotte  ·  {int(flotte_df['nveic'].sum()) if not flotte_df.empty else 0} veicoli",
        S["body"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACC, spaceAfter=20))

    # ── KPI SOMMARIO ──
    if not flotte_df.empty and calcoli:
        tot_veic  = int(flotte_df["nveic"].sum())
        tot_prem  = sum(c["lordo_fleet"] for c in calcoli)
        tot_sin   = sum(c["sin_attesi"] for c in calcoli)
        tot_ris   = float(sinistri_df["riserva"].sum()) if not sinistri_df.empty else 0
        lr_pct    = (tot_ris / tot_prem * 100) if tot_prem > 0 else 0
        story.append(_metric_table([
            ("Veicoli totali",       fmt_n(tot_veic),          "#4F8EF7"),
            ("Premio RCA lordo",     fmt_e(round(tot_prem)),    "#22C55E"),
            ("Sinistri att./anno",   fmt_n(tot_sin, 1),         "#F59E0B"),
            ("Riserva totale",       fmt_e(round(tot_ris)),     "#EF4444"),
            ("Loss ratio est.",      f"{lr_pct:.1f}%",          "#7C5CFC"),
        ]))
        story.append(Spacer(1, 0.5*cm))

    # ── ANAGRAFICA FLOTTE ──
    story.append(Paragraph("1 · Anagrafica portafoglio flotte", S["section"]))
    if not flotte_df.empty:
        zona_label = {1: "Zona 1 — alto rischio", 2: "Zona 2 — medio", 3: "Zona 3 — basso", 4: "Zona 4 — molto basso"}
        data = [["Nome flotta", "Provincia", "Veicoli", "Cilindrata", "Uso", "Scadenza", "Referente"]]
        for _, r in flotte_df.iterrows():
            data.append([
                str(r.get("nome", "")),
                str(r.get("provincia", "")),
                str(r.get("nveic", "")),
                str(r.get("cilindrata", "")),
                str(r.get("uso", "")),
                str(r.get("scadenza", "") or "—"),
                str(r.get("referente", "") or "—"),
            ])
        t = Table(data, colWidths=[3.8*cm, 1.8*cm, 1.5*cm, 1.8*cm, 1.8*cm, 2.0*cm, 2.5*cm])
        t.setStyle(_table_style())
        story.append(t)
    else:
        story.append(Paragraph("Nessuna flotta registrata.", S["body"]))
    story.append(Spacer(1, 0.4*cm))

    # ── TARIFFAZIONE ──
    story.append(Paragraph("2 · Riepilogo tariffario per flotta", S["section"]))
    if calcoli and not flotte_df.empty:
        data = [["Flotta", "Zona", "Freq.", "Sev. media", "PP cred.", "Netto RCA", "Lordo RCA", "Fleet totale", "Sin. att."]]
        for i, (_, row) in enumerate(flotte_df.iterrows()):
            if i >= len(calcoli):
                break
            c = calcoli[i]
            p = c["prov"]
            data.append([
                str(row["nome"])[:22],
                f"Z{p['zona']}",
                f"{p['freq']:.3f}",
                fmt_e(p["srca"]),
                fmt_e(round(c["pp_adj"])),
                fmt_e(round(c["netto"])),
                fmt_e(round(c["lordo_rca"])),
                fmt_e(round(c["lordo_fleet"])),
                f"{c['sin_attesi']:.1f}",
            ])
        t = Table(data, colWidths=[3.2*cm, 1.0*cm, 1.1*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.6*cm, 2.0*cm, 1.3*cm])
        t.setStyle(_table_style(header_bg=C_ACC2))
        story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # ── SINISTRI ──
    story.append(Paragraph("3 · Sinistri registrati", S["section"]))
    if not sinistri_df.empty:
        aperti  = sinistri_df[sinistri_df["stato"] == "aperto"]
        riserva = sinistri_df[sinistri_df["stato"] == "riserva"]
        chiusi  = sinistri_df[sinistri_df["stato"] == "chiuso"]
        story.append(_metric_table([
            ("Totale sinistri",  str(len(sinistri_df)),                     "#4F8EF7"),
            ("Aperti",           str(len(aperti)),                           "#EF4444"),
            ("In riserva",       str(len(riserva)),                          "#F59E0B"),
            ("Chiusi",           str(len(chiusi)),                           "#22C55E"),
            ("Riserva totale",   fmt_e(round(sinistri_df["riserva"].sum())), "#7C5CFC"),
            ("Pagato totale",    fmt_e(round(sinistri_df["pagato"].sum())),  "#2EC4B6"),
        ]))
        story.append(Spacer(1, 0.3*cm))
        data = [["Targa", "Flotta", "Data", "Tipo", "Riserva", "Pagato", "Stato", "Descrizione"]]
        for _, r in sinistri_df.head(40).iterrows():
            data.append([
                str(r.get("targa", "")),
                str(r.get("flotta_nome", ""))[:18],
                str(r.get("data_sinistro", "") or "—"),
                str(r.get("tipo", "")),
                fmt_e(r.get("riserva", 0)),
                fmt_e(r.get("pagato", 0)),
                str(r.get("stato", "")),
                str(r.get("descrizione", "") or "")[:25],
            ])
        t = Table(data, colWidths=[1.5*cm, 2.8*cm, 1.5*cm, 1.4*cm, 1.7*cm, 1.7*cm, 1.4*cm, 3.2*cm])
        t.setStyle(_table_style(header_bg=C_ERR))
        story.append(t)
    else:
        story.append(Paragraph("Nessun sinistro registrato.", S["body"]))

    # ── FOOTER ──
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"ActuarialFleet v2.0  ·  Report generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}  ·  "
        "Uso interno — dati riservati",
        S["footer"]))

    doc.build(story)
    return buf.getvalue()
