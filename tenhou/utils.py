def wind_ordinal_to_string(ordinal):
    if ordinal == 0:
        return u"東"
    if ordinal == 1:
        return u"南"
    if ordinal == 2:
        return u"西"
    else:
        return u"北"


def calculate_score_deltas(scores, position):
    """Calculate the difference in score for a list of scores, relative to the value at index `position`."""
    return [scores[idx] - scores[position] for idx in range(len(scores))]