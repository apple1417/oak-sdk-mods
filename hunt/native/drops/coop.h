#ifndef HUNT_NATIVE_DROPS_COOP_H
#define HUNT_NATIVE_DROPS_COOP_H

#include "pyunrealsdk/pch.h"

namespace unrealsdk::unreal {

class UObject;

}

namespace hunt::drops::coop {

/**
 * @brief Enables the coop transmission hooks.
 */
void enable(void);

/**
 * @brief Disables the coop transmission hooks.
 */
void disable(void);

/**
 * @brief Transmits a valid pickup to clients.
 *
 * @param pickup The pickup to transmit.
 */
void transmit_valid_pickup_to_clients(unrealsdk::unreal::UObject* pickup);

/**
 * @brief On world change, resets any relevant state.
 */
void reset_state_on_world_change(void);

/**
 * @brief Set the blink count to use. Set to 0 to disable coop support.
 *
 * @param num_blinks The number of blinks.
 */
void set_blink_count(uint32_t num_blinks);

}  // namespace hunt::drops::coop

#endif /* HUNT_NATIVE_DROPS_COOP_H */
