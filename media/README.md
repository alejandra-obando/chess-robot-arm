# Media

Where photos and GIFs of the arm live, once you have them.

```
media/
├── raw/       Original phone videos/photos (gitignored — these can be large)
├── photos/    Final photos you want committed to the repo
└── demo.gif   The GIF referenced from the root README
```

## Getting footage from your phone to here

Any transfer method works (USB cable, Google Photos/iCloud download, AirDrop
to a synced folder, etc.) — the point is just to end up with files under
`media/raw/`. `raw/` is gitignored so you can drop full-size phone videos in
there without bloating the repo.

## Turning a video into the demo GIF

```bash
scripts/make_gif.sh media/raw/your_video.mp4 media/demo.gif
```

Tune size/smoothness with the optional `fps` and `width` args (defaults:
15 fps, 600px wide) — see the script header for details. Once
`media/demo.gif` exists, uncomment the `<img>` block near the top of the
root `README.md` so it actually renders.

## Photos

Drop finished photos (not raw phone dumps) directly in `media/photos/` and
link them from the README wherever useful — e.g. a wiring closeup next to
`docs/wiring.md`, or a full setup shot in the README intro.
