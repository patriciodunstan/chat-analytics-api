"""PDF report generator (generic)."""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


class ReportGenerator:
    """Generate PDF reports with LLM analysis."""

    def __init__(self, output_dir: str = "reports_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self):
        """Add custom paragraph styles."""
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#2c3e50'),
            ))

        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=16,
                spaceBefore=20,
                spaceAfter=10,
                textColor=colors.HexColor('#34495e'),
            ))

        if 'BodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                parent=self.styles['Normal'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=14,
            ))

    def generate_summary_report(
        self,
        title: str,
        data_summary: dict,
        analysis_text: str,
        recommendations: list[str] | None = None,
    ) -> str:
        """Generate a generic data summary report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = title.replace(' ', '_').replace('/', '_')[:50]
        filename = f"summary_{safe_title}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        story = []

        # Title
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))

        # Summary table
        story.append(Paragraph("Resumen de Datos", self.styles['SectionHeader']))
        summary_data = [['Métrica', 'Valor']]
        for key, value in data_summary.items():
            summary_data.append([str(key), str(value)])

        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        # Analysis section
        story.append(PageBreak())
        story.append(Paragraph("Análisis", self.styles['SectionHeader']))

        for paragraph in analysis_text.split('\n\n'):
            if paragraph.strip():
                if paragraph.strip().startswith('**') and paragraph.strip().endswith('**'):
                    clean_text = paragraph.strip().strip('*')
                    story.append(Paragraph(clean_text, self.styles['Heading4']))
                else:
                    story.append(Paragraph(paragraph.strip(), self.styles['BodyText']))

        # Recommendations
        if recommendations:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Recomendaciones", self.styles['SectionHeader']))
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec}", self.styles['BodyText']))

        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "Este reporte fue generado automáticamente utilizando análisis de IA.",
            self.styles['Italic']
        ))

        doc.build(story)
        return filepath


# Singleton instance
report_generator = ReportGenerator()
