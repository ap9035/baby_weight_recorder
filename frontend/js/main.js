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

    const babyIdInput = document.getElementById('baby-id-input');
    if (babyIdInput) {
        babyIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleRefresh();
            }
        });
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
function showMainContent() {
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('main-container').style.display = 'block';

    // 初始化圖表
    initChart();

    // 嘗試從 localStorage 取得上次使用的 baby_id
    const savedBabyId = localStorage.getItem('baby_id');
    if (savedBabyId) {
        document.getElementById('baby-id-input').value = savedBabyId;
        currentBabyId = savedBabyId;
        loadGrowthData(savedBabyId);
    }
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
    const babyIdInput = document.getElementById('baby-id-input');
    const babyId = babyIdInput.value.trim();

    if (!babyId) {
        showError('請輸入 Baby ID');
        return;
    }

    // 儲存 baby_id
    localStorage.setItem('baby_id', babyId);
    currentBabyId = babyId;

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
        const weights = await fetchWeights(babyId, true);

        if (!weights || weights.length === 0) {
            showError('目前沒有體重記錄，請先新增記錄');
            loading.style.display = 'none';
            return;
        }

        // 更新圖表
        updateChart(weights);

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
    const texts = {
        'severely_underweight': '體重嚴重不足',
        'underweight': '體重偏低',
        'normal': '正常範圍',
        'overweight': '體重偏高',
        'severely_overweight': '體重過重',
    };
    return texts[assessment] || assessment;
}

/**
 * 顯示錯誤訊息
 */
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

// 頁面載入完成後初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    // DOM 已經載入完成，直接初始化
    initApp();
}
