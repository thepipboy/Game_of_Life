import numpy as np
import cv2
import random
from enum import IntEnum

class CellState(IntEnum):
    EMPTY = 0
    SAND = 1
    WATER = 2
    PLANT = 3
    FIRE = 4
    LAVA = 5
    STONE = 6

class CellularAutomaton:
    def __init__(self, width=200, height=200):
        self.width = width
        self.height = height
        self.grid = np.zeros((height, width), dtype=np.uint8)
        self.initialize_grid()
        self.colors = {
            CellState.EMPTY: (0, 0, 0),
            CellState.SAND: (210, 190, 120),
            CellState.WATER: (30, 144, 255),
            CellState.PLANT: (34, 139, 34),
            CellState.FIRE: (255, 69, 0),
            CellState.LAVA: (207, 16, 32),
            CellState.STONE: (128, 128, 128)
        }
        self.paused = False
        self.brush_size = 3
        self.brush_type = CellState.SAND
        self.initialize_random()

    def initialize_grid(self):
        # Create initial patterns
        self.grid.fill(CellState.EMPTY)
        
        # Create sand dunes
        for _ in range(10):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height//2)
            self.create_blob(x, y, CellState.SAND, 15)
        
        # Create water pools
        for _ in range(5):
            x, y = random.randint(0, self.width-1), random.randint(self.height//2, self.height-1)
            self.create_blob(x, y, CellState.WATER, 10)
        
        # Create plants
        for _ in range(20):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            if self.grid[y, x] == CellState.EMPTY:
                self.grid[y, x] = CellState.PLANT
        
        # Create stone formations
        for _ in range(7):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            self.create_blob(x, y, CellState.STONE, 8)

    def initialize_random(self):
        # Random initialization for quick start
        for _ in range(3000):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            self.grid[y, x] = random.choice(list(CellState)[1:])  # Exclude EMPTY

    def create_blob(self, x, y, cell_type, size):
        for i in range(-size, size):
            for j in range(-size, size):
                if (i*i + j*j) < size*size:
                    nx, ny = x + i, y + j
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if random.random() > 0.3:  # Create organic shapes
                            self.grid[ny, nx] = cell_type

    def update(self):
        if self.paused:
            return
            
        new_grid = self.grid.copy()
        
        for y in range(self.height-1, -1, -1):
            for x in range(self.width):
                cell = self.grid[y, x]
                
                # Skip empty cells
                if cell == CellState.EMPTY:
                    continue
                
                # Physics for SAND
                if cell == CellState.SAND:
                    self.move_sand(new_grid, x, y)
                
                # Physics for WATER
                elif cell == CellState.WATER:
                    self.move_water(new_grid, x, y)
                
                # Plant growth and fire interaction
                elif cell == CellState.PLANT:
                    self.grow_plants(new_grid, x, y)
                
                # Fire physics
                elif cell == CellState.FIRE:
                    self.spread_fire(new_grid, x, y)
                
                # Lava physics
                elif cell == CellState.LAVA:
                    self.flow_lava(new_grid, x, y)
        
        self.grid = new_grid

    def move_sand(self, new_grid, x, y):
        # Sand falls down or diagonally
        below = (x, y+1)
        dirs = [(x-1, y+1), (x+1, y+1), (x, y+1)]
        random.shuffle(dirs)
        
        for nx, ny in dirs:
            if 0 <= nx < self.width and ny < self.height:
                if new_grid[ny, nx] == CellState.EMPTY or new_grid[ny, nx] == CellState.WATER:
                    new_grid[y, x] = new_grid[ny, nx]  # Swap positions
                    new_grid[ny, nx] = CellState.SAND
                    return

    def move_water(self, new_grid, x, y):
        # Water flows down, then sideways
        below = (x, y+1)
        sides = [(x-1, y), (x+1, y)]
        down_sides = [(x-1, y+1), (x+1, y+1)]
        random.shuffle(sides)
        random.shuffle(down_sides)
        
        # Try to move down
        for nx, ny in [below] + down_sides:
            if 0 <= nx < self.width and ny < self.height:
                if new_grid[ny, nx] == CellState.EMPTY:
                    new_grid[y, x] = CellState.EMPTY
                    new_grid[ny, nx] = CellState.WATER
                    return
        
        # Try to move sideways
        for nx, ny in sides:
            if 0 <= nx < self.width:
                if new_grid[ny, nx] == CellState.EMPTY:
                    new_grid[y, x] = CellState.EMPTY
                    new_grid[ny, nx] = CellState.WATER
                    return

    def grow_plants(self, new_grid, x, y):
        # Plants can grow upward and to sides
        if y > 0 and random.random() < 0.01:
            dirs = [(x, y-1), (x-1, y), (x+1, y)]
            random.shuffle(dirs)
            
            for nx, ny in dirs:
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if new_grid[ny, nx] == CellState.EMPTY:
                        new_grid[ny, nx] = CellState.PLANT
        
        # Plants catch fire when near lava or fire
        neighbors = self.get_neighbors(x, y)
        if CellState.LAVA in neighbors or CellState.FIRE in neighbors:
            if random.random() < 0.3:
                new_grid[y, x] = CellState.FIRE

    def spread_fire(self, new_grid, x, y):
        # Fire spreads to adjacent plants
        neighbors = self.get_neighbors(x, y)
        for nx, ny in neighbors:
            if new_grid[ny, nx] == CellState.PLANT and random.random() < 0.4:
                new_grid[ny, nx] = CellState.FIRE
        
        # Fire may turn to smoke (empty) or be extinguished by water
        if CellState.WATER in self.get_neighbors(x, y, True):
            new_grid[y, x] = CellState.EMPTY
        elif random.random() < 0.1:
            new_grid[y, x] = CellState.EMPTY

    def flow_lava(self, new_grid, x, y):
        # Lava flows like sand but can set things on fire
        below = (x, y+1)
        dirs = [(x-1, y+1), (x+1, y+1), (x, y+1)]
        random.shuffle(dirs)
        
        for nx, ny in dirs:
            if 0 <= nx < self.width and ny < self.height:
                target = new_grid[ny, nx]
                
                if target == CellState.EMPTY:
                    new_grid[y, x] = CellState.EMPTY
                    new_grid[ny, nx] = CellState.LAVA
                    return
                elif target == CellState.WATER:
                    new_grid[y, x] = CellState.STONE
                    new_grid[ny, nx] = CellState.STONE
                    return
                elif target == CellState.PLANT:
                    new_grid[ny, nx] = CellState.FIRE

    def get_neighbors(self, x, y, include_diagonals=True):
        neighbors = []
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if include_diagonals:
            dirs += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny, self.grid[ny, nx]))
        
        return [state for _, _, state in neighbors]

    def render(self):
        # Create RGB image
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for y in range(self.height):
            for x in range(self.width):
                img[y, x] = self.colors[self.grid[y, x]]
        
        # Scale up for better visualization
        return cv2.resize(img, (800, 800), interpolation=cv2.INTER_NEAREST)

    def draw_with_brush(self, x, y):
        for i in range(-self.brush_size, self.brush_size+1):
            for j in range(-self.brush_size, self.brush_size+1):
                nx, ny = x + i, y + j
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if i*i + j*j <= self.brush_size*self.brush_size:
                        self.grid[ny, nx] = self.brush_type

