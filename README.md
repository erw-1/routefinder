# RouteFinder Builder

This project builds a static matrix routing webmap with your own data.
No-code UI and drag & drop export.

---

Project builder with your data:

![builder](https://github.com/erw-1/erw.one/blob/main/files/img/demos/routfinderbuilder.png?raw=true)

Generated static webmap running on APIs:

![demo](https://github.com/erw-1/erw.one/blob/main/files/img/demos/routefinder.png?raw=true)
[Live Demo](https://erw.one/apps/routefinder)

---

My first attempt at an actual github project! Still not fully released.

> [!IMPORTANT]
> #### Requirements
> - Python 3.13
> - Git
> - Windows (for now)
>
> #### Quickstart:
> ```shell
> curl -L "https://github.com/erw-1/routefinder/releases/download/rc-0.7/routefinder_setup_v0.7-alpha.py" -o routefinder_setup_v0.7-alpha.py && py routefinder_setup_v0.7-alpha.py
> ```
> > <sup>Or run the latest Python file in [releases.](https://github.com/erw-1/routefinder/releases)</sup>

> [!CAUTION]
> ### DOCS SOON, WIP, EXPERIMENTAL PROJECT

> [!WARNING]
> #### Known issues
> - I had no clue how to work with venv/ multi platforms yet, so the start of the program is janky. It worked on every windows system I tried, but it probably won't work on Unix systems. Docker soon ?
> - Whole project is in French (all the Python stuff was made for an explorative school project in France)  
> - Only tested on Windows 10 & 11
> - Did not do extensive testing with all geodata file formats and API types

> [!TIP]
> #### Ideas
> - Ability to load and save a .cfg file in RouteFinder Builder to save/ share project configurations
> - Ability to load data directly in the web page 
> - Auto chose the correct geometry type in loaded geodata when several ones are found (*eww*)
> - Baselayer picker
> - Docker
> - More
