# Media

Photos and GIFs of the arm in action.

```
media/
├── raw/                      Original phone videos/photos (gitignored — these can be large)
├── photos/                   Final photos committed to the repo
├── demo.gif                  Hero clip, referenced from the root README
├── mechanism_gripper.gif     Gripper mechanism close-up
└── board_complete.gif        Assembled board (reed matrix + mux) in action
```

## Why GIFs instead of the original MP4s

The repo used to carry the raw phone MP4s directly. GIFs are the better fit
for a README: they autoplay inline on GitHub with no click-to-play, need no
video player/codec support, and — cut down to a short highlight — end up
smaller than the source clip. The tradeoff is no audio and a bigger file
than an equivalent-length MP4, which is why each GIF here is trimmed to the
part worth watching rather than converting a full-length clip.

## Getting footage from your phone to here

Any transfer method works (USB cable, Google Photos/iCloud download, AirDrop
to a synced folder, etc.) — the point is just to end up with files under
`media/raw/`. `raw/` is gitignored so you can drop full-size phone videos in
there without bloating the repo.

## Turning a video into a GIF

```bash
scripts/make_gif.sh media/raw/your_video.mp4 media/demo.gif
```

Tune it with the optional `fps`, `width`, `start` and `duration` args
(defaults: 15 fps, 600px wide, full length) — see the script header for
details. `start`/`duration` matter most for long clips: a full-length phone
video turns into a huge GIF (no inter-frame compression like a real video
codec), so trim it to the highlight, e.g.:

```bash
scripts/make_gif.sh media/raw/full_game.mp4 media/demo.gif 8 300 00:00:00 10
```

## Photos

Drop finished photos (not raw phone dumps) directly in `media/photos/` and
link them from the README wherever useful — e.g. a wiring closeup next to
`docs/wiring.md`, or a full setup shot in the README intro.
