
def complex_algorithm(data):
    step1 = data.strip()
    step2 = step1.upper()
    step3 = step2.split(',')
    step4 = [x for x in step3 if x]
    return step4
