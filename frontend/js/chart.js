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
 */
function updateChart(weights) {
    if (!growthChart || !weights || weights.length === 0) {
        return;
    }

    // 排序體重記錄（按時間）
    const sortedWeights = [...weights].sort((a, b) => {
        return new Date(a.timestamp) - new Date(b.timestamp);
    });

    // 計算月齡（需要嬰兒的出生日期，這裡假設從第一個記錄的時間計算）
    // 注意：實際上需要從嬰兒資料取得出生日期
    // 這裡先用相對時間來顯示
    const labels = sortedWeights.map((w, index) => index.toString());
    const weightData = sortedWeights.map((w) => w.weight_g / 1000); // 轉換為公斤

    // 更新圖表數據
    growthChart.data.labels = labels;
    growthChart.data.datasets = [
        {
            label: '實際體重',
            data: weightData,
            borderColor: 'rgb(102, 126, 234)',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.4,
            pointRadius: 6,
            pointHoverRadius: 8,
        },
    ];

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
