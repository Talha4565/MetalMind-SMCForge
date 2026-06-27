---
name: claude-mem
description: Agent memory management skill for ml-signals. Provides guidelines for storing, retrieving, and sharing memory across trading signal agents. Use when agents need to persist context, share learnings, or maintain state across sessions.
---

# Claude Memory Management

Memory management skill for the ml-signals agent system. Enables agents to store, retrieve, and share persistent context across sessions and tasks.

## When to Use This Skill

Automatically activate for:
- Agent context persistence across sessions
- Cross-agent knowledge sharing
- Trading pattern memory
- Signal accuracy tracking
- Market condition caching

## Memory Architecture

### Namespaces

Organize memory by domain:

| Namespace | Purpose | Retention |
|-----------|---------|-----------|
| `signals:analysis` | Signal patterns, accuracy metrics | 7 days |
| `market:context` | Current market conditions | 24 hours |
| `backtest:results` | Historical performance | 30 days |
| `risk:alerts` | Risk events, thresholds | 7 days |
| `model:metrics` | Training metrics, drift | 14 days |

### Storage Patterns

```typescript
// Store signal analysis result
await agentOrchestrator.storeMemory(
  'signals:analysis',
  `signal_${asset}_${timestamp}`,
  {
    asset: 'XAUUSD',
    signal: 'BUY',
    confidence: 0.85,
    features: { rsi: 45.2, atr: 12.5 },
    outcome: 'pending'
  }
);

// Store market context
await agentOrchestrator.storeMemory(
  'market:context',
  `condition_${asset}`,
  {
    trend: 'uptrend',
    volatility: 'medium',
    volume_profile: 'accumulation',
    last_update: Date.now()
  }
);
```

### Retrieval Patterns

```typescript
// Search for similar past signals
const similarSignals = await agentOrchestrator.searchMemory(
  'signals:analysis',
  'BUY signal XAUUSD high confidence',
  10
);

// Get recent accuracy metrics
const accuracy = await agentOrchestrator.searchMemory(
  'signals:analysis',
  'signal outcome wins losses',
  5
);
```

## Agent Memory Responsibilities

### Signal Analyzer
- Store: signal predictions with features and confidence
- Retrieve: past signal outcomes for accuracy calculation
- Share: signal patterns with backtest-executor

### Backtest Executor
- Store: backtest results, strategy performance
- Retrieve: historical signal patterns for validation
- Share: performance metrics with risk-monitor

### Risk Monitor
- Store: risk events, threshold breaches
- Retrieve: current market conditions
- Share: risk alerts with signal-analyzer

### Data Curator
- Store: data quality metrics, anomalies
- Retrieve: data freshness, coverage gaps
- Share: data status with all agents

## Best Practices

1. **Use descriptive keys** — include asset, timestamp, or signal type
2. **Set appropriate retention** — don't keep stale data
3. **Share relevant context** — configure `shared_with` in agent definitions
4. **Include timestamps** — track when data was stored
5. **Limit search results** — use `limit` parameter to avoid overload

## Memory Cleanup

Memory with expired retention is automatically cleaned. For manual cleanup:

```typescript
// Check memory namespace size
const entries = await agentOrchestrator.searchMemory('signals:analysis', '*', 100);

// Store only recent entries
if (entries.length > 50) {
  // Keep only last 50 entries
}
```
