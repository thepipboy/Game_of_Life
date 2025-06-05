import cv2
import numpy as np

# Initialize webcam
cap = cv2.VideoCapture(0)
cv2.namedWindow('Block Art Generator')

# Interactive parameters
block_size = 20
color_intensity = 5
mode = 0  # 0: Normal, 1: Warp, 2: Psychedelic

def update_block_size(val):
    global block_size
    block_size = max(5, val)

def update_color_intensity(val):
    global color_intensity
    color_intensity = max(1, val)

# Create trackbars
cv2.createTrackbar('Block Size', 'Block Art Generator', block_size, 100, update_block_size)
cv2.createTrackbar('Color Intensity', 'Block Art Generator', color_intensity, 20, update_color_intensity)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert to block art
    height, width = frame.shape[:2]
    
    # Downscale for block effect
    small = cv2.resize(frame, 
                      (width // block_size, height // block_size),
                      interpolation=cv2.INTER_NEAREST)
    
    # Upscale back to original size
    blocky = cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)
    
    # Apply artistic effects based on mode
    if mode == 1:
        # Warp effect
        map_x = np.float32([[(x + 30*np.sin(y/20)) % width for x in range(width)] for y in range(height)])
        map_y = np.float32([[(y + 30*np.cos(x/20)) % height for x in range(width)] for y in range(height)])
        blocky = cv2.remap(blocky, map_x, map_y, cv2.INTER_CUBIC)
    elif mode == 2:
        # Psychedelic color shift
        hsv = cv2.cvtColor(blocky, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + color_intensity * 10) % 180
        hsv[:, :, 1] = np.minimum(hsv[:, :, 1] * color_intensity, 255)
        blocky = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    # Display instructions
    cv2.putText(blocky, f'M: Change Mode (Current: {["Normal", "Warp", "Psychedelic"][mode]})', 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(blocky, 'ESC: Exit', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Show result
    cv2.imshow('Block Art Generator', blocky)
    
    # Handle key presses
    key = cv2.waitKey(1)
    if key == 27:  # ESC
        break
    elif key == ord('m'):
        mode = (mode + 1) % 3

cap.release()
cv2.destroyAllWindows()