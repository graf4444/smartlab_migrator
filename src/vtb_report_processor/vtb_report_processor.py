import xlrd
import datetime

# ------------------- settings --------------------

input_file_name = 'report_name.xls'
output_file_name = 'output_file_name.txt'

# -------------------------------------------------


class ActionRow:
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


def processor():
    global input_file_name, output_file_name 

    l = []

    wb = xlrd.open_workbook(input_file_name)
    sheet = wb.sheet_by_index(0)

    start_row = -1
    end_row = -1
    for row_num in range(sheet.nrows):
        row_value = sheet.row_values(row_num)
        if row_value[1] == 'Завершенные в отчетном периоде сделки с ценными бумагами (обязательства прекращены)':
            start_row = row_num + 2
        if start_row != -1 and row_value[1] == '':
            end_row = row_num - 1
            break

    for row_num in range(start_row, end_row):
        row_value = sheet.row_values(row_num)

        action = ''
        if row_value[5].lower() == 'Покупка'.lower():
            action = 'buy'
        elif row_value[5].lower() == 'Продажа'.lower():
            action = 'sell'
        else:
            print('На строке %s не понятное действие "%s"' % (row_num, row_value[26]))

        company = row_value[1].split(',')[0]

        quantity = int(row_value[9])
        if quantity < 0:
            quantity *= -1
        
        # print(row_num, row_value)
        price = float(row_value[16])

        date_val = sheet.cell_value(rowx=row_num, colx=3)
        date = datetime.datetime(*xlrd.xldate_as_tuple(date_val, wb.datemode))

        # print(action, company, quantity, price, date)

        l.append(ActionRow(action, company, quantity, price, date))

    with open(output_file_name, 'w') as f:
        for x in l:
            print("%s | %s | %s | %s | %s" % (x.action, x.company, x.quantity, x.price, x.date.strftime('%Y-%m-%d %H:%M:%S')), file=f)


processor()