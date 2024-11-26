# RouteFinder Builder

This project lets you build a static matrix routing webmap app with your own data.
No code interface and drag and drop export.

> [!CAUTION]
> ### DOCS SOON, WIP, EXPERIMENTAL PROJECT

> [!WARNING]
> #### Known issues
> - I had no clue how to work with venv/ multi platforms yet, so the start of the program is janky. It worked on every windows system I tried, but it probably won't work on Unix systems. Docker soon ?
> - Whole project is in French (all the Python stuff was made for an explorative school project in France)  
> - Only tested on Windows 10 & 11
> - Did not do extensive testing with all geodata file formats and API types

> [!IMPORTANT]
> #### Requirements
> - Python 3.13
> - Git
>
> #### Quickstart:
> ```shell
> curl -L "https://github.com/erw-1/routefinder/releases/download/rc-0.7/routefinder_setup_v0.7-alpha.py" -o routefinder_setup_v0.7-alpha.py && py routefinder_setup_v0.7-alpha.py
> ```
> > <sup>Or run the latest Python file in [releases.](https://github.com/erw-1/routefinder/releases)</sup>

> [!TIP]
> #### Ideas
> - Ability to load and save a .cfg file in RouteFinder Builder to keep
> - Ability to load data directly in the web page 
> - Auto chose the correct geometry type in loaded geodata when several ones are found (*eww*)
> - Baselayer picker
> - More
