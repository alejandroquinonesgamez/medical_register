from .translations import get_bmi_description as get_bmi_text


def calculate_bmi(weight_kg, height_m):
    if height_m <= 0:
        return 0
    return round(weight_kg / (height_m ** 2), 1)


def get_bmi_description(bmi):
    if bmi < 18.5:
        return get_bmi_text("underweight")
    elif 18.5 <= bmi < 25:
        return get_bmi_text("normal")
    elif 25 <= bmi < 30:
        return get_bmi_text("overweight")
    else:
        return get_bmi_text("obese")


