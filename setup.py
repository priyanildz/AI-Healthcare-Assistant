#!/usr/bin/env python
"""
Setup and initialization script for AI Healthcare Project
Run this script to set up the project environment
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from template"""
    env_path = Path('.env')
    env_example_path = Path('.env.example')
    
    if env_path.exists():
        print("✓ .env file already exists")
        return
    
    if env_example_path.exists():
        env_example_path.rename(env_path)
        print("✓ Created .env from template")
    else:
        # Create minimal .env
        with open(env_path, 'w') as f:
            f.write("""# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key_here

# Server
FLASK_PORT=5000
""")
        print("✓ Created .env file")
    
    print("\n⚠️  IMPORTANT: Edit .env and set your OPENAI_API_KEY")

def verify_structure():
    """Verify project structure"""
    required_dirs = [
        'backend',
        'backend/models',
        'angular-frontend'
    ]
    
    required_files = [
        'backend/app.py',
        'backend/config.py',
        'backend/models/report_summarizer.py',
        'backend/models/medication_analyzer.py',
        'backend/models/xray_analyzer.py',
        'angular-frontend/package.json',
        'requirements.txt',
        'README.md'
    ]
    
    print("\nVerifying project structure...")
    
    all_good = True
    for dir in required_dirs:
        if Path(dir).exists():
            print(f"✓ {dir}/")
        else:
            print(f"✗ {dir}/ (missing)")
            all_good = False
    
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} (missing)")
            all_good = False
    
    return all_good

def main():
    """Run setup"""
    print("=" * 60)
    print("AI Healthcare Project - Setup")
    print("=" * 60)
    
    # Verify structure
    if not verify_structure():
        print("\n✗ Project structure incomplete!")
        return False
    
    print("\n✓ Project structure verified")
    
    # Create .env
    print("\nSetting up environment...")
    create_env_file()
    
    print("\n" + "=" * 60)
    print("Setup completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Edit .env and set OPENAI_API_KEY")
    print("2. Run backend: cd backend && python app.py")
    print("3. Run frontend: cd angular-frontend && npm install && npm start")
    print("4. Open http://localhost:4200 in your browser")
    print("\nFor more details, see QUICKSTART.md")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)