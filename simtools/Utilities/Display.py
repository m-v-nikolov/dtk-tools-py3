from collections import Iterable


def on_off(test):
    return "on" if test else "off"


def pluralize(i, l="s"):
    if isinstance(i, Iterable):
        return l if len(i) > 1 else ""
    return l if i > 1 else ""


def verbose_timedelta(delta):
    if isinstance(delta, float):
        if delta < 1:
            return "0 seconds"
        hours, remainder = divmod(delta, 3600)
    else:
        if delta.seconds < 1:
            return "0 seconds"
        hours, remainder = divmod(delta.seconds, 3600)

    minutes, seconds = divmod(remainder, 60)
    hstr = "%s hour%s" % (hours, "s"[hours==1:])
    mstr = "%s minute%s" % (minutes, "s"[minutes==1:])
    sstr = "{:.2f} second{}".format(seconds, "s"[seconds==1:])
    dhms = [hstr, mstr, sstr]
    for x in range(len(dhms)):
        if not dhms[x].startswith('0'):
            dhms = dhms[x:]
            break
    dhms.reverse()
    for x in range(len(dhms)):
        if not dhms[x].startswith('0'):
            dhms = dhms[x:]
            break
    dhms.reverse()
    return ', '.join(dhms)