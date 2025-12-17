<template>
  <div id="app-container">
    <!-- 未登入狀態 -->
    <div v-if="!isAuthenticated" class="login-container">
      <div class="login-card">
        <h1>Threads Reply 搜尋器</h1>
        <p class="app-description">
          這是一個幫助你搜尋和管理 Threads 回覆的工具。你可以透過關鍵字快速找到特定的回覆內容，並查看完整的訊息詳情。
        </p>
        
        <div class="requirements-box">
          <h3>📋 使用前提條件</h3>
          <ul>
            <li>✅ 擁有 <strong>Meta Developer 帳號</strong></li>
            <li>✅ 已建立 <strong>Threads App</strong></li>
            <li>✅ 已設定 OAuth 重定向 URI</li>
          </ul>
          <p class="note">
            💡 詳細設定步驟請參考 <a href="#" class="readme-link">README 文件</a>
          </p>
        </div>

        <button @click="connectThreads" class="btn-primary">
          🚀 連接 Threads 帳號
        </button>
      </div>
    </div>

    <!-- 已登入狀態 -->
    <div v-else class="main-layout">
      <!-- 查詢表單 -->
      <header class="search-header">
        <div class="header-content">
          <div class="header-top">
            <h2>搜尋我的 Replies</h2>
            <button @click="logout" class="btn-logout">登出</button>
          </div>

          <!-- Mobile header collapse tab -->
          <button @click="toggleHeader" class="header-collapse-tab mobile-only" aria-label="Toggle header">
            <span class="arrow-icon">{{ headerCollapsed ? '↓' : '↑' }}</span>
          </button>

          <form @submit.prevent="searchThreads" :class="['search-form', { collapsed: headerCollapsed }]">
            <div class="form-group">
              <label>查詢數量 (limit)</label>
              <input
                v-model.number="form.limit"
                type="number"
                min="1"
                max="100"
                required
              >
            </div>
            <div class="form-group">
              <label>關鍵字 (選填)</label>
              <input
                v-model="form.keywords"
                type="text"
                placeholder="輸入關鍵字過濾 replies..."
              >
            </div>
            <button type="submit" :disabled="loading" class="btn-search">
              <span v-if="loading">⏳ 搜尋中...</span>
              <span v-else>🔍 搜尋 Replies</span>
            </button>

            <!-- Export section -->
            <div v-if="results.length > 0" class="export-section">
              <div class="current-search">
                <span class="search-label">目前搜尋關鍵字：</span>
                <span class="search-value">{{ form.keywords || '無' }}</span>
              </div>
              <button @click="exportToCSV" class="btn-export">
                📊 匯出 CSV
              </button>
            </div>
          </form>
        </div>
      </header>

      <!-- 有結果：兩欄布局 -->
      <div v-if="results.length > 0" class="results-layout">
        <!-- Mobile Toggle Button -->
        <button @click="toggleSidebar" class="mobile-toggle" aria-label="Toggle sidebar">
          <span class="hamburger-icon">☰</span>
          <span class="results-count">{{ results.length }} 筆結果</span>
        </button>

        <!-- Overlay for mobile -->
        <div
          v-if="sidebarOpen"
          class="sidebar-overlay"
          @click="sidebarOpen = false"
        ></div>

        <!-- Left Sidebar -->
        <aside :class="['sidebar', { open: sidebarOpen }]">
          <div class="sidebar-header">
            <h3>找到 {{ results.length }} 筆結果</h3>
            <button @click="sidebarOpen = false" class="close-sidebar" aria-label="Close sidebar">✕</button>
          </div>
          <div class="sidebar-content">
            <div
              v-for="(item, index) in results"
              :key="item.media_id"
              @click="selectMessage(index)"
              :class="['result-item', { active: selectedIndex === index }]"
            >
              <div class="result-header">
                <div class="result-date">{{ formatDateTime(item.timestamp) }}</div>
                <div class="result-author" v-if="item.username">@{{ item.username }}</div>
              </div>
              <div class="result-preview">
                {{ item.first_5_words }}
              </div>
            </div>
          </div>
        </aside>

        <!-- Right Content -->
        <main class="content">
          <div v-if="selectedIndex !== null" class="message-detail">
            <div class="message-meta">
              <span class="message-date">{{ formatDateTime(results[selectedIndex].timestamp) }}</span>
              <span class="message-username" v-if="results[selectedIndex].username">@{{ results[selectedIndex].username }}</span>
            </div>
            <h4>訊息內容</h4>
            <div class="message-text">
              {{ results[selectedIndex].first_5_words }}
            </div>
            <button
              @click="openPermalink(results[selectedIndex].permalink)"
              class="btn-permalink"
            >
              開啟 Threads 連結 →
            </button>
          </div>
          <div v-else class="empty-state">
            <div class="empty-icon">👈</div>
            <p>請從左側選擇一則訊息</p>
          </div>
        </main>
      </div>

      <!-- 無結果 -->
      <div v-else-if="searched && !loading" class="no-results">
        <div class="no-results-icon">😅</div>
        <h3>沒有找到符合條件的 replies</h3>
        <p>試試調整關鍵字或增加查詢數量。</p>
        <button @click="resetForm" class="btn-reset">
          🔄 重新搜尋
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const isAuthenticated = ref(false)
const loading = ref(false)
const results = ref([])
const searched = ref(false)
const selectedIndex = ref(null)
const sidebarOpen = ref(false)
const headerCollapsed = ref(false)

