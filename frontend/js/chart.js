// 圖表繪製相關功能

let growthChart = null;

/**
 * 初始化成長曲線圖表
 */
function initChart() {
    const ctx = document.getElementById('growth-chart');
    if (!ctx) return;

    // 如果已經有圖表，先銷毀
    if (growthChart) {
        growthChart.destroy();
    }

    growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '成長曲線（體重 vs 月齡）- 滾輪縮放 / 拖曳平移 / 雙擊重置',
                    font: {
                        size: 16,
                    },
                },
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
                zoom: {
                    pan: {
                        enabled: true,  // 啟用拖曳平移
                        mode: 'x',      // 只允許 X 軸平移
                    },
                    zoom: {
                        wheel: {
                            enabled: true, // 滾輪縮放
                        },
                        pinch: {
                            enabled: true, // 觸控縮放
                        },
                        mode: 'x', // 只縮放 X 軸
                    },
                    limits: {
                        x: { 
                            min: 0,        // 最小值固定為 0
                            max: 60,       // 最大值 60 個月
                            minRange: 1,   // 最小顯示範圍 1 個月
                        },
                    },
                },
            },
            scales: {
                x: {
                    type: 'linear', // 使用線性軸，讓數值正確對應位置
                    title: {
                        display: true,
                        text: '月齡（月）',
                    },
                    min: 0,
                    max: 60,
                    ticks: {
                        stepSize: 6, // 每 6 個月顯示一個刻度
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: '體重（公斤）',
                    },
                    beginAtZero: true,
                },
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false,
            },
        },
    });
    
    // 雙擊重置縮放
    ctx.ondblclick = () => {
        if (growthChart) {
            growthChart.resetZoom();
        }
    };
}

/**
 * 更新圖表數據
 * @param {Array} weights - 體重記錄陣列
 * @param {string} birthDate - 嬰兒出生日期 (YYYY-MM-DD 格式)
 * @param {Array} growthCurveData - WHO 生長曲線參考數據（可選）
 */
function updateChart(weights, birthDate = null, growthCurveData = null) {
    if (!growthChart || !weights || weights.length === 0) {
        return;
    }

    // 排序體重記錄（按時間）
    const sortedWeights = [...weights].sort((a, b) => {
        return new Date(a.timestamp) - new Date(b.timestamp);
    });

    // 計算月齡
    let labels;
    if (birthDate) {
        // 使用出生日期計算月齡
        const birth = new Date(birthDate);
        labels = sortedWeights.map((w) => {
            const measureDate = new Date(w.timestamp);
            // 計算月齡（月份差異 + 日期差異的近似值）
            const monthsDiff = (measureDate.getFullYear() - birth.getFullYear()) * 12 + 
                              (measureDate.getMonth() - birth.getMonth());
            const daysDiff = measureDate.getDate() - birth.getDate();
            // 月齡 = 整月數 + 天數/30（近似值，顯示到小數點後1位）
            const ageInMonths = monthsDiff + daysDiff / 30;
            return ageInMonths.toFixed(1);
        });
    } else {
        // 如果沒有出生日期，使用相對時間（從第一個記錄開始的月數）
        const firstDate = new Date(sortedWeights[0].timestamp);
        labels = sortedWeights.map((w) => {
            const measureDate = new Date(w.timestamp);
            const diffMs = measureDate - firstDate;
            const diffMonths = diffMs / (1000 * 60 * 60 * 24 * 30); // 近似值
            return diffMonths.toFixed(1);
        });
    }

    // 使用線性 X 軸，數據格式為 {x, y}
    // 實際體重數據點
    const weightDataPoints = sortedWeights.map((w, idx) => ({
        x: parseFloat(labels[idx]),
        y: w.weight_g / 1000,
    }));

    // 準備數據集
    const datasets = [
        {
            label: '實際體重',
            data: weightDataPoints,
            borderColor: 'rgb(0, 122, 51)', // 綠色主題
            backgroundColor: 'rgba(0, 122, 51, 0.1)',
            tension: 0.4,
            pointRadius: 6,
            pointHoverRadius: 8,
            borderWidth: 3,
            showLine: true,
        },
    ];

    // 如果有生長曲線參考數據，添加百分位參考線
    if (growthCurveData && growthCurveData.curve_data && growthCurveData.curve_data.length > 0) {
        // 百分位線配置（P3, P15, P50, P85, P97）
        const percentileLines = [
            { p: 'p3', label: 'P3 (第3百分位)', color: 'rgba(255, 99, 132, 0.6)', style: 'dashed' },
            { p: 'p15', label: 'P15 (第15百分位)', color: 'rgba(255, 159, 64, 0.6)', style: 'dashed' },
            { p: 'p50', label: 'P50 (中位數)', color: 'rgba(54, 162, 235, 0.7)', style: 'solid' },
            { p: 'p85', label: 'P85 (第85百分位)', color: 'rgba(255, 159, 64, 0.6)', style: 'dashed' },
            { p: 'p97', label: 'P97 (第97百分位)', color: 'rgba(255, 99, 132, 0.6)', style: 'dashed' },
        ];

        // 為每條百分位線建立數據點（只使用整數月齡，WHO 數據點）
        percentileLines.forEach(({ p, label, color, style }) => {
            const percentileData = growthCurveData.curve_data.map(d => ({
                x: d.age_months,
                y: d[p],
            }));

            datasets.push({
                label: label,
                data: percentileData,
                borderColor: color,
                backgroundColor: 'transparent',
                tension: 0.3,
                pointRadius: 0, // 不顯示點
                borderWidth: style === 'solid' ? 2 : 1.5,
                borderDash: style === 'dashed' ? [5, 5] : [],
                showLine: true,
            });
        });
    }

    // 更新圖表數據（線性軸不需要 labels）
    growthChart.data.labels = [];
    growthChart.data.datasets = datasets;
    growthChart.update();
}

/**
 * 清除圖表
 */
function clearChart() {
    if (growthChart) {
        growthChart.data.labels = [];
        growthChart.data.datasets = [];
        growthChart.update();
    }
}
