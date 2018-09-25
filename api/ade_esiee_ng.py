import json
import logging

from flask import Flask, request, render_template


from api.aurion_api import Aurion
from api.calendar_api import ADECalendar

app = Flask(__name__)

@app.route("/", methods=['GET'])
def index():
    return "Welcome to ADE-ESIEE API developed by Wall-e"

@app.route("/agenda/<mail>", methods=['GET', 'POST'])
@app.route("/api/ade-esiee/agenda/<mail>", methods=['GET', 'POST'])
def get_agenda_mail(mail):
    ade = ADECalendar()
    #ade = ADEApi()

    try:
        aurion = Aurion()
        unites_and_groups = aurion.get_unites_and_groups_from_csv(mail)
        ade.set_groups_unites(unites_and_groups)
        result = ade.get_all_cours()
        if not result:
            return "[{\"error\": \"No events\"}]"

        value = json.dumps(result)
        response = app.response_class(
            response=value,
            status=200,
            mimetype='application/json'
        )
        return response

    except Exception as e:
        return "[{\"error\": \"" + str(e) + "\"}]"


@app.route("/agenda", methods=['GET', 'POST'])
@app.route("/api/ade-esiee/agenda", methods=['GET', 'POST'])
def get_agenda():
    if request.method == 'GET':
        return render_template("index.html")

    mail = request.form['mail']
    ade = ADECalendar()
    #ade = ADEApi()

    try:
        aurion = Aurion()
        unites_and_groups = aurion.get_unites_and_groups_from_csv(mail)
        ade.set_groups_unites(unites_and_groups)

        result = ade.get_all_cours()
        if not result:
            return "[{\"error\": \"No events\"}]"

        value = json.dumps(result)
        response = app.response_class(
            response=value,
            status=200,
            mimetype='application/json'
        )
        return response

    except Exception as e:
        return "[{\"error\": \"" + str(e) + "\"}]"


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    app.run(host='0.0.0.0', port=5000)
