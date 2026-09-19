// Pico 2 / RP2350 dual-sensor calibration DAQ.
//
// This is fixture firmware, not plotter-control firmware.  It never sends
// commands to the Pro Micro and never drives a motor.  It timestamps raw data
// with the Pico monotonic microsecond clock and writes it to USB CDC.
//
// Wiring is authoritative in docs/hardware/WIRING_TABLE.md.

#include <cstdint>
#include <cstdio>
#include <cstring>

#include "hardware/adc.h"
#include "hardware/gpio.h"
#include "pico/stdio_usb.h"
#include "pico/stdlib.h"

namespace {

constexpr uint kCsSckPin = 2;
constexpr uint kCsDoutPin = 3;
constexpr uint kReferenceAdcGpio = 26;  // ADC0
constexpr uint kMotionActivePin = 14;
constexpr uint kRunSwitchPin = 15;

constexpr uint32_t kCsReadyTimeoutUs = 30'000;
constexpr uint32_t kBitDelayUs = 1;  // Datasheet t5 minimum is 455 ns.
constexpr uint8_t kCs1238Configuration = 0x6c;
// 0x6c = external reference, 640 SPS, gain 128, channel A.

enum class RunSource { kNone, kSwitch, kUsb };

struct MarkerEvent {
    uint64_t time_us;
    bool active;
};

constexpr uint kMarkerEventCapacity = 64;
volatile MarkerEvent g_marker_events[kMarkerEventCapacity];
volatile uint g_marker_write = 0;
volatile uint g_marker_read = 0;
volatile uint32_t g_marker_overflow_count = 0;
volatile bool g_capture_active = false;
uint64_t g_run_start_us = 0;
uint64_t g_sample_count = 0;
RunSource g_run_source = RunSource::kNone;

inline void bit_delay() {
    busy_wait_us_32(kBitDelayUs);
}

inline void clock_pulse() {
    gpio_put(kCsSckPin, 1);
    bit_delay();
    gpio_put(kCsSckPin, 0);
    bit_delay();
}

uint32_t read_bits(uint8_t bit_count) {
    uint32_t value = 0;
    for (uint8_t i = 0; i < bit_count; ++i) {
        gpio_put(kCsSckPin, 1);
        bit_delay();
        value = (value << 1u) | (gpio_get(kCsDoutPin) ? 1u : 0u);
        gpio_put(kCsSckPin, 0);
        bit_delay();
    }
    return value;
}

void write_bits(uint8_t value, uint8_t bit_count) {
    for (int bit = bit_count - 1; bit >= 0; --bit) {
        gpio_put(kCsDoutPin, (value >> bit) & 0x01u);
        clock_pulse();
    }
}

void dout_input() {
    gpio_set_dir(kCsDoutPin, GPIO_IN);
    gpio_pull_up(kCsDoutPin);
}

void dout_output_high() {
    gpio_put(kCsDoutPin, 1);  // Prevent a brief low when changing direction.
    gpio_set_dir(kCsDoutPin, GPIO_OUT);
}

bool wait_for_cs_ready() {
    const uint64_t start_us = time_us_64();
    while (gpio_get(kCsDoutPin)) {
        if (time_us_64() - start_us >= kCsReadyTimeoutUs) {
            return false;
        }
        tight_loop_contents();
    }
    return true;
}

bool wait_for_cs_not_ready() {
    const uint64_t start_us = time_us_64();
    while (!gpio_get(kCsDoutPin)) {
        if (time_us_64() - start_us >= kCsReadyTimeoutUs) {
            return false;
        }
        tight_loop_contents();
    }
    return true;
}

// Completes the 27-clock data transaction and sign-extends the 24-bit code.
int32_t read_cs1238_conversion() {
    const uint32_t value = read_bits(24);
    clock_pulse();
    clock_pulse();
    clock_pulse();
    return (value & 0x00800000u) ? static_cast<int32_t>(value | 0xff000000u)
                                 : static_cast<int32_t>(value);
}

bool read_cs1238_configuration(uint8_t* configuration) {
    if (!wait_for_cs_ready()) {
        return false;
    }

    // CS1238 configuration-read transaction. The update bit is the first bit
    // after the discarded conversion code; a successful write must set it.
    for (uint8_t i = 0; i < 24; ++i) {
        clock_pulse();
    }
    const bool update = (read_bits(3) & 0x04u) != 0;
    clock_pulse();
    clock_pulse();
    dout_output_high();
    write_bits(0x56, 7);  // Read configuration register command.
    dout_input();
    clock_pulse();
    *configuration = static_cast<uint8_t>(read_bits(8));
    clock_pulse();
    return update;
}

bool configure_cs1238() {
    if (!wait_for_cs_ready()) {
        return false;
    }

    // CS1238 configuration-write transaction, derived from Chipsea's serial
    // timing table. The first conversion is intentionally discarded.
    (void)read_bits(24);
    clock_pulse();
    clock_pulse();
    clock_pulse();
    clock_pulse();
    clock_pulse();
    dout_output_high();
    write_bits(0x65, 7);  // Write configuration register command.
    clock_pulse();
    write_bits(kCs1238Configuration, 8);
    dout_input();
    clock_pulse();

    // The device first releases DOUT while it starts the next conversion and
    // later drives it low again at data-ready. Verify the written register
    // before allowing a run to begin.
    if (!wait_for_cs_not_ready() || !wait_for_cs_ready()) {
        return false;
    }
    uint8_t configuration = 0;
    return read_cs1238_configuration(&configuration) &&
           configuration == kCs1238Configuration;
}

const char* source_name(RunSource source) {
    return source == RunSource::kSwitch ? "switch" : "usb";
}

void marker_irq(uint gpio, uint32_t events) {
    if (gpio != kMotionActivePin || !g_capture_active ||
        !(events & (GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL))) {
        return;
    }

    const uint next = (g_marker_write + 1u) % kMarkerEventCapacity;
    if (next == g_marker_read) {
        ++g_marker_overflow_count;
        return;
    }
    g_marker_events[g_marker_write].time_us = time_us_64();
    g_marker_events[g_marker_write].active = gpio_get(kMotionActivePin);
    g_marker_write = next;
}

void emit_marker_events() {
    while (g_marker_read != g_marker_write) {
        const uint64_t event_time_us = g_marker_events[g_marker_read].time_us;
        const bool event_active = g_marker_events[g_marker_read].active;
        g_marker_read = (g_marker_read + 1u) % kMarkerEventCapacity;
        const uint64_t relative_time = event_time_us - g_run_start_us;
        std::printf("EVENT,%llu,%s,%u\n", static_cast<unsigned long long>(relative_time),
                    event_active ? "motion_start" : "motion_end", event_active ? 1u : 0u);
    }
}

void stop_capture(const char* reason) {
    if (!g_capture_active) {
        return;
    }
    g_capture_active = false;
    emit_marker_events();
    std::printf("TEST_STOP,reason=%s,samples=%llu,marker_overflow=%lu\n", reason,
                static_cast<unsigned long long>(g_sample_count),
                static_cast<unsigned long>(g_marker_overflow_count));
    std::fflush(stdout);
    g_run_source = RunSource::kNone;
}

void start_capture(RunSource source) {
    if (g_capture_active) {
        return;
    }
    if (!stdio_usb_connected()) {
        std::printf("START_REJECTED,reason=usb_not_connected\n");
        return;
    }

    g_marker_read = 0;
    g_marker_write = 0;
    g_marker_overflow_count = 0;
    g_sample_count = 0;
    g_run_start_us = time_us_64();
    g_run_source = source;
    g_capture_active = true;

    std::printf("TEST_START,source=%s,monotonic_origin_us=%llu\n", source_name(source),
                static_cast<unsigned long long>(g_run_start_us));
    std::printf("SAMPLES_HEADER,toolhead_time_us,toolhead_cs1238_raw,reference_time_us,reference_adc_raw\n");
    std::printf("EVENTS_HEADER,pico_time_us,event,marker_level\n");
    std::fflush(stdout);
}

void emit_sample() {
    if (!wait_for_cs_ready()) {
        stop_capture("cs1238_ready_timeout");
        return;
    }

    const int32_t cs_raw = read_cs1238_conversion();
    const uint64_t cs_time_us = time_us_64() - g_run_start_us;
    const uint16_t reference_raw = adc_read();
    const uint64_t reference_time_us = time_us_64() - g_run_start_us;
    std::printf("SAMPLE,%llu,%ld,%llu,%u\n", static_cast<unsigned long long>(cs_time_us),
                static_cast<long>(cs_raw), static_cast<unsigned long long>(reference_time_us),
                static_cast<unsigned>(reference_raw));
    ++g_sample_count;
    emit_marker_events();
}

void handle_usb_command() {
    static char command[24];
    static uint length = 0;
    const int character = getchar_timeout_us(0);
    if (character == PICO_ERROR_TIMEOUT) {
        return;
    }
    if (character == '\r') {
        return;
    }
    if (character == '\n') {
        command[length] = '\0';
        if (std::strcmp(command, "START") == 0) {
            // The physical switch remains the DAQ enable: GP15 must be low.
            if (gpio_get(kRunSwitchPin)) {
                std::printf("START_REJECTED,reason=daq_switch_off\n");
            } else {
                start_capture(RunSource::kUsb);
            }
        } else if (std::strcmp(command, "STOP") == 0) {
            stop_capture("usb_command");
        } else if (std::strcmp(command, "STATUS") == 0) {
            std::printf("STATUS,capture=%u,switch=%u,samples=%llu\n", g_capture_active ? 1u : 0u,
                        gpio_get(kRunSwitchPin) ? 0u : 1u,
                        static_cast<unsigned long long>(g_sample_count));
        } else if (length != 0) {
            std::printf("COMMAND_ERROR,expected=START|STOP|STATUS\n");
        }
        length = 0;
        return;
    }
    if (length + 1u < sizeof(command)) {
        command[length++] = static_cast<char>(character);
    } else {
        length = 0;
    }
}

}  // namespace

