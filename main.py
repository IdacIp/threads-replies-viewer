from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",    # local development
        "https://yourdomain.com",   # tunnel frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# API URLs
AUTH_URL = "https://threads.net/oauth/authorize"
TOKEN_URL = "https://graph.threads.net/oauth/access_token"
LONG_LIVED_URL = "https://graph.threads.net/access_token"
REPLIES_URL = "https://graph.threads.net/v1.0/me/replies"


def exchange_code_for_token(code: str):
    """Exchange authorization code for short-lived token"""
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code': code
    }
    response = requests.post(TOKEN_URL, data=data)
    return response.json()


def exchange_short_lived_for_long_lived(short_lived_token: str):
    """Exchange short-lived token for long-lived token"""
    params = {
        'grant_type': 'th_exchange_token',
        'client_secret': CLIENT_SECRET,
        'access_token': short_lived_token
    }
    response = requests.get(LONG_LIVED_URL, params=params)
    return response.json()


@app.get("/", response_class=HTMLResponse)
def homepage():
    # 簡化首頁，只給 debug 用
    return """
    <h2>🔧 Backend API 運行中</h2>
    <p>前端請到 <a href="http://127.0.0.1:5173" style="color:blue;font-size:20px;">127.0.0.1:5173</a></p>
    <hr>
    <a href="/api/auth/threads/start" style="background:#4CAF50;color:white;padding:10px;text-decoration:none;border-radius:5px;">登入 Threads (debug)</a>
    """


@app.get("/api/auth/status")
def auth_status(request: Request):
    """檢查登入狀態（前端用）"""
    token = request.cookies.get("threads_session")
    print(f"🔍 DEBUG: cookie token: {token[:20] if token else 'None'}...")
    is_authenticated = token is not None
    return {"authenticated": is_authenticated}


@app.get("/api/auth/threads/start")
def start_oauth():
    """開始 OAuth 流程"""
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'threads_basic,threads_content_publish,threads_manage_replies,threads_manage_insights,threads_read_replies',
        'response_type': 'code'
    }
    auth_url = f"{AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    return RedirectResponse(auth_url)


@app.get("/api/auth/threads/callback")
async def oauth_callback(request: Request, code: str = None, error: str = None):
    if error or not code:
        return RedirectResponse("https://subdomain.yourdomain.com/?login=failed", status_code=302)

    try:
        token_data = exchange_code_for_token(code)
        short_lived_token = token_data['access_token']
        long_lived_data = exchange_short_lived_for_long_lived(short_lived_token)
        final_token = long_lived_data.get('access_token', short_lived_token)

        print(f"✅ OAuth 成功，儲存 cookie: {final_token[:20]}...")

        response = RedirectResponse("https://subdomain.yourdomain.com/?login=success", status_code=302)
        response.set_cookie(
            key="threads_session",
            value=final_token,
            httponly=True,   # 防止 JavaScript 存取，有助於防 XSS
            samesite="lax",  # 允許從其他網站重導過來的請求存取 cookie
            max_age=60*60*24*30,  # 30 天
            secure=True,    # 啟用 HTTPS 需要 secure=True
        )
        return response

    except Exception as e:
        print(f"💥 OAuth 錯誤: {e}")
        return RedirectResponse("https://subdomain.yourdomain.com/?login=failed", status_code=302)


@app.get("/logout")
def logout():
    """登出 - 清 cookie"""
    response = RedirectResponse("https://subdomain.yourdomain.com/")
    response.delete_cookie("threads_session")
    print("🔓 已登出，清空 cookie")
    return response


