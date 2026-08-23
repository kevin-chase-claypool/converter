#pragma once

#include <Arduino.h>
#include <atomic>

enum ToolheadStatus : uint32_t {
  STATUS_CORE0_READY = 1u << 0,
  STATUS_CORE1_READY = 1u << 1,
  STATUS_TOOL_LIFTED = 1u << 2,
  STATUS_SAFE_FOR_HOMING = 1u << 3,
  STATUS_PRESSURE_FAULT = 1u << 4,
  STATUS_TMAG_ONLINE = 1u << 5,
  STATUS_TMAG_BASELINE_READY = 1u << 6,
  STATUS_MAG_SCAN_ACTIVE = 1u << 7,
  STATUS_MAG_DETECTED = 1u << 8,
  STATUS_MAG_FAULT = 1u << 9,
  STATUS_HX_ONLINE = 1u << 10,
};

extern std::atomic<uint32_t> g_status;
extern std::atomic<uint32_t> g_core0_heartbeat;
extern std::atomic<uint32_t> g_core1_heartbeat;
extern std::atomic<int32_t> g_mag_x_millimt;
extern std::atomic<int32_t> g_mag_y_millimt;
extern std::atomic<int32_t> g_mag_z_millimt;
extern std::atomic<int32_t> g_mag_delta_millimt;
extern std::atomic<uint32_t> g_mag_sample_count;
extern std::atomic<uint32_t> g_mag_state;

inline void setStatusFlag(ToolheadStatus flag, bool active) {
  if (active) {
    g_status.fetch_or(static_cast<uint32_t>(flag), std::memory_order_release);
  } else {
    g_status.fetch_and(~static_cast<uint32_t>(flag), std::memory_order_release);
  }
}

inline bool statusFlag(ToolheadStatus flag) {
  return (g_status.load(std::memory_order_acquire) & static_cast<uint32_t>(flag)) != 0;
}
