#ifndef HUNT_NATIVE_DROPS_HOOKS_H
#define HUNT_NATIVE_DROPS_HOOKS_H

#include "pyunrealsdk/static_py_object.h"

namespace hunt::drops {

/**
 * @brief Enables the drop detection hooks.
 */
void enable(void);

/**
 * @brief Disables the drop detection hooks.
 */
void disable(void);

/**
 * @brief Sets the drop callback.
 *
 * @param getter A python callback which takes the balance name of a found drop as it's single arg.
 */
void set_drop_callback(const pyunrealsdk::StaticPyObject&& getter);

}  // namespace hunt::drops

#endif /* HUNT_NATIVE_DROPS_HOOKS_H */
