"""
Project : ade-esiee-ng
File : ade_api
Author : DELEVACQ Wallerand
Date : 25/03/18
"""
import csv
import ujson
import logging
import re
from datetime import datetime, timedelta
import requests
from xml.etree import ElementTree


class ADEApi():
    events = ()
    groups_and_unites = ()
    unites = ()
    groups = {}

    def __init__(self):
        self._get_events_from_xml()
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
        pass

    def _get_events_from_xml(self):
        try:
            tree = ElementTree.parse("data/ade.xml")
            self.events = tree.getroot().findall("event")
        except FileNotFoundError as e:
            print(e)
            logging.error("[ADE-API] ade xml file not found")

    def set_groups_unites(self, aurion_data):
        self.groups_and_unites = tuple()
        self.unites = tuple()
        for data in aurion_data:
            groups = self.groups_finder(data)
            try:
                self.groups[self.format_unites(data)] += groups
            except KeyError:
                self.groups[self.format_unites(data)] = groups
            for group in groups:
                d = dict([("unite", self.format_unites(data)), ("groupe", group)])
                self.groups_and_unites += tuple([d])
                self.unites += tuple([self.format_unites(data)])

    @staticmethod
    def groups_finder(data):
        '''

        :param data: row of aurion provided data
        :return: list of different possible cases of group number
        '''
        back = [m.start() for m in re.finditer("_", data[::-1])]
        if "EIG_2022" in data:
            real_group = data[len(data) - back[0]:]
            return [real_group, real_group[0].upper() + real_group[1:].lower(),
                    real_group[0].lower() + real_group[1:].upper(), real_group.upper(), real_group.lower()]
        if "EIG" in data:
            return data[len(data) - 3:len(data) - 2] + data[len(data) - 2:len(data) - 1].lower() + data[len(data):]

        if "PR_3001" in data and len(back) > 4:
            real_group = data[len(data) - back[0]:].replace("_", "-")
            return [real_group, real_group[0].upper() + real_group[1:].lower(),
                    real_group[0].lower() + real_group[1:].upper(), real_group.upper(), real_group.lower()]

        if "PR" in data and len(back) > 4:
            real_group = data[len(data) - back[1]:].replace("_", "-")
            return [real_group, real_group[0].upper() + real_group[1:].lower(),
                    real_group[0].lower() + real_group[1:].upper(), real_group.upper(), real_group.lower()]

        if "EN3" in data:
            real_group = data[len(data) - back[0]:].replace("_", "-")
            if len(real_group) >= 2:
                return [real_group, real_group[0].upper() + real_group[1:].lower(),
                        real_group[0].lower() + real_group[1:].upper(), real_group.upper(), real_group.lower()]
            else:
                return ["xx"]

        if len(back) <= 1:
            # return [data[data.find("_")+1:]]
            return ["", data[data.find("_") + 1:]]

        real_group = data[len(data) - back[0]:]
        if len(real_group) >= 2:
            return [real_group, real_group[0].upper() + real_group[1:].lower(),
                    real_group[0].lower() + real_group[1:].upper(), real_group.upper(), real_group.lower()]
        # elif not "EN3" in data:
        else:
            return [real_group, real_group.upper(), real_group.lower()]

    @staticmethod
    def format_unites(data):
        '''

        :param data: row of aurion provided data
        :return: unite name formatted likes unite name in calendar api
        '''
        back = [m.start() for m in re.finditer("_", data)]
        if len(back) == 1:
            real_group = data[back[0] + 1:]
            real_group = real_group.replace("_", "-")
            # Correction pour les noms de promos
            real_group += ":"
            return real_group
        if len(back) == 3:  # 16_E4FR_RE4R23_2R
            real_group = data[back[1] + 1:back[2]]
            real_group = real_group.replace("_", "-")
            return real_group
        if len(back) == 4:  # 16_E2_IGE_2102_2
            real_group = data[back[1] + 1:back[3]]
            real_group = real_group.replace("_", "-")
            return real_group
        if len(back) == 5:  # 16_E2_ESP_2003_S2_2
            if "PR" in data:
                real_group = data[back[1] + 1:back[3]]
                real_group = real_group.replace("_", "-")
            else:
                real_group = data[back[1] + 1:back[4]]
                real_group = real_group.replace("_", "-")
            return real_group

    @staticmethod
    def _has_cours(xml_event, unite, groups):
        name = xml_event.attrib["name"]
        if unite == ADEApi._get_unite(xml_event):
            rows = (xml_event.find("resources")).findall("resource")
            for row in rows:
                if "trainee" == row.attrib["category"]:
                    if row.attrib["name"] in groups:
                        return True
        return False

    @staticmethod
    def _get_instructor(xml_event):
        instructors = []
        for row in (xml_event.find("resources")).findall("resource"):
            if "instructor" in row.attrib["category"]:
                instructors.append(row.attrib["name"])
        return instructors

    @staticmethod
    def _get_name(xml_event):
        for row in (xml_event.find("resources")).findall("resource"):
            if "category6" in row.attrib["category"]:
                return xml_event.attrib["name"]
        return ""

    @staticmethod
    def _get_unite(xml_event):
        for row in (xml_event.find("resources")).findall("resource"):
            if "category6" in row.attrib["category"]:
                return row.attrib["name"]
        return ""

    @staticmethod
    def _get_classroom(xml_event):
        classrooms = []
        for row in (xml_event.find("resources")).findall("resource"):
            if "classroom" in row.attrib["category"]:
                classrooms.append(row.attrib["name"])
        return classrooms

    @staticmethod
    def _get_start_date(xml_event):
        date = xml_event.attrib["date"]
        date = datetime.strptime(date, "%d/%m/%Y")

        start_hour = xml_event.attrib["startHour"]
        start_hour = datetime.strptime(start_hour, "%H:%M")
        start_hour -= timedelta(hours=1)

        return datetime.strftime(date, "%Y-%m-%d") + "T" + datetime.strftime(start_hour, "%H:%M") + ":00.000Z"

    @staticmethod
    def _get_end_date(xml_event):
        date = xml_event.attrib["date"]
        date = datetime.strptime(date, "%d/%m/%Y")

        end_hour = xml_event.attrib["endHour"]
        end_hour = datetime.strptime(end_hour, "%H:%M")
        end_hour -= timedelta(hours=1)

        return datetime.strftime(date, "%Y-%m-%d") + "T" + datetime.strftime(end_hour, "%H:%M") + ":00.000Z"

    @staticmethod
    def get_json_calendar():
        try:
            with open("data/calendar.json", "r") as f:
                events = ujson.load(f)
                f.close()
                return events

        except Exception as e:
            print(e)
            return None

    @staticmethod
    def search_unite_from_csv(unite_code):
        with open("data/BDE_UNITES.csv", "r") as f:
            lines = f.readlines()
            fieldsnames = ["Code.Unité", "Libellé.Unité"]
            data = csv.DictReader(lines, fieldsnames, delimiter=';')
            for row in data:
                if unite_code.replace("-", "_") in row.get(fieldsnames[0]):
                    return row.get(fieldsnames[1])

            return ""

    def get_all_cours(self):
        result = []
        for event in self.events:
            unite = ADEApi._get_unite(event)
            if unite in self.unites:
                group = self.groups[unite]
                if ADEApi._has_cours(event, unite, group):
                    name = ADEApi._get_name(event)
                    instructors = ADEApi._get_instructor(event)
                    unite = ADEApi._get_unite(event)
                    classrooms = ADEApi._get_classroom(event)
                    start = ADEApi._get_start_date(event)
                    end = ADEApi._get_end_date(event)

                    obj = {"name": name, "prof": ", ".join(instructors), "rooms": " ".join(classrooms),
                           "start": start, "end": end, "unite": self.search_unite_from_csv(unite),
                           "description": unite + " " + " ".join(instructors) + " " + " ".join(group)}
                    if obj not in result:
                        result.append(obj)

        return result
