// API 呼叫相關功能
// 版本：2026-01-18

console.log('✅ api.js 正在載入...');

// API_BASE_URL 已在 auth.js 中定義（先載入），直接使用
// 不需要重複定義

/**
 * 取得 API 請求 headers（包含 token）
 */
function getHeaders() {
    const token = getToken();
    if (!token) {
        throw new Error('未登入');
    }

    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };
}

/**
 * 處理 API 錯誤
 */
async function handleApiError(response) {
    if (response.status === 401) {
        // Token 過期或無效
        logout();
        throw new Error('登入已過期，請重新登入');
    }

    const error = await response.json().catch(() => ({ detail: '請求失敗' }));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
}

/**
 * 取得體重記錄列表（含評估）
 */
async function fetchWeights(babyId, includeAssessment = true) {
    const params = new URLSearchParams();
    if (includeAssessment) {
        params.append('include_assessment', 'true');
    }

    const url = `${API_BASE_URL}/v1/babies/${babyId}/weights?${params.toString()}`;
    const response = await fetch(url, {
        method: 'GET',
        headers: getHeaders(),
    });

    if (!response.ok) {
        await handleApiError(response);
    }

    return await response.json();
}

/**
 * 取得單筆體重的完整評估（含 WHO 參考範圍）
 */
async function fetchWeightAssessment(babyId, weightId) {
    const url = `${API_BASE_URL}/v1/babies/${babyId}/weights/${weightId}/assessment`;
    const response = await fetch(url, {
        method: 'GET',
        headers: getHeaders(),
    });

    if (!response.ok) {
        await handleApiError(response);
    }

    return await response.json();
}

/**
 * 取得嬰兒列表
 */
async function fetchBabies() {
    const url = `${API_BASE_URL}/v1/babies`;
    const response = await fetch(url, {
        method: 'GET',
        headers: getHeaders(),
    });

    if (!response.ok) {
        await handleApiError(response);
    }

    return await response.json();
}

/**
 * 新增體重記錄
 */
async function createWeight(babyId, weightKg, timestamp, note = null) {
    const url = `${API_BASE_URL}/v1/babies/${babyId}/weights`;
    const weightG = Math.round(weightKg * 1000); // 轉換為克
    
    const data = {
        weight_g: weightG,
        timestamp: timestamp,
    };
    
    if (note) {
        data.note = note;
    }

    const response = await fetch(url, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        await handleApiError(response);
    }

    return await response.json();
}

/**
 * 更新體重記錄
 */
async function updateWeight(babyId, weightId, weightKg = null, timestamp = null, note = null) {
    const url = `${API_BASE_URL}/v1/babies/${babyId}/weights/${weightId}`;
    
    const data = {};
    if (weightKg !== null) {
        data.weight_g = Math.round(weightKg * 1000); // 轉換為克
    }
    if (timestamp !== null) {
        data.timestamp = timestamp;
    }
    if (note !== null) {
        data.note = note;
    }

    const response = await fetch(url, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        await handleApiError(response);
    }

    return await response.json();
}

/**
 * 刪除體重記錄
 */
async function deleteWeight(babyId, weightId) {
    const url = `${API_BASE_URL}/v1/babies/${babyId}/weights/${weightId}`;
    const response = await fetch(url, {
        method: 'DELETE',
        headers: getHeaders(),
    });

    if (!response.ok) {
        await handleApiError(response);
    }

    // DELETE 成功時返回 204 No Content，沒有 body
    return null;
}

/**
 * 取得 WHO 生長曲線參考數據
 */
async function fetchGrowthCurve(babyId, fromMonth = 0, toMonth = 60) {
    const url = `${API_BASE_URL}/v1/babies/${babyId}/growth-curve?from_month=${fromMonth}&to_month=${toMonth}`;
    const response = await fetch(url, {
        method: 'GET',
        headers: getHeaders(),
    });

    if (!response.ok) {
        await handleApiError(response);
    }

    return await response.json();
}

// 確認函數已定義
console.log('✅ api.js 載入完成，fetchWeights 已定義:', typeof fetchWeights);
