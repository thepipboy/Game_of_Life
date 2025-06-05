import pygame
import numpy as np
import time

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 10
COLS, ROWS = WIDTH // CELL_SIZE, HEIGHT // CELL_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

# Create screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Conway's Game of Life")

def create_grid():
    """Initialize a random grid"""
    return np.random.choice([0, 1], size=(ROWS, COLS))

def count_neighbors(grid, row, col):
    """Count live neighbors with wrap-around boundaries"""
    count = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            # Wrap around edges
            r = (row + i) % ROWS
            c = (col + j) % COLS
            count += grid[r][c]
    return count

def update_grid(grid):
    """Apply Conway's Game of Life rules"""
    new_grid = grid.copy()
    for row in range(ROWS):
        for col in range(COLS):
            neighbors = count_neighbors(grid, row, col)
            
            # Apply rules
            if grid[row][col] == 1:  # Live cell
                if neighbors < 2 or neighbors > 3:
                    new_grid[row][col] = 0
            else:  # Dead cell
                if neighbors == 3:
                    new_grid[row][col] = 1
    return new_grid

def draw_grid(grid):
    """Render the grid to the screen"""
    screen.fill(BLACK)
    for row in range(ROWS):
        for col in range(COLS):
            if grid[row][col] == 1:
                pygame.draw.rect(screen, WHITE, 
                                (col * CELL_SIZE, row * CELL_SIZE, 
                                 CELL_SIZE - 1, CELL_SIZE - 1))
    
    # Draw grid lines
    for x in range(0, WIDTH, CELL_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (WIDTH, y), 1)
    
    pygame.display.flip()

def main():
    grid = create_grid()
    running = True
    paused = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_r:
                    grid = create_grid()
                if event.key == pygame.K_c:
                    grid = np.zeros((ROWS, COLS))
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                col, row = pos[0] // CELL_SIZE, pos[1] // CELL_SIZE
                grid[row][col] = 1 - grid[row][col]  # Toggle cell state
        
        if not paused:
            grid = update_grid(grid)
        
        draw_grid(grid)
        time.sleep(0.1)  # Control simulation speed
    
    pygame.quit()

if __name__ == "__main__":
    main()