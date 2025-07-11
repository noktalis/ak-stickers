from datetime import date, datetime
import json
import re

class Sticker:

	def __init__(self, key: int, name: str,
			  			href: str = "",
						alt: str = "Alternative text",
						caption: str = None):
		self.key = key
		self.name = name
		self.href = href
		self.alt = alt
		self.caption = caption

	def to_dict(self):
		return {
			"key": self.key,
			"name": self.name,
			"href": self.href,
			"alt": self.alt,
			"caption": self.caption
		}

class StickerPack:

	def __init__(self, pack, 
			  			fullname, 
						cn_date: date = None,
						cn_src: str = None,
						en_date: date = None,
						en_src: str = None,
						tmbr_src1: str = None,
						tmbr_src2: str = None,
						src: str = None,
						src_text: str = None,
						featured: list[str] = [],
						aliases: list[str] = [],
						note: str = None,
						stickers: list[Sticker] = []):
		
		self.pack: str 			= pack
		self.fullname: str 		= fullname
		self.cn_date: date		= cn_date
		self.cn_src: str		= cn_src
		self.en_date: date		= en_date
		self.en_src: str		= en_src
		self.tumblr1: str		= tmbr_src1
		self.tumblr2: str		= tmbr_src2
		self.src: str			= src
		self.src_text: str		= src_text
		self.featured: list[str]= featured
		self.aliases: list[str]	= aliases
		self.note: str			= note
		self.stickers: list[Sticker]	= stickers
		
		self.sticker_count = len(self.stickers) # key of next sticker

		# if cn_date exists, get year. else, set as None and raise flag
		# TODO: raise flag
		self.year: int = None
		if cn_date is not None:
			self.year = self.cn_date.year

	def to_dict(self):
		onEN = self.en_date is not None
		return {
			"pack": self.pack,
			"fullname": self.fullname,
			"cn-date": self.cn_date.isoformat(),
			"cn-src": self.cn_src,
			"en-date":(self.en_date.isoformat() if onEN else None),
			"en-src":self.en_src,
			"tumblr-source1": self.tumblr1,
			"tumblr-source2": self.tumblr2,
			"src": self.src,
			"src-text": self.src_text,
			"featured": self.featured,
			"search": self.aliases,
			"note": self.note,
			"stickers": [sticker.to_dict() for sticker in self.stickers]
		}
	
	def add_new_sticker(self, name, alt: str = "Alternative text", caption: str = None):
		# concat link to sticker
		href = "https://noktalis.github.io/ak-stickers/" + str(self.year) + "/" + self.pack + "/" + name + ".png"

		# create new sticker obj
		new_sticker = Sticker(self.sticker_count, name, href, alt, caption)

		# add to pack obj list
		self.stickers.append(new_sticker)
		self.sticker_count = len(self.stickers) # update

