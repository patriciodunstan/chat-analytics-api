"""Chart generation for reports."""
import io
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def create_bar_chart(
    data: dict[str, float],
    title: str = "Gráfico de Barras",
    color: str = "#3498db",
) -> bytes:
    """Create a bar chart from data dictionary."""
    labels = list(data.keys())
    values = list(data.values())

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(labels, values, color=color, width=0.5)

    ax.set_ylabel('Valor')
    ax.set_title(title)
    ax.set_xticklabels(labels, rotation=45, ha='right')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

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
    ax.set_ylabel('Valor')
    ax.set_title(title)
    ax.legend()

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