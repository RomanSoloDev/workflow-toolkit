# Devlog

## 17 October 2026

### What I did
- Created the GitHub repo and set up the project structure
- Created the `workflow-toolkit` repo complete with a README, Python .gitignore and MIT licence
- Set up project structure (`docs/`, `src/`, `tests/`)
- Planned the features, 11 issues

### Why I'm building this
I'm paid by the exact time worked, so I need a time tracker that can pause and handle time away from my desk. I also take a lot of screenshots as evidence, and I constantly need quick access to downloaded files. I'd rather have one tool I built and trust than several third-party apps especially while under NDA.

### Design decisions
- **Desktop app using PySide6:** it needs to stay on top, sit in the tray, and let me drag files out of the app into upload boxes.
- **Timer stores timestamps:** totals stay exact and survive a crash or restart.
- **Idle detection doesn't auto pause:** after 5 minutes idle, the timer keeps running and flags the time. Which the user can later decide if it was idle or work time, complete with a slider.
- I decided the slider will have 15 second increments plus a box to type the exact amount (slider might be changed to have exact value functionality)
- **Generic session ID numbers (Session ID1, ID2, ID3...):** no actual session IDs are shown or stored
- **Work data stays out of the repo:** screenshots, notes and clipboard history are saved in AppData, not the project folder as the repo is public.
- **Text snippets:** might be used later unsure if necessary.