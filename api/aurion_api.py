"""
Project : ade-esiee-ng
File : aurion-api
Author : DELEVACQ Wallerand
Date : 25/03/18
"""
import csv
import logging


class Aurion:
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

    def get_unites_and_groups_from_csv(self, mail):

        groups = []

        with open("data/BDE_MES_GROUPES.csv", "r") as f:
            lines = f.readlines()
            fieldsnames = ["login.Individu", "Coordonnée.Coordonnée", "Code.Groupe"]
            data = csv.DictReader(lines, fieldsnames, delimiter=';')
            for row in data:
                if mail in row.get(fieldsnames[1]):
                    groups.append(row.get(fieldsnames[2]))
                elif mail in row.get(fieldsnames[0]):
                    groups.append(row.get(fieldsnames[2]))

            if len(groups) == 0:
                logging.WARNING("[AURION-API] User " + mail + " not found in groups file")
            else:
                return groups
