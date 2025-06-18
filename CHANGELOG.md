# Changelog

## [0.8.3](https://github.com/lnqs/textual-image/compare/v0.8.2...v0.8.3) (2025-06-18)


### Documentation

* mention warp and textual-serve in README ([7c38db8](https://github.com/lnqs/textual-image/commit/7c38db8a8f334394b0b8bc333c887fc0a8a9746d))

## [0.8.2](https://github.com/lnqs/textual-image/compare/v0.8.1...v0.8.2) (2025-04-01)


### Bug Fixes

* fall back to default cell size ([524f6e4](https://github.com/lnqs/textual-image/commit/524f6e47d6add6daa8f16050be4212ff493d90eb))


### Documentation

* update Windows Terminal note ([76c5c91](https://github.com/lnqs/textual-image/commit/76c5c91a94f4761cb6b299990e690e9ade95aaf3))

## [0.8.1](https://github.com/lnqs/textual-image/compare/v0.8.0...v0.8.1) (2025-03-27)


### Bug Fixes

* fix re-rendering TGP images ([e1c13bc](https://github.com/lnqs/textual-image/commit/e1c13bcc808a7f74b33e7d5da012910a0fac9153))

## [0.8.0](https://github.com/lnqs/textual-image/compare/v0.7.0...v0.8.0) (2025-03-27)


### Features

* add byte stream support ([b697ce0](https://github.com/lnqs/textual-image/commit/b697ce01c6fe3ecbb4d746b1adc78907e58da93d))
* add non-seekable stream support ([c2b0a76](https://github.com/lnqs/textual-image/commit/c2b0a7698cec1b868b9721877d6d18b77e6947ca))

## [0.7.0](https://github.com/lnqs/textual-image/compare/v0.6.6...v0.7.0) (2024-12-28)


### Features

* python 3.13 support ([f14cdab](https://github.com/lnqs/textual-image/commit/f14cdabc399462359309920f6877b8fea9859c24))


### Bug Fixes

* re-rendering widget on image change ([59f83d6](https://github.com/lnqs/textual-image/commit/59f83d648d0ef927f8a680ebb484072f19f5b6cc))

## [0.6.6](https://github.com/lnqs/textual-image/compare/v0.6.5...v0.6.6) (2024-10-21)


### Bug Fixes

* include demo image ([4d1e516](https://github.com/lnqs/textual-image/commit/4d1e516946e8f64a5c6fc60310e9fba654a84241))

## [0.6.5](https://github.com/lnqs/textual-image/compare/v0.6.4...v0.6.5) (2024-10-14)


### Bug Fixes

* prevent image from not being rendered ([05566f9](https://github.com/lnqs/textual-image/commit/05566f93e34dff8fa84035b9865f15aaf4d55cbe))

## [0.6.4](https://github.com/lnqs/textual-image/compare/v0.6.3...v0.6.4) (2024-10-12)


### Bug Fixes

* fix failing assertion ([00e2d01](https://github.com/lnqs/textual-image/commit/00e2d010a57b8d02f9eb2db371132b109e5c51b2))

## [0.6.3](https://github.com/lnqs/textual-image/compare/v0.6.2...v0.6.3) (2024-10-11)


### Bug Fixes

* add missing py.typed marker ([db0f83f](https://github.com/lnqs/textual-image/commit/db0f83f90b37bedaba5e064ebd7a020b7673a74e))

## [0.6.2](https://github.com/lnqs/textual-image/compare/v0.6.1...v0.6.2) (2024-10-09)


### Bug Fixes

* improve cursor position handling for sixels ([bb37ee4](https://github.com/lnqs/textual-image/commit/bb37ee41d3b7c27d7f826ae704c2bd96845c6218))
* reorder preferred rendering methods ([a5a4efb](https://github.com/lnqs/textual-image/commit/a5a4efb80253e589071c26ea8339eed8283be88f))


### Documentation

* cleanup compatibility matrix ([652f7ee](https://github.com/lnqs/textual-image/commit/652f7ee91b7a6b6fd30b122ae756999ac37a308d))
* describe the high image issue in the README ([84389ee](https://github.com/lnqs/textual-image/commit/84389ee1eb14502cefaa44358cac8ba739834bc5))

## [0.6.1](https://github.com/lnqs/textual-image/compare/v0.6.0...v0.6.1) (2024-10-08)


### Bug Fixes

* add missing files in distribution ([3370879](https://github.com/lnqs/textual-image/commit/33708793bb3a7437d72bfa3279d4858ec03e9683))

## [0.6.0](https://github.com/lnqs/textual-image/compare/v0.5.0...v0.6.0) (2024-10-07)


### Features

* basic Windows support ([79d1114](https://github.com/lnqs/textual-image/commit/79d1114df02c86f583c089b33710d62d492642c4))
* use escape sequence to get cell size ([a13bb9c](https://github.com/lnqs/textual-image/commit/a13bb9c768011e67e4a743a04584357d2bcbc320))


### Documentation

* add badges to README.md ([f3239db](https://github.com/lnqs/textual-image/commit/f3239db1b40673f69ded016f046d59fff05599ac))

## [0.5.0](https://github.com/lnqs/textual-image/compare/v0.4.0...v0.5.0) (2024-10-02)


### ⚠ BREAKING CHANGES

* rename to textual-image
* consistent usage of underscore for symbols

### Features

* improve demo ([26595b0](https://github.com/lnqs/textual-image/commit/26595b037d08ebb89ca230913dfa78dbf275d002))
* sixel support ([3afd860](https://github.com/lnqs/textual-image/commit/3afd860a345c9409f4f95ad3059d348fd5993057))


### Bug Fixes

* fix render method selection in demo ([79c12c1](https://github.com/lnqs/textual-image/commit/79c12c1946cd9f5a78b0f0bcb9698d8f81586f4c))


### Documentation

* add demo gif to readme ([960d334](https://github.com/lnqs/textual-image/commit/960d334e9e6d10550ccd97a9037cae893c6a7fc4))
* add information about tested terminals ([3e9f738](https://github.com/lnqs/textual-image/commit/3e9f73811b5ffc2c203f500f0a60c295d1ae5b47))
* add sixel support to README ([52ab610](https://github.com/lnqs/textual-image/commit/52ab6104016bf4eeca7e881957df0f9e562e6286))
* describe how to enable Sixels on xterm ([f68697c](https://github.com/lnqs/textual-image/commit/f68697cd6e359bc4a883d7e090dc05e3faf0183e))


### Miscellaneous Chores

* consistent usage of underscore for symbols ([0b0d6e8](https://github.com/lnqs/textual-image/commit/0b0d6e80676b5b79a7dd8bff9ad8386e1a56dfa0))
* rename to textual-image ([5552677](https://github.com/lnqs/textual-image/commit/5552677a070058ead5d2240030b9da6a489e8f88))

## [0.4.0](https://github.com/lnqs/textual-image/compare/v0.3.0...v0.4.0) (2024-09-28)


### ⚠ BREAKING CHANGES

* refactor and reorganize code

### Miscellaneous Chores

* refactor and reorganize code ([3dc0190](https://github.com/lnqs/textual-image/commit/3dc01907e8dc005e34f567b80915e0ac0d91dd5e))

## [0.3.0](https://github.com/lnqs/textual-image/compare/v0.2.0...v0.3.0) (2024-09-20)


### Features

* add unicode fallback to render images ([14f30ff](https://github.com/lnqs/textual-image/commit/14f30ff65a0fa65b7984b26039f298bd46286b3d))

## [0.2.0](https://github.com/lnqs/textual-image/compare/v0.1.1...v0.2.0) (2024-09-15)


### Features

* add py.typed marker ([072f279](https://github.com/lnqs/textual-image/commit/072f27922ca904d13792934f3487a379cad7eb14))

## 0.1.1 (2024-09-15)


### Features

* add Textual widget for images ([c2ea342](https://github.com/lnqs/textual-image/commit/c2ea342d500cf535f8304845dc313f86d878c4da))
* implement async processing in textual widget ([7425506](https://github.com/lnqs/textual-image/commit/742550648854c5ea8042c6553f1e813e13adcb08))
* implement rich renderable for images ([a7371cc](https://github.com/lnqs/textual-image/commit/a7371cc64da8fc5bf6768c639d67d03ca1ef7ff6))
* improve error handling ([ac24d5e](https://github.com/lnqs/textual-image/commit/ac24d5e477ff8338be9c29c2f99257d3c05181c7))


### Documentation

* add docstrings ([ff52e39](https://github.com/lnqs/textual-image/commit/ff52e3907fcf06cc7ba24b282ba2b097cf4b0f4c))
* add README.md ([1f23367](https://github.com/lnqs/textual-image/commit/1f23367bbae06d8fb0916b114e7494c9cda61004))


### Miscellaneous Chores

* release 0.1.1 ([39d1f9f](https://github.com/lnqs/textual-image/commit/39d1f9f6b2608e029c59de5f0bb13f6604828790))
