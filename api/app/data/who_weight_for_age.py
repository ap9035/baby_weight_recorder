"""WHO 兒童生長標準 - 體重對年齡 (Weight-for-age).

資料來源: WHO Child Growth Standards
https://www.who.int/tools/child-growth-standards/standards/weight-for-age

台灣衛福部國健署採用此標準作為兒童生長評估依據。

數據格式:
- age_months: 月齡 (0-24 個月)
- L: Box-Cox 變換參數
- M: 中位數 (P50)
- S: 變異係數

使用 LMS 方法計算百分位:
Z = ((weight/M)^L - 1) / (L * S)  when L != 0
Z = ln(weight/M) / S              when L == 0

Percentile = Φ(Z) * 100  (標準常態分佈累積機率)
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class LMSParams:
    """LMS 參數."""

    age_months: int
    L: float
    M: float
    S: float


# WHO Weight-for-age: Boys (0-24 months)
# 資料來源: WHO Child Growth Standards (2006)
BOYS_WEIGHT_FOR_AGE: list[LMSParams] = [
    LMSParams(0, 0.3487, 3.3464, 0.14602),
    LMSParams(1, 0.2297, 4.4709, 0.13395),
    LMSParams(2, 0.1970, 5.5675, 0.12385),
    LMSParams(3, 0.1738, 6.3762, 0.11727),
    LMSParams(4, 0.1553, 7.0023, 0.11316),
    LMSParams(5, 0.1395, 7.5105, 0.10990),
    LMSParams(6, 0.1257, 7.9340, 0.10652),
    LMSParams(7, 0.1134, 8.2970, 0.10337),
    LMSParams(8, 0.1021, 8.6151, 0.10119),
    LMSParams(9, 0.0917, 8.9014, 0.09961),
    LMSParams(10, 0.0820, 9.1649, 0.09844),
    LMSParams(11, 0.0730, 9.4122, 0.09756),
    LMSParams(12, 0.0644, 9.6479, 0.09685),
    LMSParams(13, 0.0563, 9.8749, 0.09626),
    LMSParams(14, 0.0487, 10.0953, 0.09576),
    LMSParams(15, 0.0413, 10.3108, 0.09532),
    LMSParams(16, 0.0343, 10.5228, 0.09495),
    LMSParams(17, 0.0275, 10.7319, 0.09462),
    LMSParams(18, 0.0211, 10.9385, 0.09432),
    LMSParams(19, 0.0148, 11.1430, 0.09405),
    LMSParams(20, 0.0087, 11.3462, 0.09379),
    LMSParams(21, 0.0029, 11.5486, 0.09355),
    LMSParams(22, -0.0028, 11.7504, 0.09332),
    LMSParams(23, -0.0083, 11.9514, 0.09311),
    LMSParams(24, -0.0137, 12.1515, 0.09291),
]

# WHO Weight-for-age: Girls (0-24 months)
# 資料來源: WHO Child Growth Standards (2006)
GIRLS_WEIGHT_FOR_AGE: list[LMSParams] = [
    LMSParams(0, 0.3809, 3.2322, 0.14171),
    LMSParams(1, 0.1714, 4.1873, 0.13724),
    LMSParams(2, 0.0962, 5.1282, 0.13000),
    LMSParams(3, 0.0402, 5.8458, 0.12619),
    LMSParams(4, -0.0050, 6.4237, 0.12402),
    LMSParams(5, -0.0430, 6.8985, 0.12274),
    LMSParams(6, -0.0756, 7.2970, 0.12204),
    LMSParams(7, -0.1039, 7.6422, 0.12178),
    LMSParams(8, -0.1288, 7.9487, 0.12181),
    LMSParams(9, -0.1507, 8.2254, 0.12199),
    LMSParams(10, -0.1700, 8.4800, 0.12223),
    LMSParams(11, -0.1872, 8.7192, 0.12247),
    LMSParams(12, -0.2024, 8.9481, 0.12268),
    LMSParams(13, -0.2158, 9.1699, 0.12283),
    LMSParams(14, -0.2278, 9.3870, 0.12294),
    LMSParams(15, -0.2384, 9.6008, 0.12299),
    LMSParams(16, -0.2478, 9.8124, 0.12303),
    LMSParams(17, -0.2562, 10.0226, 0.12306),
    LMSParams(18, -0.2637, 10.2315, 0.12309),
    LMSParams(19, -0.2703, 10.4393, 0.12315),
    LMSParams(20, -0.2762, 10.6464, 0.12323),
    LMSParams(21, -0.2815, 10.8534, 0.12335),
    LMSParams(22, -0.2862, 11.0608, 0.12351),
    LMSParams(23, -0.2903, 11.2688, 0.12370),
    LMSParams(24, -0.2941, 11.4775, 0.12393),
]


# 預計算的百分位表 (方便快速查詢)
# P3, P15, P50, P85, P97 對應 Z-score: -1.88, -1.04, 0, 1.04, 1.88
PERCENTILE_Z_SCORES = {
    3: -1.88079,
    5: -1.64485,
    10: -1.28155,
    15: -1.03643,
    25: -0.67449,
    50: 0.0,
    75: 0.67449,
    85: 1.03643,
    90: 1.28155,
    95: 1.64485,
    97: 1.88079,
}


def get_lms_params(
    gender: Literal["male", "female"], age_months: int
) -> LMSParams | None:
    """取得指定性別和月齡的 LMS 參數.
    
    Args:
        gender: 性別 ("male" 或 "female")
        age_months: 月齡 (0-24)
    
    Returns:
        LMSParams 或 None (如果超出範圍)
    """
    if age_months < 0 or age_months > 24:
        return None
    
    data = BOYS_WEIGHT_FOR_AGE if gender == "male" else GIRLS_WEIGHT_FOR_AGE
    return data[age_months]


def weight_to_zscore(
    weight_kg: float, gender: Literal["male", "female"], age_months: int
) -> float | None:
    """將體重轉換為 Z-score.
    
    Args:
        weight_kg: 體重 (公斤)
        gender: 性別
        age_months: 月齡
    
    Returns:
        Z-score 或 None
    """
    params = get_lms_params(gender, age_months)
    if params is None:
        return None
    
    L, M, S = params.L, params.M, params.S
    
    if abs(L) < 0.0001:  # L ≈ 0
        return (weight_kg / M - 1) / S
    else:
        return (pow(weight_kg / M, L) - 1) / (L * S)


def zscore_to_percentile(z: float) -> float:
    """將 Z-score 轉換為百分位.
    
    使用標準常態分佈累積分佈函數 (CDF).
    """
    import math
    
    # 使用 error function 近似
    return 0.5 * (1 + math.erf(z / math.sqrt(2))) * 100


def weight_to_percentile(
    weight_kg: float, gender: Literal["male", "female"], age_months: int
) -> float | None:
    """將體重轉換為百分位.
    
    Args:
        weight_kg: 體重 (公斤)
        gender: 性別
        age_months: 月齡
    
    Returns:
        百分位 (0-100) 或 None
    """
    z = weight_to_zscore(weight_kg, gender, age_months)
    if z is None:
        return None
    return zscore_to_percentile(z)


def percentile_to_weight(
    percentile: float, gender: Literal["male", "female"], age_months: int
) -> float | None:
    """將百分位轉換為體重.
    
    Args:
        percentile: 百分位 (0-100)
        gender: 性別
        age_months: 月齡
    
    Returns:
        體重 (公斤) 或 None
    """
    import math
    
    params = get_lms_params(gender, age_months)
    if params is None:
        return None
    
    # 百分位轉 Z-score (使用逆標準常態分佈)
    # 近似公式
    p = percentile / 100
    if p <= 0 or p >= 1:
        return None
    
    # Rational approximation for inverse normal CDF
    # Abramowitz and Stegun approximation
    if p < 0.5:
        t = math.sqrt(-2 * math.log(p))
        z = -(t - (2.515517 + 0.802853 * t + 0.010328 * t * t) / 
              (1 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t * t * t))
    else:
        t = math.sqrt(-2 * math.log(1 - p))
        z = t - (2.515517 + 0.802853 * t + 0.010328 * t * t) / \
            (1 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t * t * t)
    
    L, M, S = params.L, params.M, params.S
    
    if abs(L) < 0.0001:  # L ≈ 0
        return M * math.exp(S * z)
    else:
        return M * pow(1 + L * S * z, 1 / L)


def get_percentile_weights(
    gender: Literal["male", "female"], age_months: int
) -> dict[int, float] | None:
    """取得指定性別和月齡的常用百分位體重.
    
    Args:
        gender: 性別
        age_months: 月齡
    
    Returns:
        百分位對應體重的字典 {3: 2.5, 15: 2.9, 50: 3.3, 85: 3.8, 97: 4.2}
    """
    result = {}
    for p in [3, 15, 50, 85, 97]:
        weight = percentile_to_weight(p, gender, age_months)
        if weight:
            result[p] = round(weight, 2)
    return result if result else None


# 預計算常用百分位表 (供快速查詢)
def generate_percentile_tables() -> dict:
    """產生完整百分位表."""
    tables = {"male": {}, "female": {}}
    
    for gender in ["male", "female"]:
        for age in range(25):  # 0-24 months
            tables[gender][age] = get_percentile_weights(gender, age)  # type: ignore
    
    return tables


# 快速查詢表
PERCENTILE_TABLES = generate_percentile_tables()


if __name__ == "__main__":
    # 測試
    print("=== WHO 體重-年齡百分位表 (0-24 個月) ===\n")
    
    print("【男嬰】")
    print("月齡 |   P3  |  P15  |  P50  |  P85  |  P97")
    print("-" * 50)
    for age in range(25):
        weights = PERCENTILE_TABLES["male"][age]
        if weights:
            print(f" {age:2d}  | {weights[3]:5.2f} | {weights[15]:5.2f} | "
                  f"{weights[50]:5.2f} | {weights[85]:5.2f} | {weights[97]:5.2f}")
    
    print("\n【女嬰】")
    print("月齡 |   P3  |  P15  |  P50  |  P85  |  P97")
    print("-" * 50)
    for age in range(25):
        weights = PERCENTILE_TABLES["female"][age]
        if weights:
            print(f" {age:2d}  | {weights[3]:5.2f} | {weights[15]:5.2f} | "
                  f"{weights[50]:5.2f} | {weights[85]:5.2f} | {weights[97]:5.2f}")
    
    print("\n=== 測試計算 ===")
    # 測試: 3 個月男嬰 6.5kg
    z = weight_to_zscore(6.5, "male", 3)
    p = weight_to_percentile(6.5, "male", 3)
    print(f"3 個月男嬰 6.5kg: Z-score={z:.2f}, 百分位={p:.1f}%")
    
    # 測試: 12 個月女嬰 9.0kg
    z = weight_to_zscore(9.0, "female", 12)
    p = weight_to_percentile(9.0, "female", 12)
    print(f"12 個月女嬰 9.0kg: Z-score={z:.2f}, 百分位={p:.1f}%")
