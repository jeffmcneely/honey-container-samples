import os
import time
import random
import multiprocessing as mp


PHASE_MIN_SECONDS = int(os.getenv("PHASE_MIN_SECONDS", "5"))
PHASE_MAX_SECONDS = int(os.getenv("PHASE_MAX_SECONDS", "30"))

MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "512"))
CPU_WORKERS = int(os.getenv("CPU_WORKERS", str(os.cpu_count() or 2)))


def cpu_burn(stop_event):
    x = 0
    while not stop_event.is_set():
        x = (x * 3 + 1) % 1000003


def run_cpu_phase(duration, workers):
    print(f"CPU phase: {duration}s, workers={workers}", flush=True)

    stop_event = mp.Event()
    procs = []

    for _ in range(workers):
        p = mp.Process(target=cpu_burn, args=(stop_event,))
        p.start()
        procs.append(p)

    time.sleep(duration)

    stop_event.set()

    for p in procs:
        p.join()


def run_memory_phase(duration, memory_mb):
    print(f"Memory phase: {duration}s, memory={memory_mb}MB", flush=True)

    chunks = []
    chunk_size = 10 * 1024 * 1024

    for _ in range(max(1, memory_mb // 10)):
        chunks.append(bytearray(chunk_size))
        time.sleep(0.2)

    time.sleep(duration)

    chunks.clear()


def run_mixed_phase(duration, memory_mb, workers):
    print(
        f"Mixed phase: {duration}s, memory={memory_mb}MB, workers={workers}",
        flush=True,
    )

    stop_event = mp.Event()
    procs = []

    for _ in range(workers):
        p = mp.Process(target=cpu_burn, args=(stop_event,))
        p.start()
        procs.append(p)

    chunks = []
    chunk_size = 10 * 1024 * 1024

    for _ in range(max(1, memory_mb // 10)):
        chunks.append(bytearray(chunk_size))
        time.sleep(0.1)

    time.sleep(duration)

    chunks.clear()
    stop_event.set()

    for p in procs:
        p.join()


def run_idle_phase(duration):
    print(f"Idle phase: {duration}s", flush=True)
    time.sleep(duration)


def random_duration():
    return random.randint(PHASE_MIN_SECONDS, PHASE_MAX_SECONDS)


def main():
    print("Starting variable workload generator", flush=True)

    while True:
        phase = random.choice(["idle", "cpu", "memory", "mixed"])

        duration = random_duration()
        memory_mb = random.randint(64, MAX_MEMORY_MB)
        workers = random.randint(1, CPU_WORKERS)

        if phase == "idle":
            run_idle_phase(duration)
        elif phase == "cpu":
            run_cpu_phase(duration, workers)
        elif phase == "memory":
            run_memory_phase(duration, memory_mb)
        elif phase == "mixed":
            run_mixed_phase(duration, memory_mb, workers)


if __name__ == "__main__":
    main()