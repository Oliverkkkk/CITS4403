# path.py
# 简单版本：生成水与陆地网格，并提供打印函数。

import random

def generate_grid(width=10, height=10, water_ratio=0.3, seed=None):
    """
    生成一个二维网格，True 表示水，False 表示陆地。
    """
    if seed is not None:
        random.seed(seed)
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            # 根据比例随机分配水或陆地
            row.append(random.random() < water_ratio)  # True=水, False=陆地
        grid.append(row)
    return grid

def print_grid(grid):
    """
    控制台打印网格：~ 表示水，. 表示陆地
    """
    for row in grid:
        line = ''.join('~' if cell else '.' for cell in row)
        print(line)

# 示例用法（直接运行 path.py 时）
if __name__ == "__main__":
    g = generate_grid(width=8, height=6, water_ratio=0.4, seed=42)
    print_grid(g)
