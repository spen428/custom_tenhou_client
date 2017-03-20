import datetime


def wind_ordinal_to_string(ordinal):
    if ordinal == 0:
        return u"東"
    if ordinal == 1:
        return u"南"
    if ordinal == 2:
        return u"西"
    else:
        return u"北"


def calculate_score_deltas(scores):
    return [scores[n] - scores[0] for n in range(len(scores))]


def seconds_to_time_string(seconds):
    """Convert `seconds` seconds into a string of the form Days:HH:MM:SS.Millis"""
    # Handle days
    days = 0
    if seconds > 86400:  # 24 hours
        days = int(seconds / 86400)
        seconds %= 86400
    time_string = str(datetime.timedelta(seconds=seconds))
    # Make sure it reads 00:00:00 instead of 0:00:00
    if seconds < 36000:  # 10 hours
        time_string = "0" + time_string
    if days > 0:
        time_string = str(days) + ":" + time_string
    return time_string