@app.get("/api/threads")
def api_threads(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    keywords: str = Query("", alias="q")
):
    token = request.cookies.get("threads_session")
    if not token:
        return JSONResponse(
            {"error": "not_authenticated"},
            status_code=401
        )

    params = {
        "fields": "id,media_product_type,media_type,media_url,permalink,username,text,topic_tag,timestamp,shortcode,thumbnail_url,children,is_quote_post,has_replies,root_post,replied_to,is_reply,is_reply_owned_by_me,reply_audience",
        "limit": str(limit),
        "access_token": token
    }

    try:
        res = requests.get(REPLIES_URL, params=params, timeout=10)
        # 讓前端看到真實錯誤
        if res.status_code >= 400:
            return JSONResponse(
                {
                    "error": "threads_api_error",
                    "status_code": res.status_code,
                    "raw": res.text,
                },
                status_code=500,
            )
        data = res.json()
    except Exception as e:
        return JSONResponse(
            {"error": "backend_exception", "detail": str(e)},
            status_code=500
        )

    # 關鍵字過濾
    keyword_lower = keywords.lower().strip()
    filtered = []
    for entry in data.get("data", []):
        text = entry.get("text", "") or ""
        if not keyword_lower or keyword_lower in text.lower():
            filtered.append(entry)

    # 壓成前端好用的格式
    results = []
    for entry in filtered:
        text = entry.get("text", "") or ""
        results.append({
            "media_id": entry.get("id", ""),
            "text": text,
            "preview": " ".join(text.split()[:5]),
            "permalink": entry.get("permalink", ""),
            "timestamp": entry.get("timestamp", ""),
            "username": entry.get("username", ""),
        })

    return {"results": results}


@app.post("/threads", response_class=HTMLResponse)
def get_threads(request: Request, limit: int = Form(...), keywords: str = Form('')):
    """查詢 threads replies"""
    token = request.cookies.get("threads_session")
    print(f"🔍 查詢 token: {token[:20] if token else 'None'}...")

    if not token:
        return HTMLResponse("""
        <h3>請先登入</h3>
        <a href="/api/auth/threads/start">登入 Threads</a>
        <br><br>
        <a href="http://127.0.0.1:5173/">回前端</a>
        """)

    params = {
        "fields": "id,media_product_type,media_type,media_url,permalink,username,text,topic_tag,timestamp,shortcode,thumbnail_url,children,is_quote_post,has_replies,root_post,replied_to,is_reply,is_reply_owned_by_me,reply_audience",
        "limit": str(limit),
        "access_token": token
    }

    try:
        res = requests.get(REPLIES_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        return f"""
        <h3>API 呼叫錯誤</h3>
        <pre>{str(e)}</pre>
        <a href="http://127.0.0.1:5173/">回前端</a>
        """

    # 關鍵字過濾
    filtered_replies = []
    keyword_lower = keywords.lower().strip()
    for entry in data.get("data", []):
        text = entry.get("text", "")
        if not keyword_lower or keyword_lower in text.lower():
            filtered_replies.append(entry)

    if not filtered_replies:
        return f"""
        <h3>沒有找到 replies</h3>
        <a href="http://127.0.0.1:5173/">回前端重新查詢</a>
        """

    # 產生結果連結
    items = []
    for entry in filtered_replies:
        media_id = entry.get("id", "")
        text = entry.get("text", "")
        permalink = entry.get("permalink", "")
        words = text.split()[:5]
        first_5_words = " ".join(words)
        items.append((media_id, first_5_words, permalink))

    result_list = "".join([
        f"<a href='{html_escape(permalink)}' target='_blank' rel='noopener noreferrer' "
        f"style='display: block; margin-bottom: 10px; padding: 8px; border: 1px solid #ccc; "
        f"border-radius: 4px; text-decoration: none; color: #333;'>"
        f"<strong>{html_escape(media_id)}</strong> - {html_escape(first_5_words)}</a>"
        for media_id, first_5_words, permalink in items
    ])

    return f"""
    <h3>✅ 查詢成功: {len(filtered_replies)} 筆結果</h3>
    <div>{result_list}</div>
    <hr>
    <p>Limit: {limit} | Keywords: {html_escape(keywords) if keywords else '無'}</p>
    <a href="http://127.0.0.1:5173/">回前端</a>
    """


def html_escape(s: str) -> str:
    """HTML escape"""
    return (s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))
