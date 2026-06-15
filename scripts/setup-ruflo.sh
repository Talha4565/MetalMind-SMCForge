#!/bin/bash
# Ruflo Integration Setup Script for MetalMind SMCForge
# This script initializes Ruflo agent orchestration with trading-specific agents

set -e

echo "🚀 Initializing Ruflo for MetalMind SMCForge..."

# Check if Ruflo is installed
if ! command -v ruflo &> /dev/null; then
    echo "📦 Installing Ruflo globally..."
    npm install -g ruflo@latest
fi

# Initialize Ruflo in non-interactive mode
echo "⚙️ Setting up Ruflo configuration..."
npx ruflo@latest init --skip-wizard

# Register Ruflo as MCP server in Claude Code
echo "🔌 Registering Ruflo MCP server..."
claude mcp add ruflo -- npx ruflo@latest mcp start

# Install core Ruflo plugins
echo "📦 Installing Ruflo plugins..."
/plugin install ruflo-core@ruflo
/plugin install ruflo-swarm@ruflo
/plugin install ruflo-autopilot@ruflo
/plugin install ruflo-federation@ruflo

# Create Ruflo hooks for auto-learning
echo "🧠 Setting up auto-learning hooks..."
mkdir -p .claude-flow/hooks

# Create post-task learning hook
cat > .claude-flow/hooks/post-task.sh << 'EOF'
#!/bin/bash
# Post-task hook: Learn from successful patterns
TASK_RESULT=$1
TASK_ID=$2

if [ "$TASK_RESULT" = "success" ]; then
    echo "✅ Learning from task: $TASK_ID"
    ruflo memory store --namespace="learned_patterns" \
        --key="$TASK_ID" \
        --value="$(cat)"
fi
EOF

chmod +x .claude-flow/hooks/post-task.sh

echo "✅ Ruflo initialization complete!"
echo ""
echo "📚 Next steps:"
echo "   1. cd ml-signals && npx ruflo init wizard (for interactive setup)"
echo "   2. Configure your trading agents in .claude/agents/"
echo "   3. Start the Ruflo web UI: npx ruflo web start"
echo "   4. View live agents at: http://localhost:3001"
echo ""
echo "🔗 Resources:"
echo "   - Web UI: https://flo.ruv.io"
echo "   - Goal Planner: https://goal.ruv.io"
echo "   - Docs: https://github.com/ruvnet/ruflo"
