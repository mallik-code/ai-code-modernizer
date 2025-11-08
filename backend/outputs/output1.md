python -m agents.migration_planner
================================================================================
MIGRATION PLANNER AGENT - STANDALONE TEST
================================================================================

Test Project: C:\projects\ai-code-modernizer\backend\tests\sample_projects\express-app
Testing with: package.json

1. Creating Migration Planner Agent...
2025-11-08T01:15:52.891345Z [info     ] mcp_config_loaded              servers=['github', 'filesystem']
   Provider: gemini
   Model: genai.GenerativeModel(
    model_name='models/gemini-2.0-flash',
    generation_config={},
    safety_settings={},
    tools=None,
    system_instruction=None,
    cached_content=None
)

2. Analyzing dependencies...
2025-11-08T01:15:52.892843Z [info     ] starting_migration_analysis    project_path=C:\projects\ai-code-modernizer\backend\tests\sample_projects\express-app
2025-11-08T01:15:52.894629Z [info     ] dependency_file_read           file=C:\projects\ai-code-modernizer\backend\tests\sample_projects\express-app\package.json size=658
2025-11-08T01:15:52.894749Z [info     ] dependencies_detected          dependency_count=6 file=C:\projects\ai-code-modernizer\backend\tests\sample_projects\express-app\package.json project_type=nodejs
2025-11-08T01:15:52.894836Z [info     ] sending_to_llm                 prompt_length=1472
PROMPT SENT TO LLM:
Analyze these NODEJS dependencies and create a migration plan.

PROJECT TYPE: nodejs
DEPENDENCY FILE: C:\projects\ai-code-modernizer\backend\tests\sample_projects\express-app\package.json

CURRENT DEPENDENCIES:
{
  "express": "4.16.0",
  "body-parser": "1.18.3",
  "cors": "2.8.4",
  "dotenv": "6.0.0",
  "morgan": "1.9.1",
  "nodemon": "1.18.4"
}

TASKS:
1. For each dependency:
   - Determine if it's outdated (check major/minor versions)
   - Identify the latest stable version
   - Research known breaking changes between current and target version
   - Assess migration risk (low/medium/high)
   - Determine action: upgrade, remove (if deprecated), or keep

2. Create a phased migration strategy:
   - Phase 1: Low-risk updates (patch versions, minor updates with no breaking changes)
   - Phase 2: Medium-risk updates (minor updates with small breaking changes)
   - Phase 3: High-risk updates (major version changes, deprecated package removal)

3. Provide:
   - Rollback plan for each phase
   - Estimated time per phase
   - Overall recommendations
   - Overall risk assessment

IMPORTANT:
- For Node.js: Check if body-parser is used (deprecated in Express 5+)
- For Python: Check for packages with known security vulnerabilities
- Consider dependency conflicts (e.g., package A requires old version of package B)
- Be specific about breaking changes

