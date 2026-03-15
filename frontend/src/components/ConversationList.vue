<template>
  <div class="conversation-list">
    <div class="conversation-header">
      <el-input
        v-model="tagFilter"
        placeholder="按标签筛选..."
        style="width: 200px; margin-right: 10px;"
        @input="fetchConversations"
      />
      <el-button type="primary" @click="createNewConversation">
        <el-icon><Plus /></el-icon>
        新建对话
      </el-button>
    </div>

    <el-list border :data="conversations" class="conversation-list-items">
      <el-list-item
        v-for="item in conversations"
        :key="item.id"
        :class="{ active: item.id === currentConversationId }"
        @click="selectConversation(item.id)"
      >
        <template #header>
          <div class="conversation-title">
            {{ item.title }}
            <el-button
              size="small"
              type="text"
              @click.stop="editTitle(item.id, item.title)"
            >
              <el-icon><Edit /></el-icon>
            </el-button>
          </div>
        </template>
        <div class="conversation-tags">
          <el-tag
            v-for="tag in item.tags"
            :key="tag.tag_name"
            size="small"
            @click.stop="removeTag(item.id, tag.tag_name)"
          >
            {{ tag.tag_name }}
            <el-icon class="tag-close"><Close /></el-icon>
          </el-tag>
          <el-button
            size="small"
            type="text"
            @click.stop="addTag(item.id)"
          >
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>
        <el-button
          size="small"
          type="danger"
          text
          @click.stop="handleDeleteConversation(item.id)"  <!-- 👈 修改函数名 -->
          class="delete-btn"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </el-list-item>
    </el-list>

    <!-- 标题编辑弹窗（补充缺失的弹窗模板） -->
    <el-dialog
      v-model="titleDialogVisible"
      title="编辑对话标题"
      width="300px"
      @confirm="saveTitle"
    >
      <el-input v-model="newTitle" placeholder="请输入对话标题" />
    </el-dialog>

    <!-- 标签添加弹窗（补充缺失的弹窗模板） -->
    <el-dialog
      v-model="tagDialogVisible"
      title="添加对话标签"
      width="300px"
      @confirm="saveTag"
    >
      <el-input v-model="newTag" placeholder="请输入标签名称" />
    </el-dialog>
  </template>
</script>

<script setup>
import { ref, onMounted } from 'vue'
// 👈 1. 补充导入 ElMessageBox 和缺失的组件
import {
  ElMessage, ElInput, ElTag, ElButton, ElList, ElListItem,
  ElIcon, ElDialog, ElMessageBox
} from 'element-plus'
import { Plus, Edit, Close, Delete, Warning } from '@element-plus/icons-vue'
// 👈 2. 保留导入的 deleteConversation API
import {
  getConversations, createConversation, updateConversation,
  deleteConversation, addConversationTag
} from '@/api/conversation'
import { useChatStore } from '@/store'

const chatStore = useChatStore()

const props = defineProps({
  currentConversationId: {
    type: [String, Number],
    default: ''
  }
})

const emit = defineEmits(['conversationSelected'])

const conversations = ref([])
const tagFilter = ref('')
const tagDialogVisible = ref(false)
const newTag = ref('')
const currentTagConversationId = ref('')
const titleDialogVisible = ref(false)
const newTitle = ref('')
const currentTitleConversationId = ref('')

// 获取对话列表
const fetchConversations = async () => {
  try {
    const res = await getConversations(tagFilter.value)
    conversations.value = res
  } catch (error) {
    ElMessage.error('获取对话列表失败')
  }
}

// 创建新对话
const createNewConversation = async () => {
  try {
    const res = await createConversation()
    ElMessage.success('创建成功')
    fetchConversations()
    selectConversation(res.id)
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

// 选择对话
const selectConversation = (id) => {
  chatStore.setCurrentConversationId(id)
  emit('conversationSelected', id)
}

// 编辑标题
const editTitle = (id, title) => {
  currentTitleConversationId.value = id
  newTitle.value = title
  titleDialogVisible.value = true
}

// 保存标题
const saveTitle = async () => {
  if (!newTitle.value.trim()) {
    ElMessage.warning('标题不能为空')
    return
  }

  try {
    await updateConversation(currentTitleConversationId.value, newTitle.value)
    ElMessage.success('更新成功')
    titleDialogVisible.value = false
    fetchConversations()
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// 添加标签
const addTag = (id) => {
  currentTagConversationId.value = id
  newTag.value = ''
  tagDialogVisible.value = true
}

// 保存标签
const saveTag = async () => {
  if (!newTag.value.trim()) {
    ElMessage.warning('标签不能为空')
    return
  }

  try {
    await addConversationTag(currentTagConversationId.value, newTag.value)
    ElMessage.success('添加标签成功')
    tagDialogVisible.value = false
    fetchConversations()
  } catch (error) {
    ElMessage.error('添加标签失败')
  }
}

// 删除标签（重新获取列表即可）
const removeTag = (id, tagName) => {
  // 这里简化处理，实际项目中需要调用删除标签的API
  ElMessage.info('标签删除功能需实现对应API')
  fetchConversations()
}

// 👈 3. 重命名函数，避免和导入的 deleteConversation 冲突
const handleDeleteConversation = async (id) => {
  try {
    await ElMessageBox.confirm(
      '此操作将永久删除该对话及其所有消息, 是否继续?',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    // 👈 调用导入的 deleteConversation API
    await deleteConversation(id)
    ElMessage.success('删除成功')
    fetchConversations()
    if (id === props.currentConversationId) {
      selectConversation('')
    }
  } catch (error) {
    ElMessage.info('已取消删除')
  }
}

onMounted(() => {
  fetchConversations()
})
</script>

<style scoped>
.conversation-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.conversation-header {
  padding: 10px;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
}

.conversation-list-items {
  flex: 1;
  overflow-y: auto;
}

.conversation-list-items .el-list-item {
  cursor: pointer;
}

.conversation-list-items .el-list-item.active {
  background-color: #e3f2fd;
}

.conversation-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.conversation-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.tag-close {
  margin-left: 4px;
  cursor: pointer;
}

.delete-btn {
  margin-left: auto;
}
</style>