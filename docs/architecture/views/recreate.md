# PlantUML

## VSCode Extensions

Preferably use the VSCode extension called `jebbs.plantuml`.
The `simonsiefke.svg-preview` extension helps for previewing the resulting .svg files.

This way you can preview any .plantuml file with `ALT`+`D`.

## Manual Installation of plantuml

```shell
sudo apt install openjdk-11-jre graphviz
```

Get the most recent plantuml .jar file from [https://plantuml.com/](https://plantuml.com/)

## Generate SVG files

To generate the files manually, one would typically use:

```shell
java -jar plantuml-1.2023.12.jar views/context_end_of_line_calibration.plantuml -tsvg
```

Note: The new file name of the .svg is chosen based on the title set in the first line of the .plantuml file. Make sure to name source .plantuml file the same as the resulting .svg file for consistency.

To generate files for all the plantuml files

```shell
cd docs/architecture/views/
find . -iname '*.plantuml' | xargs java -jar plantuml-1.2024.7.jar -tsvg
```