const form = ref({
  limit: 10,
  keywords: ''
})

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const toggleHeader = () => {
  headerCollapsed.value = !headerCollapsed.value
}

const selectMessage = (index) => {
  selectedIndex.value = index
  // Close sidebar on mobile after selection
  if (window.innerWidth <= 620) {
    sidebarOpen.value = false
  }
}

const formatDateTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const connectThreads = () => {
  window.location.href = 'https://oauth.boatswain.cc/api/auth/threads/start'
}

const logout = () => {
  window.location.href = 'https://oauth.boatswain.cc/logout'
}

const checkAuth = async () => {
  console.log('🔍 Vue 載入，開始 checkAuth...')

  try {
    const res = await fetch('https://oauth.boatswain.cc/api/auth/status', {
      credentials: 'include'
    })
    const data = await res.json()
    console.log('📡 /api/auth/status 回傳:', data)

    isAuthenticated.value = !!data.authenticated
    console.log(`✅ 認證狀態: ${isAuthenticated.value ? '已登入' : '未登入'}`)
  } catch (e) {
    console.error('💥 checkAuth 失敗:', e)
    isAuthenticated.value = false
  }

  // 處理 URL params（只用於顯示訊息，不存取 token）
  const urlParams = new URLSearchParams(window.location.search)
  const loginParam = urlParams.get('login')
  if (loginParam === 'success') {
    console.log('✅ OAuth 登入成功')
    window.history.replaceState({}, document.title, window.location.pathname)
  } else if (loginParam === 'failed') {
    alert('登入失敗，請重試')
    window.history.replaceState({}, document.title, window.location.pathname)
  }
}

