from src.nutrition.calculations import calculate_bmi, calculate_bmr, calculate_tdee, calculate_calorie_target, calculate_macros


# Test valid BMI

bmi = calculate_bmi(75, 175)

if round(bmi, 2) == 24.49:
    print("PASS: Valid BMI calculated correctly")
else:
    raise ValueError("FAIL: BMI calculation is incorrect")


# Test invalid weight

try:
    calculate_bmi(0, 175)
except ValueError:
    print("PASS: Invalid weight rejected")
else:
    raise ValueError("FAIL: Invalid weight was accepted")


# Test invalid height

try:
    calculate_bmi(75, 0)
except ValueError:
    print("PASS: Invalid height rejected")
else:
    raise ValueError("FAIL: Invalid height was accepted")

# Test valid male BMR

bmr = calculate_bmr(
    weight_kg=75,
    height_cm=175,
    age=25,
    sex="Male"
)

if round(bmr, 2) == 1723.75:
    print("PASS: Male BMR calculated correctly")
else:
    raise ValueError("FAIL: Male BMR calculation is incorrect")


# Test valid female BMR

bmr = calculate_bmr(
    weight_kg=60,
    height_cm=165,
    age=25,
    sex="Female"
)

if round(bmr, 2) == 1345.25:
    print("PASS: Female BMR calculated correctly")
else:
    raise ValueError("FAIL: Female BMR calculation is incorrect")


# Test invalid age

try:
    calculate_bmr(
        weight_kg=75,
        height_cm=175,
        age=0,
        sex="Male"
    )
except ValueError:
    print("PASS: Invalid BMR age rejected")
else:
    raise ValueError("FAIL: Invalid BMR age was accepted")


# Test unsupported sex value

try:
    calculate_bmr(
        weight_kg=75,
        height_cm=175,
        age=25,
        sex="Prefer not to say"
    )
except ValueError:
    print("PASS: Unsupported BMR sex value rejected")
else:
    raise ValueError("FAIL: Unsupported BMR sex value was accepted")

# Test valid TDEE

tdee = calculate_tdee(
    1723.75,
    "Moderately Active"
)

if round(tdee, 2) == 2671.81:
    print("PASS: TDEE calculated correctly")
else:
    raise ValueError("FAIL: TDEE calculation is incorrect")


# Test invalid BMR

try:
    calculate_tdee(
        0,
        "Moderately Active"
    )
except ValueError:
    print("PASS: Invalid TDEE BMR rejected")
else:
    raise ValueError("FAIL: Invalid TDEE BMR was accepted")


# Test invalid activity level

try:
    calculate_tdee(
        1723.75,
        "Super Active"
    )
except ValueError:
    print("PASS: Invalid activity level rejected")
else:
    raise ValueError("FAIL: Invalid activity level was accepted")

# Test fat loss calorie target

calorie_target = calculate_calorie_target(
    2500,
    "Fat Loss"
)

if round(calorie_target, 2) == 2125.00:
    print("PASS: Fat loss calorie target calculated correctly")
else:
    raise ValueError("FAIL: Fat loss calorie target is incorrect")


# Test maintenance calorie target

calorie_target = calculate_calorie_target(
    2500,
    "Maintenance"
)

if round(calorie_target, 2) == 2500.00:
    print("PASS: Maintenance calorie target calculated correctly")
else:
    raise ValueError("FAIL: Maintenance calorie target is incorrect")


# Test muscle gain calorie target

calorie_target = calculate_calorie_target(
    2500,
    "Muscle Gain"
)

if round(calorie_target, 2) == 2750.00:
    print("PASS: Muscle gain calorie target calculated correctly")
else:
    raise ValueError("FAIL: Muscle gain calorie target is incorrect")


# Test invalid TDEE

try:
    calculate_calorie_target(
        0,
        "Maintenance"
    )
except ValueError:
    print("PASS: Invalid calorie target TDEE rejected")
else:
    raise ValueError("FAIL: Invalid calorie target TDEE was accepted")


# Test invalid goal

try:
    calculate_calorie_target(
        2500,
        "Extreme Bulk"
    )
except ValueError:
    print("PASS: Invalid calorie goal rejected")
else:
    raise ValueError("FAIL: Invalid calorie goal was accepted")


# Test valid macros

macros = calculate_macros(
    calorie_target=2500,
    weight_kg=75,
    protein_g_per_kg=2.0,
    fat_percentage=0.25
)

if (
    round(macros["protein_g"], 2) == 150.00
    and round(macros["fat_g"], 2) == 69.44
    and round(macros["carbs_g"], 2) == 318.75
):
    print("PASS: Macros calculated correctly")
else:
    raise ValueError("FAIL: Macro calculation is incorrect")


# Test invalid calorie target

try:
    calculate_macros(
        calorie_target=0,
        weight_kg=75,
        protein_g_per_kg=2.0,
        fat_percentage=0.25
    )
except ValueError:
    print("PASS: Invalid macro calorie target rejected")
else:
    raise ValueError("FAIL: Invalid macro calorie target was accepted")


# Test invalid weight

try:
    calculate_macros(
        calorie_target=2500,
        weight_kg=0,
        protein_g_per_kg=2.0,
        fat_percentage=0.25
    )
except ValueError:
    print("PASS: Invalid macro weight rejected")
else:
    raise ValueError("FAIL: Invalid macro weight was accepted")


# Test invalid protein rate

try:
    calculate_macros(
        calorie_target=2500,
        weight_kg=75,
        protein_g_per_kg=0,
        fat_percentage=0.25
    )
except ValueError:
    print("PASS: Invalid protein rate rejected")
else:
    raise ValueError("FAIL: Invalid protein rate was accepted")


# Test invalid fat percentage

try:
    calculate_macros(
        calorie_target=2500,
        weight_kg=75,
        protein_g_per_kg=2.0,
        fat_percentage=1.2
    )
except ValueError:
    print("PASS: Invalid fat percentage rejected")
else:
    raise ValueError("FAIL: Invalid fat percentage was accepted")


# Test macros exceeding calorie target

try:
    calculate_macros(
        calorie_target=1000,
        weight_kg=100,
        protein_g_per_kg=3.0,
        fat_percentage=0.50
    )
except ValueError:
    print("PASS: Macro targets exceeding calories rejected")
else:
    raise ValueError("FAIL: Excessive macro targets were accepted")