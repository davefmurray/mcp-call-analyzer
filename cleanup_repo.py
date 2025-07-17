#!/usr/bin/env python3
"""
Repository Cleanup Script for MCP Call Analyzer

This script safely cleans and reorganizes the repository structure.
It includes safety checks and creates backups before making changes.
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
import argparse
import sys

class RepoCleanup:
    def __init__(self, repo_path=".", dry_run=True):
        self.repo_path = Path(repo_path).resolve()
        self.dry_run = dry_run
        self.backup_dir = self.repo_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.actions_log = []
        
        # Define folder structure
        self.folders = {
            "src": ["scrapers", "pipelines", "utils", "downloaders"],
            "tests": [],
            "scripts": [],
            "docs": ["images", "api", "examples"],
            "data": ["downloads", "logs", "temp"],
            "config": []
        }
        
        # File mappings (source -> destination)
        self.file_mappings = {
            # Scrapers
            "scraper_api.py": "src/scrapers/",
            "final_scraper.py": "src/scrapers/",
            "mcp_browser_scraper.py": "src/scrapers/",
            "scrape_aggrid_calls.py": "src/scrapers/",
            
            # Pipelines
            "api_pipeline_complete.py": "src/pipelines/",
            "final_hybrid_pipeline.py": "src/pipelines/",
            "batch_processor.py": "src/pipelines/",
            
            # Utils
            "capture_headers.py": "src/utils/",
            "find_api_endpoints.py": "src/utils/",
            "find_audio_link.py": "src/utils/",
            "setup_storage.py": "src/utils/",
            
            # Downloaders
            "download_call_audio.py": "src/downloaders/",
            "complete_transcription.py": "src/downloaders/",
            
            # Scripts
            "check_calls.py": "scripts/",
            "check_calls_table.py": "scripts/",
            "upload_to_supabase.py": "scripts/",
            
            # Tests
            "test_*.py": "tests/",
            "*_test.py": "tests/",
            
            # Images
            "*.png": "docs/images/",
            
            # Logs
            "*.log": "data/logs/"
        }
        
        # Files to remove
        self.files_to_remove = [
            # Redundant files
            "api_pipeline_demo.py",
            "final_pipeline_demo.py",
            "final_pipeline_deepgram.py",
            "complete_pipeline_test.py",
            "debug_scraper.py",
            "scrape_fresh_calls.py",
            "scrape_with_network.py",
            "test_multiple_calls.py",  # Keep only the fixed version
            "simple_click_test.py",
            "manual_test.py",
            
            # Temporary test files
            "test_download.mp3",
            "downloads/test_*.mp3",
            
            # Demo files (already documented)
            "mcp_browser_complete_demo.py",
            "*_demo.py"
        ]
        
        # Sensitive files to handle
        self.sensitive_files = [
            "captured_headers.json",
            ".mcp.json"
        ]

    def log_action(self, action, details):
        """Log actions for review"""
        self.actions_log.append({
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{'[DRY RUN] ' if self.dry_run else ''}✓ {action}: {details}")

    def create_backup(self):
        """Create backup of current state"""
        if not self.dry_run:
            self.backup_dir.mkdir(exist_ok=True)
            self.log_action("Created backup directory", str(self.backup_dir))
            
            # Backup important files
            important_files = [
                ".env", "requirements.txt", "README.md",
                "captured_headers.json", ".mcp.json"
            ]
            
            for file in important_files:
                if (self.repo_path / file).exists():
                    shutil.copy2(self.repo_path / file, self.backup_dir / file)
                    self.log_action("Backed up", file)

    def create_folder_structure(self):
        """Create organized folder structure"""
        for folder, subfolders in self.folders.items():
            folder_path = self.repo_path / folder
            
            if not self.dry_run:
                folder_path.mkdir(exist_ok=True)
            self.log_action("Created folder", folder)
            
            for subfolder in subfolders:
                subfolder_path = folder_path / subfolder
                if not self.dry_run:
                    subfolder_path.mkdir(exist_ok=True)
                self.log_action("Created subfolder", f"{folder}/{subfolder}")

    def move_files(self):
        """Move files to appropriate folders"""
        from glob import glob
        
        for pattern, destination in self.file_mappings.items():
            files = glob(str(self.repo_path / pattern))
            
            for file_path in files:
                file = Path(file_path)
                if file.exists() and file.name not in self.files_to_remove:
                    dest_path = self.repo_path / destination / file.name
                    
                    if not self.dry_run:
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file), str(dest_path))
                    
                    self.log_action("Moved file", f"{file.name} -> {destination}")

    def remove_redundant_files(self):
        """Remove redundant and temporary files"""
        from glob import glob
        
        for pattern in self.files_to_remove:
            files = glob(str(self.repo_path / pattern))
            
            for file_path in files:
                file = Path(file_path)
                if file.exists():
                    if not self.dry_run:
                        file.unlink()
                    self.log_action("Removed file", file.name)

    def handle_sensitive_files(self):
        """Handle sensitive files containing credentials"""
        gitignore_path = self.repo_path / ".gitignore"
        gitignore_additions = []
        
        for sensitive_file in self.sensitive_files:
            file_path = self.repo_path / sensitive_file
            
            if file_path.exists():
                # Back it up first
                if not self.dry_run and self.backup_dir.exists():
                    shutil.copy2(file_path, self.backup_dir / sensitive_file)
                
                # Move to config folder
                new_path = self.repo_path / "config" / sensitive_file
                if not self.dry_run:
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(new_path))
                
                self.log_action("Moved sensitive file", f"{sensitive_file} -> config/")
                
                # Add to .gitignore
                gitignore_additions.append(f"config/{sensitive_file}")
        
        # Update .gitignore
        if gitignore_additions and not self.dry_run:
            with open(gitignore_path, "a") as f:
                f.write("\n# Sensitive configuration files\n")
                for item in gitignore_additions:
                    f.write(f"{item}\n")
            
            self.log_action("Updated .gitignore", f"Added {len(gitignore_additions)} entries")

    def create_init_files(self):
        """Create __init__.py files for proper package structure"""
        init_locations = [
            "src",
            "src/scrapers",
            "src/pipelines",
            "src/utils",
            "src/downloaders",
            "tests"
        ]
        
        for location in init_locations:
            init_path = self.repo_path / location / "__init__.py"
            
            if not self.dry_run:
                init_path.parent.mkdir(parents=True, exist_ok=True)
                init_path.touch()
            
            self.log_action("Created __init__.py", location)

    def create_env_example(self):
        """Create .env.example file"""
        env_example_content = """# MCP Call Analyzer Environment Variables

