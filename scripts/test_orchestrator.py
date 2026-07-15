"""Test orchestrator integration live."""
import sys
sys.path.insert(0, 'C:/Users/Talha/ml-signals')

from etl.orchestrator import PipelineOrchestrator

orch = PipelineOrchestrator()

print('=' * 60)
print('LIVE INTEGRATION TEST: Orchestrator')
print('=' * 60)

# Test 1: Freshness check
print('\n1. Freshness check:')
for asset in ['gold', 'silver']:
    fresh = orch.freshness.check(asset)
    status = 'FRESH' if fresh['is_fresh'] else 'STALE'
    print(f'   {asset.upper()}: {status} ({fresh["age_hours"]}h old, {fresh["rows"]} rows)')

# Test 2: Health status
print('\n2. Health status (before update):')
health = orch.health.get_status()
print(f'   Last update: {health["last_update"]}')
print(f'   Update status: {health["update_status"]}')
print(f'   Failures: {health["consecutive_failures"]}')

# Test 3: Run update
print('\n3. Running update for gold...')
result = orch.run_update('gold')
print(f'   Success: {result["success"]}')
print(f'   Records added: {result["records_added"]}')
if result.get('freshness'):
    print(f'   Freshness: {result["freshness"]["message"]}')
if result.get('error'):
    print(f'   Error: {result["error"]}')

# Test 4: Health status after update
print('\n4. Health status (after update):')
health = orch.health.get_status()
print(f'   Last update: {health["last_update"]}')
print(f'   Update status: {health["update_status"]}')
print(f'   Failures: {health["consecutive_failures"]}')

# Test 5: Freshness after update
print('\n5. Freshness after update:')
for asset in ['gold', 'silver']:
    fresh = orch.freshness.check(asset)
    status = 'FRESH' if fresh['is_fresh'] else 'STALE'
    print(f'   {asset.upper()}: {status} ({fresh["age_hours"]}h old)')

# Test 6: Model backups
print('\n6. Model backups:')
backups = orch.versioning.list_backups()
if backups:
    for b in backups:
        print(f'   {b["name"]} ({b["size_mb"]} MB)')
else:
    print('   No backups yet')

# Test 7: Dashboard data
print('\n7. Dashboard data:')
dashboard = orch.get_dashboard_data()
print(f'   Health: {dashboard["health"]["update_status"]}')
print(f'   Gold fresh: {dashboard["freshness"]["gold"]["is_fresh"]}')
print(f'   Silver fresh: {dashboard["freshness"]["silver"]["is_fresh"]}')
print(f'   Backups: {len(dashboard["backups"])}')

print('\n' + '=' * 60)
print('ALL TESTS COMPLETE')
print('=' * 60)
