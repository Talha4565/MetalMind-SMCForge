"""Export backtest results to CSV and PDF formats."""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BacktestExporter:
    """Export backtest results to CSV and PDF."""

    def export_trades_csv(self, data: Dict[str, Any], output_path: str) -> bool:
        """Export trade log to CSV."""
        try:
            trades = data.get("trades", [])
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            if not trades:
                df = __import__("pandas").DataFrame()
                df.to_csv(path, index=False)
                return True

            df = __import__("pandas").DataFrame(trades)
            df.to_csv(path, index=False)
            logger.info(f"Exported {len(trades)} trades to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export trades CSV: {e}")
            return False

    def export_summary_csv(self, data: Dict[str, Any], output_path: str) -> bool:
        """Export summary metrics to CSV."""
        try:
            summary = data.get("summary", {})
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            df = __import__("pandas").DataFrame([summary])
            df.to_csv(path, index=False)
            logger.info(f"Exported summary to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export summary CSV: {e}")
            return False

    def export_equity_csv(self, data: Dict[str, Any], output_path: str) -> bool:
        """Export equity curve to CSV."""
        try:
            equity = data.get("equity_curve", [])
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            df = __import__("pandas").DataFrame(equity)
            df.to_csv(path, index=False)
            logger.info(f"Exported equity curve ({len(equity)} points) to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export equity CSV: {e}")
            return False

    def export_full_report_csv(self, data: Dict[str, Any], output_prefix: str) -> bool:
        """Export all three CSV files (trades, summary, equity)."""
        base = Path(output_prefix)
        results = [
            self.export_trades_csv(data, f"{base}_trades.csv"),
            self.export_summary_csv(data, f"{base}_summary.csv"),
            self.export_equity_csv(data, f"{base}_equity.csv"),
        ]
        return all(results)

    def export_pdf(self, data: Dict[str, Any], output_path: str) -> bool:
        """Export backtest report to PDF."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.units import inch

            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            doc = SimpleDocTemplate(str(path), pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            elements.append(Paragraph("MetalMind SMCForge — Backtest Report", styles["Title"]))
            elements.append(Spacer(1, 12))

            # Summary table
            summary = data.get("summary", {})
            if summary:
                elements.append(Paragraph("Performance Summary", styles["Heading2"]))
                summary_data = [["Metric", "Value"]]
                metric_labels = {
                    "n_trades": "Total Trades",
                    "win_rate": "Win Rate",
                    "avg_win": "Avg Win ($)",
                    "avg_loss": "Avg Loss ($)",
                    "profit_factor": "Profit Factor",
                    "total_return_usd": "Total Return ($)",
                    "total_return_pct": "Total Return (%)",
                    "max_drawdown_pct": "Max Drawdown (%)",
                    "sharpe_ratio": "Sharpe Ratio",
                    "sortino_ratio": "Sortino Ratio",
                    "calmar_ratio": "Calmar Ratio",
                }
                for key, label in metric_labels.items():
                    val = summary.get(key, "N/A")
                    if isinstance(val, float):
                        if "rate" in key or "pct" in key:
                            val = f"{val:.2%}" if "rate" in key else f"{val:.2f}%"
                        else:
                            val = f"{val:.2f}"
                    summary_data.append([label, str(val)])

                table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a9e6f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f2f5")]),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 20))

            # Trades table (last 20)
            trades = data.get("trades", [])
            if trades:
                elements.append(Paragraph(f"Trade Log ({len(trades)} total, showing last 20)", styles["Heading2"]))
                trade_data = [["Entry Time", "Entry Price", "Exit Time", "Exit Price", "PnL ($)", "Result"]]
                for t in trades[-20:]:
                    result = "WIN" if t.get("pnl_usd", 0) > 0 else "LOSS"
                    trade_data.append([
                        t.get("entry_time", "")[:16],
                        f"${t.get('entry_price', 0):.2f}",
                        t.get("exit_time", "")[:16],
                        f"${t.get('exit_price', 0):.2f}",
                        f"${t.get('pnl_usd', 0):.2f}",
                        result,
                    ])

                table = Table(trade_data, colWidths=[1.5 * inch, 1 * inch, 1.5 * inch, 1 * inch, 0.8 * inch, 0.7 * inch])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a9e6f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("ALIGN", (3, 0), (5, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f2f5")]),
                ]))
                elements.append(table)

            doc.build(elements)
            logger.info(f"Exported PDF report to {path}")
            return True

        except ImportError:
            logger.warning("reportlab not installed — falling back to text PDF")
            return self._export_pdf_fallback(data, output_path)
        except Exception as e:
            logger.error(f"Failed to export PDF: {e}")
            return self._export_pdf_fallback(data, output_path)

    def _export_pdf_fallback(self, data: Dict[str, Any], output_path: str) -> bool:
        """Fallback PDF using plain text if reportlab is not available."""
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=16)
            pdf.cell(200, 10, txt="MetalMind SMCForge - Backtest Report", ln=True, align="C")
            pdf.ln(10)

            summary = data.get("summary", {})
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 8, txt="Performance Summary", ln=True)
            pdf.set_font("Arial", size=10)
            for key, val in summary.items():
                if isinstance(val, float):
                    val = f"{val:.4f}"
                pdf.cell(200, 6, txt=f"  {key}: {val}", ln=True)

            pdf.ln(10)
            trades = data.get("trades", [])
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 8, txt=f"Trade Log ({len(trades)} trades)", ln=True)
            pdf.set_font("Arial", size=8)
            pdf.cell(200, 6, txt="  Entry -> Exit | PnL | Result", ln=True)
            for t in trades[-30:]:
                result = "WIN" if t.get("pnl_usd", 0) > 0 else "LOSS"
                line = f"  {t.get('entry_time','')[:16]} -> {t.get('exit_time','')[:16]} | ${t.get('pnl_usd',0):.2f} | {result}"
                pdf.cell(200, 5, txt=line, ln=True)

            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            pdf.output(str(path))
            logger.info(f"Exported PDF (fpdf) to {path}")
            return True
        except Exception as e:
            logger.error(f"PDF fallback also failed: {e}")
            return False
