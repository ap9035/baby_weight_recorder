// 主要應用邏輯

let currentBabyId = null;

/**
 * 初始化應用
 */
function initApp() {
    // 檢查登入狀態
    if (isLoggedIn()) {
        showMainContent();
    } else {
        showLoginForm();
    }

    // 綁定登入表單事件
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // 綁定按鈕事件
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleRefresh);
    }

    // 綁定寶寶選擇下拉選單
    const babySelect = document.getElementById('baby-select');
    if (babySelect) {
        babySelect.addEventListener('change', handleBabySelect);
    }

    // 綁定新增按鈕
    const addWeightBtn = document.getElementById('add-weight-btn');
    if (addWeightBtn) {
        addWeightBtn.addEventListener('click', () => openWeightForm());
    }

    // 綁定表單提交
    const weightForm = document.getElementById('weight-form');
    if (weightForm) {
        weightForm.addEventListener('submit', handleWeightFormSubmit);
    }
}

/**
 * 顯示登入表單
 */
function showLoginForm() {
    document.getElementById('login-container').style.display = 'block';
    document.getElementById('main-container').style.display = 'none';
}

/**
 * 顯示主要內容
 */
async function showMainContent() {
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('main-container').style.display = 'block';

    // 初始化圖表
    initChart();

    // 載入寶寶列表
    await loadBabyList();
}

/**
 * 載入寶寶列表到下拉選單
 */
async function loadBabyList() {
    const babySelect = document.getElementById('baby-select');
    if (!babySelect) return;

    try {
        const babies = await fetchBabies();
        
        // 清空現有選項（保留第一個預設選項）
        babySelect.innerHTML = '<option value="">-- 選擇寶寶 --</option>';
        
        // 填充寶寶選項
        babies.forEach(baby => {
            const option = document.createElement('option');
            option.value = baby.baby_id;
            option.textContent = `${baby.name} (${baby.birth_date})`;
            babySelect.appendChild(option);
        });

        // 嘗試從 localStorage 取得上次使用的 baby_id
        const savedBabyId = localStorage.getItem('baby_id');
        if (savedBabyId) {
            // 檢查是否在列表中
            const exists = babies.some(b => b.baby_id === savedBabyId);
            if (exists) {
                babySelect.value = savedBabyId;
                currentBabyId = savedBabyId;
                loadGrowthData(savedBabyId);
            }
        }
    } catch (error) {
        console.error('載入寶寶列表失敗:', error);
        showError('無法載入寶寶列表');
    }
}

/**
 * 處理寶寶選擇變更
 */
function handleBabySelect() {
    const babySelect = document.getElementById('baby-select');
    const babyId = babySelect.value;
    
    if (!babyId) {
        // 清空圖表和列表
        clearChart();
        document.getElementById('weights-list').innerHTML = '<p class="empty-message">請選擇寶寶</p>';
        document.getElementById('assessment-section').style.display = 'none';
        currentBabyId = null;
        localStorage.removeItem('baby_id');
        return;
    }

    currentBabyId = babyId;
    localStorage.setItem('baby_id', babyId);
    loadGrowthData(babyId);
}

/**
 * 處理登入
 */
async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');
    const submitBtn = e.target.querySelector('button[type="submit"]');

    // 隱藏錯誤訊息
    errorDiv.style.display = 'none';
    errorDiv.textContent = '';

    // 顯示載入狀態
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '登入中...';
    }

    try {
        console.log('開始登入...', email);
        await login(email, password);
        console.log('登入成功');
        showMainContent();
    } catch (error) {
        console.error('登入錯誤:', error);
        errorDiv.textContent = error.message || '登入失敗，請檢查帳號密碼';
        errorDiv.style.display = 'block';
    } finally {
        // 恢復按鈕狀態
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = '登入';
        }
    }
}

/**
 * 處理登出
 */
function handleLogout() {
    logout();
    clearChart();
    currentBabyId = null;
    showLoginForm();
}

/**
 * 處理刷新
 */
async function handleRefresh() {
    const babySelect = document.getElementById('baby-select');
    const babyId = babySelect.value;

    if (!babyId) {
        showError('請先選擇寶寶');
        return;
    }

    await loadGrowthData(babyId);
}

/**
 * 載入成長數據
 */
