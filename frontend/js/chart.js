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
                    text: '成長曲線（體重 vs 月齡）',
                    font: {
                        size: 18,
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
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '月齡（月）',
                    },
                    beginAtZero: true,
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

    const weightData = sortedWeights.map((w) => w.weight_g / 1000); // 轉換為公斤

    // 準備數據集
    const datasets = [
        {
            label: '實際體重',
            data: weightData,
            borderColor: 'rgb(0, 122, 51)', // 綠色主題
            backgroundColor: 'rgba(0, 122, 51, 0.1)',
            tension: 0.4,
            pointRadius: 6,
            pointHoverRadius: 8,
            borderWidth: 3,
        },
    ];

    // 如果有生長曲線參考數據，添加百分位參考線
    if (growthCurveData && growthCurveData.curve_data && growthCurveData.curve_data.length > 0) {
        // 建立月齡到體重的映射（用於對齊實際數據的月齡）
        const curveMap = new Map(growthCurveData.curve_data.map(d => [d.age_months, d]));
        
        // 根據實際數據的月齡範圍，生成對應的參考線數據
        const ageLabels = labels.map(parseFloat);
        const minAge = Math.min(...ageLabels);
        const maxAge = Math.max(...ageLabels);
        const startMonth = Math.floor(minAge);
        const endMonth = Math.ceil(maxAge);
        
        // 生成完整的月齡標籤（0.0, 0.5, 1.0, 1.5...）
        const fullAgeLabels = [];
        for (let age = Math.max(0, startMonth); age <= Math.min(60, endMonth); age++) {
            fullAgeLabels.push(age.toFixed(1));
        }
        
        // 百分位線配置（P3, P15, P50, P85, P97）
        const percentileLines = [
            { p: 'p3', label: 'P3 (第3百分位)', color: 'rgba(255, 99, 132, 0.6)', style: 'dashed' },
            { p: 'p15', label: 'P15 (第15百分位)', color: 'rgba(255, 159, 64, 0.6)', style: 'dashed' },
            { p: 'p50', label: 'P50 (中位數)', color: 'rgba(54, 162, 235, 0.7)', style: 'solid' },
            { p: 'p85', label: 'P85 (第85百分位)', color: 'rgba(255, 159, 64, 0.6)', style: 'dashed' },
            { p: 'p97', label: 'P97 (第97百分位)', color: 'rgba(255, 99, 132, 0.6)', style: 'dashed' },
        ];

        percentileLines.forEach(({ p, label, color, style }) => {
            const percentileData = fullAgeLabels.map(ageLabel => {
                const ageMonths = Math.floor(parseFloat(ageLabel));
                const curvePoint = curveMap.get(ageMonths);
                return curvePoint ? curvePoint[p] : null;
            });

            datasets.push({
                label: label,
                data: percentileData,
                borderColor: color,
                backgroundColor: 'transparent',
                tension: 0.3,
                pointRadius: 0, // 不顯示點
                borderWidth: style === 'solid' ? 2 : 1.5,
                borderDash: style === 'dashed' ? [5, 5] : [],
                order: p === 'p50' ? 0 : 1, // P50 顯示在實際數據上方
            });
        });

        // 更新 labels 為完整月齡範圍
        growthChart.data.labels = fullAgeLabels;
    } else {
        // 沒有參考數據時使用原始 labels
        growthChart.data.labels = labels;
    }

    // 更新圖表數據
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
