import board

class Settings:
    led_max_brightness = 0.1 # A decimal between 0 and 1 (e.g. 0.25 = 25%)
    mouth_led_count = 8 # Number of LEDs in the mouth
    eye_led_count = 7 # Number of LEDs in each eye
    port = 5000 # This must match the value in Zach's box
    led_pin = board.D37 # Pin number the LEDs are plugged into
    servo_pin = board.D35 # Pin number the servo is plugged into
    ssid = ""
    ssid_password = ""
    ssid_channel = 1
    espnow_zachbox_mac = b''

    total_leds = 30

