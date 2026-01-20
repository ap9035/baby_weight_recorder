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
                    text: '成長曲線（體重 vs 月齡）- 滾輪縮放月齡範圍 / 雙擊重置',
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
                        enabled: false, // 關閉拖曳平移
                    },
                    zoom: {
                        wheel: {
                            enabled: true, // 滾輪縮放
                        },
                        pinch: {
                            enabled: true, // 觸控縮放
                        },
                        mode: 'x', // 只縮放 X 軸
                        onZoom: ({ chart }) => {
                            // 縮放時保持左邊從 0 開始
                            const xScale = chart.scales.x;
                            if (xScale.min < 0) {
                                chart.zoomScale('x', { min: 0 }, 'none');
                            }
                        },
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
        
        // 計算實際數據的月齡範圍
        const ageLabels = labels.map(parseFloat);
        
        // 初始顯示完整的 0-60 個月（5 歲）WHO 生長曲線
        const displayEndMonth = 60;
        
        // 建立統一的月齡標籤集合
        // 包含：實際數據點 + 0-60 個月的整數點（完整 WHO 曲線）
        const allAgeLabelsSet = new Set(labels); // 先加入實際數據的月齡
        for (let age = 0; age <= 60; age++) {
            allAgeLabelsSet.add(age.toFixed(1)); // 加入所有整數月齡（完整參考線）
        }
        // 轉換為陣列並排序
        const allAgeLabels = Array.from(allAgeLabelsSet).sort((a, b) => parseFloat(a) - parseFloat(b));
        
        // 將實際體重數據對齊到統一的 labels
        // 建立月齡到體重的映射
        const weightMap = new Map();
        sortedWeights.forEach((w, idx) => {
            weightMap.set(labels[idx], w.weight_g / 1000);
        });
        
        // 對齊實際體重數據到統一的 labels
        const alignedWeightData = allAgeLabels.map(ageLabel => {
            return weightMap.get(ageLabel) || null;
        });
        
        // 更新實際體重數據集
        datasets[0].data = alignedWeightData;
        
        // 百分位線配置（P3, P15, P50, P85, P97）
        const percentileLines = [
            { p: 'p3', label: 'P3 (第3百分位)', color: 'rgba(255, 99, 132, 0.6)', style: 'dashed' },
            { p: 'p15', label: 'P15 (第15百分位)', color: 'rgba(255, 159, 64, 0.6)', style: 'dashed' },
            { p: 'p50', label: 'P50 (中位數)', color: 'rgba(54, 162, 235, 0.7)', style: 'solid' },
            { p: 'p85', label: 'P85 (第85百分位)', color: 'rgba(255, 159, 64, 0.6)', style: 'dashed' },
            { p: 'p97', label: 'P97 (第97百分位)', color: 'rgba(255, 99, 132, 0.6)', style: 'dashed' },
        ];

        // 線性內插函數：計算非整數月齡的參考值
        const interpolatePercentile = (ageLabel, percentileKey) => {
            const age = parseFloat(ageLabel);
            const lowerAge = Math.floor(age);
            const upperAge = Math.ceil(age);
            
            // 如果是整數月齡，直接返回
            if (lowerAge === upperAge) {
                const point = curveMap.get(lowerAge);
                return point ? point[percentileKey] : null;
            }
            
            // 取得前後兩個整數月齡的數據
            const lowerPoint = curveMap.get(lowerAge);
            const upperPoint = curveMap.get(upperAge);
            
            if (!lowerPoint || !upperPoint) {
                // 如果缺少數據，使用最接近的整數月齡
                const nearestAge = Math.round(age);
                const nearestPoint = curveMap.get(nearestAge);
                return nearestPoint ? nearestPoint[percentileKey] : null;
            }
            
            // 線性內插
            const ratio = age - lowerAge; // 0.0 ~ 1.0
            const lowerValue = lowerPoint[percentileKey];
            const upperValue = upperPoint[percentileKey];
            return lowerValue * (1 - ratio) + upperValue * ratio;
        };

        percentileLines.forEach(({ p, label, color, style }) => {
            const percentileData = allAgeLabels.map(ageLabel => {
                return interpolatePercentile(ageLabel, p);
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

        // 使用統一的 labels
        growthChart.data.labels = allAgeLabels;
        
        // 更新圖表數據
        growthChart.data.datasets = datasets;
        growthChart.update();
        
        // 設定初始顯示範圍（從 0 到 displayEndMonth）
        // 用戶可以透過滾輪縮放看到完整的 0-60 個月
        growthChart.zoomScale('x', { min: 0, max: displayEndMonth }, 'none');
    } else {
        // 沒有參考數據時使用原始 labels
        growthChart.data.labels = labels;
        
        // 更新圖表數據
        growthChart.data.datasets = datasets;
        growthChart.update();
    }
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