OUTPUT FORMAT: Return ONLY valid JSON matching the specified schema. No markdown, no explanations outside JSON.
==================================================
2025-11-08T01:15:52.895581Z [info     ] thinking                       llm_provider=gemini prompt_preview='Analyze these NODEJS dependencies and create a migration plan.\n\nPROJECT TYPE: nodejs\nDEPENDENCY FILE'
RESPONSE RECEIVED FROM LLM:
```json
{
  "dependencies_analysis": [
    {
      "name": "express",
      "current_version": "4.16.0",
      "latest_version": "4.19.2",
      "outdated": true,
      "breaking_changes": "Several minor breaking changes and feature additions between 4.16.0 and 4.19.x. Most relate to new features and edge cases. Middleware handling and request/response objects largely remain compatible. Potential issues with deprecated features that have been removed.",
      "migration_risk": "Medium",
      "action": "upgrade"
    },
    {
      "name": "body-parser",
      "current_version": "1.18.3",
      "latest_version": "1.20.2",
      "outdated": true,
      "breaking_changes": "Minor breaking changes related to default options and parsing behavior. Express 4.16+ includes body-parser functionality, so consider removing if not using custom options. Express 5+ integrates body-parser functionality directly, making this package redundant.",
      "migration_risk": "Medium",
      "action": "upgrade"
    },
    {
      "name": "cors",
      "current_version": "2.8.4",
      "latest_version": "2.8.5",
      "outdated": true,
      "breaking_changes": "Minimal breaking changes. Primarily bug fixes and minor feature additions. Should be a safe upgrade.",
      "migration_risk": "Low",
      "action": "upgrade"
    },
    {
      "name": "dotenv",
      "current_version": "6.0.0",
      "latest_version": "16.4.5",
      "outdated": true,
      "breaking_changes": "Significant changes in how `.env` files are parsed and handled. Environment variable precedence might be different. Check for changes in how the package handles special characters or edge cases in the .env file.",
      "migration_risk": "Medium",
      "action": "upgrade"
    },
    {
      "name": "morgan",
      "current_version": "1.9.1",
      "latest_version": "1.10.0",
      "outdated": true,
      "breaking_changes": "Minor breaking changes. Primarily bug fixes and improvements to logging format. Custom format strings may need adjustment.", 
      "migration_risk": "Low",
      "action": "upgrade"
    },
    {
      "name": "nodemon",
      "current_version": "1.18.4",
      "latest_version": "3.1.0",
      "outdated": true,
      "breaking_changes": "Significant changes in configuration options, CLI arguments, and restart behavior. Check for changes in how nodemon handles file watching and process management. Consider changes in configuration file format.",
      "migration_risk": "Medium",
      "action": "upgrade"
    }
  ],
  "migration_strategy": {
    "phase_1": {
      "description": "Low-risk updates: cors and morgan",
      "dependencies": ["cors", "morgan"],
      "rollback_plan": "Revert package.json and package-lock.json to previous state. Reinstall dependencies using `npm install` or `yarn install`.",    
      "estimated_time": "1 hour"
    },
    "phase_2": {
      "description": "Medium-risk updates: dotenv and nodemon",
      "dependencies": ["dotenv", "nodemon"],
      "rollback_plan": "Revert package.json and package-lock.json to previous state. Reinstall dependencies using `npm install` or `yarn install`. Inspect .env files and nodemon configuration for unexpected changes. Potentially revert to older versions of these packages if major issues arise.",
      "estimated_time": "4 hours"
    },
    "phase_3": {
      "description": "High-risk updates: express and body-parser. Evaluate if body-parser is still needed.",
      "dependencies": ["express", "body-parser"],
      "rollback_plan": "Revert package.json and package-lock.json to previous state. Reinstall dependencies using `npm install` or `yarn install`. Thoroughly test all API endpoints and middleware functionality. Inspect request handling and response formats for unexpected changes. If body-parser removal causes issues, revert and retain the package.",
      "estimated_time": "8 hours"
    }
  },
  "overall_recommendations": [
    "Perform updates in a development environment first.",
    "Thoroughly test all functionality after each phase.",
    "Pay close attention to breaking changes and adjust code accordingly.",
    "Consider using a version control system (e.g., Git) to track changes and facilitate rollbacks.",
    "Review express middleware and routing after express update.",
    "Review error handling after express update.",
    "Evaluate if body-parser is necessary before upgrading express and potentially remove it."
  ],
  "overall_risk_assessment": "Medium. The project has outdated dependencies, some with potential breaking changes. Careful planning, testing, and a well-defined rollback plan are crucial for a successful migration.",
  "dependency_conflicts": "No immediate dependency conflicts detected based on the provided package.json. However, a full dependency audit after each upgrade is recommended to identify any hidden conflicts."
}
```
==================================================
2025-11-08T01:16:03.063364Z [info     ] llm_response_received          response_length=4866
2025-11-08T01:16:03.063586Z [warning  ] missing_field_in_plan          field=dependencies
2025-11-08T01:16:03.063749Z [info     ] migration_plan_complete        cost_usd=0.000622 overall_risk=medium phases=3 total_dependencies=0

================================================================================
RESULTS
================================================================================

Project Type: NODEJS
Analysis Date: 2025-11-08T06:46:03.063564
Overall Risk: MEDIUM
Estimated Time: See individual phases

--- DEPENDENCIES (0) ---

--- MIGRATION STRATEGY (3 phases) ---

Phase 1: Low-risk updates: cors and morgan
  Dependencies: cors, morgan
  Time: 1 hour
  Description: Low-risk updates: cors and morgan

Phase 2: Medium-risk updates: dotenv and nodemon
  Dependencies: dotenv, nodemon
  Time: 4 hours
  Description: Medium-risk updates: dotenv and nodemon

Phase 3: High-risk updates: express and body-parser. Evaluate if body-parser is still needed.
  Dependencies: express, body-parser
  Time: 8 hours
  Description: High-risk updates: express and body-parser. Evaluate if body-parser is still needed.

--- RECOMMENDATIONS (7) ---
1. Perform updates in a development environment first.
2. Thoroughly test all functionality after each phase.
3. Pay close attention to breaking changes and adjust code accordingly.
4. Consider using a version control system (e.g., Git) to track changes and facilitate rollbacks.
5. Review express middleware and routing after express update.
6. Review error handling after express update.
7. Evaluate if body-parser is necessary before upgrading express and potentially remove it.

================================================================================
COST REPORT
================================================================================
Provider: gemini
Model: genai.GenerativeModel(
    model_name='models/gemini-2.0-flash',
    generation_config={},
    safety_settings={},
    tools=None,
    system_instruction=None,
    cached_content=None
)
Total Tokens: 721
  Input: 193
  Output: 528
Total Cost: $0.0006

================================================================================
TEST COMPLETE
================================================================================
2025-11-08T01:16:03.065928Z [info     ] cleaning_up_servers            count=0
(.venv) PS C:\projects\ai-code-modernizer\backend> 