import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import re
import pickle


def load_table():
    page = requests.get("https://www.mirea.ru/schedule/")
    soup = BeautifulSoup(page.text, "html.parser")

    result = soup.find_all("a", {"class": "uk-link-toggle"})
    groups = {}
    for res in tqdm(result):
        if "xlsx" in res['href']:
            path = "data/" + res['href'].split("/")[-1]
            file = open(path, "wb")
            resp = requests.get(res['href'])
            file.write(resp.content)

            excel_data = pd.read_excel(path)
            data = pd.DataFrame(excel_data)
            table = data.values
            shape = table.shape

            for i in range(shape[1]):
                if not pd.isna(table[0][i]):
                    if len(re.findall(r'.+-\d{2}-\d{2}', str(table[0][i]))) == 1:
                        name = re.findall(r'.+-\d{2}-\d{2}', str(table[0][i]))[0]
                        group = []
                        for j in range(2, 74):
                            if not pd.isna(table[j][i]):
                                group.append(
                                    table[j][i] + ' ' +
                                    str(table[j][i + 1]) + ' ' +
                                    str(table[j][i + 2]) + ' ' +
                                    str(table[j][i + 3]))
                            else:
                                group.append("-")
                        groups.update({name: group})
            file.close()
    return groups


def download_table():
    with open('table.pickle', 'wb') as f:
        table = load_table()
        pickle.dump(table, f)
