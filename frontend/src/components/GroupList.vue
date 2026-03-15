<template>
  <div class="group-list">
    <div class="group-header">
      <el-button type="primary" @click="createNewGroup">
        <el-icon><Plus /></el-icon>
        新建群组
      </el-button>
    </div>

    <el-list border :data="groups" class="group-list-items">
      <el-list-item
        v-for="item in groups"
        :key="item.id"
        :class="{ active: item.id === currentGroupId }"
        @click="selectGroup(item.id)"
      >
        <div class="group-title">{{ item.title }}</div>
        <div class="group-members">
          成员: {{ item.members.length }}人/机器人
        </div>
      </el-list-item>
    </el-list>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElButton, ElList, ElListItem, ElIcon } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getGroups, createGroup } from '@/api/group'
import { useChatStore } from '@/store'

const chatStore = useChatStore()

const props = defineProps({
  currentGroupId: {
    type: [String, Number],
    default: ''
  }
})

const emit = defineEmits(['groupSelected'])

const groups = ref([])

// 获取群组列表
const fetchGroups = async () => {
  try {
    const res = await getGroups()
    groups.value = res
  } catch (error) {
    ElMessage.error('获取群组列表失败')
  }
}

// 创建新群组
const createNewGroup = async () => {
  try {
    const res = await createGroup('新群组', [1, 2, 3])
    ElMessage.success('创建成功')
    fetchGroups()
    selectGroup(res.id)
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

// 选择群组
const selectGroup = (id) => {
  chatStore.setCurrentGroupId(id)
  emit('groupSelected', id)
}

onMounted(() => {
  fetchGroups()
})
</script>

<style scoped>
.group-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.group-header {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.group-list-items {
  flex: 1;
  overflow-y: auto;
}

.group-list-items .el-list-item {
  cursor: pointer;
}

.group-list-items .el-list-item.active {
  background-color: #e3f2fd;
}

.group-title {
  font-weight: bold;
}

.group-members {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}
</style>