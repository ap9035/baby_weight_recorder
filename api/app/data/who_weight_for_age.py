"""WHO 兒童生長標準 - 體重對年齡 (Weight-for-age).

資料來源: WHO Child Growth Standards
https://www.who.int/tools/child-growth-standards/standards/weight-for-age

台灣衛福部國健署採用此標準作為兒童生長評估依據。

數據格式:
- age_months: 月齡 (0-60 個月 / 0-5 歲)
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


# 最大支援月齡
MAX_AGE_MONTHS = 60

# WHO Weight-for-age: Boys (0-60 months / 0-5 years)
# 資料來源: WHO Child Growth Standards (2006)
BOYS_WEIGHT_FOR_AGE: list[LMSParams] = [
    # 0-12 months
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
    # 13-24 months
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
    # 25-36 months (2-3 years)
    LMSParams(25, -0.0189, 12.3502, 0.09272),
    LMSParams(26, -0.0240, 12.5466, 0.09254),
    LMSParams(27, -0.0289, 12.7401, 0.09237),
    LMSParams(28, -0.0337, 12.9303, 0.09221),
    LMSParams(29, -0.0385, 13.1169, 0.09205),
    LMSParams(30, -0.0431, 13.2997, 0.09190),
    LMSParams(31, -0.0476, 13.4792, 0.09175),
    LMSParams(32, -0.0520, 13.6556, 0.09160),
    LMSParams(33, -0.0563, 13.8293, 0.09145),
    LMSParams(34, -0.0605, 14.0006, 0.09131),
    LMSParams(35, -0.0646, 14.1694, 0.09117),
    LMSParams(36, -0.0687, 14.3360, 0.09103),
    # 37-48 months (3-4 years)
    LMSParams(37, -0.0726, 14.5001, 0.09090),
    LMSParams(38, -0.0764, 14.6619, 0.09076),
    LMSParams(39, -0.0802, 14.8216, 0.09063),
    LMSParams(40, -0.0839, 14.9791, 0.09050),
    LMSParams(41, -0.0875, 15.1348, 0.09037),
    LMSParams(42, -0.0910, 15.2888, 0.09025),
    LMSParams(43, -0.0944, 15.4410, 0.09012),
    LMSParams(44, -0.0978, 15.5917, 0.09000),
    LMSParams(45, -0.1011, 15.7409, 0.08988),
    LMSParams(46, -0.1043, 15.8888, 0.08977),
    LMSParams(47, -0.1074, 16.0354, 0.08965),
    LMSParams(48, -0.1105, 16.1808, 0.08954),
    # 49-60 months (4-5 years)
    LMSParams(49, -0.1135, 16.3252, 0.08943),
    LMSParams(50, -0.1164, 16.4687, 0.08933),
    LMSParams(51, -0.1193, 16.6113, 0.08922),
    LMSParams(52, -0.1221, 16.7532, 0.08913),
    LMSParams(53, -0.1249, 16.8945, 0.08903),
    LMSParams(54, -0.1276, 17.0353, 0.08894),
    LMSParams(55, -0.1302, 17.1756, 0.08885),
    LMSParams(56, -0.1328, 17.3155, 0.08877),
    LMSParams(57, -0.1353, 17.4551, 0.08869),
    LMSParams(58, -0.1378, 17.5945, 0.08861),
    LMSParams(59, -0.1402, 17.7336, 0.08854),
    LMSParams(60, -0.1426, 17.8727, 0.08847),
]

# WHO Weight-for-age: Girls (0-60 months / 0-5 years)
# 資料來源: WHO Child Growth Standards (2006)
GIRLS_WEIGHT_FOR_AGE: list[LMSParams] = [
    # 0-12 months
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
    # 13-24 months
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
    # 25-36 months (2-3 years)
    LMSParams(25, -0.2975, 11.6864, 0.12420),
    LMSParams(26, -0.3005, 11.8947, 0.12451),
    LMSParams(27, -0.3032, 12.1015, 0.12486),
    LMSParams(28, -0.3057, 12.3061, 0.12526),
    LMSParams(29, -0.3080, 12.5083, 0.12569),
    LMSParams(30, -0.3101, 12.7076, 0.12615),
    LMSParams(31, -0.3120, 12.9039, 0.12663),
    LMSParams(32, -0.3138, 13.0970, 0.12713),
    LMSParams(33, -0.3155, 13.2869, 0.12764),
    LMSParams(34, -0.3170, 13.4737, 0.12816),
    LMSParams(35, -0.3185, 13.6575, 0.12869),
    LMSParams(36, -0.3198, 13.8384, 0.12922),
    # 37-48 months (3-4 years)
    LMSParams(37, -0.3211, 14.0164, 0.12976),
    LMSParams(38, -0.3222, 14.1918, 0.13030),
    LMSParams(39, -0.3233, 14.3646, 0.13084),
    LMSParams(40, -0.3244, 14.5350, 0.13138),
    LMSParams(41, -0.3253, 14.7030, 0.13192),
    LMSParams(42, -0.3263, 14.8688, 0.13246),
    LMSParams(43, -0.3271, 15.0324, 0.13300),
    LMSParams(44, -0.3280, 15.1940, 0.13354),
    LMSParams(45, -0.3288, 15.3536, 0.13408),
    LMSParams(46, -0.3295, 15.5112, 0.13462),
    LMSParams(47, -0.3303, 15.6670, 0.13516),
    LMSParams(48, -0.3310, 15.8211, 0.13570),
    # 49-60 months (4-5 years)
    LMSParams(49, -0.3316, 15.9735, 0.13624),
    LMSParams(50, -0.3323, 16.1243, 0.13678),
    LMSParams(51, -0.3329, 16.2736, 0.13732),
    LMSParams(52, -0.3335, 16.4214, 0.13787),
    LMSParams(53, -0.3341, 16.5679, 0.13841),
    LMSParams(54, -0.3347, 16.7130, 0.13896),
    LMSParams(55, -0.3353, 16.8569, 0.13950),
    LMSParams(56, -0.3358, 16.9996, 0.14005),
    LMSParams(57, -0.3364, 17.1412, 0.14060),
    LMSParams(58, -0.3369, 17.2817, 0.14116),
    LMSParams(59, -0.3375, 17.4213, 0.14171),
    LMSParams(60, -0.3380, 17.5599, 0.14227),
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


def get_lms_params(gender: Literal["male", "female"], age_months: int) -> LMSParams | None:
    """取得指定性別和月齡的 LMS 參數.

    Args:
        gender: 性別 ("male" 或 "female")
        age_months: 月齡 (0-60)

    Returns:
        LMSParams 或 None (如果超出範圍)
    """
    if age_months < 0 or age_months > MAX_AGE_MONTHS:
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
        z = -(
            t
            - (2.515517 + 0.802853 * t + 0.010328 * t * t)
            / (1 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t * t * t)
        )
    else:
        t = math.sqrt(-2 * math.log(1 - p))
        z = t - (2.515517 + 0.802853 * t + 0.010328 * t * t) / (
            1 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t * t * t
        )

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
def generate_percentile_tables() -> dict[str, dict[int, dict[int, float] | None]]:
    """產生完整百分位表."""
    tables: dict[str, dict[int, dict[int, float] | None]] = {"male": {}, "female": {}}

    for gender in ["male", "female"]:
        for age in range(MAX_AGE_MONTHS + 1):  # 0-60 months
            tables[gender][age] = get_percentile_weights(gender, age)  # type: ignore

    return tables


# 快速查詢表
PERCENTILE_TABLES = generate_percentile_tables()


if __name__ == "__main__":
    # 測試
    print("=== WHO 體重-年齡百分位表 (0-60 個月 / 0-5 歲) ===\n")

    print("【男童】")
    print("月齡 |   P3  |  P15  |  P50  |  P85  |  P97  | 年齡")
    print("-" * 60)
    for age in range(MAX_AGE_MONTHS + 1):
        weights = PERCENTILE_TABLES["male"][age]
        years = age // 12
        months = age % 12
        age_str = f"{years}歲{months}月" if years > 0 else f"{months}月"
        if weights:
            print(
                f" {age:2d}  | {weights[3]:5.2f} | {weights[15]:5.2f} | "
                f"{weights[50]:5.2f} | {weights[85]:5.2f} | {weights[97]:5.2f} | {age_str}"
            )

    print("\n【女童】")
    print("月齡 |   P3  |  P15  |  P50  |  P85  |  P97  | 年齡")
    print("-" * 60)
    for age in range(MAX_AGE_MONTHS + 1):
        weights = PERCENTILE_TABLES["female"][age]
        years = age // 12
        months = age % 12
        age_str = f"{years}歲{months}月" if years > 0 else f"{months}月"
        if weights:
            print(
                f" {age:2d}  | {weights[3]:5.2f} | {weights[15]:5.2f} | "
                f"{weights[50]:5.2f} | {weights[85]:5.2f} | {weights[97]:5.2f} | {age_str}"
            )

    print("\n=== 測試計算 ===")
    # 測試: 3 個月男嬰 6.5kg
    z = weight_to_zscore(6.5, "male", 3)
    p = weight_to_percentile(6.5, "male", 3)
    print(f"3 個月男嬰 6.5kg: Z-score={z:.2f}, 百分位={p:.1f}%")

    # 測試: 12 個月女嬰 9.0kg
    z = weight_to_zscore(9.0, "female", 12)
    p = weight_to_percentile(9.0, "female", 12)
    print(f"12 個月女嬰 9.0kg: Z-score={z:.2f}, 百分位={p:.1f}%")

    # 測試: 3 歲男童 (36 個月) 14.5kg
    z = weight_to_zscore(14.5, "male", 36)
    p = weight_to_percentile(14.5, "male", 36)
    print(f"3 歲男童 14.5kg: Z-score={z:.2f}, 百分位={p:.1f}%")

    # 測試: 5 歲女童 (60 個月) 18.0kg
    z = weight_to_zscore(18.0, "female", 60)
    p = weight_to_percentile(18.0, "female", 60)
    print(f"5 歲女童 18.0kg: Z-score={z:.2f}, 百分位={p:.1f}%")
