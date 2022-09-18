# MDL - Mortoray's Document Language

My markdown language for documents: blogs, ebooks, and print.

I use this tool on a day-to-day basis for my own work. It is fairly stable, though I can't guarantee I won't add anything that changes the formatting, or accepts a new syntax. As I use it on more sites, it becomes ever more stable.

Follow the development at [mortoray.com](https://mortoray.com/) or follow me on [Twitter](https://twitter.com/edaqa)

I actively use this generator/parser for:

- **[Edaqa's Kitchen](https://edaqaskitchen.com):** Healthy modern recipes. I use it for the text part of recipes.
- **[Edaqa's Room](https://edaqasroom.com):** Online escape rooms. I use it for documentations as well as the game's high-level language.
- **Soon… [Musing Mortoray](https://mortoray.com):** Technical Blog. I will use it for the articles.

## Running

There is an entry point defined on the module that that reads MDL files and emits either HTML or Markdown.

```
python -m mdl --help
```

Example:

```
python -m mdl README.mdl --write markdown README.md
```

Be aware that not all emitters will support all of the doc-tree at any given time. It's all in flux now.

## Python 3.8

```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.8
sudo apt install python3.8-distutils python3.8-dev


sudo apt-get install python3.8-venv
```

