from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_async_db
from app.crud.group_conversation import (
    GroupConversationCRUD, GroupMemberCRUD, GroupRobotCRUD,
    GroupMessageCRUD, GroupConversationStateCRUD
)
from app.schemas.group_conversation import (
    GroupCreate, GroupUpdate, GroupResponse,
    GroupMemberCreate, GroupMemberResponse,
    GroupRobotCreate, GroupRobotResponse,
    GroupMessageCreate, GroupMessageResponse,
    GroupStateResponse, ResponseModel
)

router = APIRouter(prefix="/groups", tags=["群组对话管理"])

# ------------------------------
# 群组基础接口
# ------------------------------
@router.post("", response_model=ResponseModel, summary="创建群组")
async def create_group(
    group_in: GroupCreate,
    db: AsyncSession = Depends(get_async_db)
):
    group, msg = await GroupConversationCRUD.create_group(
        db, creator_id=group_in.creator_id, group_name=group_in.name
    )
    if not group:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=GroupResponse.from_orm(group)
    )

@router.get("/{group_id}", response_model=ResponseModel, summary="查询单个群组")
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    group = await GroupConversationCRUD.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    return ResponseModel(
        code=200, message="查询成功", data=GroupResponse.from_orm(group)
    )

@router.get("/creator/{user_id}", response_model=ResponseModel, summary="查询用户创建的群组")
async def get_user_created_groups(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    groups = await GroupConversationCRUD.get_user_created_groups(db, user_id, skip, limit)
    data = [GroupResponse.from_orm(g) for g in groups]
    return ResponseModel(
        code=200, message="查询成功", data=data
    )

@router.put("/{group_id}/name", response_model=ResponseModel, summary="更新群组名称")
async def update_group_name(
    group_id: int,
    group_in: GroupUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    group, msg = await GroupConversationCRUD.update_group_name(db, group_id, group_in.name)
    if not group:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=GroupResponse.from_orm(group)
    )

@router.delete("/{group_id}", response_model=ResponseModel, summary="删除群组（级联删所有关联数据）")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    is_del, msg = await GroupConversationCRUD.delete_group(db, group_id)
    if not is_del:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=True
    )

# ------------------------------
# 群组成员接口
# ------------------------------
@router.post("/members", response_model=ResponseModel, summary="添加群组成员")
async def add_group_member(
    member_in: GroupMemberCreate,
    db: AsyncSession = Depends(get_async_db)
):
    member, msg = await GroupMemberCRUD.add_member_to_group(
        db, group_id=member_in.group_id, user_id=member_in.user_id
    )
    if not member:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=GroupMemberResponse.from_orm(member)
    )

@router.get("/{group_id}/members", response_model=ResponseModel, summary="查询群组成员")
async def get_group_members(
    group_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    members = await GroupMemberCRUD.get_group_members(db, group_id)
    data = [GroupMemberResponse.from_orm(m) for m in members]
    return ResponseModel(
        code=200, message="查询成功", data=data
    )

@router.get("/members/user/{user_id}", response_model=ResponseModel, summary="查询用户加入的群组")
async def get_user_groups(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    members = await GroupMemberCRUD.get_user_groups(db, user_id)
    # 提取群组ID列表（如需完整群组信息可关联查询）
    data = [{"group_id": m.group_id, "join_time": m.created_at} for m in members]
    return ResponseModel(
        code=200, message="查询成功", data=data
    )

@router.delete("/{group_id}/members/{user_id}", response_model=ResponseModel, summary="移出群组成员")
async def remove_group_member(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    is_del, msg = await GroupMemberCRUD.remove_member_from_group(db, group_id, user_id)
    if not is_del:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=True
    )

# ------------------------------
# 群组机器人接口
# ------------------------------
@router.post("/robots", response_model=ResponseModel, summary="添加机器人到群组")
async def add_group_robot(
    robot_in: GroupRobotCreate,
    db: AsyncSession = Depends(get_async_db)
):
    group_robot, msg = await GroupRobotCRUD.add_robot_to_group(
        db, group_id=robot_in.group_id, robot_id=robot_in.robot_id
    )
    if not group_robot:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=GroupRobotResponse.from_orm(group_robot)
    )

@router.get("/{group_id}/robots", response_model=ResponseModel, summary="查询群组机器人")
async def get_group_robots(
    group_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    robots = await GroupRobotCRUD.get_group_robots(db, group_id)
    data = [GroupRobotResponse.from_orm(r) for r in robots]
    return ResponseModel(
        code=200, message="查询成功", data=data
    )

@router.delete("/{group_id}/robots/{robot_id}", response_model=ResponseModel, summary="移出群组机器人")
async def remove_group_robot(
    group_id: int,
    robot_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    is_del, msg = await GroupRobotCRUD.remove_robot_from_group(db, group_id, robot_id)
    if not is_del:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=True
    )

# ------------------------------
# 群组消息接口
# ------------------------------
@router.post("/messages", response_model=ResponseModel, summary="发送群组消息")
async def send_group_message(
    message_in: GroupMessageCreate,
    db: AsyncSession = Depends(get_async_db)
):
    message, msg = await GroupMessageCRUD.send_group_message(
        db,
        group_id=message_in.group_id,
        message=message_in.message,
        is_human=message_in.is_human,
        sender_id=message_in.sender_id,
        robot_id=message_in.robot_id,
        reply_to_message_id=message_in.reply_to_message_id
    )
    if not message:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=GroupMessageResponse.from_orm(message)
    )

@router.get("/{group_id}/messages", response_model=ResponseModel, summary="查询群组消息")
async def get_group_messages(
    group_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db)
):
    messages = await GroupMessageCRUD.get_group_messages(db, group_id, skip, limit)
    data = [GroupMessageResponse.from_orm(m) for m in messages]
    return ResponseModel(
        code=200, message="查询成功", data=data
    )

@router.delete("/messages/{message_id}", response_model=ResponseModel, summary="删除群组消息")
async def delete_group_message(
    message_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    is_del, msg = await GroupMessageCRUD.delete_group_message(db, message_id)
    if not is_del:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=True
    )

# ------------------------------
# 群组状态接口
# ------------------------------
@router.get("/{group_id}/state", response_model=ResponseModel, summary="查询群组状态")
async def get_group_state(
    group_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    state = await GroupConversationStateCRUD.get_group_state(db, group_id)
    if not state:
        raise HTTPException(status_code=404, detail="群组状态不存在")
    return ResponseModel(
        code=200, message="查询成功", data=GroupStateResponse.from_orm(state)
    )

@router.post("/{group_id}/state/reset", response_model=ResponseModel, summary="重置机器人连续回复数")
async def reset_robot_replies(
    group_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    is_reset, msg = await GroupConversationStateCRUD.reset_robot_replies(db, group_id)
    if not is_reset:
        raise HTTPException(status_code=400, detail=msg)
    return ResponseModel(
        code=200, message=msg, data=True
    )