# Digital Concierge Dashboard
DASHBOARD_USERNAME=your_username
DASHBOARD_PASSWORD=your_password

# API Keys
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=your_deepgram_key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Optional: MCP Tokens (if using MCP tools)
# GITHUB_TOKEN=ghp_...
# RAILWAY_TOKEN=...
"""
        
        env_example_path = self.repo_path / ".env.example"
        
        if not self.dry_run:
            env_example_path.write_text(env_example_content)
        
        self.log_action("Created .env.example", "Template for environment variables")

    def generate_cleanup_report(self):
        """Generate a cleanup report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "actions": self.actions_log,
            "backup_location": str(self.backup_dir) if not self.dry_run else None
        }
        
        report_path = self.repo_path / "cleanup_report.json"
        
        if not self.dry_run:
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Cleanup {'Preview' if self.dry_run else 'Complete'}!")
        print(f"Total actions: {len(self.actions_log)}")
        
        if not self.dry_run:
            print(f"Backup location: {self.backup_dir}")
            print(f"Report saved to: {report_path}")
        else:
            print("\nRun with --execute to perform these actions")

    def cleanup(self):
        """Main cleanup process"""
        print(f"🧹 MCP Call Analyzer Repository Cleanup")
        print(f"{'='*60}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"Repository: {self.repo_path}\n")
        
        # Create backup (only if not dry run)
        if not self.dry_run:
            self.create_backup()
        
        # Execute cleanup steps
        self.create_folder_structure()
        self.move_files()
        self.remove_redundant_files()
        self.handle_sensitive_files()
        self.create_init_files()
        self.create_env_example()
        
        # Generate report
        self.generate_cleanup_report()


def main():
    parser = argparse.ArgumentParser(
        description="Clean and reorganize MCP Call Analyzer repository"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute cleanup (default is dry run)"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Path to repository (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Safety check
    if args.execute:
        print("⚠️  WARNING: This will reorganize your repository!")
        print("✅ Auto-confirming cleanup execution...")
    
    # Run cleanup
    cleanup = RepoCleanup(repo_path=args.path, dry_run=not args.execute)
    cleanup.cleanup()


if __name__ == "__main__":
    main()