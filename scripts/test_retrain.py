"""Test orchestrator retrain integration."""
import sys
sys.path.insert(0, 'C:/Users/Talha/ml-signals')

from etl.orchestrator import PipelineOrchestrator

orch = PipelineOrchestrator()

print('=' * 60)
print('TEST: Orchestrator.run_retrain()')
print('=' * 60)

# Test retrain with minimal trials
print('\nRunning retrain for gold (2 trials)...')
result = orch.run_retrain('gold', trials=2)

print(f'\nResult:')
print(f'  Success: {result["success"]}')
print(f'  Accuracy: {result.get("accuracy", "N/A")}')
print(f'  Model path: {result.get("model_path", "N/A")}')
if result.get('error'):
    print(f'  Error: {result["error"]}')

# Check health
health = orch.health.get_status()
print(f'\nHealth:')
print(f'  Last retrain: {health["last_retrain"]}')
print(f'  Retrain status: {health["retrain_status"]}')
print(f'  Failures: {health["consecutive_failures"]}')

# Check backups
backups = orch.versioning.list_backups()
print(f'\nBackups: {len(backups)}')
for b in backups:
    print(f'  {b["name"]} ({b["size_mb"]} MB)')

print('\n' + '=' * 60)
print('TEST COMPLETE')
print('=' * 60)
