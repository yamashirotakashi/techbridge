"""Slackコマンドエンドポイント"""

import hmac
import hashlib
import time
from typing import Dict, Any
from urllib.parse import parse_qs

from fastapi import APIRouter, Request, HTTPException, Depends, status, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.config import settings
from app.core.deps import get_db
from app.core.logging import log_slack_command
from app.services.workflow import WorkflowService
from app.services.slack import SlackService
from app.models.enums import ProgressStatus as WorkflowStatus

logger = structlog.get_logger(__name__)
router = APIRouter()


def verify_slack_signature(
    request_body: bytes,
    timestamp: str,
    signature: str
) -> bool:
    """Slack署名を検証"""
    # タイムスタンプが5分以内であることを確認
    if abs(time.time() - float(timestamp)) > 60 * 5:
        return False
    
    # 署名ベース文字列を構築
    sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}"
    
    # 期待される署名を計算
    expected_signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


async def parse_slack_command(request: Request) -> Dict[str, Any]:
    """Slackコマンドリクエストをパース"""
    # ヘッダーを取得
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")
    
    if not timestamp or not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Slack headers"
        )
    
    # ボディを取得
    body = await request.body()
    
    # 署名を検証
    if not verify_slack_signature(body, timestamp, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid request signature"
        )
    
    # フォームデータをパース
    form_data = parse_qs(body.decode('utf-8'))
    
    return {
        "token": form_data.get("token", [""])[0],
        "team_id": form_data.get("team_id", [""])[0],
        "team_domain": form_data.get("team_domain", [""])[0],
        "channel_id": form_data.get("channel_id", [""])[0],
        "channel_name": form_data.get("channel_name", [""])[0],
        "user_id": form_data.get("user_id", [""])[0],
        "user_name": form_data.get("user_name", [""])[0],
        "command": form_data.get("command", [""])[0],
        "text": form_data.get("text", [""])[0],
        "response_url": form_data.get("response_url", [""])[0],
        "trigger_id": form_data.get("trigger_id", [""])[0],
    }


