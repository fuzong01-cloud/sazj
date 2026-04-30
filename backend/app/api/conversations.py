from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth import get_current_user
from app.repositories.conversation_repository import (
    count_conversations,
    delete_conversation,
    get_conversation_detail,
    list_conversations_page,
    rename_conversation,
)
from app.schemas.auth import UserPublic
from app.schemas.conversation import ConversationDetail, ConversationPage, ConversationRenameRequest, ConversationStored

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationPage)
def list_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserPublic = Depends(get_current_user),
) -> ConversationPage:
    return ConversationPage(
        items=list_conversations_page(user_id=current_user.id, limit=limit, offset=offset),
        total=count_conversations(user_id=current_user.id),
        limit=limit,
        offset=offset,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    current_user: UserPublic = Depends(get_current_user),
) -> ConversationDetail:
    conversation = get_conversation_detail(conversation_id, current_user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_conversation(
    conversation_id: int,
    current_user: UserPublic = Depends(get_current_user),
) -> None:
    if not delete_conversation(conversation_id, current_user.id):
        raise HTTPException(status_code=404, detail="会话不存在")


@router.patch("/{conversation_id}", response_model=ConversationStored)
def update_conversation_title(
    conversation_id: int,
    payload: ConversationRenameRequest,
    current_user: UserPublic = Depends(get_current_user),
) -> ConversationStored:
    conversation = rename_conversation(conversation_id, current_user.id, payload.title)
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conversation
