import json

def read_json(filename):
	"""'filename' is the unique argument. Opens a json file named filename in a pythonic format (dict)"""
	with open(f"dados/{filename}.json") as f:
		data = json.load(f)
	return data

def write_json(data, filename):
	"""Takes 'data' as first argument, and then 'filename' as second argument. Data is saved to file in json format."""
	with open(f"dados/{filename}.json", "w") as f:
		json.dump(data, f, indent=4)