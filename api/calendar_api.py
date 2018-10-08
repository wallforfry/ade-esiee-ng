"""
Project : ADE-ESIEE
File : calendar_api.py
Author : DELEVACQ Wallerand
Date : 21/03/2017
"""
import csv

import ujson
import urllib.request
import urllib.error
import re

import datetime


class ADECalendar():
    """
    ADECalendar class allow to get ESIEE Calendar from https://bde.esiee.fr/api/calendar/activities api

    Attributes :
        all_cours : all element provided by the api
        groups_unites : list of dict {'unite' : UNITE, 'groupe': GROUPE}
    """
    all_cours = []
    groups_unites = []

    rooms_available = []

    def __init__(self):
        '''
        Get and set event to all_cours variable
        '''
        self.all_cours = self.get_json_calendar()
        try:
            with open("data/rooms.json", "r", encoding="UTF-8") as f:
                self.rooms_available = ujson.load(f)
                f.close()

        except Exception as e:
            print(e)

        print(self.rooms_available)

    @staticmethod
    def get_json_calendar():
        try:
            with open("data/calendar.json", "r", encoding="UTF-8") as f:
                events = ujson.load(f)
                f.close()
                return events

        except Exception as e:
            print(e)
            return None

    def search_unite_from_csv(self, unite_code):
        with open("data/BDE_UNITES.csv", "r") as f:
            lines = f.readlines()
            fieldsnames = ["Code.Unité", "Libellé.Unité"]
            data = csv.DictReader(lines, fieldsnames, delimiter=';')
            for row in data:
                if unite_code in self.format_unites_from_csv(row.get(fieldsnames[0])):
                    return row.get(fieldsnames[1])
            return ""

    def get_cours_of(self, day, month):
        """
        Main method
        :param day: day
        :param month: month
        :return: cours of day and month
        """
        data = self.all_cours
        all = self.get_cours_by_unites_and_groups(data, self.groups_unites)
        all = self.get_cours_by_month(all, month)
        all = self.get_cours_by_day(all, day)
        return [{"name": elt['name'], "start": elt['start'], "end": elt['end'], "rooms": self.get_rooms(elt["rooms"]),
                 "prof": self.prof_finder(elt), "unite": self.unite_name_finder(elt["name"])} for elt in
                all]

    def get_all_cours(self):
        """
        Method to get all cours
        :return: all cours
        """
        data = self.all_cours
        all = self.get_cours_by_unites_and_groups(data, self.groups_unites)
        return [{"name": elt['name'], "start": elt['start'], "end": elt['end'], "rooms": self.get_rooms(elt["rooms"]),
                 "prof": self.prof_finder(elt), "unite": self.unite_name_finder(elt["name"]),
                 "description": elt['description']} for elt in
                all]

    def get_rooms(self, rooms_list):
        rooms = ""
        for elt in rooms_list:
            rooms = rooms + elt + " "

        return rooms
    def is_group(self, description, name, groupe):
        '''

        :param description: description of event
        :param name: name of unite
        :param groupe: groupe of this unite
        :return: boolean if this group correspond to the unite event
        '''
        back = [m.start() for m in re.finditer("\n", description)]
        startLine = 1
        if (len(description[:back[1]]) > 5):
            startLine = 1

        real_group = description[back[startLine]:description.find(name[:name.find(":")]) - 1]
        if str(groupe) in real_group:
            return True
        else:
            return False

    def has_this_cours(self, cours, groups_and_unites):
        '''

        :param cours: cours row
        :param groups_and_unites: groupes and unites
        :return: boolean if this cours is in list of groups and unites
        '''
        for elt in groups_and_unites:
            if elt['unite'] is not None:
                if (elt['unite'][:elt['unite'].find("-")] in cours['name']) and (
                            elt['unite'][elt['unite'].find("-") + 1:] in cours['name']):
                    if self.is_group(cours['description'], cours['name'], elt['groupe']):
                        return True
        return False

    def get_cours_by_unites_and_groups(self, cours, groups_and_unites):
        '''

        :param cours: cours database
        :param groups_and_unites: groupes and unites to find
        :return: cours where groups and unites correspond
        '''
        return [elt for elt in cours if self.has_this_cours(elt, groups_and_unites)]

    def get_cours_by_month(self, cours, month):
        '''

        :param cours: cours database
        :param month: month which must be find
        :return: cours of the month
        '''
        return [elt for elt in cours if elt['start'][5:7] == month]

    def get_cours_by_day(self, cours, day):
        '''

        :param cours: cours database
        :param day: day which must be find
        :return: cours of the day
        '''
        return [elt for elt in cours if elt['start'][8:10] == day]

    def get_cours_by_hour(self, cours, hour):
        '''

        :param cours: cours database
        :param hour: hour which must be find
        :return: cours of the day
        '''
        return [elt for elt in cours if elt['start'][11:13] <= hour < elt['end'][11:13]]

    def set_groups_unites(self, aurion_data):
        '''

        :param aurion_data: list of groups provided by aurion_api
        :return: set groups_unites formated as list of dict {'unite' : UNITE, 'groupe': GROUPE}
        '''
        self.groups_unites = []
        for data in aurion_data:
            groups = self.groups_finder(data)
            for group in groups:
                self.groups_unites.append(
                    {"unite": self.format_unites(self.unites_finder(data)), "groupe": group})

    def groups_finder(self, data):
        '''

        :param data: row of aurion provided data
        :return: list of different possible cases of group number
        '''
        back = [m.start() for m in re.finditer("_", data[::-1])]

        #Ajoute le groupe de promo par (ex: E4FI)
        if len(back) <= 1:
            # return [data[data.find("_")+1:]]
            return ["", data[data.find("_") + 1:]]


        real_group = data[len(data) - back[0]:]

        if len(real_group) >= 2:
            return [real_group, real_group[0].upper() + real_group[1:].lower(),
                    real_group[0].lower() + real_group[1:].upper(), real_group.upper(), real_group.lower()]
        else:
            return [real_group, real_group.upper(), real_group.lower()]

    def unites_finder(self, data):
        '''

        :param data: row of aurion provided data
        :return: unite name
        '''
        back = [m.start() for m in re.finditer("_", data)]
        real_unites = data[:]  # back[0]+1
        return real_unites

    def format_unites_from_csv(self, data):
        '''
           :param data: row of BDE_UNITES.csv
           :return: unite name formatted likes unite name in calendar api
       '''
        back = [m.start() for m in re.finditer("_", data)]

        if len(back) <= 1:
            return ""

        real_group = data[back[1] + 1:]
        real_group = real_group.replace("_", "-")

        if len(back) == 2:
            real_group = real_group[:2] + "-" + real_group[2:]

        return real_group

    def format_unites(self, data):
        '''

        :param data: row of aurion provided data
        :return: unite name formatted likes unite name in calendar api
        '''
        back = [m.start() for m in re.finditer("_", data)]
        if len(back) == 3:
            real_group = data[back[1] + 1:back[2]]
            real_group = real_group[:2] + "_" + real_group[2:]
            real_group = real_group.replace("_", "-")
            return real_group
        if len(back) == 4:  # 16_E2_IGE_2102_2
            real_group = data[back[1] + 1:back[3]]
            real_group = real_group.replace("_", "-")
            return real_group

    def prof_finder(self, data):
        '''

        :param data: row of aurion provided data
        :return: professors names
        '''
        description = data["description"]
        exp = description.find("(Expor") - 1 #Gère "Exported" ou "Exporté"
        aurion = description.find("AURION") + len("AURION") + 1
        return description[aurion:exp]

    def unite_name_finder(self, data):
        '''

        :param data: row of aurion provided data
        :return: unite natural name
        '''
        return self.search_unite_from_csv(data[:data.find(":")])

    def get_free_rooms(self, hour):
        now = datetime.datetime.now()
        current_day = "0"+str(now.day) if len(str(now.day)) == 1 else str(now.day)
        current_month = "0"+str(now.month) if len(str(now.month)) == 1 else str(now.month)
        current_hour = now.hour+int(hour)
        print(current_hour)
        current_hour = "0"+str(current_hour) if len(str(current_hour)) == 1 else str(current_hour)
        data = self.all_cours
        month = self.get_cours_by_month(data, current_month)
        day = self.get_cours_by_day(month, current_day)
        hour = self.get_cours_by_hour(day, current_hour)

        rooms = []
        lists = [elt["rooms"] for elt in hour]

        for groups in lists:
            for elt in groups:
                if (len(elt)) > 4:
                    rooms.append(elt[:4])
                else:
                    rooms.append(elt)

        rooms_available_set = set(self.rooms_available)
        rooms_available_list = list(rooms_available_set.difference(set(rooms)))
        return sorted(rooms_available_list)