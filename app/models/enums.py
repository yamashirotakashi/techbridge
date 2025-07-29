"""
TechBridge 列挙型定義
"""

from enum import Enum


class ProgressStatus(str, Enum):
    """進捗ステータス"""
    DISCOVERED = "discovered"              # 発見済み（[tech]でスクレイピング）
    PURCHASED = "purchased"                # 購入完了（[tech]で購入）
    MANUSCRIPT_REQUESTED = "manuscript_requested"  # 原稿依頼（著者へ依頼送信）
    MANUSCRIPT_RECEIVED = "manuscript_received"    # 原稿受領（著者から原稿受信）
    FIRST_PROOF = "first_proof"           # 初校（[techzip]変換後）
    SECOND_PROOF = "second_proof"         # 再校（編集者レビュー後）
    COMPLETED = "completed"               # 完成（最終承認済み）
    
    @classmethod
    def get_display_name(cls, status: 'ProgressStatus') -> str:
        """表示名を取得"""
        display_names = {
            cls.DISCOVERED: "発見済み",
            cls.PURCHASED: "購入完了",
            cls.MANUSCRIPT_REQUESTED: "原稿依頼中",
            cls.MANUSCRIPT_RECEIVED: "原稿受領済み",
            cls.FIRST_PROOF: "初校中",
            cls.SECOND_PROOF: "再校中",
            cls.COMPLETED: "完成"
        }
        return display_names.get(status, status.value)
    
    @classmethod
    def get_emoji(cls, status: 'ProgressStatus') -> str:
        """ステータス絵文字を取得"""
        emojis = {
            cls.DISCOVERED: "🔍",
            cls.PURCHASED: "💰",
            cls.MANUSCRIPT_REQUESTED: "✍️",
            cls.MANUSCRIPT_RECEIVED: "📄",
            cls.FIRST_PROOF: "📝",
            cls.SECOND_PROOF: "✏️",
            cls.COMPLETED: "✅"
        }
        return emojis.get(status, "❓")
    
    def get_next_status(self) -> 'ProgressStatus':
        """次のステータスを取得"""
        transitions = {
            self.DISCOVERED: self.PURCHASED,
            self.PURCHASED: self.MANUSCRIPT_REQUESTED,
            self.MANUSCRIPT_REQUESTED: self.MANUSCRIPT_RECEIVED,
            self.MANUSCRIPT_RECEIVED: self.FIRST_PROOF,
            self.FIRST_PROOF: self.SECOND_PROOF,
            self.SECOND_PROOF: self.COMPLETED,
        }
        return transitions.get(self, self)
    
    def can_transition_to(self, target_status: 'ProgressStatus') -> bool:
        """指定したステータスへの遷移が可能かチェック"""
        # 順序を定義
        status_order = [
            self.DISCOVERED,
            self.PURCHASED,
            self.MANUSCRIPT_REQUESTED,
            self.MANUSCRIPT_RECEIVED,
            self.FIRST_PROOF,
            self.SECOND_PROOF,
            self.COMPLETED
        ]
        
        try:
            current_index = status_order.index(self)
            target_index = status_order.index(target_status)
            
            # 前進のみ許可（同じステータスへの更新も許可）
            return target_index >= current_index
        except ValueError:
            return False


class NotificationChannel(str, Enum):
    """通知チャンネル種別"""
    MANAGEMENT = "management"       # 管理チャンネル
    AUTHOR = "author"              # 著者チャンネル
    EDITOR = "editor"              # 編集者チャンネル
    DEFAULT = "default"            # デフォルトチャンネル


class EventType(str, Enum):
    """イベント種別"""
    STATUS_CHANGE = "status_change"           # ステータス変更
    WEBHOOK_RECEIVED = "webhook_received"     # Webhook受信
    NOTIFICATION_SENT = "notification_sent"   # 通知送信
    ERROR_OCCURRED = "error_occurred"         # エラー発生
    MANUAL_UPDATE = "manual_update"           # 手動更新
    SYSTEM_UPDATE = "system_update"           # システム更新


class WebhookSource(str, Enum):
    """Webhook送信元"""
    TECH = "tech"           # [tech]プロジェクト
    TECHZIP = "techzip"     # [techzip]プロジェクト
    MANUAL = "manual"       # 手動更新
    SYSTEM = "system"       # システム自動更新


class NotificationStatus(str, Enum):
    """通知ステータス"""
    PENDING = "pending"     # 送信待ち
    SENT = "sent"          # 送信完了
    FAILED = "failed"      # 送信失敗
    RETRYING = "retrying"  # リトライ中