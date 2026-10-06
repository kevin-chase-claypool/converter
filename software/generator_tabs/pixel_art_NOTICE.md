# Pixel Art tab - third-party notice

The Pixel Art tab ports the MIT-licensed vpype-pixelart
(https://github.com/abey79/vpype-pixelart). All three upstream modes are
implemented from its source: `big` (5x5 square spiral per pixel), `line`
(horizontal runs of one colour with overdraw), and `snake` (connected path
through each colour's pixels, with singleton ticks). The pen-width setting is
exposed as `Pixel pitch`, and the line-mode overdraw fraction is a control.

The upstream command creates one layer per colour; this app drives a single
pen, so the tab draws all colours together into one path set. That fusion is
the only behavioural adaptation.
