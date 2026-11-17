---
tags: [writing-prds]
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

公司的訪客登記系統是兩年前一位同事寫的，他已經離職，沒有留下任何規格。我找到主要的程式（app.py）和當時的操作說明（manual.md）。幫我整理成一份規格放在 visitor-prd 資料夾，讓接手的工程師看得懂現在有什麼。

下一版只打算加一件事：下班（18:00）後還有訪客沒標記離開時，提醒櫃台。

負責人寫我，行政部吳采潔。

Input files: app.py, manual.md
