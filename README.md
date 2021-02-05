# TranscriptEdit

![](images/transcribEdit_basic-example.png)

This is a transcription editor developed specifically for preparing transcriptions files that are compatible with the Institute for Textual Scholarship and Electronic Editing collation editor (https://github.com/itsee-birmingham/standalone_collation_editor).

The strength of this editor is that it produces and retrieves transcriptions files that require no conversion at all to be used with the collation editor. Perhaps the biggest drawback of this editor is that it was developed to transcribe one verse at a time. I don't plan for this to always be true.

I use this editor daily for my doctoral research and so it is being actively improved as I think of useful features that help with my own research.

I will add documentation if/when anyone other than myself expresses interest in using it.

## Installation
### Windows
Windows users can simply download and run the MSI installer. The installer was built with `briefcase` from Beeware (https://github.com/beeware/briefcase).
### Other Platforms
Mac users should, theoretically, be able to run this as a Python module. *However*, I have barely tested the app on anything other than Windows. The GUI needs significant tweaking to get the proportions correct on MacOS. The GUI library is Qt via `PySide2` and the abstraction library `PySimpleGUIQt`.