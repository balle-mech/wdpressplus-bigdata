import time
import tracemalloc

# --- return を使った関数 ---
def use_return():
    return [i for i in range(1000000)]

# --- yield を使った関数 ---
def use_yield():
    for i in range(1000000):
        yield i

# --- 測定用関数 ---
def measure_memory(func, is_generator=False):
    print(f"\n--- {func.__name__} ---")
    tracemalloc.start()  # メモリ使用量の測定開始
    start = time.time()

    total = 0
    if is_generator:
        for value in func():
            total += value
    else:
        data = func()
        for value in data:
            total += value

    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"合計値: {total}")
    print(f"処理時間: {end - start:.2f}秒")
    print(f"ピークメモリ使用量: {peak / 10**6:.2f} MB")

# --- 実行 ---
measure_memory(use_return, is_generator=False)
measure_memory(use_yield, is_generator=True)
