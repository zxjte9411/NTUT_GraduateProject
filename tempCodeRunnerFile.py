a = requests.Session()

response = a.get("http://zxjte9411.ddns.net:8000/trading")

soup = bs4.BeautifulSoup(response.text, 'html.parser')

csrfmiddlewaretoken = soup.find("input",{"name":"csrfmiddlewaretoken"})["value"] 

result = a.post("http://zxjte9411.ddns.net:8000/trading", data={"stock_num":"2302", "csrfmiddlewaretoken":csrfmiddlewaretoken})

xxx = json.loads(result.text)