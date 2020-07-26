#!/usr/bin/python3

import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime

import settings

# ------------------- settings --------------------

# format file:
# action| company | quantity | price | date
file_name = settings.data_file_name

login = settings.login_smartlab
portfolio_id = settings.portfolio_id
security_ls_key = settings.security_ls_key
headers = {'cookie': settings.cookie }

# -------------------------------------------------

class Action:
    def __init__(self, action, company, quantity, price, date = None):
        self.action = action
        self.company = company
        self.quantity = quantity
        self.price = price
        self.date = date

    def __str__(self):
        s = "self.action: " + str(self.action)
        s += "self.company: " + str(self.company)
        s += "\t| self.quantity: " + str(self.quantity)
        s += "\t| self.price: " + str(self.price)
        s += "\t| self.date: " + str(self.date)
        return s


class SymbolResponse():
    def __init__(self, symbol, sec_type, last_price):
        self.symbol = symbol
        self.sec_type = sec_type
        self.last_price = last_price

    def __str__(self):
        s = "self.symbol: " + str(self.symbol)
        s += "\t| self.sec_type: " + str(self.sec_type)
        s += "\t| self.last_price: " + str(self.last_price)
        return s


class ExistCompanyInPortfel():
    def __init__(self, symbol, list_id, investment_id):
        self.symbol = symbol
        self.list_id = list_id
        self.investment_id = investment_id

    def __str__(self):
        s = "self.symbol: " + str(self.symbol)
        s += "\t| self.list_id: " + str(self.list_id)
        s += "\t| self.investment_id: " + str(self.investment_id)
        return s


# -------------------------------------------------


def get_symbol(company):
    global headers
    get_symbol_url = 'https://smart-lab.ru/q/portfolio-autocomplete-ajax/'

    data = {
        'json' : '1',
        'value' : company
    }

    response = requests.post(get_symbol_url, headers=headers, data = data)
    json_resp = json.loads(response.text)

    if len(json_resp) == 0 :
        print("symbol компании '%s' не найден!" % (company))
        return None
    else:
        # TODO: возможно хорошо сделать выбор компании, если найдено несколько
        symbol = json_resp[0]['symbol']
        sec_type = json_resp[0]['sec_type']
        last_price = json_resp[0]['last']
        
        return SymbolResponse(symbol, sec_type, last_price)


def send_action(type, company, quantity, price, date = None):
    global portfolio_id, security_ls_key, headers
    send_act_url = 'https://smart-lab.ru/q/portfolio-ajax/'

    exist_companies_in_portfel = None
    if date is not None:
        exist_companies_in_portfel = get_portfel()
    symbol_response = get_symbol(company)

    if symbol_response is None:
        print("get_symbol вернул None. Компания: %s" % (company))
        return

    data = {
        'portfolio_id' : portfolio_id,
        'security_ls_key' : security_ls_key,

        'action' : type,
        'quantity' : quantity,
        'price' : price,
        'symbol' : symbol_response.symbol,
        'sec_type' : symbol_response.sec_type
    }

    send_response = requests.post(send_act_url, headers=headers, data = data)

    json_resp = json.loads(send_response.text)
    if json_resp['bStateError'] == True:
        print("Ошибка! Msg: %s" % (json_resp['sMsg']))
    else:
        print(json_resp['sMsg'])

    if date is not None and exist_companies_in_portfel is not None:
        new_portfel = get_portfel()
        new_rows = []
        for x in new_portfel:
            if x.list_id not in [l.list_id for l in exist_companies_in_portfel]:
                new_rows.append(x)

        if len(new_rows) >= 1:
            edit_action(new_rows[0], symbol_response, type, quantity, price, date)


def edit_action(created_row, symbol, type, quantity, price, date):
    global portfolio_id, security_ls_key, headers
    send_act_url = 'https://smart-lab.ru/q/portfolio-ajax/'

    data = {
        'action' : 'set_investment',
        'portfolio_id' : portfolio_id,
        'security_ls_key' : security_ls_key,
        'symbol' : symbol.symbol,
        'sec_type' : symbol.sec_type,

        'type' : type,
        'date' : date.strftime('%Y-%m-%d %H:%M:%S'),
        'quantity' : quantity,
        'price' : price,
        'investment_id' : created_row.list_id
    }

    requests.post(send_act_url, headers=headers, data=data)


def get_portfel():
    global login, portfolio_id, headers, exist_companies_in_portfel
    get_portfel_url = 'https://smart-lab.ru/q/portfolio/%s/%s/more/' % (login, portfolio_id)

    exist_companies_in_portfel = []

    response = requests.get(get_portfel_url, headers=headers)

    soup = BeautifulSoup(response.text, 'lxml')
 
    table = soup.find('table', class_='simple-little-table trades-table')

    if table is None:
        return []

    rows = table.find_all('tr')
    for row in rows:
        span_edit = row.find_all('span', class_='portfolio_action', type='edit')
        if len(span_edit) == 1:
            symbol = span_edit[0]['symbol']
            investment_id = span_edit[0]['investment-id']
            list_id = span_edit[0]['list-id']
            exist_companies_in_portfel.append(ExistCompanyInPortfel(symbol, investment_id, list_id))
    
    # for x in exist_companies_in_portfel:
    #     print(x)

    return exist_companies_in_portfel

def buy(company, quantity, price, date = None):
    send_action('buy', company, quantity, price, date)

def sell(company, quantity, price, date = None):
    send_action('sell', company, quantity, price, date)


# -------------------------------------------------

def read_file():
    global file_name
    r = []
    content = []

    with open(file_name) as f:
        content = f.readlines()
    
    for line in content:
        if line.startswith('#') == True or not line or line.isspace():
            continue
        s = list(map(lambda x: x.strip(), line.split('|')))
        
        action = s[0]
        company = s[1]
        quantity = s[2]
        price = s[3]
        date = None
        if len(s) == 5:
            date = datetime.strptime(s[4], '%Y-%m-%d %H:%M:%S')

        r.append(Action(action, company, quantity, price, date))

    return r


data = read_file()

for x in data:
    if x.action == 'buy':
        buy(x.company, x.quantity, x.price, x.date)
    if x.action == 'sell':
        sell(x.company, x.quantity, x.price, x.date)
