
def verbose_timedelta(delta):
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    dstr = "%s day%s" % (delta.days, "s"[delta.days==1:])
    hstr = "%s hour%s" % (hours, "s"[hours==1:])
    mstr = "%s minute%s" % (minutes, "s"[minutes==1:])
    sstr = "%s second%s" % (seconds, "s"[seconds==1:])
    dhms = [dstr, hstr, mstr, sstr]
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