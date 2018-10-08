"""
Project : ade-esiee-ng
File : ade-parser
Author : DELEVACQ Wallerand
Date : 25/03/18
"""
import urllib.request
import urllib.error

import json
from xml.etree import ElementTree

import csv
import requests
from icalendar import Calendar
import time, threading
import logging



import codecs
import xml.etree.ElementTree as et


class xml2csv:
    def __init__(self, input_file, output_file, encoding='utf-8'):
        """Initialize the class with the paths to the input xml file
        and the output csv file

        Keyword arguments:
        input_file -- input xml filename
        output_file -- output csv filename
        encoding -- character encoding
        """

        self.output_buffer = []
        self.output = None

        # open the xml file for iteration
        self.context = et.iterparse(input_file, events=("start", "end"))

        # output file handle
        try:
            self.output = codecs.open(output_file, "w", encoding=encoding)
        except:
            print("Failed to open the output file")
            raise

    def convert(self, tag="item", delimiter=",", ignore=[], noheader=False,
                limit=-1, buffer_size=1000, quotes=True):

        """Convert the XML file to CSV file

            Keyword arguments:
            tag -- the record tag. eg: item
            delimiter -- csv field delimiter
            ignore -- list of tags to ignore
            limit -- maximum number of records to process
            buffer_size -- number of records to keep in buffer before writing to disk
            quotes -- insert quotes around values (e.g. "user@domain.com")

            Returns:
            number of records converted,
        """

        # get to the root
        event, root = self.context.__next__()

        items = []
        header_line = []
        field_name = ''
        processed_fields = []

        tagged = False
        started = False
        n = 0

        # iterate through the xml
        for event, elem in self.context:
            # if elem is an unignored child node of the record tag, it should be written to buffer
            should_write = elem.tag != tag and started and elem.tag not in ignore
            # and if a header is required and if there isn't one
            should_tag = not tagged and should_write and not noheader

            if event == 'start':
                if elem.tag == tag:
                    processed_fields = []
                if elem.tag == tag and not started:
                    started = True
                elif should_tag:
                    # if elem is nested inside a "parent", field name becomes parent_elem
                    field_name = '_'.join((field_name, elem.tag)) if field_name else elem.tag

            else:
                if should_write and elem.tag not in processed_fields:
                    processed_fields.append(elem.tag)
                    if should_tag:
                        header_line.append(field_name)  # add field name to csv header
                        # remove current tag from the tag name chain
                        field_name = field_name.rpartition('_' + elem.tag)[0]
                    items.append('' if elem.text is None else elem.text.strip().replace('"', r'""'))

                # end of traversing the record tag
                elif elem.tag == tag and len(items) > 0:
                    # csv header (element tag names)
                    if header_line and not tagged:
                        self.output.write(delimiter.join(header_line) + '\n')
                    tagged = True

                    # send the csv to buffer
                    if quotes:
                        self.output_buffer.append(r'"' + (r'"' + delimiter + r'"').join(items) + r'"')
                    else:
                        self.output_buffer.append((delimiter).join(items))
                    items = []
                    n += 1

                    # halt if the specified limit has been hit
                    if n == limit:
                        break

                    # flush buffer to disk
                    if len(self.output_buffer) > buffer_size:
                        self._write_buffer()

                elem.clear()  # discard element and recover memory

        self._write_buffer()  # write rest of the buffer to file
        self.output.close()

        return n

    def _write_buffer(self):
        """Write records from buffer to the output file"""

        self.output.write('\n'.join(self.output_buffer) + '\n')
        self.output_buffer = []



