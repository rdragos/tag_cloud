Requirements
============

Python 2.7


Installation
============

	$ pip -r install requirements.txt


Usage
=====

	$ python main.py num_seconds num_words stopwords_path
	$ One should replace the appropriate Twitter credential keys in the TwitterData constructor

Example
========

	Retrieves the top 5 words from tweets within the last 3 seconds considering the stopwords located at stopwords.txt

	$ python main.py 3.0 5 stopwords.txt