@router.post("/commands/status")
async def handle_status_command(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Slack /statusコマンドを処理"""
    # コマンドをパース
    command_data = await parse_slack_command(request)
    
    logger.info(
        "Received /status command",
        user=command_data["user_name"],
        channel=command_data["channel_name"],
        text=command_data["text"]
    )
    
    try:
        # N番号を抽出
        n_number = command_data["text"].strip().upper()
        if not n_number:
            return JSONResponse(
                content={
                    "response_type": "ephemeral",
                    "text": "使用方法: `/status N番号`\n例: `/status N12345`"
                }
            )
        
        # ワークフローサービスを使用して取得
        workflow_service = WorkflowService(db)
        item = await workflow_service.get_by_n_number(n_number)
        
        if not item:
            log_slack_command(
                command="/status",
                user=command_data["user_name"],
                channel=command_data["channel_name"],
                success=False,
                error="Not found"
            )
            
            return JSONResponse(
                content={
                    "response_type": "ephemeral",
                    "text": f"❌ {n_number} の進捗情報が見つかりませんでした。"
                }
            )
        
        # ステータスを日本語に変換
        status_ja = {
            WorkflowStatus.DISCOVERED: "🔍 発見",
            WorkflowStatus.PURCHASED: "💰 購入完了",
            WorkflowStatus.MANUSCRIPT_REQUESTED: "✍️ 原稿依頼",
            WorkflowStatus.MANUSCRIPT_RECEIVED: "📄 原稿受領",
            WorkflowStatus.FIRST_PROOF: "📝 初校",
            WorkflowStatus.SECOND_PROOF: "✏️ 再校",
            WorkflowStatus.COMPLETED: "✅ 完成"
        }
        
        # レスポンスを構築
        response_text = f"""📊 *{n_number}の進捗*
📖 タイトル: {item.title}
✍️ 著者: {item.author}
📅 ステータス: {status_ja.get(item.status, item.status.value)}
🕐 更新日時: {item.updated_at.strftime('%Y-%m-%d %H:%M')}"""
        
        if item.assigned_editor:
            response_text += f"\n👤 担当編集者: {item.assigned_editor}"
        
        log_slack_command(
            command="/status",
            user=command_data["user_name"],
            channel=command_data["channel_name"],
            success=True,
            n_number=n_number
        )
        
        return JSONResponse(
            content={
                "response_type": "in_channel",
                "text": response_text
            }
        )
        
    except Exception as e:
        logger.error(
            "Failed to process /status command",
            error=str(e),
            user=command_data["user_name"]
        )
        
        log_slack_command(
            command="/status",
            user=command_data["user_name"],
            channel=command_data["channel_name"],
            success=False,
            error=str(e)
        )
        
        return JSONResponse(
            content={
                "response_type": "ephemeral",
                "text": f"❌ エラーが発生しました: {str(e)}"
            }
        )


@router.post("/commands/update")
async def handle_update_command(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Slack /updateコマンドを処理"""
    # コマンドをパース
    command_data = await parse_slack_command(request)
    
    logger.info(
        "Received /update command",
        user=command_data["user_name"],
        channel=command_data["channel_name"],
        text=command_data["text"]
    )
    
    try:
        # 引数をパース
        parts = command_data["text"].strip().split()
        if len(parts) < 2:
            return JSONResponse(
                content={
                    "response_type": "ephemeral",
                    "text": "使用方法: `/update N番号 ステータス`\n例: `/update N12345 first_proof`\n\n利用可能なステータス:\n- discovered (発見)\n- purchased (購入完了)\n- manuscript_requested (原稿依頼)\n- manuscript_received (原稿受領)\n- first_proof (初校)\n- second_proof (再校)\n- completed (完成)"
                }
            )
        
        n_number = parts[0].upper()
        status_str = parts[1].lower()
        
        # ステータスをEnumに変換
        try:
            new_status = WorkflowStatus[status_str.upper()]
        except KeyError:
            return JSONResponse(
                content={
                    "response_type": "ephemeral",
                    "text": f"❌ 無効なステータス: {status_str}\n\n利用可能なステータス:\n- discovered\n- purchased\n- manuscript_requested\n- manuscript_received\n- first_proof\n- second_proof\n- completed"
                }
            )
        
        # ワークフローサービスを使用して更新
        workflow_service = WorkflowService(db)
        
        # 既存のアイテムを取得
        item = await workflow_service.get_by_n_number(n_number)
        if not item:
            return JSONResponse(
                content={
                    "response_type": "ephemeral",
                    "text": f"❌ {n_number} の進捗情報が見つかりませんでした。"
                }
            )
        
        old_status = item.status
        
        # ステータスを更新
        item = await workflow_service.update_status(
            n_number=n_number,
            status=new_status,
            metadata={"updated_by": command_data["user_name"]}
        )
        
        # Slack通知を送信
        slack_service = SlackService(settings.SLACK_BOT_TOKEN)
        await slack_service.send_status_update(
            channel=item.slack_channel,
            n_number=n_number,
            title=item.title,
            old_status=old_status,
            new_status=new_status
        )
        
        # ステータスを日本語に変換
        status_ja = {
            WorkflowStatus.DISCOVERED: "発見",
            WorkflowStatus.PURCHASED: "購入完了",
            WorkflowStatus.MANUSCRIPT_REQUESTED: "原稿依頼",
            WorkflowStatus.MANUSCRIPT_RECEIVED: "原稿受領",
            WorkflowStatus.FIRST_PROOF: "初校",
            WorkflowStatus.SECOND_PROOF: "再校",
            WorkflowStatus.COMPLETED: "完成"
        }
        
        log_slack_command(
            command="/update",
            user=command_data["user_name"],
            channel=command_data["channel_name"],
            success=True,
            n_number=n_number,
            new_status=new_status.value
        )
        
        return JSONResponse(
            content={
                "response_type": "in_channel",
                "text": f"✅ {n_number} のステータスを「{status_ja.get(new_status, new_status.value)}」に更新しました。"
            }
        )
        
    except Exception as e:
        logger.error(
            "Failed to process /update command",
            error=str(e),
            user=command_data["user_name"]
        )
        
        log_slack_command(
            command="/update",
            user=command_data["user_name"],
            channel=command_data["channel_name"],
            success=False,
            error=str(e)
        )
        
        return JSONResponse(
            content={
                "response_type": "ephemeral",
                "text": f"❌ エラーが発生しました: {str(e)}"
            }
        )