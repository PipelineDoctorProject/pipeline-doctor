def normalize_dtype(dtype):

    dtype = str(dtype).lower()

    if "int" in dtype:
        return "int"

    elif "float" in dtype:
        return "float"

    elif "bool" in dtype:
        return "bool"

    elif "datetime" in dtype:
        return "datetime"

    else:
        return "object"