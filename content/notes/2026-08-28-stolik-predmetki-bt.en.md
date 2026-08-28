---
date: 28.08.2026
time: 12:00
tags: slider, electronics
---
Practically overnight, within a single day, I managed to mod a cheap Chinese product-photography turntable — now it can be controlled by my remote. The turntable looks roughly like this:

![Screenshot of an AliExpress product page: a black rotating platform with R/L, SR, ASA buttons and a USB-C port](img/notes/turntable-aliexpress.webp)

At first I planned to replace the entire guts except the motor, while keeping the control panel. But in the evening I realized I could burn a ton of time fitting new internals to the existing panel. Decided to figure out the board instead — an unmarked controller chip was running the whole thing. Here it is under the probe.

![The turntable's green board on a helping-hands stand, a multimeter probe touching an unmarked chip](img/notes/turntable-probe-chip.webp)

Also, the device already had a lot of what I wanted to add to the project anyway: a charging circuit, a boost converter, an 18650 battery bay.

Here's what I ended up with. I'll clearly keep refining it, but it's already usable. Looks the same from the outside, just controlled over Bluetooth now.

![Inside the turntable from above: a stepper motor in its mount, a green control board, colorful wires, and the battery bay](img/notes/turntable-internals.webp)
