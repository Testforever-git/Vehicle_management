def mask_plate(plate: str) -> str:
    if not plate:
        return ""
    if len(plate) <= 4:
        return plate
    return plate[:2] + "**" + plate[-2:]
