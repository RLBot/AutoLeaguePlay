# OBS script for AutoLeaguePlay

Instructions:

> Work around "On windows, currently only Python 3.6 is supported" https://obsproject.com/docs/scripting.html by installing a compatible Python version; do not add it to path.
>
> install dependencies of obs-script into that python installation.
> `%AppData%\..\Local\Programs\Python\Python36\scripts\pip install -r obs-script\requirements.txt`
>
> Install/open OBS.
>
> set your obs settings. like record folder, video settings, etc
>
> Go to tools -> scripts
>
> on python setting, set the path to your python installation (must be py3.6)
>
> now on the scripts tab, press the + and add the `obs-Auto-League.py`
>
> overlay path files should point to the Files folder
>
> Auto league folder should point to where auto league is
>
> goal delay should be 1.65,
> end delay should be 12
>
> press on setup. this will add a new scene ready for league play
>
> start the script.
>
> it is currently waiting or rocket league to start so it can start recording.
> do the auto-league command to run it, and it should auto record every match.
