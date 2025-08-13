#!/usr/bin/env python3
"""
Simple import test for TechWF
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath('.'))

def main():
    try:
        print("Testing imports...")
        
        # 1. 基本的なモジュール
        print("1. Testing repository...")
        from src.repositories.publication_repository import PublicationRepository
        print("   ✅ PublicationRepository")
        
        print("2. Testing config service...")
        from src.services.config_service import get_config_service
        print("   ✅ ConfigService")
        
        print("3. Testing theme...")
        from src.gui.theme import ThemeManager
        print("   ✅ ThemeManager")
        
        print("4. Testing service manager...")
        from src.gui.service_manager import ServiceManager
        print("   ✅ ServiceManager")
        
        print("5. Testing main window class...")
        from src.gui.main_window import TechWFMainWindow
        print("   ✅ TechWFMainWindow")
        
        print("\n🎉 All imports successful!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()