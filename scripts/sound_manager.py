import pygame
import os
from config import *

# Try to import pygame.sndarray for sound manipulation
try:
    import pygame.sndarray
    sndarray_available = True
except ImportError:
    sndarray_available = False
    print("WARNING: pygame.sndarray not available - falling back to full sound files.")

class SoundManager:
    """Class to manage all game sounds and music"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if self._initialized:
            return
            
        # Track if audio is actually working
        self.audio_available = False
        self.init_error = None
        
        # Initialize pygame mixer
        try:
            pygame.mixer.init()
            # Test if mixer is actually working by trying to set volume
            pygame.mixer.music.set_volume(0.5)
            self.audio_available = True
            print("Pygame mixer initialized successfully")
        except Exception as e:
            self.init_error = str(e)
            print(f"WARNING: Audio system unavailable - {e}")
            print("The game will run without sound. This is common in WSL environments.")
            # We'll still set _initialized to True so the game can continue
            
        self._initialized = True
        self.music_enabled = True
        self.sfx_enabled = True
        self.music_volume = 0.5  # 50% volume
        self.sfx_volume = 0.7    # 70% volume
        
        # Define sound paths
        self.sound_dir = SOUNDS_PATH
        
        # Dictionary to store loaded sounds
        self.sounds = {}
        
        # Define music tracks
        self.music_tracks = {
            'menu': os.path.join(self.sound_dir, "welcome_screen.mp3"),
            'game': os.path.join(self.sound_dir, "game_music.mp3"),
            # 'game_over': os.path.join(self.sound_dir, "game_over.mp3"),  # To be added later
        }
        
        # Current playing music track
        self.current_music = None
        
        # Set initial volume if audio is available
        if self.audio_available:
            pygame.mixer.music.set_volume(self.music_volume)
            print(f"SoundManager initialized with tracks: {list(self.music_tracks.keys())}")
        else:
            print("SoundManager initialized in silent mode (no audio available)")
            
        # Check if music files exist
        for track_name, track_path in self.music_tracks.items():
            if not os.path.exists(track_path):
                print(f"WARNING: Music file for '{track_name}' not found at: {track_path}")
            else:
                print(f"Found music file: {track_name} at {track_path}")
    
    def play_music(self, track_key, loop=-1):
        """Play a music track with option to loop"""
        if not self._initialized or not self.music_enabled:
            return
            
        if not self.audio_available:
            print(f"Silent mode: Would play '{track_key}' music if audio was available")
            return
            
        if track_key not in self.music_tracks:
            print(f"Error: Music track '{track_key}' not found")
            return
            
        # If the requested track is already playing, do nothing
        if self.current_music == track_key and pygame.mixer.music.get_busy():
            return
            
        try:
            music_path = self.music_tracks[track_key]
            if not os.path.exists(music_path):
                print(f"Error: Music file not found at {music_path}")
                return
                
            # Stop any currently playing music
            self.stop_music()
            
            # Load and play the new track
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(loop)
            self.current_music = track_key
            print(f"Now playing: {track_key} music")
        except Exception as e:
            print(f"Error playing music track '{track_key}': {e}")
            # If there was an error, mark audio as unavailable
            self.audio_available = False
    
    def stop_music(self):
        """Stop the currently playing music"""
        if not self._initialized or not self.audio_available:
            return
            
        try:
            pygame.mixer.music.stop()
            self.current_music = None
        except Exception as e:
            print(f"Error stopping music: {e}")
            self.audio_available = False
    
    def pause_music(self):
        """Pause the currently playing music"""
        if not self._initialized or not self.audio_available:
            return
            
        try:
            pygame.mixer.music.pause()
        except Exception as e:
            print(f"Error pausing music: {e}")
            self.audio_available = False
    
    def unpause_music(self):
        """Unpause the currently playing music"""
        if not self._initialized or not self.audio_available:
            return
            
        try:
            pygame.mixer.music.unpause()
        except Exception as e:
            print(f"Error unpausing music: {e}")
            self.audio_available = False
    
    def set_music_volume(self, volume):
        """Set the music volume (0.0 to 1.0)"""
        if not self._initialized or not self.audio_available:
            return
            
        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except Exception as e:
            print(f"Error setting volume: {e}")
            self.audio_available = False
    
    def toggle_music(self):
        """Toggle music on/off"""
        self.music_enabled = not self.music_enabled
        if not self.audio_available:
            print(f"Music {'enabled' if self.music_enabled else 'disabled'} (but audio system unavailable)")
            return self.music_enabled
            
        if self.music_enabled:
            self.unpause_music()
        else:
            self.pause_music()
        return self.music_enabled
    
    def toggle_sfx(self):
        """Toggle sound effects on/off"""
        self.sfx_enabled = not self.sfx_enabled
        if not self.audio_available:
            print(f"Sound effects {'enabled' if self.sfx_enabled else 'disabled'} (but audio system unavailable)")
        return self.sfx_enabled
    
    def play_sound(self, sound_name, loop=0):
        """
        Play a sound effect with optional looping
        
        Args:
            sound_name (str): The name of the sound to play (without extension)
            loop (int): Number of times to loop the sound (-1 for infinite loop, 0 for no loop)
            
        Returns:
            pygame.mixer.Channel or None: The channel the sound is playing on, or None if not available
        """
        if not self._initialized or not self.sfx_enabled or not self.audio_available:
            return None
            
        # Load the sound if not already loaded
        if sound_name not in self.sounds:
            sound_path = os.path.join(self.sound_dir, f"{sound_name}.wav")
            try:
                self.sounds[sound_name] = pygame.mixer.Sound(sound_path)
                self.sounds[sound_name].set_volume(self.sfx_volume)
            except Exception as e:
                print(f"Error loading sound '{sound_name}': {e}")
                return None
        
        # Play the sound
        try:
            channel = self.sounds[sound_name].play(loops=loop)
            return channel
        except Exception as e:
            print(f"Error playing sound '{sound_name}': {e}")
            self.audio_available = False
            return None
            
    def stop_sound_channel(self, channel):
        """
        Stop a playing sound on a specific channel
        
        Args:
            channel: The channel to stop the sound on
        """
        if not self._initialized or not self.audio_available or channel is None:
            return
            
        try:
            channel.stop()
        except Exception as e:
            print(f"Error stopping sound channel: {e}")
            self.audio_available = False
    
    def play_sound_portion(self, sound_name, start_ms=0, duration_ms=2000, loop=0):
        """
        Play a specific portion of a sound effect with optional looping
        
        Args:
            sound_name (str): The name of the sound to play (without extension)
            start_ms (int): Start time in milliseconds
            duration_ms (int): Duration to play in milliseconds
            loop (int): Number of times to loop the sound (-1 for infinite loop, 0 for no loop)
            
        Returns:
            pygame.mixer.Channel or None: The channel the sound is playing on, or None if not available
        """
        if not self._initialized or not self.sfx_enabled or not self.audio_available:
            return None
            
        # If sndarray is not available, fall back to playing the full sound
        if not sndarray_available:
            print(f"sndarray not available, playing full sound for: {sound_name}")
            return self.play_sound(sound_name, loop)
            
        # Create a unique key for the portion
        portion_key = f"{sound_name}_{start_ms}_{duration_ms}"
            
        # Load the sound portion if not already loaded
        if portion_key not in self.sounds:
            # First load the full sound
            sound_path = os.path.join(self.sound_dir, f"{sound_name}.wav")
            try:
                # Load the full sound temporarily
                full_sound = pygame.mixer.Sound(sound_path)
                
                # Get sound array data
                full_array = pygame.sndarray.array(full_sound)
                
                # Calculate position in array based on milliseconds
                sample_rate = pygame.mixer.get_init()[0]
                channels = 2  # Stereo sound (most common)
                start_pos = (start_ms * sample_rate) // 1000
                duration_pos = (duration_ms * sample_rate) // 1000
                
                # Extract the desired portion
                if start_pos + duration_pos > len(full_array):
                    duration_pos = len(full_array) - start_pos
                    
                if duration_pos <= 0:
                    print(f"Error: Invalid duration for sound portion '{portion_key}'")
                    return None
                    
                try:
                    portion_array = full_array[start_pos:start_pos + duration_pos]
                    
                    # Create a new sound from the portion
                    self.sounds[portion_key] = pygame.sndarray.make_sound(portion_array)
                    self.sounds[portion_key].set_volume(self.sfx_volume)
                    print(f"Created sound portion: {portion_key}")
                except Exception as e:
                    print(f"Error creating sound portion '{portion_key}': {e}")
                    # Fall back to using the full sound
                    self.sounds[portion_key] = full_sound
                    self.sounds[portion_key].set_volume(self.sfx_volume)
                    print(f"Falling back to full sound for '{portion_key}'")
            except Exception as e:
                print(f"Error loading sound '{sound_name}' for portion: {e}")
                return None
        
        # Play the sound portion
        try:
            channel = self.sounds[portion_key].play(loops=loop)
            return channel
        except Exception as e:
            print(f"Error playing sound portion '{portion_key}': {e}")
            self.audio_available = False
            return None

# Function to get the singleton instance
def get_sound_manager():
    return SoundManager() 