"""Chart generation for reports."""
import io
from typing import Optional
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def create_cost_vs_expense_bar_chart(
    costs_by_category: dict[str, float],
    expenses_by_category: dict[str, float],
    title: str = "Costos vs Gastos por Categoría",
) -> bytes:
    """Create a bar chart comparing costs vs expenses by category."""
    # Get all categories
    all_categories = sorted(set(costs_by_category.keys()) | set(expenses_by_category.keys()))
    
    # Get values for each category
    cost_values = [costs_by_category.get(cat, 0) for cat in all_categories]
    expense_values = [expenses_by_category.get(cat, 0) for cat in all_categories]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(all_categories))
    width = 0.35
    
    bars1 = ax.bar([i - width/2 for i in x], cost_values, width, label='Costos', color='#3498db')
    bars2 = ax.bar([i + width/2 for i in x], expense_values, width, label='Gastos', color='#e74c3c')
    
    ax.set_xlabel('Categoría')
    ax.set_ylabel('Monto ($)')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(all_categories, rotation=45, ha='right')
    ax.legend()
    
    # Add value labels on bars
    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(f'${height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)
    
    return buf.getvalue()


def create_trend_line_chart(
    data_points: list[dict],
    x_field: str = "date",
    y_field: str = "amount",
    title: str = "Tendencia",
    label: str = "Valor",
) -> bytes:
    """Create a line chart showing trends over time."""
    dates = [dp[x_field] for dp in data_points]
    values = [dp[y_field] for dp in data_points]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(dates, values, marker='o', linewidth=2, markersize=4, color='#2ecc71', label=label)
    ax.fill_between(dates, values, alpha=0.3, color='#2ecc71')
    
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Monto ($)')
    ax.set_title(title)
    ax.legend()
    
    # Format x-axis for dates
    if isinstance(dates[0], datetime):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
    
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)
    
    return buf.getvalue()


def create_pie_chart(
    data: dict[str, float],
    title: str = "Distribución",
) -> bytes:
    """Create a pie chart showing distribution."""
    labels = list(data.keys())
    values = list(data.values())
    
    # Colors
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    wedges, texts, autotexts = ax.pie(
        values, 
        labels=labels, 
        autopct='%1.1f%%',
        colors=colors[:len(values)],
        startangle=90,
        explode=[0.02] * len(values),
    )
    
    # Style
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)
    
    return buf.getvalue()


def create_summary_comparison_chart(
    total_costs: float,
    total_expenses: float,
    title: str = "Resumen: Costos vs Gastos",
) -> bytes:
    """Create a simple comparison bar chart for totals."""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    categories = ['Costos Totales', 'Gastos Totales']
    values = [total_costs, total_expenses]
    colors = ['#3498db', '#e74c3c']
    
    bars = ax.bar(categories, values, color=colors, width=0.5)
    
    # Add value labels
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.annotate(f'${value:,.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold')
    
    ax.set_ylabel('Monto ($)')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add difference annotation
    diff = total_costs - total_expenses
    diff_text = f"Diferencia: ${abs(diff):,.2f}"
    if diff > 0:
        diff_text += " (Costos > Gastos)"
    elif diff < 0:
        diff_text += " (Gastos > Costos)"
    
    ax.annotate(diff_text,
                xy=(0.5, 0.95),
                xycoords='axes fraction',
                ha='center',
                fontsize=11,
                style='italic')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)
    
    return buf.getvalue()
