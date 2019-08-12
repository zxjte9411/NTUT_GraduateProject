from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

from django.shortcuts import render

from .TechnologyPointer import TechnologyPointer, stock_nums
import pandas as pd
import json


def contact(request):
    return render(request, 'contact.html')


def trading(request):
    return render(request, 'trading.html')


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
    return render(request, 'stockPoint.html')
