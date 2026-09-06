---
date: 21.08.2026
tags: slider, electronics
---
Today the replacement components arrived. The ESP32 board fit the existing footprint perfectly. I did have to desolder the pin header, but I've done that before with the previous board, so it wasn't a big deal.

Stayed up late again, but got everything soldered back into place, and sorted out some of the wire lengths while I was at it. But once I assembled everything, the screen didn't light up. I figured I'd lost a connection somewhere, so I had to take apart everything I'd already rebuilt inside the case. And right at the very end of taking it apart, I realized I'd simply forgotten to connect the pin that controls the screen's backlight.

Once I connected it, everything worked. I haven't run a full test yet, but at the very least the screen lights up, and the buttons and encoder respond. Really all that's left is to check that the motor spins and the sensors work.

![The slider's electronics disassembled inside the case next to the battery pack on the Creality 42-3 motor](img/notes/slider-repaired-open.webp)

I also found that I still had one GPIO pin free, and decided to hang a buzzer off it. I've got a few ideas for what it could be useful for while shooting. And besides that, a buzzer lets you add sound effects for various situations — a light click when turning the encoder, for example. A small thing, but a nice one.

So tomorrow I need to add a power switch and wire up the speaker. And then the case can finally be closed :)

Also, very briefly, basically as a background task, I did a bit of work on the remote. Mostly I just reprinted a slightly modified layout to arrange the buttons nicely.

In the end I decided not to make any pushers for the buttons, and instead just leave what's there exposed, to speed up development of this device.

![A cross-shaped layout of five button modules on a red 3D-printed panel, no caps yet](img/notes/remote-dpad-switches.webp)

![The same panel with black round caps on the buttons](img/notes/remote-dpad-caps.webp)
