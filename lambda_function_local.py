# To run:
# $ python lambda_function_local.py sudoku_01.txt 

import lambda_function

if __name__ == '__main__':
    print(lambda_function.solve_sudoku(file_location='data/sudoku_01.txt'))
