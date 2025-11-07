# Legacy Express.js Application

This is a sample Express.js application with **intentionally outdated dependencies** for testing the AI Code Modernizer.

## Current Dependencies (Outdated)

- **Express**: 4.16.0 (Released: 2017) → Latest: 5.0.0+
- **body-parser**: 1.18.3 (Now built into Express)
- **cors**: 2.8.4 → Latest: 2.8.5+
- **dotenv**: 6.0.0 → Latest: 16.0.0+
- **morgan**: 1.9.1 → Latest: 1.10.0+

## Known Issues with Current Versions

1. **Express 4.16.0**:
   - Missing security patches
   - No async/await error handling
   - Outdated body parsing

2. **body-parser 1.18.3**:
   - Deprecated as separate package
   - Now built into Express

3. **Security Vulnerabilities**:
   - Multiple CVEs in outdated versions
   - Missing critical security patches

## Expected Modernization

The Migration Planner Agent should:

1. **Identify Outdated Packages**:
   - Detect all packages are outdated
   - Flag security vulnerabilities

2. **Create Migration Strategy**:
   - Upgrade Express 4.16 → 5.0
   - Remove body-parser (use Express built-in)
   - Update other dependencies
   - Maintain API compatibility

3. **Handle Breaking Changes**:
   - Express 5.0 breaking changes
   - body-parser removal
   - Middleware signature changes

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /api/users` - List all users
- `GET /api/users/:id` - Get user by ID
- `POST /api/users` - Create new user
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user

## Installation (Manual Testing)

```bash
cd tests/sample_projects/express-app
npm install
npm start
```

## Testing Migration

```bash
# From backend directory
python agents/migration_planner.py --project tests/sample_projects/express-app
```

## Expected Migration Output

```json
{
  "dependencies": {
    "express": {
      "current": "4.16.0",
      "target": "5.0.0",
      "breaking_changes": ["..."],
      "risk": "medium"
    },
    "body-parser": {
      "current": "1.18.3",
      "action": "remove",
      "reason": "Built into Express 5.0"
    }
  },
  "strategy": {
    "phases": [
      {
        "name": "Update dependencies",
        "order": 1
      },
      {
        "name": "Remove body-parser",
        "order": 2
      },
      {
        "name": "Update middleware",
        "order": 3
      }
    ]
  }
}
```
