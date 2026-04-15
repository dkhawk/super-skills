# Gemini Skill Manager (GSM)

Gemini Skill Manager (GSM) is a catalog-driven CLI tool for managing skills for Gemini agents. It allows you to track, install, and update skills from a centralized JSON catalog, making it easier to manage complex agent environments.

This tool is designed for both human users and AI agents (LLMs) to orchestrate skill lifecycles.

## For LLMs (Agent Skill Definition)

If you are an LLM attempting to use this tool, here is the capability definition:

- **Purpose**: Manage lifecycle of Gemini agent skills.
- **Catalog File**: `skills_catalog.json` in the same directory.
- **Executable**: `./gsm.py`

### Commands

- `list`: Lists all skills in the catalog with their installation status and description.
- `add <id> <url> [--path <path>] [--description <description>]`: Adds a new skill to the catalog.
- `install <id>`: Installs a skill or a super-skill bundle by ID.
- `update`: Updates all currently installed skills that are present in the catalog.

## For Users

### Installation

Ensure you have the `gemini` CLI installed and accessible in your path.

Clone this repository or copy `gsm.py` and `skills_catalog.json` to your desired location.

Make the script executable:
```bash
chmod +x gsm.py
```

### Usage

#### List Skills
To see the catalog and what is installed:
```bash
./gsm.py list
```

#### Add a Skill
To add a new skill to track:
```bash
./gsm.py add my-skill https://github.com/user/repo.git --path subfolder --description "My awesome skill"
```

#### Install a Skill or Bundle
To install a skill or a super-skill bundle by its ID:
```bash
./gsm.py install google-maps-3d-android
```

#### Update Skills
To update all skills that are currently installed and tracked in the catalog:
```bash
./gsm.py update
```

## Catalog Structure

The `skills_catalog.json` file maintains the state:

```json
{
  "skills": {
    "skill-id": {
      "url": "https://...",
      "path": "path/to/skill",
      "description": "Description"
    }
  },
  "super_skills": {
    "bundle-id": {
      "description": "Bundle Description",
      "skills": ["skill-id-1", "skill-id-2"]
    }
  }
}
```
