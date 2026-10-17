# Landscape composition and product explainers

Create with `dx-studio init projects/demo --format 16:9`. The supplied template
reflows at creation; arbitrary custom scenes do not become responsive by swapping
width and height. Build dimensions, element boxes and text widths from project.json.

Establish the whole interface, focus on the relevant control, show the action,
and return to context. Use native-looking proportions rather than squeezing a
portrait scene into a landscape canvas. Put labels in quiet margins. Derive
highlights and connectors from the same geometry used by the target components.

`kits/editorial16x9.py` provides optional cameras, rings, elbow connectors,
callouts and chapter moments. Copy it beside scene.py. Kits may contain fixed
layout tokens; adapt them for your composition. Keep screenshots and recorded
footage licensed and distinguish illustrative interfaces from real product output.

Split every independently editable part into a Layer with a correct selection box.
Check chapter transitions at full size and run framecheck before long exports.
