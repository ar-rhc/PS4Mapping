# Controller Module

This module contains all controller-related functionality for the DS4 controller system.

## Components

### `data_parser.py` - DS4 Data Parser

A comprehensive parser for DualShock 4 controller HID reports that handles:

- **Analog Inputs**: Left/right sticks, L2/R2 triggers
- **Digital Inputs**: All buttons, D-pad, PS button, touchpad
- **Sensors**: Gyroscope, accelerometer, touchpad data
- **System Data**: Battery level, connection status

#### Key Features

- **Normalized Data**: Analog values are normalized to -1 to 1 range
- **Change Detection**: Tracks digital input changes for event-driven systems
- **Validation**: Validates HID report structure
- **Convenience Methods**: Easy access to common data queries

#### Usage Example

```python
from controller.data_parser import DS4DataParser

# Create parser
parser = DS4DataParser()

# Parse HID report
data = parser.parse_controller_data(hid_report)

# Check for button changes
changes = parser.check_digital_changes(data)

# Get summaries
analog_data = parser.get_analog_summary(data)
digital_data = parser.get_digital_summary(data)
sensor_data = parser.get_sensor_summary(data)
```

#### Data Structure

The parser returns a structured dictionary with:

```python
{
    'left_stick': {'x': float, 'y': float, 'raw_x': int, 'raw_y': int},
    'right_stick': {'x': float, 'y': float, 'raw_x': int, 'raw_y': int},
    'l2': {'value': float, 'raw': int},
    'r2': {'value': float, 'raw': int},
    'buttons': {
        'square': bool, 'cross': bool, 'circle': bool, 'triangle': bool,
        'l1': bool, 'r1': bool, 'l2_pressed': bool, 'r2_pressed': bool,
        'share': bool, 'options': bool, 'l3': bool, 'r3': bool
    },
    'dpad': str,  # 'none', 'up', 'down', 'left', 'right', 'ne', 'se', 'sw', 'nw'
    'ps_button': bool,
    'touchpad_pressed': bool,
    'gyro': {'x': int, 'y': int, 'z': int},
    'accelerometer': {'x': int, 'y': int, 'z': int},
    'touchpad': {'active': bool, 'id': int, 'x': int, 'y': int},
    'battery': int
}
```

### `hid_controller.py` - HID Controller Interface

Handles the low-level HID communication with the DS4 controller.

## Benefits of Modularization

By extracting the data parser into its own module, we gain:

1. **Separation of Concerns**: Data parsing is isolated from GUI logic
2. **Reusability**: The parser can be used by multiple components
3. **Testability**: Easy to unit test parsing logic independently
4. **Maintainability**: Changes to parsing logic don't affect GUI code
5. **Performance**: Optimized parsing without GUI overhead

## Future Components

This module will eventually include:

- **Sensor Fusion**: Advanced gyro/accelerometer processing
- **Calibration**: Controller calibration and deadzone management
- **Mapping**: Input mapping and transformation
- **Profiles**: Controller configuration profiles 