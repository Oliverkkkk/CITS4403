import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

H, W = 25, 25

def make_maps(H, W):
    # vegetation: 随机 0..4
    veg = np.random.choice([0,1,2,3,4], size=(H, W),
                           p=[0.4,0.2,0.15,0.15,0.1]).astype(np.int16)
    np.savetxt("veg_25x25.csv", veg, fmt="%d", delimiter=",")

    # river: 中间一条竖向正弦弯曲
    river = np.zeros((H, W), dtype=bool)
    thickness = 2
    cx = W // 2
    for y in range(H):
        rx = int(cx + 2*np.sin(2*np.pi*y/max(1,H)))
        xL, xR = max(0, rx - thickness//2), min(W, rx + (thickness+1)//2)
        river[y, xL:xR] = True
    np.savetxt("river_25x25.csv", river.astype(int), fmt="%d", delimiter=",")

    return veg, river

def visualize(veg, river):
    fig, ax = plt.subplots(1,2, figsize=(8,4))
    ax[0].imshow(veg, cmap="Greens", origin="upper")
    ax[0].set_title("Vegetation (0-4)")
    ax[1].imshow(river, cmap="Blues", origin="upper")
    ax[1].set_title("River (mask)")
    plt.show()

if __name__ == "__main__":
    veg, river = make_maps(H, W)
    print("veg shape:", veg.shape, "min:", veg.min(), "max:", veg.max())
    print("river shape:", river.shape, "cells of river:", river.sum())
    visualize(veg, river)

    # 另存为 PNG（方便 GUI 加载）
    Image.fromarray((veg/4.0*255).astype(np.uint8), mode="L").save("veg_25x25.png")
    Image.fromarray((river*255).astype(np.uint8), mode="L").save("river_25x25.png")
