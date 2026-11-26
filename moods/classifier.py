"""Mood Weather classification (predefined rule, not machine learning).

Each rating is 1-5. Mood counts double. Stress is reversed (low stress is good), so:

    score = 2*mood + energy + sleep_quality + (6 - stress)      # range 5 to 25

    score >= 21  -> Sunny
    17 - 20      -> Partly Cloudy
    13 - 16      -> Cloudy
     9 - 12      -> Rainy
     <= 8        -> Stormy
"""

SUNNY = "sunny"
PARTLY_CLOUDY = "partly_cloudy"
CLOUDY = "cloudy"
RAINY = "rainy"
STORMY = "stormy"

WEATHER_CHOICES = [
    (SUNNY, "Sunny"),
    (PARTLY_CLOUDY, "Partly Cloudy"),
    (CLOUDY, "Cloudy"),
    (RAINY, "Rainy"),
    (STORMY, "Stormy"),
]

WEATHER_ICONS = {SUNNY: "☀️", PARTLY_CLOUDY: "⛅", CLOUDY: "☁️", RAINY: "\U0001f327️", STORMY: "⛈️"}

WEATHER_MESSAGES = {
    SUNNY: "A bright day. Notice what helped you feel this way.",
    PARTLY_CLOUDY: "Mostly good with a few clouds. A fairly balanced day.",
    CLOUDY: "A neutral, in-between day.",
    RAINY: "A heavier day. Be gentle with yourself.",
    STORMY: "A very tough day. Rest, and reach out to someone you trust if you need to.",
}


def mood_score(mood, stress, energy, sleep_quality):
    return 2 * mood + energy + sleep_quality + (6 - stress)


def classify(mood, stress, energy, sleep_quality):
    score = mood_score(mood, stress, energy, sleep_quality)
    if score >= 21:
        return SUNNY
    if score >= 17:
        return PARTLY_CLOUDY
    if score >= 13:
        return CLOUDY
    if score >= 9:
        return RAINY
    return STORMY
