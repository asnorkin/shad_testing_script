# shad_testing_script

python3.5 -m pip install pytest==2.9.0

python3.5 -m pytest test_shad.py --solutions "<solution_file> <solution_file> ..." --iterations <number_of_iterations> [--input="<input_file>"] 

<input_file> -- it is a file where each line is an input for next test iteration

if --input option is not specified then you have to implement user_input_generator func in input_generation.py
