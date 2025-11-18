"""Test the new branch and commit format"""
from agents.staging_deployer import StagingDeployerAgent

agent = StagingDeployerAgent()

# Test plan with single upgrade
plan_single = {
    'dependencies': {
        'express': {
            'current_version': '4.16.0',
            'target_version': '5.0.0',
            'action': 'upgrade',
            'risk': 'high'
        }
    },
    'project_type': 'nodejs',
    'migration_strategy': {'total_phases': 1},
    'overall_risk': 'high'
}

# Test plan with multiple upgrades
plan_multi = {
    'dependencies': {
        'express': {
            'current_version': '4.16.0',
            'target_version': '5.0.0',
            'action': 'upgrade',
            'risk': 'high'
        },
        'cors': {
            'current_version': '2.8.4',
            'target_version': '2.8.5',
            'action': 'upgrade',
            'risk': 'low'
        }
    },
    'project_type': 'nodejs',
    'migration_strategy': {'total_phases': 1},
    'overall_risk': 'medium'
}

validation = {'status': 'success'}

print("=" * 80)
print("BRANCH NAME FORMAT")
print("=" * 80)
print(f"Branch: {agent._generate_branch_name(plan_single)}")
print()

print("=" * 80)
print("COMMIT MESSAGE - SINGLE UPGRADE")
print("=" * 80)
print(agent._generate_commit_message(plan_single, validation))
print()

print("=" * 80)
print("COMMIT MESSAGE - MULTIPLE UPGRADES")
print("=" * 80)
print(agent._generate_commit_message(plan_multi, validation))
