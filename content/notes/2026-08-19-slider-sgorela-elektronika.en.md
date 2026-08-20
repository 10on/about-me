---
date: 19.08.2026
tags: slider, electronics
---
The slider project was nearing completion. I thought all that was left was to mount the electronics panel and wire up the transistor that switches the load in the circuit — breaking the ground connection between the slider's main electronics and the power source.

![The slider's board mounted in the case: the Creality 42-3 stepper motor next to the electronics board](img/notes/slider-panel-mounted.webp)

Turns out not quite, and the slider gave up the ghost. I fried pretty much all of the electronics.

I never fully figured out the cause, but the most likely culprit is one of the connectors — the only one I hadn't covered with heat-shrink. Most likely it shorted out there, and high voltage ended up on the 3.3V rail.

![The slider board from the side, a tangle of wires next to brass inserts and tools laid out on the table](img/notes/slider-panel-side.webp)

The ESP32-WROOM and the accelerometer definitely died. That's all I've been able to confirm so far. I got lucky that the screen wasn't connected at the time, so it survived. The INA226 seems to have survived too, but I'll probably replace it just to be safe.

![Close-up of the ADXL345 accelerometer board among the wires on the back panel of the case](img/notes/slider-adxl-board.webp)

On the bright side, the motor driver survived, so at least I won't have to pull it out. Everything else is getting replaced.

The step-down converter probably survived too, but I'm eyeing it with suspicion as well and thinking about swapping it out anyway. It probably has reverse-voltage protection.

Unfortunately, I couldn't find the exact same ESP32 board. But if I'm reading the markings right, I found a slightly older revision of the same board, and it should match up in footprint and pin count. So I'm waiting for it to arrive any day now, and then I'll be able to continue.

Also, to cut down on the number of wires and reduce the odds of breaking something else with my clumsy hands, I ordered a ready-made MOSFET switch board. That way I won't have to build it all around a bare transistor, and the circuit gets a bit more compact.

Here's a screenshot of the order:

![Screenshot of the parts order: ESP32, a 3.3V converter, a GY-291 ADXL345 accelerometer, a piezo buzzer, IRF4905PBF and AOD4184 MOSFETs, a TC29548A, shipping — total 3270 dinars](img/notes/slider-order-parts.webp)
