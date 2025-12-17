# Threads Reply 搜尋器

一個幫助你搜尋和管理 Threads 回覆的工具。你可以透過關鍵字快速找到特定的回覆內容，並查看完整的訊息詳情。

## 🚀 快速開始

### 1. 環境需求

- **Python 3.10+**
- **Node.js 16+**
- **Meta Developer 帳號**

### 2. Meta Developer 設定

1. 前往 [Meta for Developers](https://developers.facebook.com/)
2. 建立新的 App（選擇 "Business" 類型）
3. 在 App 設定中新增 "Threads" 產品
4. 設定 OAuth 重定向 URI（使用你自己的網域）：
   ```
   https://your-domain.com/api/auth/threads/callback
   ```
5. 記錄以下資訊：
   - **App ID**
   - **App Secret**
   - **Threads User Token**（用於測試）

### 3. 本地環境設定

1. **複製專案**
   ```bash
   git clone <repository-url>
   cd threads-prototype
   ```

2. **設定環境變數**
   ```bash
   # 複製範例檔案並填入你的憑證
   cp Threads/.env.example Threads/.env
   cp Threads/config.yaml.example Threads/config.yaml
   
   # 編輯 Threads/.env，填入你的 Meta App 資訊
   CLIENT_ID=your_app_id
   CLIENT_SECRET=your_app_secret
   REDIRECT_URI=https://your-domain.com/api/auth/threads/callback
   ```
   
   **⚠️ 重要安全提醒：**
   - 永遠不要將 `.env` 或 `config.yaml` 檔案提交到 Git
   - 這些檔案已被加入 `.gitignore` 以避免意外洩露
   - 每個開發者都應該使用自己的 Meta App 憑證

3. **啟動服務**

   **後端 (FastAPI)**
   ```bash
   cd Threads
   python main.py
   ```

   **前端 (Vue 3 + Vite)**
   ```bash
   cd Threads/frontend
   npm install
   npm run dev
   ```

   **Cloudflare Tunnel (用於 OAuth 回調)**
   ```bash
   cd Threads
   cloudflared tunnel --url http://localhost:8000 --hostname your-subdomain.boatswain.cc
   ```

4. **存取應用程式**
   - 前端：http://localhost:5173
   - 後端：http://localhost:8000
   - 公開 URL：https://your-subdomain.boatswain.cc

## 📱 功能特色

- 🔍 **關鍵字搜尋**：快速找到特定的 Threads 回覆
- 📊 **CSV 匯出**：將搜尋結果匯出為 CSV 檔案
- 📱 **響應式設計**：支援桌面和手機端
- 🔒 **安全本地運行**：所有資料處理都在本地進行
- 🎨 **現代化 UI**：使用 Vue 3 和自訂 CSS 設計

## ⚠️ 重要限制

**API 使用限制**：
- 此應用程式**僅使用 Meta 官方提供的 Threads API**
- **除非通過 Business Verification**，否則只能用於**個人 Threads 帳號**
- 請務必遵守 [Meta for Developers](https://developers.facebook.com/) 上關於 Threads API 和 OAuth API 的使用限制和規則

**使用規範**：
- 僅限個人使用，不得用於商業用途
- 請遵守 Meta 的 API 速率限制
- 不得將資料用於未經授權的目的

## 🛠️ 技術架構

### 前端
- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite
- **Styling**: 自訂 CSS (類似 Pico.css)
- **Dependencies**:
  - `vue`: ^3.5.24 - Vue.js 框架
  - `axios`: ^1.13.2 - HTTP 客戶端
- **Dev Dependencies**:
  - `@vitejs/plugin-vue`: ^6.0.1 - Vite Vue 插件
  - `vite`: ^7.2.4 - 建構工具

### 後端
- **Framework**: FastAPI (Python 3.10)
- **API**: Meta Threads API
- **Authentication**: OAuth 2.0
- **Dependencies**:
  - `fastapi` - Web 框架
  - `requests` - HTTP 請求庫
  - `python-dotenv` - 環境變數管理

### 網路
- **Tunnel**: Cloudflare Tunnel (cloudflared)
- **Domain**: boatswain.cc

## 🔒 安全性與隱私

### 本地安全使用

這個應用程式設計為**完全在本地運行**，不涉及任何外部資料傳輸：

1. **OAuth 流程**：雖然使用外部 OAuth 服務進行身份驗證，但所有 API 呼叫都是從您的瀏覽器直接發送到 Meta 的伺服器
2. **資料處理**：所有搜尋、過濾和顯示邏輯都在您的本地瀏覽器中執行
3. **CSV 匯出**：資料匯出功能只會將已經下載到您瀏覽器的資料儲存到本地檔案
4. **無後端儲存**：應用程式後端只負責代理 API 呼叫，不會儲存任何您的個人資料

### 資料流程
```
您的瀏覽器 ↔ Meta Threads API (直接)
您的瀏覽器 ↔ 本地後端 (只用於代理，不儲存資料)
```

## 📋 使用說明

1. **登入**：點擊「連接 Threads 帳號」按鈕進行 OAuth 驗證
2. **搜尋**：輸入查詢數量和關鍵字，點擊搜尋
3. **瀏覽**：在左側欄選擇訊息，在右側查看詳情
4. **匯出**：點擊「匯出 CSV」按鈕下載搜尋結果

### 手機端功能
- **側邊欄切換**：點擊右下角的漢堡選單開啟/關閉側邊欄
- **Header 收起**：點擊右下角的 tab 按鈕收起/展開搜尋表單

## 🐛 疑難排解

### 常見問題

**Q: OAuth 登入失敗**
A: 確認 Meta Developer App 的重定向 URI 設定正確

**Q: 搜尋無結果**
A: 確認您有足夠的 Threads 回覆，且關鍵字設定正確

**Q: 前端無法載入**
A: 確認所有服務都已啟動，且網路設定正確

## 📄 授權

**MIT License**

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

**商業使用限制**：
- 禁止將此軟體直接用於商業用途
- 禁止將此軟體作為商業產品或服務的一部分銷售
- 如需商業使用，請聯絡原作者取得授權

**免責聲明**：
- 本軟體僅供學習和個人使用
- 使用者需自行遵守 Meta 的開發者條款和 API 使用限制
- 作者對使用此軟體造成的任何損失不承擔責任

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

## 📞 聯絡方式

有任何疑問歡迎聯絡我：
- **Threads**: [@ida.cip](https://threads.net/@ida.cip)

**注意**：請確保遵守 Meta 的開發者條款和 Threads API 的使用限制。
