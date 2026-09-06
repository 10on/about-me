---
date: 11.08.2026
tags: slider, 3d-printing
---
I figured today's post would be about finishing the slider build. Turned out fate had other plans.

Finished the enclosure, installed all the components, fixed one broken connection, closed the lid.

![Slider from the side — closed enclosure, USB-C port for flashing](img/notes/slider-final-side.webp)

Hit a firmware bug once and had to open the enclosure back up to reflash over wire. But overall OTA updates now install fine over the air.

![Front panel screen during an OTA firmware update — "Updating", 9%](img/notes/slider-updating.webp)

Passed all the basic tests and went to mount everything on the slider, hoping to at least test-fit it today.

![Slider from the side, with the metal quick-release plate and a roller underneath it](img/notes/slider-mount-clip.webp)

And that's when it turned out I hadn't accounted for the roller clearance: the rollers that wrap the belt around the pulley run straight into the slider carriage's own rollers.

![Close-up: the slider carriage roller pressing into the enclosure's corner right by the mount](img/notes/slider-roller-clash.webp)

No quick fix in sight so far. I did swap the bulky screws for slimmer ones, but it's still short by a few millimeters for comfortable use.

I see two possible solutions.

First — extend the enclosure. For example, cut off part of the old case, glue in and screw down an insert that shifts the case relative to the slider by a few millimeters.

The second option is more radical — redo the enclosure entirely. Move the stepper motor somewhere else and start figuring out a cleaner layout for everything.

![Top-down view of the open slider enclosure: the pulleys and the stepper motor mount](img/notes/slider-top-open.webp)

The downside is I'd have to take everything apart again right now — peel off a pile of glue, desolder a pile of wires, and reassemble it all. What I like about this option is I'd get to tidy up the inside of the enclosure; what I don't like is that a full rework would eat up way too much time, and I want a finished slider now.

There seems to be a middle ground between the two: skip designing a whole new super-enclosure and just add the missing bits to the current one, bump its clearance up a little, and keep working from there.

The inside will need tidying up regardless, but at least without a full redesign.
