echo '1111'
slave_device --port=40000 -u 1 --device-info=led_timer &
echo '2222'
slave_device --port=40001 -u 1 --device-info=led_timer &
