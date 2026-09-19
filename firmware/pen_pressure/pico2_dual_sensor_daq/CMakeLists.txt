cmake_minimum_required(VERSION 3.13)

# Set PICO_SDK_PATH to a Pico SDK checkout before configuring this project.
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(pico2_dual_sensor_daq C CXX ASM)
pico_sdk_init()

add_executable(pico2_dual_sensor_daq
    pico2_dual_sensor_daq.cpp
)

target_link_libraries(pico2_dual_sensor_daq
    pico_stdlib
    hardware_adc
    hardware_gpio
    hardware_timer
)

# This fixture is deliberately USB-CDC only. It must not use the Pico UART.
pico_enable_stdio_usb(pico2_dual_sensor_daq 1)
pico_enable_stdio_uart(pico2_dual_sensor_daq 0)
pico_add_extra_outputs(pico2_dual_sensor_daq)
