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
    
    def create_blood_splash(self, x, y, amount=10):
        """Create a blood splash effect at the specified position"""
        for _ in range(amount):
            speed = random.uniform(0.5, 3.0)
            angle = random.uniform(0, math.pi * 2)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed
            lifetime = random.randint(20, 60)  # frames
            size = random.randint(2, 6)
            
            # Create a particle with blood-like properties
            particle = {
                'x': x,
                'y': y,
                'velocity_x': velocity_x,
                'velocity_y': velocity_y,
                'color': (
                    random.randint(100, 200),  # R - various dark reds
                    random.randint(0, 20),     # G - very little green
                    random.randint(0, 20)      # B - very little blue
                ),
                'size': size,
                'lifetime': lifetime,
                'alpha': 255,
                'gravity': 0.1,  # Blood is affected by gravity
                'fade_speed': random.uniform(2, 5)
            }
            self.particles.append(particle)
            
    def create_fire_effect(self, x, y, amount=15):
        """Create a fire effect at the specified position"""
        for _ in range(amount):
            speed = random.uniform(1.0, 4.0)
            # Mostly upward with some sideways variation
            angle = random.uniform(-math.pi/4, math.pi/4) - math.pi/2  # -pi/2 is up
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed
            lifetime = random.randint(20, 60)  # frames
            size = random.randint(3, 10)
            
            # Fire colors: yellow, orange, red
            fire_colors = [
                (255, 255, 0),    # Yellow
                (255, 165, 0),    # Orange
                (255, 100, 0),    # Dark orange
                (255, 50, 0)      # Reddish orange
            ]
            
            # Create a particle with fire-like properties
            particle = {
                'x': x + random.randint(-10, 10),  # Slight position variation
                'y': y + random.randint(-5, 5),
                'velocity_x': velocity_x,
                'velocity_y': velocity_y,
                'color': random.choice(fire_colors),
                'size': size,
                'lifetime': lifetime,
                'alpha': 255,
                'gravity': -0.05,  # Fire rises slightly
                'fade_speed': random.uniform(3, 7)
            }
            self.particles.append(particle)
            
    def create_blood_pool(self, x, y, amount=5, size_range=(4, 10)):
        """Create a slow-spreading blood pool effect for death sequence"""
        min_size, max_size = size_range
        
        for _ in range(amount):
            # Very slow outward movement - like blood slowly spilling
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.1, 0.5)  # Very slow
            
            # Darker blood colors for pools
            color = (
                random.randint(80, 150),  # R - darker reds for pooling blood
                random.randint(0, 15),    # G - minimal green
                random.randint(0, 15)     # B - minimal blue
            )
            
            # Blood pools last longer and are larger
            size = random.uniform(min_size, max_size)
            lifetime = random.randint(80, 120)  # Longer lifetime
            
            # Create a particle with blood pool properties
            particle = {
                'x': x + random.randint(-5, 5),  # Small position variation
                'y': y + random.randint(-5, 5),
                'velocity_x': math.cos(angle) * speed,
                'velocity_y': math.sin(angle) * speed,
                'color': color,
                'size': size,
                'lifetime': lifetime,
                'alpha': 255,
                'gravity': 0.0,  # No gravity - stays at the same level
                'fade_speed': random.uniform(0.3, 0.6),  # Much slower fade
                'is_pool': True  # Mark as a pool particle
            }
            self.particles.append(particle)
    
    def update(self):
        """Update all particles and remove dead ones"""
        # List to track particles to remove
        particles_to_remove = []
        
        # Update all particles
        for i, particle in enumerate(self.particles):
            if isinstance(particle, Particle):
                # For Particle class objects
                particle.update()
                if not particle.alive:
                    particles_to_remove.append(i)
            else:
                # For dictionary-based particles
                # Update position
                particle['x'] += particle['velocity_x']
                particle['y'] += particle['velocity_y']
                
                # Apply gravity if present
                if 'gravity' in particle:
                    particle['velocity_y'] += particle['gravity']
                
                # Apply drag to velocity
                particle['velocity_x'] *= 0.95
                particle['velocity_y'] *= 0.95
                
                # Special handling for blood pool particles
                if particle.get('is_pool', False):
                    # Blood pools grow slightly as they spread
                    if particle['lifetime'] > 60:  # Only grow during initial phase
                        growth_rate = 0.03
                        particle['size'] += growth_rate
                    
                    # Make pool particles stick to the ground faster
                    particle['velocity_x'] *= 0.8
                    particle['velocity_y'] *= 0.8
                
                # Update lifetime
                particle['lifetime'] -= 1
                
                # Shrink particles as they age
                if 'fade_speed' in particle:
                    # Blood pools fade slower
                    if particle.get('is_pool', False):
                        # Only start shrinking in the last third of lifetime
                        if particle['lifetime'] < particle.get('lifetime', 30) / 3:
                            particle['size'] -= particle['fade_speed'] * 0.025
                    else:
                        particle['size'] -= particle['fade_speed'] * 0.05
                
                # Mark dead particles
                if particle['lifetime'] <= 0 or particle['size'] <= 0:
                    particles_to_remove.append(i)
        
        # Remove dead particles - in reverse order to avoid index issues
        for i in sorted(particles_to_remove, reverse=True):
            if i < len(self.particles):  # Safety check
                self.particles.pop(i)
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw all particles to the surface"""
        # Sort particles so blood pools are drawn first (underneath everything else)
        # This ensures blood splatter appears on top of pools
        sorted_particles = sorted(
            self.particles, 
            key=lambda p: 0 if isinstance(p, Particle) or not p.get('is_pool', False) else 1
        )
        
        for particle in sorted_particles:
            if isinstance(particle, Particle):
                # For Particle class objects
                particle.draw(surface, camera_offset)
            else:
                # For dictionary-based particles
                # Only draw if alive
                if particle['lifetime'] <= 0 or particle['size'] <= 0:
                    continue
                
                # Apply camera offset
                draw_x = int(particle['x'] - camera_offset[0])
                draw_y = int(particle['y'] - camera_offset[1])
                
                # Draw the particle
                try:
                    # Special drawing for blood pools - flatter ellipses instead of circles
                    if particle.get('is_pool', False):
                        size = max(1, int(particle['size']))
                        height = max(1, int(size * 0.4))  # Flatter height
                        
                        # For very large pools, use irregular shapes
                        if size > 6:
                            # Draw a slightly irregular pool shape
                            points = []
                            segments = 8
                            for i in range(segments):
                                angle = i * (2 * math.pi / segments)
                                # Vary the radius slightly for irregular shape
                                radius_x = size * (0.9 + random.random() * 0.2)
                                radius_y = height * (0.9 + random.random() * 0.2)
                                point_x = draw_x + int(math.cos(angle) * radius_x)
                                point_y = draw_y + int(math.sin(angle) * radius_y)
                                points.append((point_x, point_y))
                            
                            # Draw the pool as a polygon
                            pygame.draw.polygon(surface, particle['color'], points)
                        else:
                            # For smaller pools, use an ellipse
                            ellipse_rect = pygame.Rect(
                                draw_x - size, 
                                draw_y - height, 
                                size * 2, 
                                height * 2
                            )
                            pygame.draw.ellipse(surface, particle['color'], ellipse_rect)
                    elif 'color' in particle and len(particle['color']) >= 3:
                        # Draw glow effect for fire particles
                        glow_size = int(particle['size'] * 2)
                        if glow_size > 0:
                            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                            glow_alpha = min(150, int(particle['alpha'] * 0.6) if 'alpha' in particle else 100)
                            glow_color = (*particle['color'][:3], glow_alpha)
                            pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                            surface.blit(glow_surf, (draw_x - glow_size, draw_y - glow_size))
                        
                        # Draw the actual particle
                        size = max(1, int(particle['size']))
                        pygame.draw.circle(surface, particle['color'], (draw_x, draw_y), size)
                except Exception as e:
                    print(f"Error drawing particle: {e}")
                    
    def draw_blood_pools_only(self, surface, camera_offset=(0, 0)):
        """Draw only blood pool particles to the surface"""
        for particle in self.particles:
            # Skip Particle class objects and non-pool particles
            if isinstance(particle, Particle) or not particle.get('is_pool', False):
                continue
                
            # Skip dead particles
            if particle['lifetime'] <= 0 or particle['size'] <= 0:
                continue
            
            # Apply camera offset
            draw_x = int(particle['x'] - camera_offset[0])
            draw_y = int(particle['y'] - camera_offset[1])
            
            # Draw the blood pool
            try:
                size = max(1, int(particle['size']))
                height = max(1, int(size * 0.4))  # Flatter height
                
                # For very large pools, use irregular shapes
                if size > 6:
                    # Draw a slightly irregular pool shape
                    points = []
                    segments = 8
                    for i in range(segments):
                        angle = i * (2 * math.pi / segments)
                        # Vary the radius slightly for irregular shape
                        radius_x = size * (0.9 + random.random() * 0.2)
                        radius_y = height * (0.9 + random.random() * 0.2)
                        point_x = draw_x + int(math.cos(angle) * radius_x)
                        point_y = draw_y + int(math.sin(angle) * radius_y)
                        points.append((point_x, point_y))
                    
                    # Draw the pool as a polygon
                    pygame.draw.polygon(surface, particle['color'], points)
                else:
                    # For smaller pools, use an ellipse
                    ellipse_rect = pygame.Rect(
                        draw_x - size, 
                        draw_y - height, 
                        size * 2, 
                        height * 2
                    )
                    pygame.draw.ellipse(surface, particle['color'], ellipse_rect)
            except Exception as e:
                print(f"Error drawing blood pool: {e}")
                
    def draw_except_blood_pools(self, surface, camera_offset=(0, 0)):
        """Draw all particles except blood pools to the surface"""
        for particle in self.particles:
            # Skip blood pool particles
            if not isinstance(particle, Particle) and particle.get('is_pool', False):
                continue
                
            if isinstance(particle, Particle):
                # For Particle class objects
                particle.draw(surface, camera_offset)
            else:
                # Skip dead particles
                if particle['lifetime'] <= 0 or particle['size'] <= 0:
                    continue
                
                # Apply camera offset
                draw_x = int(particle['x'] - camera_offset[0])
                draw_y = int(particle['y'] - camera_offset[1])
                
                # Draw regular (non-pool) particles
                try:
                    # Draw glow effect for fire particles
                    if 'color' in particle and len(particle['color']) >= 3:
                        glow_size = int(particle['size'] * 2)
                        if glow_size > 0:
                            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                            glow_alpha = min(150, int(particle['alpha'] * 0.6) if 'alpha' in particle else 100)
                            glow_color = (*particle['color'][:3], glow_alpha)
                            pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                            surface.blit(glow_surf, (draw_x - glow_size, draw_y - glow_size))
                    
                    # Draw the actual particle
                    size = max(1, int(particle['size']))
                    pygame.draw.circle(surface, particle['color'], (draw_x, draw_y), size)
                except Exception as e:
                    print(f"Error drawing regular particle: {e}") 