const searchThreads = async () => {
  loading.value = true
  searched.value = true
  results.value = []

  try {
    const params = new URLSearchParams({
      limit: form.value.limit.toString(),
      q: form.value.keywords || ""
    })

    const res = await fetch(`https://oauth.boatswain.cc/api/threads?${params}`, {
      credentials: 'include'
    })

    const data = await res.json()
    console.log('📡 backend /api/threads 回傳:', data)

    if (!res.ok) {
      if (data.error === 'not_authenticated') {
        alert('登入過期，請重新連接 Threads')
      } else {
        alert(`後端錯誤: ${data.error || 'unknown'} (${data.status_code || res.status})`)
      }
      return
    }

    results.value = (data.results || []).map(item => ({
      media_id: item.media_id,
      text: item.text,
      first_5_words: item.preview,
      permalink: item.permalink,
      timestamp: item.timestamp,
      username: item.username
    }))

    selectedIndex.value = 0
  } catch (e) {
    console.error('💥 /api/threads 失敗:', e)
    results.value = []
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value.keywords = ''
  results.value = []
  searched.value = false
  selectedIndex.value = null
}

const openPermalink = (url) => {
  window.open(url, '_blank', 'noopener,noreferrer')
}

const exportToCSV = () => {
  if (results.value.length === 0) return

  // CSV headers
  const headers = [
    'Media ID',
    'Username',
    'Text',
    'Preview',
    'Permalink',
    'Timestamp',
    'Search Keywords',
    'Search Limit'
  ]

  // CSV data rows
  const rows = results.value.map(item => [
    item.media_id,
    item.username || '',
    `"${item.text.replace(/"/g, '""')}"`, // Escape quotes in text
    `"${item.first_5_words.replace(/"/g, '""')}"`, // Escape quotes in preview
    item.permalink,
    item.timestamp,
    form.value.keywords || '',
    form.value.limit.toString()
  ])

  // Combine headers and rows
  const csvContent = [headers, ...rows]
    .map(row => row.join(','))
    .join('\n')

  // Create and download the file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', `threads_replies_${new Date().toISOString().split('T')[0]}.csv`)
  link.style.visibility = 'hidden'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

onMounted(() => {
  checkAuth()
})
</script>

<style scoped>
/* Reset and base styles */
* {
  box-sizing: border-box;
}

#app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0f2fe 0%, #ddd6fe 100%);
}

/* Login page */
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
}

.login-card {
  background: white;
  padding: 3rem;
  border-radius: 1rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  max-width: 700px;
  width: 100%;
  text-align: center;
}

