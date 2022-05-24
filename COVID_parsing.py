import requests
from bs4 import BeautifulSoup
import PIL.Image as Image
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.ticker import FormatStrFormatter
import re


def parse_tr(tr):
    th = tr.find_next('th')
    td = tr.find_all('td')
    res = [th.string, int(td[0].text.split(' ')[1]), int(td[1].text.split(' ')[1]), int(td[2].text.split(' ')[1])]
    return res


def draw_stat_rus_ten():
    page = requests.get("https://coronavirusstat.ru/country/russia/")
    soup = BeautifulSoup(page.text, "html.parser")
    table = soup.find("table", attrs={'class': "table table-bordered small"})
    table_body = table.find('tbody').find_all('tr')
    res = [parse_tr(x) for x in table_body]
    res = res[:10]

    x = []
    y = {'Активных': [], 'Вылечено': [], 'Умерло': []}
    for i in res:
        x.append(i[0])
        y["Активных"].append(i[1])
        y["Вылечено"].append(i[2])
        y["Умерло"].append(i[3])

    fig, ax = plt.subplots()

    ax.stackplot(x, y.values(),
                 labels=y.keys(), alpha=0.8)
    fig.autofmt_xdate(rotation=20)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.0f}'.format(x)))
    ax.legend(loc='upper left')
    fig.savefig('plt.png')
    return 'plt.png'


def get_today():
    page = requests.get("https://coronavirusstat.ru/#world")
    soup = BeautifulSoup(page.text, "html.parser")
    rus = soup.find("div", attrs={'class': "row border border-bottom-0 c_search2_row", 'id': "c_russia"})
    big = rus.find_all("span", attrs={'class': "dline"})
    all = rus.find_all("div", attrs={'class': "h6 m-0"})[-1]
    small = rus.find_all("span", attrs={'title': "За 1 день"})

    data = soup.find("strong").text
    buf = all.text.replace("\n", "")
    buf = buf.replace("\t", " ")
    buf = buf.split(" ")[4]
    msg = f"По состоянию {data}\n" \
          f"Случаев {buf} ({small[3].text} за cегодня) \n" \
          f"Активных {big[0].text} ({small[0].text} за cегодня) \n" \
          f"Вылечено {big[1].text} ({small[1].text} за сегодня) \n" \
          f"Умерло {big[2].text} ({small[2].text} за cегодня) \n"
    return msg


def get_area(area):
    page = requests.get("https://coronavirusstat.ru/country/russia/")
    soup = BeautifulSoup(page.text, "html.parser")
    rus = soup.find(area)
    big = rus.find_all("a", text=area)
    all = rus.find_all("div", attrs={'class': "h6 m-0"})[-1]
    small = rus.find_all("span", attrs={'title': "За 1 день"})

    data = soup.find("strong").text
    buf = all.text.replace("\n", "")
    buf = buf.replace("\t", " ")
    buf = buf.split(" ")[4]
    msg = f"По состоянию {data}\n" \
          f"Случаев {buf} ({small[3].text} за cегодня) \n" \
          f"Активных {big[0].text} ({small[0].text} за cегодня) \n" \
          f"Вылечено {big[1].text} ({small[1].text} за сегодня) \n" \
          f"Умерло {big[2].text} ({small[2].text} за cегодня) \n"
    return msg


if __name__ == '__main__':
    get_area("Нижегородская обл.")
