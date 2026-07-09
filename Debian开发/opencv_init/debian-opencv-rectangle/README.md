# Debian OpenCV Rectangle Detection

Host-Debian OpenCV camera service that detects rectangular shapes in real time.

This is separate from the basic `debian-opencv` example. It runs directly on the
UNO Q Debian host and serves the processed camera stream on port `8080`.

## Run

```bash
cd "/home/arduino/ArduinoApps/debian-opencv-rectangle"
./run_host.sh
```

Open:

```text
http://<board-ip>:8080
```

Example:

```text
http://10.233.80.145:8080
```

## What It Detects

The current `process_frame(frame)` pipeline:

- converts the frame to grayscale;
- blurs to reduce noise;
- runs Canny edge detection;
- closes small edge gaps with morphology;
- finds contours;
- approximates contours as polygons;
- keeps convex four-point polygons that pass area, aspect-ratio, and fill checks;
- draws detected rectangles on the output frame.

## Endpoints

- `/` - Web preview page.
- `/stream.mjpg` - MJPEG video stream with rectangle overlays.
- `/snapshot.jpg` - Single JPEG frame.
- `/health` - Plain text status.
- `/result.json` - Latest rectangle detection result.

Example `/result.json`:

```json
{
  "status": "streaming",
  "brightness": 92.4,
  "rectangles_count": 1,
  "rectangles": [
    {
      "x": 120,
      "y": 80,
      "width": 210,
      "height": 130,
      "area": 26780.5,
      "aspect_ratio": 1.62
    }
  ],
  "label": "rectangle_detected"
}
```

## Tuning

If too many false rectangles are detected, tune these values in `process_frame()`:

- Canny thresholds: `cv2.Canny(blurred, 60, 160)`
- minimum contour area: `min_area = 1200`
- polygon approximation: `0.03 * perimeter`
- fill-ratio threshold: `fill_ratio < 0.45`
