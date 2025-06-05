import pygame
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import time

# Initialize pygame
pygame.init()
width, height = 1000, 700
pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D Conway's Game of Life")

# Set grid dimensions
GRID_SIZE = 12
CELL_SIZE = 1.0

# Colors
BACKGROUND = (0.1, 0.1, 0.15, 1.0)
GRID_COLOR = (0.2, 0.2, 0.3, 0.6)
ALIVE_COLOR = (0.2, 0.8, 0.6, 1.0)
NEW_CELL_COLOR = (0.9, 0.4, 0.2, 1.0)
DYING_CELL_COLOR = (0.6, 0.1, 0.4, 1.0)
UI_COLOR = (0.9, 0.9, 1.0, 1.0)

# Camera settings
camera_distance = 25.0
camera_x, camera_y = 0, 0
rotation_x, rotation_y = 30, 30
dragging = False
last_mouse_x, last_mouse_y = 0, 0

# Simulation control
paused = False
generation = 0
generation_time = 0.5
last_update = 0
grid = None
new_grid = None

def init_grid():
    """Initialize a random 3D grid"""
    global grid, new_grid, generation
    grid = np.zeros((GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=np.int8)
    
    # Create a random initial pattern
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for z in range(GRID_SIZE):
                if np.random.random() > 0.85:
                    grid[x, y, z] = 1
    
    new_grid = np.copy(grid)
    generation = 0

def count_neighbors(x, y, z):
    """Count the number of alive neighbors for a cell"""
    count = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                
                nx, ny, nz = x + dx, y + dy, z + dz
                
                # Check boundaries
                if (0 <= nx < GRID_SIZE and 
                    0 <= ny < GRID_SIZE and 
                    0 <= nz < GRID_SIZE):
                    count += grid[nx, ny, nz]
    return count

def update_grid():
    """Update the grid based on Conway's Game of Life rules"""
    global grid, new_grid, generation
    if paused:
        return
    
    new_grid = np.copy(grid)
    changes = 0
    
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for z in range(GRID_SIZE):
                neighbors = count_neighbors(x, y, z)
                
                # Apply Conway's Game of Life rules
                if grid[x, y, z] == 1:  # Cell is alive
                    if neighbors < 2 or neighbors > 5:
                        new_grid[x, y, z] = -1  # Dying
                        changes += 1
                else:  # Cell is dead
                    if neighbors == 3:
                        new_grid[x, y, z] = 2  # Newborn
                        changes += 1
    
    grid = np.where(new_grid > 0, 1, 0)
    generation += 1
    
    # If no changes, randomize to avoid stagnation
    if changes == 0:
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                for z in range(GRID_SIZE):
                    if np.random.random() > 0.99:
                        grid[x, y, z] = 1

def draw_cube(x, y, z, state):
    """Draw a cube at the given position"""
    # Define cube vertices
    s = CELL_SIZE / 2
    vertices = [
        [x-s, y-s, z-s], [x+s, y-s, z-s], [x+s, y+s, z-s], [x-s, y+s, z-s],
        [x-s, y-s, z+s], [x+s, y-s, z+s], [x+s, y+s, z+s], [x-s, y+s, z+s]
    ]
    
    # Define cube faces
    faces = [
        [0, 1, 2, 3], [3, 2, 6, 7], [7, 6, 5, 4],
        [4, 5, 1, 0], [0, 3, 7, 4], [1, 5, 6, 2]
    ]
    
    # Set color based on cell state
    if state == 1:  # Alive
        color = ALIVE_COLOR
    elif state == 2:  # Newborn
        color = NEW_CELL_COLOR
    elif state == -1:  # Dying
        color = DYING_CELL_COLOR
    else:
        return
    
    # Draw the cube
    glBegin(GL_QUADS)
    glColor4f(*color)
    for face in faces:
        for vertex in face:
            glVertex3f(vertices[vertex][0], vertices[vertex][1], vertices[vertex][2])
    glEnd()

def draw_grid_lines():
    """Draw the grid lines for reference"""
    glBegin(GL_LINES)
    glColor4f(*GRID_COLOR)
    
    # Draw grid lines
    for i in range(GRID_SIZE + 1):
        offset = i - GRID_SIZE/2
        # X-axis lines
        glVertex3f(offset, -GRID_SIZE/2, -GRID_SIZE/2)
        glVertex3f(offset, -GRID_SIZE/2, GRID_SIZE/2)
        glVertex3f(offset, GRID_SIZE/2, -GRID_SIZE/2)
        glVertex3f(offset, GRID_SIZE/2, GRID_SIZE/2)
        
        # Y-axis lines
        glVertex3f(-GRID_SIZE/2, offset, -GRID_SIZE/2)
        glVertex3f(GRID_SIZE/2, offset, -GRID_SIZE/2)
        glVertex3f(-GRID_SIZE/2, offset, GRID_SIZE/2)
        glVertex3f(GRID_SIZE/2, offset, GRID_SIZE/2)
        
        # Z-axis lines
        glVertex3f(-GRID_SIZE/2, -GRID_SIZE/2, offset)
        glVertex3f(GRID_SIZE/2, -GRID_SIZE/2, offset)
        glVertex3f(-GRID_SIZE/2, GRID_SIZE/2, offset)
        glVertex3f(GRID_SIZE/2, GRID_SIZE/2, offset)
    
    glEnd()

def draw_ui():
    """Draw UI elements on screen"""
    # Switch to 2D projection for UI
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, height, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable depth test for UI
    glDisable(GL_DEPTH_TEST)
    
    # Draw semi-transparent background for UI
    glBegin(GL_QUADS)
    glColor4f(0.1, 0.1, 0.15, 0.7)
    glVertex2f(10, 10)
    glVertex2f(300, 10)
    glVertex2f(300, 180)
    glVertex2f(10, 180)
    glEnd()
    
    # Draw UI text
    font = pygame.font.SysFont('Arial', 20)
    
    texts = [
        f"Generation: {generation}",
        f"Grid: {GRID_SIZE}x{GRID_SIZE}x{GRID_SIZE}",
        "Controls:",
        "P - Pause/Resume simulation",
        "R - Reset grid",
        "C - Clear grid",
        "Mouse - Rotate view",
        "Wheel - Zoom in/out",
        "Arrow keys - Move view"
    ]
    
    # Draw each line of text
    for i, text in enumerate(texts):
        text_surface = font.render(text, True, UI_COLOR)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glRasterPos2f(20, 30 + i*25)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), 
                     GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    
    # Draw status
    status = "PAUSED" if paused else "RUNNING"
    status_color = (1.0, 0.3, 0.3, 1.0) if paused else (0.3, 1.0, 0.5, 1.0)
    status_surface = font.render(f"Status: {status}", True, status_color)
    status_data = pygame.image.tostring(status_surface, "RGBA", True)
    glRasterPos2f(20, 180)
    glDrawPixels(status_surface.get_width(), status_surface.get_height(), 
                 GL_RGBA, GL_UNSIGNED_BYTE, status_data)
    
    # Restore 3D settings
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def setup_perspective():
    """Set up the perspective projection"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (width / height), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def handle_input():
    """Handle keyboard and mouse input"""
    global paused, camera_distance, rotation_x, rotation_y, camera_x, camera_y, last_update, generation_time
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        
        # Keyboard events
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused
            elif event.key == pygame.K_r:
                init_grid()
            elif event.key == pygame.K_c:
                grid.fill(0)
            elif event.key == pygame.K_UP:
                camera_y += 1
            elif event.key == pygame.K_DOWN:
                camera_y -= 1
            elif event.key == pygame.K_LEFT:
                camera_x -= 1
            elif event.key == pygame.K_RIGHT:
                camera_x += 1
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                generation_time = max(0.1, generation_time - 0.1)
            elif event.key == pygame.K_MINUS:
                generation_time += 0.1
        
        # Mouse events
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left button
                global dragging, last_mouse_x, last_mouse_y
                dragging = True
                last_mouse_x, last_mouse_y = event.pos
            elif event.button == 4:  # Scroll up
                camera_distance = max(10, camera_distance - 1)
            elif event.button == 5:  # Scroll down
                camera_distance = min(50, camera_distance + 1)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left button
                dragging = False
        
        elif event.type == pygame.MOUSEMOTION and dragging:
            dx, dy = event.pos[0] - last_mouse_x, event.pos[1] - last_mouse_y
            rotation_y += dx * 0.3
            rotation_x += dy * 0.3
            rotation_x = max(-90, min(90, rotation_x))  # Clamp vertical rotation
            last_mouse_x, last_mouse_y = event.pos

def main():
    global last_update, grid, new_grid
    
    # Initialize grid
    init_grid()
    
    # Set up OpenGL
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glClearColor(*BACKGROUND)
    
    # Main loop
    clock = pygame.time.Clock()
    
    while True:
        current_time = pygame.time.get_ticks() / 1000.0
        
        # Handle input
        handle_input()
        
        # Update grid at regular intervals
        if current_time - last_update > generation_time:
            update_grid()
            last_update = current_time
        
        # Clear screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up camera
        setup_perspective()
        glLoadIdentity()
        glTranslatef(0, 0, -camera_distance)
        glRotatef(rotation_x, 1, 0, 0)
        glRotatef(rotation_y, 0, 1, 0)
        glTranslatef(camera_x, camera_y, 0)
        
        # Draw grid lines
        draw_grid_lines()
        
        # Draw cells
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                for z in range(GRID_SIZE):
                    if grid[x, y, z] == 1 or new_grid[x, y, z] != 0:
                        # Convert grid coordinates to world coordinates
                        world_x = x - GRID_SIZE/2 + 0.5
                        world_y = y - GRID_SIZE/2 + 0.5
                        world_z = z - GRID_SIZE/2 + 0.5
                        state = new_grid[x, y, z] if new_grid[x, y, z] != 0 else 1
                        draw_cube(world_x, world_y, world_z, state)
        
        # Draw UI
        draw_ui()
        
        # Update display
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
