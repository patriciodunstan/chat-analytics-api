"""PDF report generator."""
import io
import os
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, 
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from app.reports.charts import (
    create_cost_vs_expense_bar_chart,
    create_summary_comparison_chart,
    create_pie_chart,
)


class ReportGenerator:
    """Generate PDF reports with charts and LLM analysis."""

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
        
        if 'Recommendation' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Recommendation',
                parent=self.styles['Normal'],
                fontSize=11,
                leftIndent=20,
                spaceAfter=8,
                textColor=colors.HexColor('#27ae60'),
            ))

    def generate_cost_vs_expense_report(
        self,
        service_name: str,
        total_costs: float,
        total_expenses: float,
        costs_by_category: dict[str, float],
        expenses_by_category: dict[str, float],
        analysis_text: str,
        recommendations: list[str],
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> str:
        """Generate a cost vs expense analysis report."""
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cost_vs_expense_{service_name.replace(' ', '_')}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph(
            f"Análisis de Costos vs Gastos",
            self.styles['CustomTitle']
        ))
        story.append(Paragraph(
            f"Servicio: {service_name}",
            self.styles['Heading3']
        ))
        
        # Period info
        period_text = "Período: "
        if period_start and period_end:
            period_text += f"{period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')}"
        else:
            period_text += "Todo el historial"
        story.append(Paragraph(period_text, self.styles['Normal']))
        story.append(Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))
        
        # Summary table
        story.append(Paragraph("Resumen Ejecutivo", self.styles['SectionHeader']))
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total Costos', f'${total_costs:,.2f}'],
            ['Total Gastos', f'${total_expenses:,.2f}'],
            ['Diferencia', f'${(total_costs - total_expenses):,.2f}'],
            ['Ratio (Costos/Gastos)', f'{(total_costs/total_expenses if total_expenses else 0):.2f}'],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Summary chart
        story.append(Paragraph("Comparación Visual", self.styles['SectionHeader']))
        summary_chart_bytes = create_summary_comparison_chart(total_costs, total_expenses)
        summary_chart = Image(io.BytesIO(summary_chart_bytes))
        summary_chart.drawWidth = 5*inch
        summary_chart.drawHeight = 3*inch
        story.append(summary_chart)
        story.append(Spacer(1, 20))
        
        # Category comparison chart
        if costs_by_category or expenses_by_category:
            story.append(Paragraph("Análisis por Categoría", self.styles['SectionHeader']))
            category_chart_bytes = create_cost_vs_expense_bar_chart(
                costs_by_category, expenses_by_category
            )
            category_chart = Image(io.BytesIO(category_chart_bytes))
            category_chart.drawWidth = 6*inch
            category_chart.drawHeight = 3.5*inch
            story.append(category_chart)
            story.append(Spacer(1, 20))
        
        # Distribution pie charts
        if costs_by_category:
            story.append(Paragraph("Distribución de Costos", self.styles['SectionHeader']))
            pie_chart_bytes = create_pie_chart(costs_by_category, "Distribución de Costos")
            pie_chart = Image(io.BytesIO(pie_chart_bytes))
            pie_chart.drawWidth = 4*inch
            pie_chart.drawHeight = 4*inch
            story.append(pie_chart)
            story.append(Spacer(1, 20))
        
        # Analysis section (from LLM)
        story.append(PageBreak())
        story.append(Paragraph("Análisis Detallado", self.styles['SectionHeader']))
        
        # Split analysis into paragraphs
        for paragraph in analysis_text.split('\n\n'):
            if paragraph.strip():
                # Handle markdown-style headers
                if paragraph.strip().startswith('**') and paragraph.strip().endswith('**'):
                    clean_text = paragraph.strip().strip('*')
                    story.append(Paragraph(clean_text, self.styles['Heading4']))
                else:
                    story.append(Paragraph(paragraph.strip(), self.styles['BodyText']))
        
        story.append(Spacer(1, 20))
        
        # Recommendations section
        story.append(Paragraph("Recomendaciones", self.styles['SectionHeader']))
        
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(
                f"<b>{i}.</b> {rec}",
                self.styles['Recommendation']
            ))
        
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(Paragraph(
            "Este reporte fue generado automáticamente utilizando análisis de IA.",
            self.styles['Italic']
        ))
        
        # Build PDF
        doc.build(story)
        
        return filepath


# Singleton instance
report_generator = ReportGenerator()
