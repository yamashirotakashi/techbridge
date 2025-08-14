#!/usr/bin/env python3
"""
PJINIT 設定機能完全性テスト
全トークン設定項目の完全性を検証
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ui.main_window import ProjectInitializerWindow


def test_settings_completeness():
    """設定タブの完全性テスト"""
    print("🔧 PJINIT 設定機能完全性テスト")
    print("=" * 60)
    
    app = QApplication([])
    window = ProjectInitializerWindow()
    
    # 1. 全必須フィールドの存在確認
    required_fields = [
        'slack_token_input',
        'slack_user_token_input', 
        'slack_invitation_token_input',  # 新追加フィールド
        'github_token_input',
        'github_org_token_input',
        'slack_signing_secret_input',
        'slack_client_id_input',
        'slack_client_secret_input',
        'google_service_key_input',
        'planning_sheet_input',
        'purchase_sheet_input'
    ]
    
    print("1. 必須フィールド存在確認:")
    all_fields_present = True
    for field_name in required_fields:
        has_field = hasattr(window, field_name)
        status = "✅" if has_field else "❌"
        print(f"   {status} {field_name}: {has_field}")
        if not has_field:
            all_fields_present = False
    
    # 2. マスクが外れているか確認
    print("\n2. パスワードマスク状態確認:")
    mask_removed = True
    for field_name in required_fields:
        if hasattr(window, field_name):
            field = getattr(window, field_name)
            # EchoModeがPasswordでないことを確認
            from PyQt6.QtWidgets import QLineEdit
            is_masked = field.echoMode() == QLineEdit.EchoMode.Password
            status = "❌ (マスク有効)" if is_masked else "✅ (マスク無効)"
            print(f"   {status} {field_name}")
            if is_masked:
                mask_removed = False
    
    # 3. _collect_parameters メソッドでの完全性確認
    print("\n3. パラメータ収集完全性確認:")
    params = window._collect_parameters()
    expected_params = [
        'slack_token', 'slack_user_token', 'slack_invitation_token',
        'github_token', 'github_org_token', 'slack_signing_secret',
        'slack_client_id', 'slack_client_secret', 'google_service_key',
        'planning_sheet_id', 'purchase_sheet_id'
    ]
    
    params_complete = True
    for param in expected_params:
        has_param = param in params
        status = "✅" if has_param else "❌"
        print(f"   {status} {param}: {has_param}")
        if not has_param:
            params_complete = False
    
    # 4. _on_save_settings メソッドでの完全性確認
    print("\n4. 設定保存完全性確認:")
    
    # モック設定でテスト実行
    test_signals_received = []
    
    def mock_settings_handler(settings):
        test_signals_received.append(settings)
        print(f"   📨 設定保存シグナル受信: {len(settings)}個のキー")
        
        expected_settings_keys = [
            'slack_token', 'slack_user_token', 'slack_invitation_token',
            'github_token', 'github_org_token', 'slack_signing_secret', 
            'slack_client_id', 'slack_client_secret', 'google_service_key',
            'planning_sheet_id', 'purchase_sheet_id'
        ]
        
        settings_complete = True
        for key in expected_settings_keys:
            has_key = key in settings
            status = "✅" if has_key else "❌"
            print(f"      {status} {key}: {has_key}")
            if not has_key:
                settings_complete = False
        
        return settings_complete
    
    # シグナル接続
    window.settings_save_requested.connect(mock_settings_handler)
    
    # テスト用の値を設定
    window.slack_invitation_token_input.setText("test-invitation-token")
    
    # 保存処理実行（実際の保存は発生しない、シグナルのみ）
    try:
        # QMessageBoxをモックして実行
        import unittest.mock
        with unittest.mock.patch('PyQt6.QtWidgets.QMessageBox.information'):
            window._on_save_settings()
    except Exception as e:
        print(f"   ❌ 設定保存処理でエラー: {e}")
        return False
    
    # 5. 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー:")
    
    overall_success = (
        all_fields_present and
        mask_removed and 
        params_complete and
        len(test_signals_received) > 0
    )
    
    if overall_success:
        print("✅ 全テスト PASSED - 設定タブ完全実装完了")
        print("   • 全必須フィールド存在 ✅")
        print("   • パスワードマスク削除 ✅") 
        print("   • パラメータ収集完全 ✅")
        print("   • 設定保存機能動作 ✅")
        print("   • SLACK_INVITATION_BOT_TOKEN対応 ✅")
    else:
        print("❌ テスト FAILED - 設定タブに問題あり")
        if not all_fields_present:
            print("   • 必須フィールド不足")
        if not mask_removed:
            print("   • パスワードマスク残存")
        if not params_complete:
            print("   • パラメータ収集不完全")
        if len(test_signals_received) == 0:
            print("   • 設定保存機能未動作")
    
    app.quit()
    return overall_success


if __name__ == "__main__":
    success = test_settings_completeness()
    sys.exit(0 if success else 1)