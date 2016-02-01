
def evaluate_expr(expresion):
	fifostack = [] # list working as fifo stack
	counter_dict = {"(":")", "[":"]", "{":"}" }

	for char in expresion:
        last_element = fifostack[-1] # get last element
		if char in counter_dict: # python dictionaries are hashed, O(1), checks if char in keys
			fifostack.append(char)
        else:
		    if char == counter_dict[last_element]:
                fifostack.pop(-1)
            else return False
    if len(fifostack) != 0:
        return False
    return True