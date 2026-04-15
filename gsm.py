#!/usr/bin/env python3
"""
Gemini Skill Manager (GSM)

This script manages skills for Gemini agents. It maintains a catalog of skills
and allows listing, installing, and updating them.
"""

import argparse
import json
import os
import subprocess
import sys

CATALOG_FILE = "skills_catalog.json"

def load_catalog():
    """
    Loads the skills catalog from the JSON file.
    
    We use JSON because it is easy to read and write, and natively supported by Python.
    """
    if not os.path.exists(CATALOG_FILE):
        print(f"Error: Catalog file {CATALOG_FILE} not found.")
        sys.exit(1)
        
    try:
        with open(CATALOG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {CATALOG_FILE}: {e}")
        sys.exit(1)

def get_installed_skills():
    """
    Checks the filesystem directly at ~/.gemini/skills/ and ~/.gemini/antigravity/skills/
    to determine installed skills.
    """
    gemini_dir = os.path.expanduser("~/.gemini/skills")
    antigravity_dir = os.path.expanduser("~/.gemini/antigravity/skills")
    
    installed_skills = {}  # Dict: skill_name -> set of targets ('gemini', 'antigravity')
    
    def scan_dir(directory, target_name):
        if not os.path.exists(directory):
            return
        try:
            entries = os.listdir(directory)
            for entry in entries:
                entry_path = os.path.join(directory, entry)
                if os.path.isdir(entry_path) and os.path.exists(os.path.join(entry_path, 'SKILL.md')):
                    installed_skills.setdefault(entry, set()).add(target_name)
        except Exception as e:
            print(f"Warning: Could not list {target_name} directory: {e}")
            
    scan_dir(gemini_dir, 'gemini')
    scan_dir(antigravity_dir, 'antigravity')
    
    return installed_skills

def list_skills(catalog, installed_skills):
    """
    Lists all skills and super-skills in the catalog, showing their status.
    """
    print("--- Gemini & Antigravity Skills Catalog ---")
    print("\nIndividual Skills:")
    
    skills = catalog.get('skills', {})
    for skill_id, info in skills.items():
        path = info.get('path', '')
        folder_name = os.path.basename(path) if path else ''
        
        targets = installed_skills.get(skill_id, set())
        if not targets and folder_name:
            targets = installed_skills.get(folder_name, set())
            
        if targets:
            status = f"[INSTALLED ({', '.join(targets)})]"
        else:
            status = "[NOT INSTALLED]"
            
        desc = info.get('description', 'No description')
        print(f"  {status} {skill_id}: {desc}")
        
    print("\nSuper-Skills (Bundles):")
    super_skills = catalog.get('super_skills', {})
    for bundle_id, info in super_skills.items():
        desc = info.get('description', 'No description')
        contained_skills = info.get('skills', [])
        
        # Count installed skills in bundle (installed if in either target)
        installed_count = 0
        for s_id in contained_skills:
            skill_info = skills.get(s_id, {})
            s_path = skill_info.get('path', '')
            s_folder = os.path.basename(s_path) if s_path else ''
            
            targets = installed_skills.get(s_id, set())
            if not targets and s_folder:
                targets = installed_skills.get(s_folder, set())
                
            if targets:
                installed_count += 1
                
        total_count = len(contained_skills)
        status = f"[{installed_count}/{total_count} skills installed]"
        
        print(f"  {bundle_id}: {desc}")
        print(f"    Status: {status}")
        print(f"    Skills: {', '.join(contained_skills)}")

def add_skill(catalog, skill_id, url, path=None, description=None):
    """
    Adds a new skill to the catalog and saves it.
    
    This allows users to track new skills easily.
    """
    skills = catalog.setdefault('skills', {})
    
    if skill_id in skills:
        print(f"Warning: Skill {skill_id} already exists in catalog. Updating.")
        
    skills[skill_id] = {'url': url}
    if path:
        skills[skill_id]['path'] = path
    if description:
        skills[skill_id]['description'] = description
        
    try:
        with open(CATALOG_FILE, 'w') as f:
            json.dump(catalog, f, indent=2)
        print(f"Successfully added skill '{skill_id}' to catalog.")
    except Exception as e:
        print(f"Error saving catalog: {e}")

def install_skill(catalog, target_id, target_env='both'):
    """
    Installs a skill or a super-skill bundle manually by cloning and copying.
    
    This is more robust than 'gemini skills install' which failed to persist
    files reliably in this environment.
    """
    import shutil
    import tempfile
    
    skills = catalog.get('skills', {})
    super_skills = catalog.get('super_skills', {})
    
    if target_id in super_skills:
        print(f"Installing Super-Skill bundle: {target_id}")
        bundle = super_skills[target_id]
        for s_id in bundle.get('skills', []):
            install_skill(catalog, s_id, target_env)
        return
        
    if target_id not in skills:
        print(f"Error: ID '{target_id}' not found in skills or super_skills catalog.")
        return
        
    skill_info = skills[target_id]
    url = skill_info.get('url')
    path = skill_info.get('path')
    
    print(f"Installing skill: {target_id} from {url} to {target_env}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone the repo
            print(f"Cloning {url}...")
            subprocess.run(['git', 'clone', url, temp_dir], check=True)
            
            # Resolve source path
            src_path = temp_dir
            if path:
                src_path = os.path.join(temp_dir, path)
                
            if not os.path.exists(src_path):
                print(f"Error: Path {path} not found in repository.")
                return
                
            # Check for SKILL.md
            if not os.path.exists(os.path.join(src_path, 'SKILL.md')):
                print(f"Warning: SKILL.md not found at {src_path}. Proceeding anyway.")
                
            # Define target paths
            targets = []
            if target_env in ['both', 'gemini']:
                targets.append(os.path.expanduser(f"~/.gemini/skills/{target_id}"))
            if target_env in ['both', 'antigravity']:
                targets.append(os.path.expanduser(f"~/.gemini/antigravity/skills/{target_id}"))
                
            for target_path in targets:
                print(f"Copying to {target_path}...")
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(src_path, target_path)
                print(f"Successfully installed to {target_path}")
                
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
        except Exception as e:
            print(f"Error during installation: {e}")

def update_skills(catalog, installed_skills):
    """
    Updates all installed skills by re-installing them from their catalog source.
    """
    print("Updating installed skills...")
    skills = catalog.get('skills', {})
    
    for skill_id, targets in installed_skills.items():
        if skill_id in skills:
            # If it was in both or either, we update it there.
            # We can just use 'both' if it was in both, or the specific one.
            target_env = 'both' if len(targets) > 1 else list(targets)[0]
            print(f"\nUpdating {skill_id} in {target_env}...")
            install_skill(catalog, skill_id, target_env)
        else:
            print(f"\nSkipping {skill_id} - not found in catalog (cannot update source).")

def export_installed(filename, installed_skills):
    """
    Exports the list of installed skill names to a file.
    """
    try:
        with open(filename, 'w') as f:
            for skill_name in installed_skills:
                f.write(f"{skill_name}\n")
        print(f"Successfully exported installed skills to {filename}")
    except Exception as e:
        print(f"Error exporting skills: {e}")

def remove_from_file(filename):
    """
    Reads a file with skill names and removes them from both environments.
    """
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found.")
        return
        
    try:
        with open(filename, 'r') as f:
            skills_to_remove = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return
        
    gemini_dir = os.path.expanduser("~/.gemini/skills")
    antigravity_dir = os.path.expanduser("~/.gemini/antigravity/skills")
    
    import shutil
    
    print(f"Processing removal of {len(skills_to_remove)} skills...")
    for skill_name in skills_to_remove:
        print(f"\nRemoving {skill_name}...")
        
        # Remove from Gemini
        p1 = os.path.join(gemini_dir, skill_name)
        if os.path.exists(p1):
            try:
                shutil.rmtree(p1)
                print(f"  Removed from Gemini")
            except Exception as e:
                print(f"  Error removing from Gemini: {e}")
                
        # Remove from Antigravity
        p2 = os.path.join(antigravity_dir, skill_name)
        if os.path.exists(p2):
            try:
                shutil.rmtree(p2)
                print(f"  Removed from Antigravity")
            except Exception as e:
                print(f"  Error removing from Antigravity: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gemini Skill Manager (GSM)")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    subparsers.add_parser('list', help='List all skills and their status')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a skill to the catalog')
    add_parser.add_argument('id', help='Unique ID for the skill')
    add_parser.add_argument('url', help='Git repository URL')
    add_parser.add_argument('--path', help='Path within the repository (optional)')
    add_parser.add_argument('--description', help='Description of the skill (optional)')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install a skill or super-skill')
    install_parser.add_argument('id', help='ID of the skill or super-skill to install')
    install_parser.add_argument('--target', choices=['gemini', 'antigravity', 'both'], default='both',
                                help='Target environment for installation (default: both)')
    
    # Update command
    subparsers.add_parser('update', help='Update all installed skills')
    
    # Export-installed command
    export_parser = subparsers.add_parser('export-installed', help='Export installed skills to a file')
    export_parser.add_argument('file', help='Filename to write to')
    
    # Remove-from-file command
    remove_parser = subparsers.add_parser('remove-from-file', help='Remove skills listed in a file')
    remove_parser.add_argument('file', help='Filename to read from')
    
    args = parser.parse_args()
    
    # Change directory to the workspace root where the script is located
    # to ensure we can find the catalog file.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    catalog = load_catalog()
    installed = get_installed_skills()
    
    if args.command == 'list':
        list_skills(catalog, installed)
    elif args.command == 'add':
        add_skill(catalog, args.id, args.url, args.path, args.description)
    elif args.command == 'install':
        install_skill(catalog, args.id, args.target)
    elif args.command == 'update':
        update_skills(catalog, installed)
    elif args.command == 'export-installed':
        export_installed(args.file, installed)
    elif args.command == 'remove-from-file':
        remove_from_file(args.file)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()


