from datetime import datetime
from datetime import timedelta
import re

def gen_timetable(start, end, interval, avoid=None):
    if type(start) is not str:
        raise TypeError("argument 'start' must be 'str'")
    else:
        start = datetime.strptime(start, "%H:%M")

    if type(end) is not str:
        raise TypeError("argument 'end' must be 'str'")
    else:
        end = datetime.strptime(end, "%H:%M")

    if type(interval) is not int and type(interval) is not str:
        raise TypeError("argument 'interval' must be 'str' or 'int'")
    else:
        if type(interval) is str:
            interval = timedelta(minutes=int(re.search('[0-9]+', interval).group()))
        elif type(interval) is int:
            interval = timedelta(minutes=interval)

    if avoid != None and (type(avoid) is list or dict):
        if type(avoid[0]) is dict:
            for i in range(len(avoid)):
                if type(avoid[i]["time"] ) is not str:
                    raise TypeError("avoid["+str(i)+"]['time'] must be str")
                avoid[i]["time"] = datetime.strptime(avoid[i]["time"], "%H:%M")
        elif type(avoid) is dict:
            if type(avoid["time"] ) is not str:
                raise TypeError("avoid['time'] must be str")
            avoid["time"] = datetime.strptime(avoid["time"], "%H:%M")
            avoid = [avoid]

    timetable = [start]
    i = 0
    while timetable[-1] < end:
        if avoid != None and avoid[i]["type"] == "restart":
            if timetable[-1] > avoid[i]["time"]:
                timetable[-1] = avoid[i]["time"]
                i+=1
                continue
        if avoid != None and avoid[i]["type"] == "shorten":
            if timetable[-1]+interval > avoid[i]["time"]:
                timetable.append(avoid[i]["time"])
                i+=1
                continue
        timetable.append(timetable[-1]+interval)
    
    i = 0
    while i < len(timetable):
        timetable[i] = timetable[i].strftime("%H:%M")
        i += 1
    return timetable