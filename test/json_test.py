import json

data = '''{
  "device_driver": "led_timer",
  "generation_interval": 1,
  "coil": {
    "start_addr": 0,
    "end_addr": 9999,
    "data": [
      {
        "name": "color_r",
        "addr": 15,
        "default": 1
      },
      {
        "name": "color_g",
        "addr": 16,
        "default": 0
      },
      {
        "name": "color_b",
        "addr": 17,
        "default": 0
      }
    ]
  }
}'''

jdata = json.loads(data)

print(jdata)
print(list(jdata.get('coil').get('data')[0].values()))


print([dt for dt in jdata['coil'].get('data', [])])

l1 = [1,2,3]
l2 = [4, 5, 6]
for i in l1+l2:
    print(i)