.login-card h1 {
  background: linear-gradient(135deg, #2563eb 0%, #9333ea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1rem;
}

.login-card p {
  color: #374151;
  margin-bottom: 2rem;
  font-size: 1.1rem;
}

.app-description {
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.requirements-box {
  background: #f0f9ff;
  border: 2px solid #bfdbfe;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
  text-align: left;
}

.requirements-box h3 {
  margin: 0 0 1rem 0;
  color: #1e40af;
  font-size: 1.125rem;
}

.requirements-box ul {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem 0;
}

.requirements-box li {
  padding: 0.5rem 0;
  color: #374151;
  font-size: 1rem;
}

.requirements-box li strong {
  color: #1f2937;
}

.note {
  margin: 0;
  padding-top: 1rem;
  border-top: 1px solid #bfdbfe;
  font-size: 0.9rem;
  color: #6b7280;
}

.readme-link {
  color: #2563eb;
  text-decoration: underline;
  font-weight: 600;
}

.readme-link:hover {
  color: #1d4ed8;
}

/* Main layout */
.main-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* Header */
.search-header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  position: relative;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.header-top h2 {
  margin: 0;
  color: #1f2937;
  font-size: 1.875rem;
}

.search-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.form-group input {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Buttons */
button {
  cursor: pointer;
  font-weight: 600;
  border: none;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 1rem 3rem;
  font-size: 1.125rem;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3);
}

.btn-logout {
  background: #ef4444;
  color: white;
  padding: 0.5rem 1.5rem;
}

.btn-logout:hover {
  background: #dc2626;
}

.header-collapse-tab {
  position: absolute;
  bottom: -1rem;
  right: 1rem;
  background: white;
  color: #6b7280;
  border-radius: 0 0 0.5rem 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 1.2rem;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

.header-collapse-tab:hover {
  background: #f9fafb;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.arrow-icon {
  display: inline-block;
  transition: transform 0.2s;
}

.search-form.collapsed {
  display: none;
}

.btn-search {
  grid-column: 1 / -1;
  background: linear-gradient(135deg, #2563eb 0%, #9333ea 100%);
  color: white;
  padding: 1rem;
  font-size: 1.25rem;
}

.btn-search:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.3);
}

.btn-search:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-permalink {
  background: #2563eb;
  color: white;
  padding: 1rem 2rem;
  font-size: 1.125rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-permalink:hover {
  background: #1d4ed8;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.btn-reset {
  background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%);
  color: white;
  padding: 1rem 2rem;
  font-size: 1.125rem;
}

.btn-reset:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(245, 158, 11, 0.3);
}

.btn-export {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: white;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-export:hover {
  background: linear-gradient(135deg, #047857 0%, #065f46 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
}

.export-section {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.current-search {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.search-label {
  color: #6b7280;
  font-weight: 500;
}

.search-value {
  color: #374151;
  font-weight: 600;
  background: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid #d1d5db;
}

/* Results layout - TWO COLUMNS */
.results-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Left sidebar */
.sidebar {
  width: 320px;
  background: #f9fafb;
  border-right: 1px solid #d1d5db;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 1rem 1.5rem;
  flex-shrink: 0;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1.25rem;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.result-item {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.result-item.active {
  background: #dbeafe;
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  gap: 0.5rem;
}

.result-date {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 500;
}

.result-author {
  font-size: 0.75rem;
  color: #3b82f6;
  font-weight: 600;
  white-space: nowrap;
}

.result-preview {
  font-size: 0.875rem;
  color: #1f2937;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Right content */
.content {
  flex: 1;
  background: white;
  overflow-y: auto;
  min-width: 0;
}

.message-detail {
  padding: 2rem;
  max-width: 100%;
}

.message-meta {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.message-date {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.message-username {
  font-size: 0.875rem;
  color: #3b82f6;
  font-weight: 600;
}

.message-detail h4 {
  font-size: 2rem;
  color: #1f2937;
  margin: 0 0 1.5rem 0;
}

.message-text {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  font-size: 1.125rem;
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9ca3af;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state p {
  font-size: 1.25rem;
}

/* No results */
.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  text-align: center;
  padding: 2rem;
}

.no-results-icon {
  font-size: 5rem;
  margin-bottom: 1rem;
}

.no-results h3 {
  font-size: 1.875rem;
  color: #374151;
  margin: 0 0 1rem 0;
}

.no-results p {
  font-size: 1.25rem;
  color: #6b7280;
  margin: 0 0 2rem 0;
  max-width: 500px;
}

/* Mobile Responsive - 620px and below */
@media (max-width: 620px) {
  /* Hide sidebar by default on mobile */
  .sidebar {
    position: fixed;
    left: -100%;
    top: 0;
    bottom: 0;
    width: 80%;
    max-width: 300px;
    z-index: 1000;
    transition: left 0.3s ease-in-out;
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  }

  .sidebar.open {
    left: 0;
  }

  /* Sidebar overlay */
  .sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
    animation: fadeIn 0.3s ease-in-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  /* Mobile toggle button */
  .mobile-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 2rem;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    z-index: 998;
    font-size: 1rem;
  }

  .mobile-toggle:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.5);
  }

  .hamburger-icon {
    font-size: 1.5rem;
    line-height: 1;
  }

  .results-count {
    font-weight: 600;
  }

  /* Close button in sidebar header */
  .close-sidebar {
    display: block;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    font-size: 1.25rem;
    line-height: 1;
    padding: 0;
  }

  .close-sidebar:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  .sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .sidebar-header h3 {
    font-size: 1.125rem;
  }

  /* Content takes full width on mobile */
  .content {
    width: 100%;
  }

  /* Adjust form for mobile */
  .search-form {
    grid-template-columns: 1fr;
  }

  .header-top h2 {
    font-size: 1.5rem;
  }

  .message-detail {
    padding: 1rem;
  }

  .message-detail h4 {
    font-size: 1.5rem;
  }

  .message-text {
    font-size: 1rem;
    padding: 1rem;
  }

  .export-section {
    padding: 0.75rem;
  }

  .current-search {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .btn-export {
    align-self: stretch;
    justify-content: center;
  }

  .mobile-only {
    display: block;
  }
}

/* Desktop - hide mobile-only elements */
@media (min-width: 621px) {
  .mobile-toggle {
    display: none;
  }

  .sidebar-overlay {
    display: none;
  }

  .close-sidebar {
    display: none;
  }

  .mobile-only {
    display: none;
  }
}

/* Mobile login card */
@media (max-width: 620px) {
  .login-card {
    max-width: 95vw;
    padding: 2rem;
  }

  .login-card h1 {
    font-size: 2rem;
  }

  .app-description {
    font-size: 1rem;
  }

  .requirements-box {
    padding: 1.25rem;
  }

  .requirements-box h3 {
    font-size: 1rem;
  }

  .requirements-box li {
    font-size: 0.9rem;
  }
}
</style>
