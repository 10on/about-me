---
date: 22.11.2026
tags: development, ai
---
![Chat with Claude: given a YouTube link, the model summarizes the video "Can you game on DDR2 in 2026?" through the Youtube reader connector](img/notes/yt-helper-summary.webp)

I've started asking LLMs to watch videos for me a lot. Usually that meant downloading subtitles through some third-party service and dropping them into a chatbot. So I vibe-coded myself a helper that lets an AI "watch" YouTube. It's an MCP server running on my home NAS, connected to Claude as a connector. Under the hood: yt-dlp and ffmpeg.

At first I only taught it to pull subtitles. Then, while I was at it, I threw in video search, channel video lists and comments. After that I wanted the model to see the picture, not just the text. I assumed that would take a complex pipeline with a local recognition model. But it turned out you can build a storyboard from the tiny previews YouTube shows when you scrub, and then ask for a sharp frame at the right moment. The frame is taken straight from the stream, no need to download the whole video.

![Claude's answer about another video: a timeline ("00:00 intro, 05:17–12:44 teardown…") worked out from frames of the video](img/notes/yt-helper-frames.webp)

Long story short, that's basically enough to get a decent amount of information out of a video.
