# Shad Testing Script

Simple testing tool that allows to test few solutions of one task on different inputs and check that their outputs are equal.  
Also it allows to check time and memory performance.

## Usage

python -m pytest test_shad.py --solutions="<solution_file_path> <solution_file_path> ..." [--timeout=<timeout_in_seconds>] [--memory=<memory_limit_in_bytes>] [--iterations=<number_of_iterations>] [--input=<input_file_path>] [--log=<log_level>]
  
python3.5 -m pytest test_shad.py --solutions "main.cpp naive.cpp" --timeout=0.5 --memory=65536 --iterations=1000

Each line of input file should contain input for one run of solutions.

If --input option is not specified then you should implement user_input_generator func in input_generation.py.