int main() {
    stdio_init_all();

    gpio_init(kCsSckPin);
    gpio_set_dir(kCsSckPin, GPIO_OUT);
    gpio_put(kCsSckPin, 0);  // CS1238 power-up state.
    gpio_init(kCsDoutPin);
    dout_input();

    adc_init();
    adc_gpio_init(kReferenceAdcGpio);
    adc_select_input(0);

    gpio_init(kMotionActivePin);
    gpio_set_dir(kMotionActivePin, GPIO_IN);
    gpio_pull_down(kMotionActivePin);
    gpio_set_irq_enabled_with_callback(kMotionActivePin,
                                       GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL,
                                       true, &marker_irq);

    gpio_init(kRunSwitchPin);
    gpio_set_dir(kRunSwitchPin, GPIO_IN);
    gpio_pull_up(kRunSwitchPin);  // Closed switch = DAQ enabled / LOW.

    sleep_ms(50);
    const bool configured = configure_cs1238();
    std::printf("READY,pico2_dual_sensor_daq,cs1238_config=%s,rate_sps=640\n",
                configured ? "ok" : "failed");
    std::fflush(stdout);

    if (!configured) {
        while (true) {
            handle_usb_command();
            tight_loop_contents();
        }
    }

    // Treat an already-closed switch after boot/configuration as a request to
    // start. This avoids requiring the operator to cycle a correctly ON switch.
    bool previous_switch_on = false;
    while (true) {
        handle_usb_command();

        const bool switch_on = !gpio_get(kRunSwitchPin);
        if (switch_on && !previous_switch_on && !g_capture_active) {
            start_capture(RunSource::kSwitch);
        } else if (!switch_on && previous_switch_on && g_capture_active) {
            stop_capture("daq_switch_off");
        }
        previous_switch_on = switch_on;

        if (g_capture_active) {
            emit_sample();
        } else {
            tight_loop_contents();
        }
    }
}
