---
article_id: KB-003
title: Advisor Pro desktop client crashes on launch
category: desktop-application
product: Advisor Pro
last_reviewed: 2026-05-02
---
# Advisor Pro crashes on launch

Known cause: a corrupted local cache in the user profile directory after an interrupted update.

Resolution:
1. Fully exit Advisor Pro, including any background process in the system tray.
2. Delete the folder `%LOCALAPPDATA%\AdvisorPro\cache`.
3. Relaunch Advisor Pro. The cache rebuilds on first launch and startup takes up to 90 seconds.

If the crash persists after clearing the cache, collect the crash log from `%LOCALAPPDATA%\AdvisorPro\logs\startup.log` and attach it to the ticket before escalating.

Advisor Pro is not supported on Windows 10 builds earlier than 19045.