class Parser:

	def __init__(self, year: int, pack_name: str, pack_fullname: str):

		self.URL = str(year) + "/" + pack_name + "/README.txt"

		# read txt file for data
		self.data = None
		with open(self.URL, 'r', encoding='utf-8') as f:
			temp = f.readlines()
			temp = [item.strip() for item in temp]
			self.data = list(filter(None, temp))
		f.close()

		# remove some non-data lines
		remove = ['(if sheet from Oyuki twitter)',
					'Sticker sheet downloaded from @oyuki_gms',
					'https://twitter.com/oyuki_gms',
					'(@arknights-archive on tumblr)',
					'Stickers from @arknights-archive on tumblr',
					'(if stickers edited and cropped myself)',
					'Stickers edited by Nat',
					'https://www.arknights.global/fankit']
		self.data = [x for x in self.data if x not in remove]

		# default values for some optional attributes
		self.en_date = None
		self.en_src = None

		# process all lines
		i = 0
		while i < len(self.data):
			line = self.data[i]
			
			# Extract CN release date and source link
			if "Released to CN" in line:
				# extract string in iso format
				date_str: str = re.search(r"\b[A-Z][a-zA-Z]*\b \d{1,2},\s\d{4}", line)

				# convert to date obj
				self.cn_date = datetime.strptime(date_str.group(),'%B %d, %Y').date()

				# next line should be a link?
				i += 1
				self.cn_src = self.data[i]
			# Extract EN release date
			elif "Released to EN" in line:
				# extract string in iso format
				date_str: str = re.search(r"\b[A-Z][a-zA-Z]*\b \d{1,2},\s\d{4}", line)

				# convert to date obj
				self.en_date = datetime.strptime(date_str.group(),'%B %d, %Y').date()

				# next line should be a link?
				i += 1
				self.en_src = self.data[i]
			# Extract Tumblr links
			elif "https://arknights-archive.tumblr.com/" in line:
				self.tumblr1 = line

				# check if next line is also tumblr link
				if "https://arknights-archive.tumblr.com/" in self.data[i+1]:
					self.tumblr2 = self.data[i+1]
					i += 1
				else:
					self.tumblr2 = None
			# TODO: "Stickers from <src> and link after"
			elif "correspond" in line or "Correspond" in line or "https://arknights.wiki.gg/wiki/" in line:
				i += 1
				continue
			elif "Features" in line:
				line = line.replace("Features ","")
				line = line.replace(".","")
				line = line.split(", ")
				line = [x.lower() for x in line]
				self.ft_list = line

			i += 1 # iterate while loop
		
		# use extracted data to create StickerPack obj
		self.stickerpack = StickerPack(pack_name, pack_fullname, 
								 		self.cn_date, self.cn_src, 
										self.en_date, self.en_src, 
										self.tumblr1, self.tumblr2, 
										src=None, src_text=None,
										featured=self.ft_list)

	def get_result(self):
		return self.stickerpack

def get_input(prompt):
	print(prompt)
	result = input()
	return result

def get_sticker_name():
	return get_input("Enter sticker's file name (without file extension):")

def get_sticker_names():
	names = []
	standardSize = False
	STANDARD: int = 16

	# If sticker pack is standard size, run loop until list is length of 16
	check_standard = get_input("Is this sticker pack the standard size of at least 16? (y/n)")
	if check_standard == "y":
		standardSize = True

	out = False
	while not out:

		# Get sticker name
		names.append(get_sticker_name())

		# Standard pack
		if standardSize and len(names) >= STANDARD:
			response = get_input("Add another sticker? (y/n)")
			if response == "n":
				out = True
		# Non standard pack
		elif not standardSize:
			response = get_input("Add another sticker? (y/n)")
			if response == "n":
				out = True

	return names

if __name__ == "__main__":

	# TODO Hard code year since it changes infrequently
	year = 2021

	# Get some input to create parser for pack
	pack_name = get_input("Enter folder name of sticker pack:")	# Pack folder name
	fullname = get_input("Enter full name of sticker pack:")	# Pack full name	

	# Get sticker pack information
	parser = Parser(year, pack_name, fullname)

	# sticker pack object
	sticker_pack = parser.get_result()

	# list of sticker names from input
	sticker_names = get_sticker_names()

	# add stickers (just names, alt text and/or captions added manually in json later) to list
	for name in sticker_names:
		sticker_pack.add_new_sticker(name)

	# initial dictionary from StickerPack
	dict_i = sticker_pack.to_dict()

	# filter out None values from stickers list
	sticker_list = []
	for sticker in dict_i["stickers"]:
		sticker_clean = {k:v for k,v in sticker.items() if v is not None}
		sticker_list.append(sticker_clean)

	# filter out None values from sticker pack dictionary
	dict_clean = {k:v for k,v in dict_i.items() if v is not None}
	dict_clean["stickers"] = sticker_list # use filtered sticker list

	with open('temp_data.json', 'w', encoding='utf-8') as f:
		json.dump(dict_clean, f, ensure_ascii=False, indent=4)
	f.close()