# MDL - Mortoray's Document Language

My markdown language for documents: blogs, ebooks, and print.

This project is in its infancy at the moment, being more of a proof-of-concept at this stage.

Follow the development over on [dev.to](https://dev.to/mortoray)


## Running

There is a simple driver program that reads MDL files and emits either HTML or Markdown.

Run `./mdl.py` to get options.

```
./mdl.py --write-markdown /tmp/out.md log/2.md
```

Be aware that not all emitters will support all of the doc-tree at any given time. It's all in flux now.


## Python 3.8

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.8
sudo apt install python3.8-distutils python3.8-dev


sudo apt-get install python3.8-venv

