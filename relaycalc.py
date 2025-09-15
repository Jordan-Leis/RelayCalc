#!/usr/bin/env python3
"""RelayCalc: compute relay settings and generate reports.

This script reads transmission line and transformer data from a CSV file,
calculates overcurrent relay pickup values, simulates a simple short-circuit
scenario, stores results in a SQLite database, plots current vs. time curves,
and generates a PDF report containing the results and plot.

Usage:
    python relaycalc.py input.csv output.pdf

The script saves results to ``relaycalc.db`` in the current directory.
"""
from __future__ import annotations

import argparse
import csv
import os
import sqlite3
from dataclasses import dataclass
from typing import List

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet

CONSTANT = 10000  # I^2 t constant for trip time calculation
DB_NAME = "relaycalc.db"


@dataclass
class EquipmentRecord:
    """Container for equipment data and calculated results."""

    line_id: str
    voltage_kv: float
    current_a: float
    transformer_mva: float
    pickup: float
    fault_current: float
    trip_time: float


def read_csv(path: str) -> List[EquipmentRecord]:
    """Read equipment data from a CSV file.

    Args:
        path: Path to the CSV file with columns Line_ID, Voltage_kV,
            Current_A, Transformer_MVA.

    Returns:
        A list of :class:`EquipmentRecord` with computed fields.
    """
    records: List[EquipmentRecord] = []
    with open(path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            current = float(row["Current_A"])
            pickup = 1.2 * current
            fault_current = current * 10
            trip_time = CONSTANT / (fault_current ** 2)
            records.append(
                EquipmentRecord(
                    line_id=row["Line_ID"],
                    voltage_kv=float(row["Voltage_kV"]),
                    current_a=current,
                    transformer_mva=float(row["Transformer_MVA"]),
                    pickup=pickup,
                    fault_current=fault_current,
                    trip_time=trip_time,
                )
            )
    return records


def save_to_db(records: List[EquipmentRecord], db_path: str = DB_NAME) -> None:
    """Save calculated records to a SQLite database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS relay_results (
            Line_ID TEXT,
            Voltage_kV REAL,
            Current_A REAL,
            Transformer_MVA REAL,
            Pickup REAL,
            Fault_Current REAL,
            Trip_Time REAL
        )
        """
    )
    cur.executemany(
        """
        INSERT INTO relay_results (
            Line_ID, Voltage_kV, Current_A, Transformer_MVA, Pickup,
            Fault_Current, Trip_Time
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r.line_id,
                r.voltage_kv,
                r.current_a,
                r.transformer_mva,
                r.pickup,
                r.fault_current,
                r.trip_time,
            )
            for r in records
        ],
    )
    conn.commit()
    conn.close()


def plot_current_time(records: List[EquipmentRecord], path: str) -> None:
    """Plot current vs. time curves and save to ``path``."""
    plt.figure()
    for rec in records:
        currents = [rec.pickup, rec.fault_current]
        times = [CONSTANT / (i ** 2) for i in currents]
        plt.plot(times, currents, label=rec.line_id)
    plt.xlabel("Time (s)")
    plt.ylabel("Current (A)")
    plt.title("Current vs. Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def build_pdf(records: List[EquipmentRecord], plot_path: str, output_pdf: str) -> None:
    """Generate a PDF report with a data table, fault simulation, and plot."""
    doc = SimpleDocTemplate(output_pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Relay Calculation Report", styles["Title"]))
    elements.append(Spacer(1, 0.2 * inch))

    # Table of equipment data
    data = [[
        "Line ID",
        "Voltage (kV)",
        "Current (A)",
        "Transformer (MVA)",
        "Pickup (A)",
        "Fault Current (A)",
        "Trip Time (s)",
    ]]
    for r in records:
        data.append([
            r.line_id,
            f"{r.voltage_kv:.2f}",
            f"{r.current_a:.2f}",
            f"{r.transformer_mva:.2f}",
            f"{r.pickup:.2f}",
            f"{r.fault_current:.2f}",
            f"{r.trip_time:.4f}",
        ])

    table = Table(data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("Current vs. Time Plot", styles["Heading2"]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Image(plot_path, width=6 * inch, height=4 * inch))

    doc.build(elements)


def main() -> None:
    parser = argparse.ArgumentParser(description="Relay calculation tool")
    parser.add_argument("input_csv", help="Input CSV file with equipment data")
    parser.add_argument("output_pdf", help="Output PDF report")
    args = parser.parse_args()

    records = read_csv(args.input_csv)
    save_to_db(records)

    plot_path = "relay_plot.png"
    plot_current_time(records, plot_path)
    try:
        build_pdf(records, plot_path, args.output_pdf)
    finally:
        if os.path.exists(plot_path):
            os.remove(plot_path)


if __name__ == "__main__":
    main()
