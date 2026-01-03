from constants import Const
import mouth_styles
import adafruit_logging as logging

class Settings:
    
    eye_colors = [
        (0, 255, 0, 0), # (Red, Green, Blue, White) each 0-255
        (255, 0, 0, 0), # (Red, Green, Blue, White) each 0-255
        (151, 3, 210, 0), # (Red, Green, Blue, White) each 0-255
        (30, 212, 255, 0), # (Red, Green, Blue, White) each 0-255
        (255, 255, 0, 0), # (Red, Green, Blue, White) each 0-255
        (0, 255, 255, 0), # (Red, Green, Blue, White) each 0-255
        (0, 0, 0, 255), # (Red, Green, Blue, White) each 0-255
        (0,0,0,0), # Until we have a sleep mode for the head, this will serve as disabling the lights.
    ]
    
    mouth_colors = [
        (0, 255, 0, 0), # (Red, Green, Blue, White) each 0-255
        (151, 3, 210, 0), # (Red, Green, Blue, White) each 0-255
        (30, 212, 255, 0), # (Red, Green, Blue, White) each 0-255
        (255, 255, 0, 0), # (Red, Green, Blue, White) each 0-255
        (0, 255, 255, 0), # (Red, Green, Blue, White) each 0-255
        (0, 0, 0, 255), # (Red, Green, Blue, White) each 0-255
        (0,0,0,0), # Until we have a sleep mode for the head, this will serve as disabling the lights.
    ]
    
    mouth_style = mouth_styles.Kitt

    
    # ---------------------------------------
    # Eye Blink Settings
    # ---------------------------------------
    eye_blink_auto = True # Default when turned on. True = eyes will randomly blink. 
    eye_blink_min_secs = 3 # The shortest amount of time (in seconds) between blinks
    eye_blink_max_secs = 10 # The longest amount of time (in seconds) between blinks
    
    # ---------------------------------------
    # Servo Settings
    # ---------------------------------------
    # See https://easings.net/ for some illustartions of the different easings. Note the names are slightly different. Use the list below.
    # 
    # Available easings:
    #   LinearInOut
    #   QuadEaseInOut, QuadEaseIn, QuadEaseOut
    #   CubicEaseIn, CubicEaseOut, CubicEaseInOut
    #   QuarticEaseIn, QuarticEaseOut, QuarticEaseInOut
    #   QuinticEaseIn, QuinticEaseOut, QuinticEaseInOut
    #   SineEaseIn, SineEaseOut, SineEaseInOut
    #   CircularEaseIn, CircularEaseOut, CircularEaseInOut
    #   ExponentialEaseIn, ExponentialEaseOut, ExponentialEaseInOut
    #   ElasticEaseIn, ElasticEaseOut, ElasticEaseInOut
    #   BackEaseIn, BackEaseOut, BackEaseInOut
    #   BounceEaseIn, BounceEaseOut, BounceEaseInOut
    servo_easing = "QuadEaseOut"
    servo_steps = 50
    servo_travel_secs = 0.5
    
    # ---------------------------------------
    # Mic Level Defaults
    # ---------------------------------------
    mic_min = 50 # Defauilt mic level at which the mouth will start responding (0-255)
    mic_max = 255 # Default mic level at which the mouth will max out (0-255)

    # ---------------------------------------
    # Wii Controller Mappings
    # ---------------------------------------
    # Available Buttons: "A", "B", "START", "SELECT", "X", "Y", "HOME", "ZL", "ZR", "L", "R", "UP", "DOWN", "LEFT", "RIGHT"
    # Use format: ([BUTTON], [COMBO BUTTON]) For example, pressing B while holding Select type ("B", "SELECT") or For just "B" type ("B", None)
    
    controller_blink = ("B", None) # Just B button
    controller_ohnono = ("A", None)
    controller_eyecolor_next = ("R", None)
    controller_eyecolor_prev = ("L", None)
    controller_mouthcolor_next = ("ZR", None)
    controller_mouthcolor_prev = ("ZL", None)
    controller_togglescreen = ("HOME", None)
    controller_mic_min_up = ("UP", "START") # Hold start and press Up on the d-pad
    controller_mic_min_down = ("DOWN", "START")
    controller_mic_max_up = ("UP", "SELECT")
    controller_mic_max_down = ("DOWN", "SELECT")
    controller_blink_auto_toggle = ("B", "SELECT")
    controller_servo_deadzone = 3  # Stick values within this distance of center are treated as center
    controller_servo_max_step = 20  # Max degrees the servo target can change per update
    controller_gaze_deadzone = 3  # Deadzone radius for right stick gaze input
    controller_joy_min = 2  # Raw joystick min (calibrate to your controller)
    controller_joy_max = 28  # Raw joystick max (calibrate to your controller)

    # ---------------------------------------
    # Logging
    # ---------------------------------------
    log_level = logging.INFO

    # ---------------------------------------
    # Debug
    # ---------------------------------------
    eye_debug_colors_on_boot = False

    # ---------------------------------------
    # Eye Gaze Tuning
    # ---------------------------------------
    eye_gaze_center_deadzone = 0.1
    eye_gaze_pupil_radius = 1
    eye_gaze_pupil_range = 1.4
    eye_gaze_pupil_edge_softness = 0.2
    controller_servo_deadzone = 3  # Stick values within this distance of center are treated as center
    

# ---------------------------------------
# Stuff you shouldn't need to touch
# ---------------------------------------
    # ssid = ""
    # ssid_password = ""
    # ssid_channel = 1
    # head_ip_address = "192.168.4.1"
    # port = 5000 # This must match the value in Zach's box
    espnow_cylon_mac = b''

    mouth_led_per_row = 8
    mouth_row_count = 2
    led_count_left_eye = 7
    led_count_right_eye = 7
    
    led_connection_order = [
        Const.MOUTH,
        Const.RIGHT_EYE,
        Const.LEFT_EYE
    ]
