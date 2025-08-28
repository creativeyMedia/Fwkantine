#!/usr/bin/env python3
"""
.ENV CONFIGURATION CHECKER für Masterpasswort & Stornierung

Überprüft ob alle erforderlichen Umgebungsvariablen korrekt gesetzt sind.
"""

import os
from dotenv import load_dotenv

def check_env_config():
    """Überprüfe .env Konfiguration"""
    
    # Load .env file
    env_path = '/app/backend/.env'
    load_dotenv(env_path)
    
    print("🔧 ENVIRONMENT CONFIGURATION CHECK")
    print("=" * 50)
    
    # Required variables for master password functionality
    required_vars = {
        'MASTER_PASSWORD': 'master123dev',
        'DEPT_1_PASSWORD': 'password1', 
        'DEPT_1_ADMIN_PASSWORD': 'admin1',
        'DEPT_2_PASSWORD': 'password2',
        'DEPT_2_ADMIN_PASSWORD': 'admin2', 
        'DEPT_3_PASSWORD': 'password3',
        'DEPT_3_ADMIN_PASSWORD': 'admin3',
        'DEPT_4_PASSWORD': 'password4',
        'DEPT_4_ADMIN_PASSWORD': 'admin4',
        'MONGO_URL': 'mongodb://localhost:27017',
        'DB_NAME': 'fw_kantine_production'
    }
    
    print(f"📄 Checking .env file: {env_path}")
    if not os.path.exists(env_path):
        print(f"❌ .env file not found at {env_path}!")
        return False
    
    all_good = True
    missing_vars = []
    
    print(f"\n🔍 REQUIRED ENVIRONMENT VARIABLES:")
    for var_name, default_value in required_vars.items():
        current_value = os.environ.get(var_name)
        
        if current_value:
            # Mask passwords for security
            if 'PASSWORD' in var_name:
                display_value = '*' * len(current_value)
            else:
                display_value = current_value
            print(f"   ✅ {var_name}={display_value}")
        else:
            print(f"   ❌ {var_name} = NOT SET (default: {default_value})")
            missing_vars.append((var_name, default_value))
            all_good = False
    
    if missing_vars:
        print(f"\n❌ MISSING VARIABLES: {len(missing_vars)}")
        print("\nAdd these lines to your .env file:")
        print("-" * 40)
        for var_name, default_value in missing_vars:
            print(f'{var_name}="{default_value}"')
        print("-" * 40)
    
    # Check if master password is specifically set
    master_pw = os.environ.get('MASTER_PASSWORD')
    if master_pw == 'master123dev':
        print(f"\n✅ MASTER PASSWORD: Correctly set to 'master123dev'")
    elif master_pw:
        print(f"\n⚠️  MASTER PASSWORD: Set to different value (not default 'master123dev')")
    else:
        print(f"\n❌ MASTER PASSWORD: NOT SET! This will break master login functionality")
    
    print(f"\n🎯 OVERALL STATUS: {'✅ ALL GOOD' if all_good else '❌ ISSUES FOUND'}")
    
    if all_good:
        print("\n📝 Next steps:")
        print("1. Restart backend: sudo supervisorctl restart backend") 
        print("2. Test master login with 'master123dev'")
    else:
        print(f"\n📝 Fix {len(missing_vars)} missing variables, then restart backend")
    
    return all_good

if __name__ == "__main__":
    check_env_config()