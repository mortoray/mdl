# MDL - Mortoray's Document Language

My multi-purpose markdown language. MDL combines a document language, similar to markdown, with a structured header language, similar to YAML.

I use this tool on a day-to-day basis for my own work. It is fairly stable, though I can't guarantee I won't add anything that changes the formatting, or accepts a new syntax. As I use it on more sites, it becomes ever more stable.

Follow the development at [mortoray.com](https://mortoray.com/) or follow me on [Mastadon](https://peoplemaking.games/@mortoray)

I actively use this generator/parser for:

- **[Edaqa's Kitchen](https://edaqaskitchen.com):** Healthy modern recipes. I use it for the text part of recipes.
- **[Edaqa's Room](https://edaqasroom.com):** Online escape rooms. I use MCL for the primary game script as well as the document language for [the grimoire](https://edaqasroom.com/grimoire/directory).
- **[Musing Mortoray](https://mortoray.com):** Technical Blog. I'm using the document language to write articles and publish in multiple formats.

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

## Python 3.10

NOTE: Uncertain if this is still needed/up-to-date

```
sudo apt install python3.10-distutils python3.10-dev
```