def download_ics_from_planif():
    url = "https://planif.esiee.fr/jsp/custom/modules/plannings/anonymous_cal.jsp?resources=147,738,739,743,744,2841,5757,746,747,748,2781,2782,3286,682,683,684,685,659,665,674,680,681,727,733,785,998,1295,2555,2743,5215,5688,731,734,735,736,740,741,742,780,782,1852,2584,4350,5321,786,787,788,789,790,2270,2275,2277,2278,2282,704,745,773,775,776,4937,728,2117,772,719,2112,183,185,196,4051,4679,2072,2074,2272,2276,2089,154,713,163,167,700,701,705,707,708,712,714,715,716,724,725,726,737,749,758,759,1057,1858,1908,2090,2108,2281,428,717,720,721,722,2265,2274,2279&projectId=4&calType=ical&nbWeeks=12"

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


def download_aurion_groups():
    url = "http://test.wallforfry.fr/BDE_MES_GROUPES.csv"

    response = requests.get(url)
    f = response.content.decode("utf-8")

    with open("data/BDE_MES_GROUPES.csv", "w") as file:
        file.writelines(f)
        file.close()
        logging.info("[ADE-PARSER] Aurion groups are up to date")

def download_aurion_groups_from_aurion():
    url = "https://webaurion.esiee.fr/ws/services/executeFavori"
    data = "<service><user>delevawa</user><password>QF2cNgL1V</password><database>prod</database><dataxml><![CDATA[<executeFavori><favori><id>18152763</id></favori><database>prod</database></executeFavori>]]></dataxml></service>"

    headers = {"Content-Type": "text/plain"}
    response = requests.post(url, data, headers=headers)

    data = response.text

    with open("data/groupes.xml", "w") as file:
        file.write(data)
        file.close()

    converter = xml2csv("data/groupes.xml", "data/BDE_MES_GROUPES.csv", encoding="utf-8")
    converter.convert(tag="row", delimiter=";")

def download_unites():
    url = "http://test.wallforfry.fr/BDE_UNITES.csv"

    response = requests.get(url)
    f = response.content.decode("utf-8")

    with open("data/BDE_UNITES.csv", "w") as file:
        file.writelines(f)
        file.close()
        logging.info("[ADE-PARSER] Unites names are up to date")

def download_files():
    url = "http://test.wallforfry.fr/rooms.json"

    response = requests.get(url)
    f = response.content.decode("utf-8")

    with open("data/rooms.json", "w") as file:
        file.writelines(f)
        file.close()
        logging.info("[ADE-PARSER] Rooms are up to date")

class ADEDownloader:
    project_id = "4"
    base_url = "https://planif.esiee.fr/jsp/webapi"
    session_id = ""

    def update_events(self):
        self._connect()
        self._set_project_id()
        self._set_events_to_xml()
        self._disconnect()

    def _connect(self):
        logging.info("[ADE-PARSER] Connecting to ade")
        url = self.base_url + "?function=connect&login=lecteur1&password="

        response = requests.get(url)

        tree = ElementTree.fromstring(response.text)

        self.session_id = tree.attrib["id"]

    def _disconnect(self):
        logging.info("[ADE-PARSER] Disconnecting from ade")
        url = self.base_url + "?function=disconnect"

        response = requests.get(url)

        return response.status_code == 200

    def _set_project_id(self):
        logging.info("[ADE-PARSER] Setting projet id to ade")
        url = self.base_url + "?sessionId=" + self.session_id + "&function=setProject&projectId=" + self.project_id

        response = requests.get(url)

        return response.status_code == 200

    def _set_events_to_xml(self):
        logging.info("[ADE-PARSER] Write xml file")
        url = self.base_url + "?sessionId=" + self.session_id + "&function=getEvents&tree=true&detail=8"

        response = requests.get(url)

        with open("data/ade.xml", mode="w") as f:
            f.write(response.text)


def main():

    use_api = False

    if not use_api:
        if download_ics_from_planif():
            ics_to_json_from_ade()
            logging.info("[ADE-PARSER] Calendar is up to date")
    else:
        ade_downloader = ADEDownloader()
        ade_downloader.update_events()

    #download_aurion_groups()
    download_aurion_groups_from_aurion()
    download_unites()
    download_files()

    threading.Timer(600, main).start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    logging.info("[ADE-PARSER] Starting..")
    main()
