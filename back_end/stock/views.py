from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .TechnologyPointer import TechnologyPointer, stock_nums, DEFAULT_STOCK_LAST_DATE
import pandas as pd
import json


def contact(request):
    return render(request, 'contact.html')


@require_http_methods(['POST'])
def detail(request):
    form = dict(request.POST)
    if request.is_ajax() or form.get('bot'):
        technology_pointer = TechnologyPointer(
            DEFAULT_STOCK_LAST_DATE, form['stock_num'][0])
        data = technology_pointer.get_all_detail(int(form['money'][0]))
        data['status'] = 1
        return HttpResponse(json.dumps(data))
    technology_pointer = TechnologyPointer(
        DEFAULT_STOCK_LAST_DATE, form['return_stock_num'][0])
    data = technology_pointer.get_all_detail(int(form['return_money'][0]))
    money = int(form['return_money'][0])
    stock_num = form['return_stock_num'][0]
    return render(request, 'detail.html', {'stock_num': stock_num, 'money': money, 'detail_data': data['details']['OBV']})


def trading(request):
    if request.method == 'POST':# and request.is_ajax():
        form = dict(request.POST)
        img_url = TechnologyPointer(
            stock_number=form['stock_num'][0]).get_CLOSE_image()
        # technology_pointer = TechnologyPointer('2019-04-12', form['stock_num'][0])
        # data = technology_pointer.get_all_detail()
        data = {'img_url': img_url, 'status': 1}
        return HttpResponse(json.dumps(data))
    return render(request, 'trading.html', {'stock_nums': stock_nums})


def withdraw(request):
    if request.method == 'POST':
        form = dict(request.POST)
        technology_pointer = TechnologyPointer(
            '2019-04-12', form['stock_num'][0])

        data = {
            'status': 1,
            'pointers': [
                {'pointer': 'DMI',
                    'value': f"{round(technology_pointer.get_DMI_profit(int(form['money'][0]))*100, 2)}%"},
                {'pointer': 'PSY',
                    'value': f"{round(technology_pointer.get_PSY_profit(int(form['money'][0]))*100, 2)}%"},
                {'pointer': 'OBV',
                    'value': f"{round(technology_pointer.get_OBV_profit(int(form['money'][0]))*100, 2)}%"},
                {'pointer': 'AR',
                    'value': f"{round(technology_pointer.get_AR_profit(int(form['money'][0]))*100, 2)}%"},
                {'pointer': 'BR',
                    'value': f"{round(technology_pointer.get_BR_profit(int(form['money'][0]))*100, 2)}%"},
                {'pointer': 'KD',
                    'value': f"{round(technology_pointer.get_KD_profit(int(form['money'][0]))*100, 2)}%"},
                {'pointer': 'RSI',
                    'value': f"{round(technology_pointer.get_RSI_profit(int(form['money'][0]))*100, 2)}%"},
                {'pointer': 'MA', 'value': f"{round(technology_pointer.get_MA_profit(int(form['money'][0]))*100, 2)}%"}]
        }
        return HttpResponse(json.dumps(data))
        # return render(request, 'resulr.html', {'data': data})
    return render(request, 'withdraw.html', {'stock_nums': stock_nums})


def stockPoint(request):
    if request.method == 'POST':# and request.is_ajax():
        form = dict(request.POST)
        technology_pointer = TechnologyPointer(
            stock_number=form['stock_num'][0])
        img_url = ''
        if form['tptype'][0] == 'OBV':
            img_url = technology_pointer.get_OBV_image()
        elif form['tptype'][0] == 'DMI':
            img_url = technology_pointer.get_DMI_image()
        elif form['tptype'][0] == 'KD':
            img_url = technology_pointer.get_KD_image()
        elif form['tptype'][0] == 'AR':
            img_url = technology_pointer.get_AR_image()
        elif form['tptype'][0] == 'BR':
            img_url = technology_pointer.get_BR_image()
        elif form['tptype'][0] == 'RSI':
            img_url = technology_pointer.get_RSI_image()
        elif form['tptype'][0] == 'MA':
            img_url = technology_pointer.get_MA_image()
        elif form['tptype'][0] == 'PSY':
            img_url = technology_pointer.get_PSY_image()

        data = {'img_url': img_url, 'status': 1}
        return HttpResponse(json.dumps(data))

    return render(request, 'stockPoint.html', {'stock_nums': stock_nums})


def home(request):
    # print(request.UserHostAddress)
    return render(request, 'index.html')

def remote_ip_address(request):
    print(dict(request.GET)['ip'])
    return HttpResponse(json.dumps({"ok": 200}))