async function loadGrowthData(babyId) {
    const loading = document.getElementById('loading');
    const errorDiv = document.getElementById('error-message');
    const assessmentSection = document.getElementById('assessment-section');

    // 隱藏錯誤和評估
    errorDiv.style.display = 'none';
    assessmentSection.style.display = 'none';

    // 顯示載入中
    loading.style.display = 'block';
    clearChart();

    try {
        // 取得體重記錄
        // 確認 fetchWeights 是否可用
        console.log('loadGrowthData 開始執行，babyId:', babyId);
        console.log('當前作用域中的 fetchWeights:', typeof fetchWeights);
        console.log('window.fetchWeights:', typeof window.fetchWeights);
        
        if (typeof fetchWeights === 'undefined') {
            // 嘗試從 window 取得
            const fetchWeightsFn = window.fetchWeights || fetchWeights;
            if (typeof fetchWeightsFn === 'undefined') {
                throw new Error('fetchWeights 函數未定義，請確認 api.js 已正確載入。當前 fetchWeights 類型: ' + typeof fetchWeights);
            }
            console.log('使用 window.fetchWeights');
            const weights = await fetchWeightsFn(babyId, true);
        } else {
            console.log('調用 fetchWeights，babyId:', babyId);
            const weights = await fetchWeights(babyId, true);
        }
        
        // 修正：將 weights 變數移到條件外
        let weights;
        if (typeof fetchWeights === 'undefined') {
            if (typeof window.fetchWeights === 'undefined') {
                throw new Error('fetchWeights 函數未定義，請確認 api.js 已正確載入');
            }
            weights = await window.fetchWeights(babyId, true);
        } else {
            weights = await fetchWeights(babyId, true);
        }

        if (!weights || weights.length === 0) {
            showError('目前沒有體重記錄，請先新增記錄');
            loading.style.display = 'none';
            return;
        }

        // 嘗試取得嬰兒資料以獲取出生日期和生長曲線數據
        let birthDate = null;
        let growthCurveData = null;
        try {
            const babies = await fetchBabies();
            const baby = babies.find(b => b.baby_id === babyId);
            if (baby && baby.birth_date) {
                birthDate = baby.birth_date;
                
                // 取得 WHO 生長曲線參考數據
                try {
                    // 計算實際數據的月齡範圍
                    // 取得完整的 0-60 個月（5歲）WHO 生長曲線數據
                    growthCurveData = await fetchGrowthCurve(babyId, 0, 60);
                } catch (error) {
                    console.warn('無法取得生長曲線數據:', error);
                }
            }
        } catch (error) {
            console.warn('無法取得嬰兒資料，將使用相對時間:', error);
        }

        // 更新圖表（傳入出生日期和生長曲線數據）
        updateChart(weights, birthDate, growthCurveData);

        // 顯示記錄列表
        displayWeightsList(weights);

        // 顯示最新一筆的評估
        const latestWeight = weights[weights.length - 1];
        if (latestWeight.assessment) {
            displayAssessment(latestWeight.assessment);
        }

        loading.style.display = 'none';
    } catch (error) {
        console.error('Load growth data error:', error);
        showError(error.message || '載入失敗，請檢查 Baby ID 或重新登入');
        loading.style.display = 'none';

        // 如果是登入相關錯誤，回到登入頁面
        if (error.message.includes('登入')) {
            handleLogout();
        }
    }
}

/**
 * 顯示評估資訊
 */
function displayAssessment(assessment) {
    const assessmentSection = document.getElementById('assessment-section');
    const assessmentContent = document.getElementById('assessment-content');

    const assessmentClass = {
        'normal': 'normal',
        'underweight': 'warning',
        'overweight': 'warning',
        'severely_underweight': 'danger',
        'severely_overweight': 'danger',
    }[assessment.assessment] || '';

    assessmentContent.innerHTML = `
        <div class="assessment-item">
            <div class="label">百分位數</div>
            <div class="value ${assessmentClass}">${assessment.percentile}%</div>
        </div>
        <div class="assessment-item">
            <div class="label">評估結果</div>
            <div class="value ${assessmentClass}">${getAssessmentText(assessment.assessment)}</div>
        </div>
        <div class="assessment-item" style="grid-column: 1 / -1;">
            <div class="label">建議</div>
            <div class="value">${assessment.message}</div>
        </div>
    `;

    assessmentSection.style.display = 'block';
}

/**
 * 取得評估文字（中文）
 */
function getAssessmentText(assessment) {
    // 如果是物件，提取 assessment 屬性
    const assessmentValue = typeof assessment === 'object' && assessment !== null 
        ? assessment.assessment || assessment 
        : assessment;
    
    const texts = {
        'severely_underweight': '體重嚴重不足',
        'underweight': '體重偏低',
        'normal': '正常範圍',
        'overweight': '體重偏高',
        'severely_overweight': '體重過重',
    };
    return texts[assessmentValue] || assessmentValue || '未知';
}

/**
 * 顯示錯誤訊息
 */
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

/**
 * 顯示體重記錄列表
 */