# Main simulation loop
def main():
    automaton = CellularAutomaton(200, 200)
    cv2.namedWindow("Automatic Cell Machine")
    
    print("Controls:")
    print("SPACE: Pause/Resume")
    print("R: Reset simulation")
    print("C: Clear grid")
    print("1-7: Select cell type")
    print("Mouse: Draw on grid")
    print("+/-: Change brush size")
    print("ESC: Exit")
    
    while True:
        img = automaton.render()
        cv2.imshow("Automatic Cell Machine", img)
        
        automaton.update()
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == ord(' '):
            automaton.paused = not automaton.paused
        elif key == ord('r'):
            automaton.initialize_grid()
        elif key == ord('c'):
            automaton.grid.fill(CellState.EMPTY)
        elif key == ord('+'):
            automaton.brush_size = min(10, automaton.brush_size + 1)
        elif key == ord('-'):
            automaton.brush_size = max(1, automaton.brush_size - 1)
        elif key in [ord(str(i)) for i in range(1, 8)]:
            automaton.brush_type = CellState(int(key) - 49)  # Convert key to enum
        
        # Mouse drawing
        mouse_x, mouse_y = cv2.getWindowImageRect("Automatic Cell Machine")[:2]
        mouse_events = [cv2.EVENT_LBUTTONDOWN, cv2.EVENT_MOUSEMOVE]
        
        def mouse_callback(event, x, y, flags, param):
            if event in mouse_events and flags & cv2.EVENT_FLAG_LBUTTON:
                # Scale mouse coordinates to grid
                grid_x = int(x * automaton.width / 800)
                grid_y = int(y * automaton.height / 800)
                automaton.draw_with_brush(grid_x, grid_y)
        
        cv2.setMouseCallback("Automatic Cell Machine", mouse_callback)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()