"""
Project : ade-esiee-ng
File : ade-parser
Author : DELEVACQ Wallerand
Date : 25/03/18
"""
import urllib.request
import urllib.error

import json

from icalendar import Calendar
import time, threading
import logging

def download_ics_from_planif():
    url = "https://planif.esiee.fr/jsp/custom/modules/plannings/anonymous_cal.jsp?resources=147,738,739,743,744,2841,5757,746,747,748,2781,2782,3286,682,683,684,685,659,665,674,680,681,727,733,785,998,1295,2555,2743,5215,5688,731,734,735,736,740,741,742,780,782,1852,2584,4350,5321,786,787,788,789,790,2270,2275,2277,2278,2282,704,745,773,775,776,4937,728,2117,772,719,2112,183,185,196,4051,4679,2072,2074,2272,2276,2089,154,713,163,167,700,701,705,707,708,712,714,715,716,724,725,726,737,749,758,759,1057,1858,1908,2090,2108,2281,428,717,720,721,722,2265,2274,2279&projectId=7&calType=ical&nbWeeks=12"

    try:
        html_data = urllib.request.urlopen(url)
        g = html_data.read().decode('utf8')

        with open("data/ADECal.ics", "w") as file:
            file.write(g)
            file.close()
            logging.info("[ADE-PARSER] ICS file is up to date")
        return True

    except urllib.error.URLError as e:
        print(e)
        return False


def str_to_date(str):
    return str[0:4] + "-" + str[4:6] + "-" + str[6:8] + str[8] + str[9:11] + ":" + str[11:13] + ":" + str[
                                                                                                      13:15] + ".000Z"


def ics_to_json_from_ade():
    events_list = []

    with open("data/ADECal.ics", "r") as g:
        gcal = Calendar.from_ical(g.read())
        for component in gcal.walk():
            if component.name == "VEVENT":
                events_list.append(dict(description=str(component.get("DESCRIPTION")),
                                        end=(str_to_date(str(component.get("DTEND").to_ical().decode("utf-8")))),
                                        start=(str_to_date(str(component.get("DTSTART").to_ical().decode("utf-8")))),
                                        name=str(component.get("SUMMARY")),
                                        rooms=(component.get("LOCATION").replace(" ", "")).split(",")))
        g.close()

    with open("data/calendar.json", "w") as f:
        json.dump(events_list, f)
        f.close()
        logging.info("[ADE-PARSER] Json file is up to date")


def get_json_calendar():
    try:
        with open("data/calendar.json", "r") as f:
            events = json.load(f)
            f.close()
            return events

    except Exception as e:
        print(e)
        return None


def update_calendar():
    if download_ics_from_planif():
        ics_to_json_from_ade()
        logging.info("[ADE-PARSER] Calendar is up to date")
    threading.Timer(600, update_calendar).start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    logging.info("[ADE-PARSER] Starting..")
    update_calendar()