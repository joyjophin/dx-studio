# Third-party notices

DX Studio's original code and documentation are MIT licensed; see LICENSE.

## Bundled fonts

The fonts in `dx_studio/fonts/` derive from Inter, copyright 2016 The Inter Project
Authors, https://github.com/rsms/inter. They are distributed under the SIL Open
Font License 1.1 in `dx_studio/fonts/OFL.txt`. The local proportional and tabular
builds have been renamed **DX Sans** / **DX Sans Tab** to distinguish them from
the upstream font family. Font software remains OFL licensed, not MIT.

## Runtime dependencies

Cairo, Cairo bindings, HarfBuzz, uharfbuzz, FontTools, NumPy, SciPy, Pillow and
SoundFile retain their respective upstream licences. They are installed as
separate dependencies. FFmpeg is a separately installed executable; its licence
depends on the selected build. No FFmpeg binary is bundled in this repository.

## Optional speech models and tools

Kokoro ONNX: https://github.com/thewh1teagle/kokoro-onnx

Sherpa ONNX / Parakeet integration: https://github.com/k2-fsa/sherpa-onnx

Weights are downloaded only by the optional speech helpers. Consult the original
model/tool licences and model cards before redistribution. This release does not
bundle models or assert that DX Studio's MIT licence applies to them.

## Artwork and trademarks

The private avatar/GIF pack is excluded. Imported art, music, footage and
recordings retain their owners' rights. Figma and other product names referenced
in optional educational kits are third-party trademarks. No endorsement or
affiliation is implied. Brand your finished videos as you choose.
