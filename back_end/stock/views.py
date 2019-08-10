from django.shortcuts import render

# Create your views here.

from django.shortcuts import render

from .TechnologyPointer import TechnologyPointer, stock_nums
import pandas as pd

def contact(request):
    return render(request, 'contact.html')

def trading(request):
    return render(request, 'trading.html')

def withdraw(request):
    return render(request, 'withdraw.html')

def stockPoint(request):
    return render(request, 'stockPoint.html')

def home(request):
    if request.method == 'POST':
        form = dict(request.POST)
        technology_pointer = TechnologyPointer(stock_number=form['stock_num'][0])

        data = {
            'DMI': f"{round(technology_pointer.get_DMI_profit(int(form['money'][0]))*100, 2)}%",
            'PSY': f"{round(technology_pointer.get_PSY_profit(int(form['money'][0]))*100, 2)}%",
            'OBV': f"{round(technology_pointer.get_OBV_profit(int(form['money'][0]))*100, 2)}%",
            'AR': f"{round(technology_pointer.get_AR_profit(int(form['money'][0]))*100, 2)}%",
            'BR': f"{round(technology_pointer.get_BR_profit(int(form['money'][0]))*100, 2)}%",
            'KD': f"{round(technology_pointer.get_KD_profit(int(form['money'][0]))*100, 2)}%",
            'RSI': f"{round(technology_pointer.get_RSI_profit(int(form['money'][0]))*100, 2)}%",
            'MA': f"{round(technology_pointer.get_MA_profit(int(form['money'][0]))*100, 2)}%"
        }

        return render(request, 'resulr.html', {'data': data})
    return render(request, 'home.html', {'stock_nums': stock_nums})

