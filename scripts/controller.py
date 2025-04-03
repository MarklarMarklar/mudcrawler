import pygame

class ControllerHandler:
    def __init__(self):
        """Initialize controller support"""
        # Initialize joystick module
        pygame.joystick.init()
        
        # Controller state
        self.controller = None
        self.connected = False
        
        # Button mappings according to requirements
        # space = Right trigger (RT)
        # mouse left click = left trigger (LT)
        # mouse right click = X button
        # esc = start button
        # WSAD = analog or dpad
        # E = Y button
        
        # Standard Xbox controller button mapping
        self.BUTTON_A = 0
        self.BUTTON_B = 1
        self.BUTTON_X = 2  # Mouse right click
        self.BUTTON_Y = 3  # E key
        self.BUTTON_LB = 4
        self.BUTTON_RB = 5
        self.BUTTON_BACK = 6
        self.BUTTON_START = 7  # ESC key
        self.BUTTON_LSTICK = 8
        self.BUTTON_RSTICK = 9
        
        # Axes
        self.AXIS_LEFT_X = 0   # Left stick X (left/right)
        self.AXIS_LEFT_Y = 1   # Left stick Y (up/down)
        self.AXIS_RIGHT_X = 2  # Right stick X
        self.AXIS_RIGHT_Y = 3  # Right stick Y
        self.AXIS_LT = 4       # Left trigger (mouse left click)
        self.AXIS_RT = 5       # Right trigger (space)
        
        # D-pad directions (some controllers use hat for d-pad)
        self.DPAD_X = 0  # D-pad X axis
        self.DPAD_Y = 1  # D-pad Y axis
        
        # Threshold values
        self.DEADZONE = 0.5  # Increased deadzone for digital movement
        self.TRIGGER_THRESHOLD = 0.5  # Threshold to consider trigger pressed
        
        # Maintain key state to properly generate key up events
        self.simulated_keys = {
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_SPACE: False,
            pygame.K_e: False,
            pygame.K_ESCAPE: False
        }
        
        # Tracking for mouse buttons
        self.simulated_mouse = {
            1: False,  # Left mouse button
            3: False   # Right mouse button
        }

        # Store aim position for right stick
        self.aim_position = None
        
        # Track whether we're in a menu
        self.in_menu = False
        self.menu_cursor_speed = 15  # Speed of cursor movement in menu
        
        # Try to connect to a controller
        self.check_for_controller()
    
    def check_for_controller(self):
        """Check if any controllers are connected"""
        # Count the number of joysticks
        joystick_count = pygame.joystick.get_count()
        
        if joystick_count > 0:
            # Initialize the first joystick
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            self.connected = True
            
            # Print controller info
            controller_name = self.controller.get_name()
            num_axes = self.controller.get_numaxes()
            num_buttons = self.controller.get_numbuttons()
            num_hats = self.controller.get_numhats()
            
            return True
        else:
            self.controller = None
            self.connected = False
            return False
    
    def process_controller_input(self):
        """Process controller input and convert to keyboard/mouse events
        Returns a list of simulated pygame events."""
        if not self.connected:
            # Try to connect to a controller if none is connected
            if not self.check_for_controller():
                return []  # No controller connected, return empty list
        
        # Reset simulated inputs list
        simulated_events = []
        
        # Store previous key and mouse states for change detection
        old_keyboard_state = self.simulated_keys.copy()
        old_mouse_state = self.simulated_mouse.copy()
        
        try:
            # Process analog stick (left stick) for WASD movement - DIGITAL MODE
            if self.controller.get_numaxes() > self.AXIS_LEFT_Y:
                x_axis = self.controller.get_axis(self.AXIS_LEFT_X)
                y_axis = self.controller.get_axis(self.AXIS_LEFT_Y)
                
                # Digital movement - either 0 or 1, no in-between
                # Set new key states based on left stick
                left_key_state = x_axis < -self.DEADZONE
                right_key_state = x_axis > self.DEADZONE
                up_key_state = y_axis < -self.DEADZONE
                down_key_state = y_axis > self.DEADZONE
                
                # Update current key states
                self.simulated_keys[pygame.K_a] = left_key_state
                self.simulated_keys[pygame.K_d] = right_key_state
                self.simulated_keys[pygame.K_w] = up_key_state
                self.simulated_keys[pygame.K_s] = down_key_state
            
            # Process D-pad for WASD movement - override analog if used
            if self.controller.get_numhats() > 0:
                dpad_x, dpad_y = self.controller.get_hat(0)
                
                # D-pad values override analog stick
                if dpad_x == -1:  # Left
                    self.simulated_keys[pygame.K_a] = True
                    self.simulated_keys[pygame.K_d] = False
                elif dpad_x == 1:  # Right
                    self.simulated_keys[pygame.K_d] = True
                    self.simulated_keys[pygame.K_a] = False
                
                if dpad_y == 1:  # Up
                    self.simulated_keys[pygame.K_w] = True
                    self.simulated_keys[pygame.K_s] = False
                elif dpad_y == -1:  # Down
                    self.simulated_keys[pygame.K_s] = True
                    self.simulated_keys[pygame.K_w] = False
            
            # Check button presses
            if self.controller.get_numbuttons() > self.BUTTON_Y:
                # Y button → E key
                self.simulated_keys[pygame.K_e] = self.controller.get_button(self.BUTTON_Y)
                
                # X button → right mouse click
                self.simulated_mouse[3] = self.controller.get_button(self.BUTTON_X)
                
                # Start button → ESC key
                self.simulated_keys[pygame.K_ESCAPE] = self.controller.get_button(self.BUTTON_START)
            
            # Check triggers
            if self.controller.get_numaxes() > self.AXIS_RT:
                # Right trigger → Space bar
                right_trigger = self.controller.get_axis(self.AXIS_RT)
                self.simulated_keys[pygame.K_SPACE] = right_trigger > self.TRIGGER_THRESHOLD
                
                # Left trigger → left mouse click
                left_trigger = self.controller.get_axis(self.AXIS_LT)
                self.simulated_mouse[1] = left_trigger > self.TRIGGER_THRESHOLD
            
            # Generate keyboard events for keys that have changed
            for key, is_pressed in self.simulated_keys.items():
                if is_pressed != old_keyboard_state[key]:
                    event_type = pygame.KEYDOWN if is_pressed else pygame.KEYUP
                    event = pygame.event.Event(event_type, {'key': key})
                    simulated_events.append(event)
            
            # Generate mouse events for buttons that have changed
            for button, is_pressed in self.simulated_mouse.items():
                if is_pressed != old_mouse_state[button]:
                    event_type = pygame.MOUSEBUTTONDOWN if is_pressed else pygame.MOUSEBUTTONUP
                    
                    # Use aim position if available, otherwise current mouse position
                    if self.aim_position:
                        pos = self.aim_position
                    else:
                        pos = pygame.mouse.get_pos()
                        
                    event = pygame.event.Event(event_type, {'button': button, 'pos': pos})
                    simulated_events.append(event)
            
            # Process right stick for menu cursor if in menu state
            if self.in_menu and self.controller.get_numaxes() > self.AXIS_RIGHT_Y:
                self.update_menu_cursor()
            
        except pygame.error:
            # Controller disconnected
            self.connected = False
            self.controller = None
            
        return simulated_events
    
    def update_menu_cursor(self):
        """Move the mouse cursor based on right stick input for menu navigation"""
        if not self.connected:
            return
        
        try:
            # Get right stick position
            right_x = self.controller.get_axis(self.AXIS_RIGHT_X)
            right_y = self.controller.get_axis(self.AXIS_RIGHT_Y)
            
            # Check if stick is moved beyond deadzone
            if abs(right_x) > 0.1 or abs(right_y) > 0.1:  # Use a smaller deadzone for cursor movement
                # Get current cursor position
                current_x, current_y = pygame.mouse.get_pos()
                
                # Calculate new position
                new_x = current_x + int(right_x * self.menu_cursor_speed)
                new_y = current_y + int(right_y * self.menu_cursor_speed)
                
                # Get window dimensions
                window_width, window_height = pygame.display.get_surface().get_size()
                
                # Constrain to window boundaries
                new_x = max(0, min(new_x, window_width - 1))
                new_y = max(0, min(new_y, window_height - 1))
                
                # Move cursor
                pygame.mouse.set_pos((new_x, new_y))
                
                # Generate a mouse motion event
                event = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (new_x, new_y), 'rel': (right_x, right_y)})
                pygame.event.post(event)
                
        except pygame.error:
            # Controller disconnected
            self.connected = False
            self.controller = None
    
    def update_controller(self):
        """Updates controller connection status and returns any simulated events"""
        # Check for newly connected controllers
        if not self.connected:
            self.check_for_controller()
            
        # Process controller input if connected
        if self.connected:
            return self.process_controller_input()
        
        return []
    
    def update_aim_from_right_stick(self, game_obj):
        """Updates aim position based on right analog stick
        Returns a tuple (is_aiming, aim_direction) where:
            - is_aiming: Boolean indicating if right stick is being used
            - aim_direction: Vector (dx, dy) indicating aim direction
        """
        if not self.connected or game_obj.player is None:
            return False, (0, 0)
            
        try:
            if self.controller.get_numaxes() > self.AXIS_RIGHT_Y:
                # Get right stick position
                right_x = self.controller.get_axis(self.AXIS_RIGHT_X)
                right_y = self.controller.get_axis(self.AXIS_RIGHT_Y)
                
                # Check if stick is moved beyond deadzone
                if abs(right_x) > self.DEADZONE or abs(right_y) > self.DEADZONE:
                    # Get player position
                    player_x, player_y = game_obj.player.rect.centerx, game_obj.player.rect.centery
                    
                    # Scale stick movement (higher value = faster/further aiming)
                    scale = 100
                    
                    # Calculate world coordinates for aim point
                    aim_x = player_x + (right_x * scale)
                    aim_y = player_y + (right_y * scale)
                    
                    # Convert to screen coordinates for mouse events
                    screen_x = (aim_x - game_obj.camera.x) * game_obj.camera.zoom
                    screen_y = (aim_y - game_obj.camera.y) * game_obj.camera.zoom
                    
                    # Get window dimensions
                    window_width = game_obj.screen.get_width()
                    window_height = game_obj.screen.get_height()
                    
                    # Add margin to prevent the cursor from going off screen
                    margin = 5
                    
                    # Constrain to window boundaries
                    screen_x = max(margin, min(int(screen_x), window_width - margin))
                    screen_y = max(margin, min(int(screen_y), window_height - margin))
                    
                    # Store the aim position for use in mouse events
                    self.aim_position = (screen_x, screen_y)
                    
                    # Set pygame mouse position to match controller aim
                    pygame.mouse.set_pos(self.aim_position)
                    
                    # Determine cardinal direction based on stick angle
                    angle = (180 / 3.14159) * -1 * pygame.math.Vector2(right_x, right_y).angle_to((1, 0))
                    if angle < 0:
                        angle += 360
                    
                    # Return world coordinates for player aim
                    return True, (right_x, right_y)
            
            return False, (0, 0)
            
        except pygame.error:
            # Controller disconnected or error
            self.connected = False
            self.controller = None
            return False, (0, 0)
            
    def keydown_event(self, key):
        """Helper to generate a keydown event"""
        return pygame.event.Event(pygame.KEYDOWN, {'key': key})
        
    def keyup_event(self, key):
        """Helper to generate a keyup event"""
        return pygame.event.Event(pygame.KEYUP, {'key': key})
    
    def get_controller_status(self):
        """Return if a controller is connected"""
        return self.connected
    
    def set_menu_state(self, in_menu):
        """Set whether we're currently in a menu state or not"""
        self.in_menu = in_menu 