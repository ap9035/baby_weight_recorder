// 認證相關功能

const API_BASE_URL = 'https://kong-gateway-dev-ggofz32qfa-de.a.run.app';
const TOKEN_KEY = 'jwt_token';

/**
 * 登入
 */
async function login(email, password) {
    try {
        console.log('呼叫登入 API:', `${API_BASE_URL}/auth/token`);
        
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        console.log('API 回應狀態:', response.status, response.statusText);

        if (!response.ok) {
            let errorDetail = '登入失敗';
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || errorData.message || `HTTP ${response.status}`;
                console.error('登入錯誤回應:', errorData);
            } catch (e) {
                console.error('無法解析錯誤回應:', e);
                errorDetail = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorDetail);
        }

        const data = await response.json();
        console.log('登入成功，取得 token');
        
        const token = data.access_token;

        if (!token) {
            console.error('回應中沒有 access_token:', data);
            throw new Error('無法取得 access_token');
        }

        // 儲存 token
        localStorage.setItem(TOKEN_KEY, token);
        console.log('Token 已儲存到 localStorage');
        return token;
    } catch (error) {
        console.error('Login error:', error);
        // 如果是網路錯誤，提供更清楚的訊息
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('無法連接到伺服器，請檢查網路連線或 CORS 設定');
        }
        throw error;
    }
}

/**
 * 取得 token
 */
function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * 清除 token（登出）
 */
function logout() {
    localStorage.removeItem(TOKEN_KEY);
}

/**
 * 檢查是否已登入
 */
function isLoggedIn() {
    return !!getToken();
}

/**
 * 檢查 token 是否過期（簡單檢查）
 * 實際的過期檢查應該由 API 回應 401 來判斷
 */
function isTokenExpired() {
    const token = getToken();
    if (!token) return true;

    try {
        // JWT token 的 payload 是 base64 編碼的
        const parts = token.split('.');
        if (parts.length !== 3) return true;

        const payload = JSON.parse(atob(parts[1]));
        const exp = payload.exp;

        if (!exp) return false; // 沒有 exp claim，假設未過期

        // 檢查是否過期（提前 5 分鐘判斷為過期）
        const now = Math.floor(Date.now() / 1000);
        return exp < now + 300;
    } catch (error) {
        console.error('Token parse error:', error);
        return true;
    }
}
