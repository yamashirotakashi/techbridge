#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage Completion Validator - ステージ完了バリデーター
各ワークフローステージの完了基準を検証するドメインサービス
"""

from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum

from ..workflow_stages import WorkflowStageType


@dataclass
class ValidationError:
    """バリデーションエラー"""
    field: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """バリデーション結果"""
    is_valid: bool
    validation_errors: List[ValidationError]
    completion_score: float = 0.0  # 0.0-1.0の完了度スコア
    
    def __str__(self) -> str:
        if self.is_valid:
            return "バリデーション成功"
        error_messages = [error.message for error in self.validation_errors]
        return f"バリデーション失敗: {', '.join(error_messages)}"


class StageCompletionValidator:
    """
    ステージ完了バリデーター
    
    各ステージの完了基準を定義し、データの妥当性を検証する
    """
    
    def __init__(self):
        # ステージ別必須フィールド定義
        self._required_fields = {
            WorkflowStageType.PROPOSAL_DRAFT: [
                "title", "overview", "assignee", "reviewer", "approval_signature"
            ],
            WorkflowStageType.PROPOSAL: [
                "title", "overview", "assignee", "reviewer", "approval_signature",
                "detailed_plan", "budget", "schedule"
            ],
            WorkflowStageType.SPECIFICATION: [
                "title", "overview", "assignee", "reviewer", "approval_signature",
                "technical_spec", "ui_design", "test_plan"
            ]
        }
    
    def validate_stage_completion(
        self,
        stage_type: WorkflowStageType,
        stage_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        ステージ完了バリデーションの実行
        
        Args:
            stage_type: ステージタイプ
            stage_data: ステージデータ
            
        Returns:
            ValidationResult: バリデーション結果
        """
        errors = []
        
        # 必須フィールドのチェック
        required_fields = self._required_fields.get(stage_type, [])
        
        for field in required_fields:
            if field not in stage_data or not stage_data.get(field):
                errors.append(ValidationError(
                    field=field,
                    message=f"{self._get_field_display_name(field)}が必須です"
                ))
        
        # ステージ固有のバリデーション
        stage_specific_errors = self._validate_stage_specific_rules(stage_type, stage_data)
        errors.extend(stage_specific_errors)
        
        # 完了度スコア計算
        completion_score = self._calculate_completion_score(stage_type, stage_data)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            validation_errors=errors,
            completion_score=completion_score
        )
    
    def _validate_stage_specific_rules(
        self,
        stage_type: WorkflowStageType,
        stage_data: Dict[str, Any]
    ) -> List[ValidationError]:
        """
        ステージ固有バリデーションルール
        
        Args:
            stage_type: ステージタイプ
            stage_data: ステージデータ
            
        Returns:
            List[ValidationError]: バリデーションエラーリスト
        """
        errors = []
        
        if stage_type == WorkflowStageType.PROPOSAL_DRAFT:
            # 企画案書固有のルール
            title = stage_data.get("title", "")
            if len(title) < 5:
                errors.append(ValidationError(
                    field="title",
                    message="タイトルは5文字以上である必要があります"
                ))
        
        elif stage_type == WorkflowStageType.PROPOSAL:
            # 企画書固有のルール
            budget = stage_data.get("budget")
            if budget and not isinstance(budget, (int, float)):
                errors.append(ValidationError(
                    field="budget",
                    message="予算は数値である必要があります"
                ))
        
        elif stage_type == WorkflowStageType.SPECIFICATION:
            # 製品仕様書固有のルール
            test_plan = stage_data.get("test_plan", "")
            if test_plan and len(test_plan) < 10:
                errors.append(ValidationError(
                    field="test_plan",
                    message="テスト計画は10文字以上である必要があります"
                ))
        
        return errors
    
    def _calculate_completion_score(
        self,
        stage_type: WorkflowStageType,
        stage_data: Dict[str, Any]
    ) -> float:
        """
        完了度スコア計算
        
        Args:
            stage_type: ステージタイプ
            stage_data: ステージデータ
            
        Returns:
            float: 完了度スコア (0.0-1.0)
        """
        required_fields = self._required_fields.get(stage_type, [])
        if not required_fields:
            return 1.0
        
        completed_fields = sum(
            1 for field in required_fields
            if field in stage_data and stage_data.get(field)
        )
        
        return completed_fields / len(required_fields)
    
    def _get_field_display_name(self, field: str) -> str:
        """フィールド名の表示名を取得"""
        display_names = {
            "title": "タイトル",
            "overview": "概要",
            "assignee": "担当者",
            "reviewer": "レビュアー",
            "approval_signature": "承認印",
            "detailed_plan": "詳細企画書",
            "budget": "予算",
            "schedule": "スケジュール",
            "technical_spec": "技術仕様",
            "ui_design": "UI設計",
            "test_plan": "テスト計画"
        }
        return display_names.get(field, field)