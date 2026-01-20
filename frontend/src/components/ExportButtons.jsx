import React from 'react';
import { Box, Button, ButtonGroup } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { saveAs } from 'file-saver';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

function ExportButtons({ data, type, filename }) {
  
  const exportToCSV = () => {
    if (type === 'backtest' && data) {
      // Export trades to CSV
      const trades = data.trades || [];
      const headers = ['Entry Time', 'Exit Time', 'Entry Price', 'Exit Price', 'Result', 'P&L USD', 'P&L %'];
      
      let csvContent = headers.join(',') + '\n';
      
      trades.forEach(trade => {
        const row = [
          new Date(trade.entry_time).toLocaleString(),
          new Date(trade.exit_time).toLocaleString(),
          trade.entry_price.toFixed(2),
          trade.exit_price.toFixed(2),
          trade.hit_tp ? 'TP' : trade.hit_sl ? 'SL' : 'TO',
          trade.pnl_usd.toFixed(2),
          (trade.pnl_pct * 100).toFixed(2)
        ];
        csvContent += row.join(',') + '\n';
      });
      
      // Add summary section
      csvContent += '\n\nSummary\n';
      csvContent += `Total Return,${data.summary.total_return_pct.toFixed(2)}%\n`;
      csvContent += `Win Rate,${(data.summary.win_rate * 100).toFixed(2)}%\n`;
      csvContent += `Total Trades,${data.summary.n_trades}\n`;
      csvContent += `Profit Factor,${data.summary.profit_factor.toFixed(2)}\n`;
      csvContent += `Sharpe Ratio,${data.summary.sharpe_ratio.toFixed(2)}\n`;
      csvContent += `Max Drawdown,${data.summary.max_drawdown_pct.toFixed(2)}%\n`;
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      saveAs(blob, `${filename || 'backtest_results'}.csv`);
    } else if (type === 'shap' && data) {
      // Export SHAP feature importance
      const features = data.feature_importance || [];
      const headers = ['Rank', 'Feature', 'Importance'];
      
      let csvContent = headers.join(',') + '\n';
      
      features.forEach((feat, idx) => {
        csvContent += `${idx + 1},${feat.feature},${(feat.importance * 100).toFixed(2)}%\n`;
      });
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      saveAs(blob, `${filename || 'shap_analysis'}.csv`);
    }
  };

  const exportToPDF = () => {
    const doc = new jsPDF();
    
    if (type === 'backtest' && data) {
      // Title
      doc.setFontSize(20);
      doc.text('Backtest Results Report', 14, 20);
      
      doc.setFontSize(12);
      doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);
      
      // Summary Metrics
      doc.setFontSize(16);
      doc.text('Performance Summary', 14, 45);
      
      doc.setFontSize(12);
      const summary = [
        ['Metric', 'Value'],
        ['Total Return', `+${data.summary.total_return_pct.toFixed(2)}%`],
        ['Total Return (USD)', `$${data.summary.total_return_usd.toFixed(2)}`],
        ['Win Rate', `${(data.summary.win_rate * 100).toFixed(2)}%`],
        ['Total Trades', data.summary.n_trades.toString()],
        ['Profit Factor', data.summary.profit_factor.toFixed(2)],
        ['Sharpe Ratio', data.summary.sharpe_ratio.toFixed(2)],
        ['Max Drawdown', `${data.summary.max_drawdown_pct.toFixed(2)}%`],
        ['Avg Win', `$${data.summary.avg_win.toFixed(2)}`],
        ['Avg Loss', `$${data.summary.avg_loss.toFixed(2)}`]
      ];
      
      autoTable(doc, {
        head: [summary[0]],
        body: summary.slice(1),
        startY: 50,
        theme: 'grid',
        headStyles: { fillColor: [102, 126, 234] }
      });
      
      // Session Performance
      doc.addPage();
      doc.setFontSize(16);
      doc.text('Session Performance', 14, 20);
      
      const sessionData = Object.entries(data.session_performance).map(([session, stats]) => [
        session,
        stats.trades.toString(),
        `$${stats.total_pnl.toFixed(2)}`,
        `$${stats.avg_pnl.toFixed(2)}`,
        `${(stats.win_rate * 100).toFixed(1)}%`
      ]);
      
      autoTable(doc, {
        head: [['Session', 'Trades', 'Total P&L', 'Avg P&L', 'Win Rate']],
        body: sessionData,
        startY: 30,
        theme: 'grid',
        headStyles: { fillColor: [102, 126, 234] }
      });
      
      // Recent Trades
      doc.addPage();
      doc.setFontSize(16);
      doc.text('Recent Trades (Last 20)', 14, 20);
      
      const trades = data.trades.slice(-20).reverse();
      const tradeData = trades.map(trade => [
        new Date(trade.entry_time).toLocaleDateString(),
        `$${trade.entry_price.toFixed(2)}`,
        `$${trade.exit_price.toFixed(2)}`,
        trade.hit_tp ? 'TP' : trade.hit_sl ? 'SL' : 'TO',
        `$${trade.pnl_usd.toFixed(2)}`
      ]);
      
      autoTable(doc, {
        head: [['Entry Date', 'Entry Price', 'Exit Price', 'Result', 'P&L']],
        body: tradeData,
        startY: 30,
        theme: 'grid',
        headStyles: { fillColor: [102, 126, 234] },
        styles: { fontSize: 9 }
      });
      
      doc.save(`${filename || 'backtest_report'}.pdf`);
      
    } else if (type === 'shap' && data) {
      // SHAP PDF Report
      doc.setFontSize(20);
      doc.text('SHAP Feature Importance', 14, 20);
      
      doc.setFontSize(12);
      doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);
      
      doc.setFontSize(16);
      doc.text('Top 10 Features', 14, 45);
      
      const features = data.feature_importance.slice(0, 10);
      const featureData = features.map((feat, idx) => [
        (idx + 1).toString(),
        feat.feature.replace(/_/g, ' '),
        `${(feat.importance * 100).toFixed(2)}%`
      ]);
      
      autoTable(doc, {
        head: [['Rank', 'Feature', 'Importance']],
        body: featureData,
        startY: 50,
        theme: 'grid',
        headStyles: { fillColor: [102, 126, 234] }
      });
      
      doc.save(`${filename || 'shap_report'}.pdf`);
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
      <ButtonGroup variant="contained" size="small">
        <Button 
          onClick={exportToCSV}
          startIcon={<DownloadIcon />}
          sx={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%)'
            }
          }}
        >
          Export CSV
        </Button>
        <Button 
          onClick={exportToPDF}
          startIcon={<PictureAsPdfIcon />}
          sx={{ 
            background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #d97de0 0%, #d94a5f 100%)'
            }
          }}
        >
          Export PDF
        </Button>
      </ButtonGroup>
    </Box>
  );
}

export default ExportButtons;