function displayWeightsList(weights) {
    const listContainer = document.getElementById('weights-list');
    if (!listContainer || !weights || weights.length === 0) {
        if (listContainer) {
            listContainer.innerHTML = '<p style="color: #718096; text-align: center; padding: 20px;">目前沒有體重記錄</p>';
        }
        return;
    }

    // 排序：最新的在前
    const sortedWeights = [...weights].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp);
    });

    listContainer.innerHTML = sortedWeights.map(weight => {
        const date = new Date(weight.timestamp);
        const dateStr = date.toLocaleString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });
        const weightKg = (weight.weight_g / 1000).toFixed(2);
        
        // 格式化評估資訊
        let assessmentText = '';
        if (weight.assessment && typeof weight.assessment === 'object') {
            const assessment = weight.assessment;
            assessmentText = ` | ${getAssessmentText(assessment.assessment)} (${assessment.percentile}%)`;
        } else if (weight.assessment && typeof weight.assessment === 'string') {
            assessmentText = ` | ${getAssessmentText(weight.assessment)}`;
        }

        // 轉義 note 中的特殊字元，避免 onclick 中的引號問題
        const safeNote = (weight.note || '').replace(/'/g, "&#39;").replace(/"/g, "&quot;").replace(/\n/g, "\\n");

        return `
            <div class="weight-item">
                <div class="weight-item-info">
                    <div class="weight-item-date">${dateStr}</div>
                    <div class="weight-item-details">
                        <span>體重：${weightKg} 公斤</span>
                        ${weight.note ? `<span>備註：${weight.note}</span>` : ''}
                        ${assessmentText ? `<span>${assessmentText}</span>` : ''}
                    </div>
                </div>
                <div class="weight-item-actions">
                    <button class="btn btn-icon btn-edit" onclick="editWeight('${weight.weight_id}', ${weightKg}, '${weight.timestamp}', '${safeNote}')">編輯</button>
                    <button class="btn btn-icon btn-delete" onclick="confirmDeleteWeight('${weight.weight_id}')">刪除</button>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * 開啟新增/編輯表單
 */
function openWeightForm(weightId = null, weightKg = '', timestamp = '', note = '') {
    const modal = document.getElementById('weight-form-modal');
    const modalTitle = document.getElementById('modal-title');
    const form = document.getElementById('weight-form');
    
    document.getElementById('weight-id-input').value = weightId || '';
    document.getElementById('weight-kg-input').value = weightKg;
    document.getElementById('note-input').value = note;

    // 設定時間（轉換為 datetime-local 格式）
    if (timestamp) {
        const date = new Date(timestamp);
        const localDateTime = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
            .toISOString()
            .slice(0, 16);
        document.getElementById('timestamp-input').value = localDateTime;
    } else {
        // 預設為當前時間
        const now = new Date();
        const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
            .toISOString()
            .slice(0, 16);
        document.getElementById('timestamp-input').value = localDateTime;
    }

    modalTitle.textContent = weightId ? '編輯體重記錄' : '新增體重記錄';
    modal.style.display = 'flex';
}

/**
 * 關閉表單
 */
function closeWeightForm() {
    const modal = document.getElementById('weight-form-modal');
    const form = document.getElementById('weight-form');
    modal.style.display = 'none';
    form.reset();
    document.getElementById('weight-id-input').value = '';
}

/**
 * 處理表單提交
 */
async function handleWeightFormSubmit(e) {
    e.preventDefault();

    const weightId = document.getElementById('weight-id-input').value;
    const weightKg = parseFloat(document.getElementById('weight-kg-input').value);
    const timestampInput = document.getElementById('timestamp-input').value;
    const note = document.getElementById('note-input').value.trim();

    // 轉換 datetime-local 為 ISO 8601
    const timestamp = new Date(timestampInput).toISOString();

    const babyId = currentBabyId;
    if (!babyId) {
        showError('請先輸入 Baby ID');
        return;
    }

    try {
        if (weightId) {
            // 編輯
            await updateWeight(babyId, weightId, weightKg, timestamp, note || null);
        } else {
            // 新增
            await createWeight(babyId, weightKg, timestamp, note || null);
        }

        closeWeightForm();
        // 重新載入數據
        await loadGrowthData(babyId);
    } catch (error) {
        console.error('儲存體重記錄錯誤:', error);
        showError(error.message || '儲存失敗');
    }
}

/**
 * 編輯體重記錄
 */
function editWeight(weightId, weightKg, timestamp, note) {
    openWeightForm(weightId, weightKg, timestamp, note);
}

/**
 * 確認刪除體重記錄
 */
function confirmDeleteWeight(weightId) {
    if (confirm('確定要刪除這筆體重記錄嗎？')) {
        deleteWeightRecord(weightId);
    }
}

/**
 * 刪除體重記錄
 */
async function deleteWeightRecord(weightId) {
    const babyId = currentBabyId;
    if (!babyId) {
        showError('請先輸入 Baby ID');
        return;
    }

    try {
        await deleteWeight(babyId, weightId);
        // 重新載入數據
        await loadGrowthData(babyId);
    } catch (error) {
        console.error('刪除體重記錄錯誤:', error);
        showError(error.message || '刪除失敗');
    }
}

// 頁面載入完成後初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    // DOM 已經載入完成，直接初始化
    initApp();
}
