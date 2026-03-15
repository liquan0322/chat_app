from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# ========== 核心：导入日志实例 ==========
from app.core.logging import api_logger, db_logger

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
    api_logger.info(f"接收到创建群组请求 - 创建者ID：{group_in.creator_id}，群组名称：{group_in.name}")
    try:
        group, msg = await GroupConversationCRUD.create_group(
            db, creator_id=group_in.creator_id, group_name=group_in.name
        )
        if not group:
            api_logger.warning(f"创建群组失败 - 创建者ID：{group_in.creator_id}，群组名称：{group_in.name}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"群组创建成功 - 群组ID：{group.id}，创建者ID：{group.creator_id}，群组名称：{group.name}")
        return ResponseModel(
            code=200, message=msg, data=GroupResponse.from_orm(group)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"创建群组异常 - 创建者ID：{group_in.creator_id}，群组名称：{group_in.name}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="创建群组时发生服务器内部错误")


@router.get("/{group_id}", response_model=ResponseModel, summary="查询单个群组")
async def get_group(
        group_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.debug(f"接收到查询单个群组请求 - 群组ID：{group_id}")
    try:
        group = await GroupConversationCRUD.get_group_by_id(db, group_id)
        if not group:
            api_logger.warning(f"查询单个群组失败 - 群组ID：{group_id}，原因：群组不存在")
            raise HTTPException(status_code=404, detail="群组不存在")

        api_logger.info(f"查询单个群组成功 - 群组ID：{group_id}，创建者ID：{group.creator_id}，群组名称：{group.name}")
        return ResponseModel(
            code=200, message="查询成功", data=GroupResponse.from_orm(group)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"查询单个群组异常 - 群组ID：{group_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询单个群组时发生服务器内部错误")


@router.get("/creator/{user_id}", response_model=ResponseModel, summary="查询用户创建的群组")
async def get_user_created_groups(
        user_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到查询用户创建的群组请求 - 用户ID：{user_id}，跳过：{skip}，每页条数：{limit}")
    try:
        groups = await GroupConversationCRUD.get_user_created_groups(db, user_id, skip, limit)
        data = [GroupResponse.from_orm(g) for g in groups]
        group_count = len(data)
        group_ids = [str(g.id) for g in groups]

        api_logger.info(
            f"查询用户创建的群组成功 - 用户ID：{user_id}，共查询到 {group_count} 个群组：{','.join(group_ids)}，跳过：{skip}，每页条数：{limit}")
        return ResponseModel(
            code=200, message="查询成功", data=data
        )
    except Exception as e:
        api_logger.error(
            f"查询用户创建的群组异常 - 用户ID：{user_id}，跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询用户创建的群组时发生服务器内部错误")


@router.put("/{group_id}/name", response_model=ResponseModel, summary="更新群组名称")
async def update_group_name(
        group_id: int,
        group_in: GroupUpdate,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到更新群组名称请求 - 群组ID：{group_id}，新名称：{group_in.name}")
    try:
        group, msg = await GroupConversationCRUD.update_group_name(db, group_id, group_in.name)
        if not group:
            api_logger.warning(f"更新群组名称失败 - 群组ID：{group_id}，新名称：{group_in.name}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"更新群组名称成功 - 群组ID：{group_id}，更新后名称：{group.name}")
        return ResponseModel(
            code=200, message=msg, data=GroupResponse.from_orm(group)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"更新群组名称异常 - 群组ID：{group_id}，新名称：{group_in.name}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="更新群组名称时发生服务器内部错误")


@router.delete("/{group_id}", response_model=ResponseModel, summary="删除群组（级联删所有关联数据）")
async def delete_group(
        group_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.warning(f"接收到删除群组请求 - 群组ID：{group_id}（级联删除成员/机器人/消息/状态）")
    try:
        is_del, msg = await GroupConversationCRUD.delete_group(db, group_id)
        if not is_del:
            api_logger.error(f"删除群组失败 - 群组ID：{group_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"删除群组成功 - 群组ID：{group_id}（已级联删除所有关联数据）")
        return ResponseModel(
            code=200, message=msg, data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.critical(
            f"删除群组异常 - 群组ID：{group_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="删除群组时发生服务器内部错误")


# ------------------------------
# 群组成员接口
# ------------------------------
@router.post("/members", response_model=ResponseModel, summary="添加群组成员")
async def add_group_member(
        member_in: GroupMemberCreate,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到添加群组成员请求 - 群组ID：{member_in.group_id}，用户ID：{member_in.user_id}")
    try:
        member, msg = await GroupMemberCRUD.add_member_to_group(
            db, group_id=member_in.group_id, user_id=member_in.user_id
        )
        if not member:
            api_logger.warning(f"添加群组成员失败 - 群组ID：{member_in.group_id}，用户ID：{member_in.user_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(
            f"添加群组成员成功 - 群组ID：{member.group_id}，用户ID：{member.user_id}，加入时间：{member.created_at}")
        return ResponseModel(
            code=200, message=msg, data=GroupMemberResponse.from_orm(member)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"添加群组成员异常 - 群组ID：{member_in.group_id}，用户ID：{member_in.user_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="添加群组成员时发生服务器内部错误")


@router.get("/{group_id}/members", response_model=ResponseModel, summary="查询群组成员")
async def get_group_members(
        group_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.debug(f"接收到查询群组成员请求 - 群组ID：{group_id}")
    try:
        members = await GroupMemberCRUD.get_group_members(db, group_id)
        data = [GroupMemberResponse.from_orm(m) for m in members]
        member_count = len(data)
        member_ids = [str(m.user_id) for m in members]

        api_logger.info(f"查询群组成员成功 - 群组ID：{group_id}，共查询到 {member_count} 名成员：{','.join(member_ids)}")
        return ResponseModel(
            code=200, message="查询成功", data=data
        )
    except Exception as e:
        api_logger.error(
            f"查询群组成员异常 - 群组ID：{group_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询群组成员时发生服务器内部错误")


@router.get("/members/user/{user_id}", response_model=ResponseModel, summary="查询用户加入的群组")
async def get_user_groups(
        user_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到查询用户加入的群组请求 - 用户ID：{user_id}")
    try:
        members = await GroupMemberCRUD.get_user_groups(db, user_id)
        # 提取群组ID列表（如需完整群组信息可关联查询）
        data = [{"group_id": m.group_id, "join_time": m.created_at} for m in members]
        group_count = len(data)
        group_ids = [str(d["group_id"]) for d in data]

        api_logger.info(f"查询用户加入的群组成功 - 用户ID：{user_id}，共加入 {group_count} 个群组：{','.join(group_ids)}")
        return ResponseModel(
            code=200, message="查询成功", data=data
        )
    except Exception as e:
        api_logger.error(
            f"查询用户加入的群组异常 - 用户ID：{user_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询用户加入的群组时发生服务器内部错误")


@router.delete("/{group_id}/members/{user_id}", response_model=ResponseModel, summary="移出群组成员")
async def remove_group_member(
        group_id: int,
        user_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.warning(f"接收到移出群组成员请求 - 群组ID：{group_id}，用户ID：{user_id}")
    try:
        is_del, msg = await GroupMemberCRUD.remove_member_from_group(db, group_id, user_id)
        if not is_del:
            api_logger.error(f"移出群组成员失败 - 群组ID：{group_id}，用户ID：{user_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"移出群组成员成功 - 群组ID：{group_id}，用户ID：{user_id}")
        return ResponseModel(
            code=200, message=msg, data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"移出群组成员异常 - 群组ID：{group_id}，用户ID：{user_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="移出群组成员时发生服务器内部错误")


# ------------------------------
# 群组机器人接口
# ------------------------------
@router.post("/robots", response_model=ResponseModel, summary="添加机器人到群组")
async def add_group_robot(
        robot_in: GroupRobotCreate,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到添加机器人到群组请求 - 群组ID：{robot_in.group_id}，机器人ID：{robot_in.robot_id}")
    try:
        group_robot, msg = await GroupRobotCRUD.add_robot_to_group(
            db, group_id=robot_in.group_id, robot_id=robot_in.robot_id
        )
        if not group_robot:
            api_logger.warning(
                f"添加机器人到群组失败 - 群组ID：{robot_in.group_id}，机器人ID：{robot_in.robot_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"添加机器人到群组成功 - 群组ID：{group_robot.group_id}，机器人ID：{group_robot.robot_id}")
        return ResponseModel(
            code=200, message=msg, data=GroupRobotResponse.from_orm(group_robot)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"添加机器人到群组异常 - 群组ID：{robot_in.group_id}，机器人ID：{robot_in.robot_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="添加机器人到群组时发生服务器内部错误")


@router.get("/{group_id}/robots", response_model=ResponseModel, summary="查询群组机器人")
async def get_group_robots(
        group_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.debug(f"接收到查询群组机器人请求 - 群组ID：{group_id}")
    try:
        robots = await GroupRobotCRUD.get_group_robots(db, group_id)
        data = [GroupRobotResponse.from_orm(r) for r in robots]
        robot_count = len(data)
        robot_ids = [str(r.robot_id) for r in robots]

        api_logger.info(f"查询群组机器人成功 - 群组ID：{group_id}，共查询到 {robot_count} 个机器人：{','.join(robot_ids)}")
        return ResponseModel(
            code=200, message="查询成功", data=data
        )
    except Exception as e:
        api_logger.error(
            f"查询群组机器人异常 - 群组ID：{group_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询群组机器人时发生服务器内部错误")


@router.delete("/{group_id}/robots/{robot_id}", response_model=ResponseModel, summary="移出群组机器人")
async def remove_group_robot(
        group_id: int,
        robot_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.warning(f"接收到移出群组机器人请求 - 群组ID：{group_id}，机器人ID：{robot_id}")
    try:
        is_del, msg = await GroupRobotCRUD.remove_robot_from_group(db, group_id, robot_id)
        if not is_del:
            api_logger.error(f"移出群组机器人失败 - 群组ID：{group_id}，机器人ID：{robot_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"移出群组机器人成功 - 群组ID：{group_id}，机器人ID：{robot_id}")
        return ResponseModel(
            code=200, message=msg, data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"移出群组机器人异常 - 群组ID：{group_id}，机器人ID：{robot_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="移出群组机器人时发生服务器内部错误")


# ------------------------------
# 群组消息接口
# ------------------------------
@router.post("/messages", response_model=ResponseModel, summary="发送群组消息")
async def send_group_message(
        message_in: GroupMessageCreate,
        db: AsyncSession = Depends(get_async_db)
):
    # 消息内容脱敏（避免日志过长/敏感信息）
    msg_content = message_in.message[:50] + "..." if len(message_in.message) > 50 else message_in.message
    sender_type = "人类" if message_in.is_human else "机器人"
    sender_info = f"发送者ID：{message_in.sender_id}" if message_in.is_human else f"机器人ID：{message_in.robot_id}"

    api_logger.info(
        f"接收到发送群组消息请求 - 群组ID：{message_in.group_id}，{sender_info}，"
        f"是否人类消息：{message_in.is_human}，回复消息ID：{message_in.reply_to_message_id}，消息内容：{msg_content}"
    )
    try:
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
            api_logger.warning(
                f"发送群组消息失败 - 群组ID：{message_in.group_id}，{sender_info}，原因：{msg}"
            )
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(
            f"发送群组消息成功 - 消息ID：{message.id}，群组ID：{message.group_id}，"
            f"是否人类消息：{message.is_human}，发送时间：{message.created_at}"
        )
        return ResponseModel(
            code=200, message=msg, data=GroupMessageResponse.from_orm(message)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"发送群组消息异常 - 群组ID：{message_in.group_id}，{sender_info}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="发送群组消息时发生服务器内部错误")


@router.get("/{group_id}/messages", response_model=ResponseModel, summary="查询群组消息")
async def get_group_messages(
        group_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=200),
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到查询群组消息请求 - 群组ID：{group_id}，跳过：{skip}，每页条数：{limit}")
    try:
        messages = await GroupMessageCRUD.get_group_messages(db, group_id, skip, limit)
        data = [GroupMessageResponse.from_orm(m) for m in messages]
        message_count = len(data)

        api_logger.info(
            f"查询群组消息成功 - 群组ID：{group_id}，共查询到 {message_count} 条消息，跳过：{skip}，每页条数：{limit}")
        return ResponseModel(
            code=200, message="查询成功", data=data
        )
    except Exception as e:
        api_logger.error(
            f"查询群组消息异常 - 群组ID：{group_id}，跳过：{skip}，每页条数：{limit}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询群组消息时发生服务器内部错误")


@router.delete("/messages/{message_id}", response_model=ResponseModel, summary="删除群组消息")
async def delete_group_message(
        message_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.warning(f"接收到删除群组消息请求 - 消息ID：{message_id}")
    try:
        is_del, msg = await GroupMessageCRUD.delete_group_message(db, message_id)
        if not is_del:
            api_logger.error(f"删除群组消息失败 - 消息ID：{message_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"删除群组消息成功 - 消息ID：{message_id}")
        return ResponseModel(
            code=200, message=msg, data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"删除群组消息异常 - 消息ID：{message_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="删除群组消息时发生服务器内部错误")


# ------------------------------
# 群组状态接口
# ------------------------------
@router.get("/{group_id}/state", response_model=ResponseModel, summary="查询群组状态")
async def get_group_state(
        group_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.debug(f"接收到查询群组状态请求 - 群组ID：{group_id}")
    try:
        state = await GroupConversationStateCRUD.get_group_state(db, group_id)
        if not state:
            api_logger.warning(f"查询群组状态失败 - 群组ID：{group_id}，原因：群组状态不存在")
            raise HTTPException(status_code=404, detail="群组状态不存在")

        api_logger.info(
            f"查询群组状态成功 - 群组ID：{group_id}，机器人连续回复数：{state.robot_continuous_replies}，"
            f"最后活跃时间：{state.last_active_at}"
        )
        return ResponseModel(
            code=200, message="查询成功", data=GroupStateResponse.from_orm(state)
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"查询群组状态异常 - 群组ID：{group_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="查询群组状态时发生服务器内部错误")


@router.post("/{group_id}/state/reset", response_model=ResponseModel, summary="重置机器人连续回复数")
async def reset_robot_replies(
        group_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    api_logger.info(f"接收到重置机器人连续回复数请求 - 群组ID：{group_id}")
    try:
        is_reset, msg = await GroupConversationStateCRUD.reset_robot_replies(db, group_id)
        if not is_reset:
            api_logger.warning(f"重置机器人连续回复数失败 - 群组ID：{group_id}，原因：{msg}")
            raise HTTPException(status_code=400, detail=msg)

        api_logger.info(f"重置机器人连续回复数成功 - 群组ID：{group_id}")
        return ResponseModel(
            code=200, message=msg, data=True
        )
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(
            f"重置机器人连续回复数异常 - 群组ID：{group_id}，异常信息：{str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="重置机器人连续回复数时发生服务器内部错误")