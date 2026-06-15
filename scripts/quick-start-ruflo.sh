#!/bin/bash
# Quick Start Guide - MetalMind SMCForge + Ruflo Integration

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 MetalMind SMCForge + Ruflo Quick Start"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 1: Check prerequisites
echo "📋 Step 1: Checking prerequisites..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Install from https://nodejs.org"
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

if ! command -v npm &> /dev/null; then
    echo "❌ npm is required"
    exit 1
fi
echo "✅ npm found: $(npm --version)"

echo ""
echo "🔧 Step 2: Install Ruflo globally..."
npm install -g ruflo@latest

echo ""
echo "📦 Step 3: Install frontend dependencies..."
cd frontend-next
npm install
cd ..

echo ""
echo "⚙️ Step 4: Initialize Ruflo..."
npx ruflo@latest init --skip-wizard

echo ""
echo "🔌 Step 5: Register Ruflo MCP Server..."
echo "⚠️  Copy this command and run in Claude Code Terminal:"
echo ""
echo "   claude mcp add ruflo -- npx ruflo@latest mcp start"
echo ""

echo ""
echo "✅ Setup Complete!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📚 What's Next?"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Start the development server:"
echo "   cd frontend-next && npm run dev"
echo ""
echo "2. Start the Ruflo daemon:"
echo "   ruflo daemon start"
echo ""
echo "3. View the Ruflo web UI:"
echo "   Open http://localhost:3001"
echo ""
echo "4. View the Goal Planner UI:"
echo "   Open http://localhost:3002"
echo ""
echo "5. Check agent status:"
echo "   ruflo agents list"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📖 Documentation"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Main Integration Guide:"
echo "   cat RUFLO_INTEGRATION.md"
echo ""
echo "Ruflo Official Docs:"
echo "   https://github.com/ruvnet/ruflo"
echo ""
echo "Your Agents:"
echo "   - signal-analyzer (analyzes real-time signals)"
echo "   - backtest-executor (runs strategy backtests)"
echo "   - risk-monitor (monitors portfolio risk)"
echo "   - performance-tracker (tracks strategy performance)"
echo "   - data-curator (validates data quality)"
echo ""
echo "═══════════════════════════════════════════════════════════════"
