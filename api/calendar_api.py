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
import aurion_api

class ADECalendar():
    """
    ADECalendar class allow to get ESIEE Calendar from https://bde.esiee.fr/api/calendar/activities api

    Attributes :
        all_cours : all element provided by the api
        groups_unites : list of dict {'unite' : UNITE, 'groupe': GROUPE}
    """
    all_cours = []
    groups_unites = []

    def __init__(self):
        '''
        Get and set event to all_cours variable
        '''
        self.all_cours = self.get_json_calendar()

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
        return [{"name": elt['name'], "start": elt['start'], "end": elt['end'], "rooms": elt["rooms"][0],
                 "prof": self.prof_finder(elt), "unite": self.unite_name_finder(elt["name"])} for elt in
                all]

    def get_all_cours(self):
        """
        Method to get all cours
        :return: all cours
        """
        data = self.all_cours
        all = self.get_cours_by_unites_and_groups(data, self.groups_unites)
        return [{"name": elt['name'], "start": elt['start'], "end": elt['end'], "rooms": elt["rooms"][0],
                 "prof": self.prof_finder(elt), "unite": self.unite_name_finder(elt["name"]),
                 "description": elt['description']} for elt in
                all]

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
        if "EIG_2022" in data:
            real_group = data[len(data) - back[0]:]
            return [real_group, real_group[0].upper() + real_group[1:].lower(), real_group[0].lower() + real_group[1:].upper(), real_group.upper(), real_group.lower()]
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

    def unites_finder(self, data):
        '''

        :param data: row of aurion provided data
        :return: unite name
        '''
        back = [m.start() for m in re.finditer("_", data)]
        real_unites = data[:]  # back[0]+1
        return real_unites

    def format_unites(self, data):
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
        # for unite_name in self.groups_unites:
        #    #print(unite_name["unite"]+" "+data[:data.find(":")])
        #    if unite_name["unite"] == data[:data.find(":")]:
        #        return unite_name["name"]
        return self.search_unite_from_csv(data[:data.find(":")])
