# Mika expression portraits

`mika-avatar.png` is a 256 × 256 face crop from the happy portrait. It is used
automatically for Mika's chat messages; there is no emoji icon selector.
`extract_portraits.py` also recreates this face crop.

`mika-reference.png` is the original user-provided sheet and is preserved.
SHA-256: `61A126EA96AD2857B754C147E2AB45CFA64AC5B4448CC6B9E2E63F9009FD92E9`.

The three extracted portraits are `mika-happy.png`, `mika-thoughtful.png`, and
`mika-playful.png`. Each is a transparent 420 × 420 PNG, with the same source
scale, top alignment, and shoulder baseline. Labels, panel borders, surrounding
figures, and decorative marks are removed with traced alpha masks. The portraits
are extracted source pixels, not AI-generated reinterpretations.

To recreate them from the original sheet:

```powershell
.\.venv\Scripts\python.exe extract_portraits.py
```

Run this command from the project root. It overwrites only the three extracted
expression PNG files and the full-body cutout. It never writes to the reference sheet. The CSS animation moves the
whole portrait vertically by four pixels and honors reduced-motion preferences.
It does not distort the character to simulate speaking or blinking.

`mika-full-body.png` is a transparent 400 × 1040 cutout of the large standing figure
at the left of the original sheet, preserving the complete head, outfit, legs, and
shoes. It is the default large character view. The original pose is retained;
the optional Portrait view continues to provide the facial animation frames.

## Closed-eye blink frame

`mika-blink.png` is an additional 420 × 420 transparent frame, created with the
built-in imagegen tool using the extracted happy portrait as its edit reference,
then uniformly resized to the common canvas. Original portraits are unchanged.
It is displayed briefly over the happy portrait; reduced-motion mode disables it.
No generation service is required by the app at runtime. It is 2D artwork, not 3D.

Generation prompt:

> Edit this existing adult anime character portrait to create ONE closed-eye blink animation frame. Preserve Mika's exact identity, head angle, hair strands, smiling mouth, clothing, necklace, linework, colors, source scale, pose, silhouette, shoulder baseline and transparent padding. Change ONLY the two open eyes to naturally closed curved eyelids with lashes, as a brief blink, not squeezed or distorted eyes. This must overlay the original open-eye portrait without movement. Output the same square canvas framing and genuine transparent background. The source contains fully transparent pixels with hidden RGB data: those invisible labels, sheet panels, surrounding figures and writing MUST STAY COMPLETELY TRANSPARENT and must not be included or repainted. Visible portrait only. No labels, no text, no border, no surrounding sheet. Do not create 3D art or change style. This is an animation frame, not a redesign.
