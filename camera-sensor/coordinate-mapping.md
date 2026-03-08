The Qualcomm Dragonwing MPU on the Uno Q processes video through a hardware-accelerated pipeline that can sometimes lead to confusion between the sensor resolution and the normalized coordinates used by the AI bricks.

## 1. The 1000-Point Normalized System

By default, most App Lab bricks, including the `VideoObjectDetection` brick, do not return raw pixel values such as `640` or `480`. Instead, they use a normalized coordinate system from `0` to `1000`.

This is crucial for your IDE agent to know, as it makes your zone logic resolution-independent.

| Zone | X-coordinate range (normalized) |
| --- | --- |
| Zone 1 (Left) | `0 <= x < 333` |
| Zone 2 (Center) | `333 <= x < 666` |
| Zone 3 (Right) | `666 <= x <= 1000` |

## 2. Bounding Box Anchors

The Uno Q typically returns the `(x, y)` coordinate for the top-left corner of the detected object. If you only check whether that single point is in a zone, a large object might be physically in Zone 2 while its top-left corner is still in Zone 1.

For accurate duration tracking, your agent should calculate the horizontal center (`x_center`):

```text
x_center = x + (width / 2)
```

## 3. Aspect Ratio and Letterboxing

The Dragonwing MPU handles a `4:3` aspect ratio natively. If your camera feed is set to `16:9`, the App Lab environment will letterbox the feed.

If letterboxed, the normalized coordinates from `(0, 0)` to `(1000, 1000)` will cover the entire sensor area, including the black bars.

Recommendation: Ensure the agent sets the camera to `vga` (`640x480`) mode during initialization so your 3-zone split aligns cleanly with the visible video.

## 4. Integration Tip for Antigravity

When you prompt the Gemini Pro agent, tell it:

> Use the `app_utils.transform` method to map the normalized detection coordinates to the `8x13` LED matrix coordinates.

This ensures that when an object is in the left zone, the LEDs on the left side of your Uno Q board light up accurately.

## 5. Optional Follow-Up

Would you like me to provide a quick JSON configuration block for the camera's field-of-view settings to ensure your zones do not have blind spots at the edges?
