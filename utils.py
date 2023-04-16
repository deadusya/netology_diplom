def diff_in_years(date1, date2):
    """Возвращает количество календарных лет между двумя датами"""
    years = (
        date1.year - date2.year - ((date1.month, date1.day) < (date2.month, date2.day))
    )
    return years


class ParseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def parse_age(agestr):
    try:
        val = int(agestr)
    except Exception as e:
        raise ParseError("Возраст должен быть числом")

    if val <= 0:
        raise ParseError("Возвраст должен быть больше 0")

    return val


def parse_sex(sexstr):
    sex = sexstr.lower()
    if sex in ["м", "ж"]:
        return {"м": 1, "ж": 2}[sex]
    else:
        raise ParseError('Пол должен быть "м" или "ж"')


def make_parse_city(api):
    def parse_city(city):
        cities = api.search_cities(city)
        if cities:
            return cities[0]['id']
        raise ParseError(f"Не знаю такого города {city}")
    return parse_city