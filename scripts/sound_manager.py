import pygame
import os
from config import *

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
    
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if not self._initialized or not self.sfx_enabled or not self.audio_available:
            return
            
        # Load the sound if not already loaded
        if sound_name not in self.sounds:
            sound_path = os.path.join(self.sound_dir, f"{sound_name}.wav")
            try:
                self.sounds[sound_name] = pygame.mixer.Sound(sound_path)
                self.sounds[sound_name].set_volume(self.sfx_volume)
            except Exception as e:
                print(f"Error loading sound '{sound_name}': {e}")
                return
        
        # Play the sound
        try:
            self.sounds[sound_name].play()
        except Exception as e:
            print(f"Error playing sound '{sound_name}': {e}")
            self.audio_available = False

# Function to get the singleton instance
def get_sound_manager():
    return SoundManager() 