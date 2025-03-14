import pygame
import random
import math
from config import *

class Particle:
    """Base class for particle effects"""
    def __init__(self, x, y, color=(255, 255, 255), size=3, lifetime=30, velocity=None):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.original_size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True
        
        # Default velocity is random if none provided
        if velocity is None:
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            self.velocity_x = math.cos(angle) * speed
            self.velocity_y = math.sin(angle) * speed
        else:
            self.velocity_x, self.velocity_y = velocity
    
    def update(self):
        """Update particle position and lifetime"""
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Apply some drag to slow particles over time
        self.velocity_x *= 0.95
        self.velocity_y *= 0.95
        
        # Decrease lifetime
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
        
        # Optionally shrink the particle as it ages
        self.size = self.original_size * (self.lifetime / self.max_lifetime)
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the particle to the surface"""
        # Only draw if alive
        if not self.alive:
            return
        
        # Apply camera offset
        draw_x = self.x - camera_offset[0]
        draw_y = self.y - camera_offset[1]
        
        # Draw the particle
        pygame.draw.circle(surface, self.color, (int(draw_x), int(draw_y)), max(1, int(self.size)))

class BloodParticle(Particle):
    """Blood splatter particle with specific behavior"""
    def __init__(self, x, y):
        # Blood colors range from dark red to brighter red
        color = (
            random.randint(120, 200),  # R
            random.randint(0, 30),     # G
            random.randint(0, 30)      # B
        )
        
        # Random size
        size = random.uniform(2, 4)
        
        # Random lifetime 
        lifetime = random.randint(20, 40)
        
        # Create with base class
        super().__init__(x, y, color, size, lifetime)
        
        # Blood particles have more dramatic movement
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 5)
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed
        
        # Add gravity to blood particles
        self.gravity = 0.1
    
    def update(self):
        """Update with blood-specific behavior"""
        self.velocity_y += self.gravity  # Apply gravity
        
        # Call the base class update
        super().update()
        
        # Blood particles leave stains when they slow down
        if abs(self.velocity_x) < 0.5 and abs(self.velocity_y) < 0.5:
            self.alive = False

class ParticleSystem:
    """Manages multiple particles"""
    def __init__(self):
        self.particles = []
    
    def add_particle(self, particle):
        """Add a particle to the system"""
        self.particles.append(particle)
    
    def create_blood_splash(self, x, y, amount=15):
        """Create a blood splash at the given position"""
        for _ in range(amount):
            self.particles.append(BloodParticle(x, y))
    
    def update(self):
        """Update all particles and remove dead ones"""
        # Update all particles
        for particle in self.particles:
            particle.update()
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw all particles to the surface"""
        for particle in self.particles:
            particle.draw(surface, camera_offset) 