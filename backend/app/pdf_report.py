"""
Générateur de rapports PDF professionnels.

Utilise ReportLab pour produire un document PDF récapitulatif
de tous les déploiements effectués via le chatbot.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

from backend.app import history


def generer_rapport_pdf() -> bytes:
    """
    Génère un rapport PDF complet des déploiements.

    Returns:
        bytes: contenu du fichier PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Styles personnalisés
    titre_style = ParagraphStyle(
        "TitreRapport",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )
    sous_titre_style = ParagraphStyle(
        "SousTitre",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor("#16213e"),
    )
    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6,
    )

    elements = []

    # ── En-tête ──
    elements.append(Paragraph("IaC Chatbot — Rapport de Déploiements", titre_style))
    elements.append(
        Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            normal_style,
        )
    )
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0f3460")))
    elements.append(Spacer(1, 0.5 * cm))

    # ── Statistiques ──
    stats = history.compter_requetes()
    elements.append(Paragraph("Statistiques Globales", sous_titre_style))

    stats_data = [
        ["Métrique", "Valeur"],
        ["Total des requêtes", str(stats["total"])],
        ["Déploiements réussis", str(stats["success"])],
        ["Erreurs", str(stats["errors"])],
        [
            "Taux de succès",
            f"{(stats['success'] / max(stats['total'], 1)) * 100:.1f}%",
        ],
    ]

    stats_table = Table(stats_data, colWidths=[10 * cm, 6 * cm])
    stats_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f0f0f5")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(stats_table)
    elements.append(Spacer(1, 1 * cm))

    # ── Historique détaillé ──
    elements.append(Paragraph("Historique des Déploiements", sous_titre_style))

    entries = history.lister_historique(limit=100)

    if not entries:
        elements.append(Paragraph("Aucun déploiement enregistré.", normal_style))
    else:
        # En-têtes du tableau
        table_data = [["#", "Date", "Requête", "Type", "Statut"]]

        for entry in entries:
            # Tronquer le prompt si trop long
            prompt_court = entry.prompt[:50] + "..." if len(entry.prompt) > 50 else entry.prompt

            # Formater la date
            try:
                dt = datetime.fromisoformat(entry.timestamp)
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except (ValueError, TypeError):
                date_str = entry.timestamp[:16] if entry.timestamp else "N/A"

            statut_label = {
                "success": "✓ Succès",
                "error": "✗ Erreur",
                "clarification": "? Clarification",
            }.get(entry.statut, entry.statut)

            table_data.append(
                [
                    str(entry.id),
                    date_str,
                    prompt_court,
                    entry.type_generation or "—",
                    statut_label,
                ]
            )

        hist_table = Table(
            table_data, colWidths=[1.2 * cm, 3.5 * cm, 7 * cm, 3 * cm, 2.5 * cm]
        )
        hist_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (-1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5fa")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elements.append(hist_table)

    elements.append(Spacer(1, 1 * cm))

    # ── Pied de page ──
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(
        Paragraph(
            "Ce rapport a été généré automatiquement par le IaC Chatbot. "
            "Infrastructure as Code & Automation pilotée par Chatbot Intelligent.",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
        )
    )

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
