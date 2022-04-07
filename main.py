import json
import logging
import re
import requests
from bs4 import BeautifulSoup
from requests import HTTPError

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

logger = logging.getLogger(__name__)


scraped_data = []


def scrape_escaladas(index: int):
    try:
        base_url = "https://www.escaladas.com.br/via/id/"
        logger.info(f"Requesting for id {index}")
        response = requests.get(base_url + str(index))
        response_status = response.status_code
        if not response_status == 200:
            raise HTTPError

        logger.info(f"Got response for id {index}")
        soup = BeautifulSoup(response.content, "html.parser")

        logger.info(f"Parsing data for id {index}")
        regex = re.compile(r'[\n\r\t]')

        route_location_keys = ["state", "city", "mountain", "route_name"]
        route_location_value = regex.sub("", soup.find("h2").find("span").text.strip()).split(">")
        route_location_data = dict(zip(route_location_keys, route_location_value))

        data = {
            "model": "routes",
            "pk": index,
            "fields": {
                "rating": soup.find("div", class_="estrelas").get("title").replace("Média", "").strip().split("de")[
                    0].strip(),
                "route_grade": soup.find("div", class_="demais-dados graduacao").text.split(" "),
                **route_location_data,
            }

        }

        for element in soup.find_all("div", class_="demais-dados"):
            local_strong_element = element.find("strong", text="Local: ")
            modalidade_strong_element = element.find("strong", text="Modalidade: ")
            type_strong_element = element.find("strong", text="Tipo de via: ")
            face_strong_element = element.find("strong", text="Face: ")
            hold_type_strong_element = element.find("strong", text="Tipo de escalada predominante: ")
            length_strong_element = element.find("strong", text="Extensão: ")
            bolt_date_element = element.find("strong", text="Data da conquista: ")
            description_element = element.find("strong", text="Descrição: ")
            coordinates_element = element.find("strong", text="Coordenadas: ")
            equipment_element = element.find("strong", text="Equipamento mínimo necessário: ")
            bolters_element = element.find("strong", text="Conquistadores (em ordem alfabética): ")

            if equipment_element:
                equipments_list = []
                for list_element in element.find_all("li"):
                    equipments_list.append(list_element.text.encode("ascii", "ignore").decode())
                data["fields"]["equipments"] = f"{equipments_list}"
            if bolters_element:
                bolters_list = []
                for list_element in element.find_all("li"):
                    bolters_list.append(list_element.text.encode("ascii", "ignore").decode())
                data["fields"]["bolters"] = f"{bolters_list}"
            if local_strong_element:
                data["fields"]["local"] = local_strong_element.next_sibling.text.encode("ascii", "ignore").decode()
            if modalidade_strong_element:
                data["fields"]["modality"] = modalidade_strong_element.next_sibling.encode("ascii", "ignore").decode()
            if type_strong_element:
                data["fields"]["type"] = type_strong_element.next_sibling.encode("ascii", "ignore").decode()
            if face_strong_element:
                data["fields"]["face"] = face_strong_element.next_sibling.encode("ascii", "ignore").decode()
            if hold_type_strong_element:
                data["fields"]["hold_type"] = hold_type_strong_element.next_sibling.encode("ascii", "ignore").decode()
            if length_strong_element:
                data["fields"]["length"] = length_strong_element.next_sibling.encode("ascii", "ignore").decode()
            if bolt_date_element:
                data["fields"]["bolted_date"] = "-".join(bolt_date_element.next_sibling.split("/")[::-1])
            if description_element:
                data["fields"]["description"] = description_element.next_sibling.encode("ascii", "ignore").decode()
            if coordinates_element:
                data["fields"]["coordinates"] = coordinates_element.next_sibling.encode("ascii", "ignore").decode()

        scraped_data.append(data)
    except HTTPError:
        logger.error(f"An error occurred for id: {index}, status {response_status}")
    except KeyError as key_error:
        logger.error(f"There was an error assigning keys", key_error)
    except Exception as unknown_exception:
        logger.exception("There was an unknown exception", unknown_exception)


for id_ in range(1, 6763):
    scrape_escaladas(index=id_)


with open('data.json', '+a') as file:
    json.dump(scraped_data, file,  sort_keys=True, indent=4)

