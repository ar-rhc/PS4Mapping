import tkinter as tk
import time
import threading
import math
from gui.main_window import DS4ControlUI

def simulate_mouse_movement(app):
    """
    This function runs in a separate thread to simulate joystick input
    and test the mouse control feature.
    """
    print("--- Test Simulation Started ---")
    
    # Give the UI a moment to initialize
    time.sleep(2)
    
    # 1. Programmatically enable mouse control
    print("Step 1: Enabling mouse control via toggle callback.")
    app.toggle_mouse_control(True)
    
    # Verify that the state was updated
    if not app.mouse_control_enabled:
        print("Error: Mouse control was not enabled correctly.")
        return
    print("Step 1: Success. app.mouse_control_enabled is True.")

    # 2. Define the movement pattern (a square)
    # Each tuple is (dx, dy, duration_seconds)
    move_pattern = [
        (1, 0, 1),   # Move right
        (0, 1, 1),   # Move down
        (-1, 0, 1),  # Move left
        (0, -1, 1),  # Move up
    ]
    
    print("\nStep 2: Starting simulated mouse movement in a square pattern.")
    
    for dx, dy, duration in move_pattern:
        print(f"  - Moving with joystick input: dx={dx}, dy={dy} for {duration}s")
        start_time = time.time()
        while time.time() - start_time < duration:
            # Create mock data packet
            mock_data = {
                'left_stick': {'x': dx, 'y': dy}
            }
            # Call the handler directly
            app.handle_mouse_movement(mock_data)
            time.sleep(0.01) # Simulate polling interval

    # 3. Disable mouse control
    print("\nStep 3: Disabling mouse control.")
    app.toggle_mouse_control(False)
    
    print("\n--- Test Simulation Finished ---")
    print("Check if your mouse cursor moved in a square pattern.")


if __name__ == '__main__':
    # This test script runs independently of the main application entry point.
    
    # We need to run the UI in the main thread, with test_mode=True
    app = DS4ControlUI(test_mode=True)
    
    # Run the simulation in a separate thread so it doesn't block the UI
    test_thread = threading.Thread(target=simulate_mouse_movement, args=(app,), daemon=True)
    test_thread.start()
    
    # Start the Tkinter main loop
    app.mainloop() 