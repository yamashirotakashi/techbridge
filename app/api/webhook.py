"""Webhook endpoints for external integrations."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_webhook_signature
from app.models.workflow import WorkflowStatus
from app.services.workflow import WorkflowService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/tech/status-change")
async def tech_status_change(
    request: Request,
    payload: Dict[str, Any],
    x_webhook_signature: str = Header(None, alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Handle status change webhook from techbookfest_scraper.
    
    Expected payload:
    {
        "book_id": "12345",
        "n_number": "N02279",
        "status": "purchased",
        "metadata": {...}
    }
    """
    # Verify webhook signature
    if x_webhook_signature:
        body = await request.body()
        if not verify_webhook_signature(
            body, x_webhook_signature, settings.TECH_WEBHOOK_SECRET
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    # Validate payload
    book_id = payload.get("book_id")
    n_number = payload.get("n_number")
    status_str = payload.get("status")
    metadata = payload.get("metadata", {})

    if not all([book_id, n_number, status_str]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields: book_id, n_number, status",
        )

    # Convert status string to enum
    try:
        status = WorkflowStatus(status_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_str}",
        )

    # Process the status change
    workflow_service = WorkflowService(db)
    try:
        await workflow_service.update_status_from_tech(
            book_id=book_id,
            n_number=n_number,
            status=status,
            metadata=metadata,
        )
        
        logger.info(
            f"Processed tech status change: book_id={book_id}, "
            f"n_number={n_number}, status={status}"
        )
        
        return {"status": "success", "message": "Status update processed"}
        
    except Exception as e:
        logger.error(f"Error processing tech status change: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process status update",
        )


@router.post("/techzip/completion")
async def techzip_completion(
    request: Request,
    payload: Dict[str, Any],
    x_webhook_signature: str = Header(None, alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Handle completion webhook from technical-fountain-series-support-tool.
    
    Expected payload:
    {
        "n_number": "N02279",
        "repository_name": "fountain-N02279",
        "status": "completed",
        "metadata": {...}
    }
    """
    # Verify webhook signature
    if x_webhook_signature:
        body = await request.body()
        if not verify_webhook_signature(
            body, x_webhook_signature, settings.TECH_WEBHOOK_SECRET
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    # Validate payload
    n_number = payload.get("n_number")
    repository_name = payload.get("repository_name")
    status_str = payload.get("status")
    metadata = payload.get("metadata", {})

    if not all([n_number, repository_name]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields: n_number, repository_name",
        )

    # Process the completion
    workflow_service = WorkflowService(db)
    try:
        await workflow_service.mark_completed_from_techzip(
            n_number=n_number,
            repository_name=repository_name,
            metadata=metadata,
        )
        
        logger.info(
            f"Processed techzip completion: n_number={n_number}, "
            f"repository={repository_name}"
        )
        
        return {"status": "success", "message": "Completion processed"}
        
    except Exception as e:
        logger.error(f"Error processing techzip completion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process completion",
        )