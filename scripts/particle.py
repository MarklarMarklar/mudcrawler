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
    
    def create_particle(self, x, y, color=(255, 255, 255), velocity=None, size=3, lifetime=30, fade_speed=None):
        """Create a custom particle with specified properties"""
        # If velocity not provided, generate random velocity
        if velocity is None:
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.0, 3.0)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed
        else:
            velocity_x, velocity_y = velocity
        
        # If fade_speed not provided, generate based on lifetime
        if fade_speed is None:
            fade_speed = size / lifetime * 2  # Scale fade speed to size and lifetime
        
        # Create the particle
        particle = {
            'x': x,
            'y': y,
            'velocity_x': velocity_x,
            'velocity_y': velocity_y,
            'color': color,
            'size': size,
            'lifetime': lifetime,
            'alpha': 255,
            'fade_speed': fade_speed
        }
        
        self.particles.append(particle)
        return particle
    
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
            
    def create_lightning_effect(self, x, y, amount=15):
        """Create a lightning effect at the specified position"""
        # Create several lightning bolt strikes instead of simple particles
        for _ in range(min(3, amount)):  # Limit to 3 main bolts for performance (reduced from 5)
            # Create a zigzag lightning bolt
            
            # Shorter length - 1.5 tiles instead of longer bolts
            bolt_length = random.randint(20, 30)  # Reduced length significantly
            
            # Random angle but more focused in a narrower cone (less random)
            angle = random.uniform(-math.pi/4, math.pi/4)  # Narrower angle range - just 90 degrees total
            
            # Random starting position near the hit point (reduced variation)
            start_x = x + random.randint(-5, 5)  # Less variation
            start_y = y + random.randint(-5, 5)  # Less variation
            
            # Direction vector
            dx = math.cos(angle)
            dy = math.sin(angle)
            
            # Create a zigzag path with multiple segments
            segments = random.randint(3, 5)  # Fewer segments (was 5-10)
            segment_length = bolt_length / segments
            
            points = [(start_x, start_y)]
            current_x, current_y = start_x, start_y
            
            # Generate zigzag pattern
            for i in range(segments):
                # Alternate zigzag by using multiplier
                zigzag_multiplier = 1 if i % 2 == 0 else -1
                
                # Reduced jitter amplitude for tighter zigzags
                perp_x = -dy * random.randint(3, 8) * zigzag_multiplier  # Less jitter (was 5-15)
                perp_y = dx * random.randint(3, 8) * zigzag_multiplier   # Less jitter (was 5-15)
                
                # Calculate next point with zigzag
                next_x = current_x + (dx * segment_length) + perp_x
                next_y = current_y + (dy * segment_length) + perp_y
                
                points.append((next_x, next_y))
                current_x, current_y = next_x, next_y
            
            # Choose a blue color for the bolt
            blue_intensity = random.randint(180, 255)
            color = (100, 150, blue_intensity)  # Blue color
            
            # Create the particle object with the bolt path
            bolt_particle = {
                'points': points,
                'color': color,
                'thickness': random.randint(2, 3),  # Slightly thinner (was 2-4)
                'lifetime': random.randint(8, 12),  # Shorter lifetime (was 10-20)
                'alpha': 255,
                'fade_speed': random.uniform(12, 18),  # Faster fade for shorter effect
                'is_lightning_bolt': True  # Mark as lightning bolt
            }
            self.particles.append(bolt_particle)
            
            # Add fewer branch bolts
            if random.random() < 0.5:  # 50% chance for branches (was 70%)
                # Only add 1-2 branches per bolt (was 1-3)
                for _ in range(random.randint(1, 2)):
                    if len(points) < 3:
                        continue
                        
                    # Choose a random point on the main bolt to branch from
                    branch_start_idx = random.randint(1, len(points) - 2)
                    branch_start_x = points[branch_start_idx][0]
                    branch_start_y = points[branch_start_idx][1]
                    
                    # Random branch direction but more controlled
                    branch_angle = angle + random.uniform(-math.pi/3, math.pi/3)  # Narrower angle
                    branch_dx = math.cos(branch_angle)
                    branch_dy = math.sin(branch_angle)
                    
                    # Shorter branch length
                    branch_length = bolt_length * random.uniform(0.3, 0.5)  # Shorter branches
                    branch_segments = random.randint(2, 3)  # Fewer segments (was 3-5)
                    branch_segment_length = branch_length / branch_segments
                    
                    # Create branch points
                    branch_points = [(branch_start_x, branch_start_y)]
                    branch_x, branch_y = branch_start_x, branch_start_y
                    
                    for i in range(branch_segments):
                        # Zigzag pattern for branch
                        zigzag_multiplier = 1 if i % 2 == 0 else -1
                        
                        # Add perpendicular jitter - smaller for branches
                        perp_x = -branch_dy * random.randint(2, 5) * zigzag_multiplier  # Smaller jitter
                        perp_y = branch_dx * random.randint(2, 5) * zigzag_multiplier   # Smaller jitter
                        
                        branch_x += branch_dx * branch_segment_length + perp_x
                        branch_y += branch_dy * branch_segment_length + perp_y
                        
                        branch_points.append((branch_x, branch_y))
                    
                    # Create branch bolt with slightly different color
                    branch_color = (120, 180, blue_intensity - 20)
                    branch_particle = {
                        'points': branch_points,
                        'color': branch_color,
                        'thickness': random.randint(1, 2),  # Thinner branches
                        'lifetime': random.randint(5, 8),  # Shorter lifetime
                        'alpha': 255,
                        'fade_speed': random.uniform(15, 20),  # Faster fade
                        'is_lightning_bolt': True
                    }
                    self.particles.append(branch_particle)
        
        # Add fewer spark particles
        for _ in range(amount // 2):  # Fewer sparks
            # Lightning has more erratic movement
            speed = random.uniform(1.0, 3.0)  # Lower max speed
            angle = random.uniform(0, 2 * math.pi)
            velocity_x = math.cos(angle) * speed
            velocity_y = math.sin(angle) * speed
            lifetime = random.randint(3, 8)  # Shorter lifetime
            size = random.randint(1, 3)  # Smaller particles
            
            # Lightning colors: white, blue, light blue
            lightning_colors = [
                (255, 255, 255),   # White
                (200, 235, 255),   # Light blue white
                (150, 200, 255),   # Light blue
            ]
            
            # Create a spark particle
            particle = {
                'x': x + random.randint(-5, 5),  # Less spread
                'y': y + random.randint(-5, 5),  # Less spread
                'velocity_x': velocity_x,
                'velocity_y': velocity_y,
                'color': random.choice(lightning_colors),
                'size': size,
                'lifetime': lifetime,
                'alpha': 255,
                'gravity': 0,  # No gravity
                'fade_speed': random.uniform(10, 15)  # Faster fade
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
                if 'points' in particle and particle.get('is_lightning_bolt', False):
                    # Lightning bolts don't move, just decrease lifetime
                    particle['lifetime'] -= 1
                    # Make bolts fade by reducing alpha
                    if 'alpha' in particle:
                        particle['alpha'] = max(0, particle['alpha'] - particle.get('fade_speed', 10))
                        if particle['alpha'] <= 0:
                            particles_to_remove.append(i)
                else:
                    # Regular particles
                    if 'x' in particle and 'y' in particle:
                        particle['x'] += particle.get('velocity_x', 0)
                        particle['y'] += particle.get('velocity_y', 0)
                    
                    # Apply gravity if present
                    if 'gravity' in particle and 'velocity_y' in particle:
                        particle['velocity_y'] += particle['gravity']
                    
                    # Apply drag to velocity
                    if 'velocity_x' in particle:
                        particle['velocity_x'] *= 0.95
                    if 'velocity_y' in particle:
                        particle['velocity_y'] *= 0.95
                    
                    # Special handling for blood pool particles
                    if particle.get('is_pool', False):
                        # Blood pools grow slightly as they spread
                        if particle['lifetime'] > 60:  # Only grow during initial phase
                            growth_rate = 0.03
                            particle['size'] += growth_rate
                        
                        # Make pool particles stick to the ground faster
                        if 'velocity_x' in particle:
                            particle['velocity_x'] *= 0.8
                        if 'velocity_y' in particle:
                            particle['velocity_y'] *= 0.8
                    
                    # Update lifetime
                    if 'lifetime' in particle:
                        particle['lifetime'] -= 1
                    
                    # Shrink particles as they age
                    if 'fade_speed' in particle and 'size' in particle:
                        # Blood pools fade slower
                        if particle.get('is_pool', False):
                            # Only start shrinking in the last third of lifetime
                            if particle['lifetime'] < particle.get('lifetime', 30) / 3:
                                particle['size'] -= particle['fade_speed'] * 0.025
                        else:
                            particle['size'] -= particle['fade_speed'] * 0.05
                
                # Mark dead particles
                if 'lifetime' in particle and particle['lifetime'] <= 0:
                    particles_to_remove.append(i)
                elif 'size' in particle and particle['size'] <= 0:
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
            elif particle.get('is_lightning_bolt', False):
                # For lightning bolt particles
                if particle['lifetime'] <= 0:
                    continue
                
                # Get the points of the bolt
                points = particle['points']
                if not points or len(points) < 2:
                    continue
                
                # Apply camera offset to all points
                offset_points = [(p[0] - camera_offset[0], p[1] - camera_offset[1]) for p in points]
                
                # Draw the main bolt
                color = particle['color']
                thickness = particle['thickness']
                alpha = particle.get('alpha', 255)
                
                if alpha < 255:
                    # Create alpha version of color
                    color = (*color, alpha)
                    
                    # Create a surface with alpha channel
                    bolt_surf = pygame.Surface((800, 600), pygame.SRCALPHA)  # Adjusted size for rendering
                    
                    # Draw the bolt on this surface
                    for i in range(len(offset_points) - 1):
                        pygame.draw.line(
                            bolt_surf,
                            color,
                            (int(offset_points[i][0]), int(offset_points[i][1])),
                            (int(offset_points[i+1][0]), int(offset_points[i+1][1])),
                            thickness
                        )
                    
                    # Draw a brighter center for the glow effect
                    for i in range(len(offset_points) - 1):
                        pygame.draw.line(
                            bolt_surf,
                            (*color[:3], min(255, alpha + 50)),  # Brighter center
                            (int(offset_points[i][0]), int(offset_points[i][1])),
                            (int(offset_points[i+1][0]), int(offset_points[i+1][1])),
                            max(1, thickness // 2)
                        )
                    
                    # Blit the surface onto the main surface
                    surface.blit(bolt_surf, (0, 0))
                else:
                    # Draw the bolt directly on the surface
                    for i in range(len(offset_points) - 1):
                        pygame.draw.line(
                            surface,
                            color,
                            (int(offset_points[i][0]), int(offset_points[i][1])),
                            (int(offset_points[i+1][0]), int(offset_points[i+1][1])),
                            thickness
                        )
                    
                    # Draw a brighter center for the glow effect
                    for i in range(len(offset_points) - 1):
                        pygame.draw.line(
                            surface,
                            (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50)),
                            (int(offset_points[i][0]), int(offset_points[i][1])),
                            (int(offset_points[i+1][0]), int(offset_points[i+1][1])),
                            max(1, thickness // 2)
                        )
            else:
                # For dictionary-based particles
                # Only draw if alive
                if 'lifetime' in particle and particle['lifetime'] <= 0:
                    continue
                if 'size' in particle and particle['size'] <= 0:
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
    
    def create_directional_lightning(self, x, y, angle, amount=10):
        """Create a lightning effect that goes in a specific direction from the source point
        
        Args:
            x, y: Starting position of the lightning
            angle: Direction in radians (0 = right, π = left, π/2 = down, -π/2 = up)
            amount: Number of particles to create
        """
        # Create a few lightning bolts in the specified direction
        for _ in range(min(2, amount)):  # Only 2 main bolts max for cleaner look
            # Create a zigzag lightning bolt with fixed direction
            
            # Use a fixed length of 1.5 tiles (based on TILE_SIZE)
            from config import TILE_SIZE
            bolt_length = TILE_SIZE * 1.5
            
            # Use the provided angle but add a small random variation
            final_angle = angle + random.uniform(-math.pi/12, math.pi/12)  # Small variation (±15 degrees)
            
            # Small random starting position variation
            start_x = x + random.randint(-3, 3)
            start_y = y + random.randint(-3, 3)
            
            # Direction vector based on the angle
            dx = math.cos(final_angle)
            dy = math.sin(final_angle)
            
            # Create a zigzag path with multiple segments
            segments = random.randint(3, 5)
            segment_length = bolt_length / segments
            
            points = [(start_x, start_y)]
            current_x, current_y = start_x, start_y
            
            # Generate zigzag pattern
            for i in range(segments):
                # Alternate zigzag by using multiplier
                zigzag_multiplier = 1 if i % 2 == 0 else -1
                
                # Calculate perpendicular vector for zigzag effect
                # We need the perpendicular to the direction vector (dx, dy)
                # The perpendicular is (-dy, dx)
                perp_x = -dy * random.randint(3, 6) * zigzag_multiplier
                perp_y = dx * random.randint(3, 6) * zigzag_multiplier
                
                # Calculate next point with zigzag
                next_x = current_x + (dx * segment_length) + perp_x
                next_y = current_y + (dy * segment_length) + perp_y
                
                points.append((next_x, next_y))
                current_x, current_y = next_x, next_y
            
            # Choose a blue color for the bolt
            blue_intensity = random.randint(180, 255)
            color = (100, 150, blue_intensity)  # Blue color
            
            # Create the particle object with the bolt path
            bolt_particle = {
                'points': points,
                'color': color,
                'thickness': random.randint(2, 3),
                'lifetime': random.randint(8, 12),
                'alpha': 255,
                'fade_speed': random.uniform(12, 18),
                'is_lightning_bolt': True  # Mark as lightning bolt
            }
            self.particles.append(bolt_particle)
            
            # Add a branch in 50% of cases
            if random.random() < 0.5:
                # Choose a random point on the main bolt to branch from
                if len(points) >= 3:
                    branch_start_idx = random.randint(1, len(points) - 2)
                    branch_start_x = points[branch_start_idx][0]
                    branch_start_y = points[branch_start_idx][1]
                    
                    # Branch angle should stay somewhat in the same direction
                    # but with more variation than the main bolt
                    branch_angle = final_angle + random.uniform(-math.pi/4, math.pi/4)
                    branch_dx = math.cos(branch_angle)
                    branch_dy = math.sin(branch_angle)
                    
                    # Shorter branch
                    branch_length = bolt_length * 0.4  # 40% of main bolt length
                    branch_segments = random.randint(2, 3)
                    branch_segment_length = branch_length / branch_segments
                    
                    # Create branch points
                    branch_points = [(branch_start_x, branch_start_y)]
                    branch_x, branch_y = branch_start_x, branch_start_y
                    
                    for i in range(branch_segments):
                        # Zigzag pattern for branch
                        zigzag_multiplier = 1 if i % 2 == 0 else -1
                        
                        # Add perpendicular jitter - smaller for branches
                        perp_x = -branch_dy * random.randint(2, 4) * zigzag_multiplier
                        perp_y = branch_dx * random.randint(2, 4) * zigzag_multiplier
                        
                        branch_x += branch_dx * branch_segment_length + perp_x
                        branch_y += branch_dy * branch_segment_length + perp_y
                        
                        branch_points.append((branch_x, branch_y))
                    
                    # Create branch bolt with slightly different color
                    branch_color = (120, 180, blue_intensity - 20)
                    branch_particle = {
                        'points': branch_points,
                        'color': branch_color,
                        'thickness': random.randint(1, 2),  # Thinner than main
                        'lifetime': random.randint(5, 8),
                        'alpha': 255,
                        'fade_speed': random.uniform(15, 20),
                        'is_lightning_bolt': True
                    }
                    self.particles.append(branch_particle)
        
        # Add a few spark particles
        for _ in range(amount // 2):
            # Create sparks that generally follow the main direction
            speed = random.uniform(1.0, 2.5)
            
            # Spark angle should be close to the main direction but with some variation
            spark_angle = angle + random.uniform(-math.pi/3, math.pi/3)  # ±60° variation
            velocity_x = math.cos(spark_angle) * speed
            velocity_y = math.sin(spark_angle) * speed
            
            lifetime = random.randint(3, 8)
            size = random.randint(1, 2)  # Smaller particles
            
            # Lightning colors
            lightning_colors = [
                (255, 255, 255),   # White
                (200, 235, 255),   # Light blue white
                (150, 200, 255),   # Light blue
            ]
            
            # Create a spark particle
            particle = {
                'x': x + random.randint(-3, 3),  # Very small spread
                'y': y + random.randint(-3, 3),  # Very small spread
                'velocity_x': velocity_x,
                'velocity_y': velocity_y,
                'color': random.choice(lightning_colors),
                'size': size,
                'lifetime': lifetime,
                'alpha': 255,
                'gravity': 0,
                'fade_speed': random.uniform(10, 15)
            }
            self.particles.append(particle) 