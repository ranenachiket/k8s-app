import requests

def test_order_count(count):
    uri = f'local.kong.com/orders/count/{count}'
    resp = requests.get(uri, verify=False)
    return resp.status_code, resp.json()

