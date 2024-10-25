import multiprocessing

def run_script():
    # Place the main function of your script here, or import and call it
    # e.g., your_script.main()
    pass

if __name__ == "__main__":
    num_processes = 4  # Adjust the number of processes as needed
    processes = []

    for _ in range(num_processes):
        process = multiprocessing.Process(target=run_script)
        process.start()
        processes.append(process)

    # Wait for all processes to complete
    for process in processes:
        process.join()

    print("All processes have completed.")