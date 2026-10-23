# Record and upload the concept video

This guide uses QuickTime Player on a Mac and an Unlisted YouTube upload. Nothing in this repository has been uploaded.

## Before you record

1. Start the demo with the commands in the root README.
2. Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in a browser window with no extra tabs.
3. Click **Reset workflow** so the first screen is **Connect MCP**.
4. Confirm the yellow **DEMO MODE** banner is visible.
5. Open [demo-script.md](demo-script.md) on a second screen, or print it.
6. Optional opening frame: show `docs/media/returnright-ai-concept.png` for about three seconds, then switch to the app. Say that the image is concept artwork.

## QuickTime Player

1. Open **QuickTime Player**.
2. Choose **File → New Screen Recording**.
3. Click the arrow next to the record button.
4. Select the browser window, not the whole desktop.
5. Turn the microphone on and pick your mic. Leave the system-audio option off unless you want click sounds.
6. Click **Record**, then click the browser window.
7. Wait one second, then read the narration in `docs/demo-script.md` while clicking through the shot list.
8. Stop with the stop button in the menu bar.
9. Choose **File → Export As → 1080p…** and save `ReturnRight-AI-demo.mov`.

If Export As is missing, use **File → Save** and upload that movie. Keep the clip under 90 seconds.

## YouTube, Unlisted

1. Sign in at [https://studio.youtube.com](https://studio.youtube.com).
2. Click **Create → Upload videos**.
3. Select `ReturnRight-AI-demo.mov`.
4. Title: `ReturnRight AI — concept walkthrough`.
5. Description: `Synthetic demo for the Amazon Developer Hackathon 2026. Sample orders and policies only. No real merchant submission, refund, or Alexa+ integration.`
6. Audience: No, it is not made for kids.
7. Visibility: **Unlisted**.
8. Publish, then copy the `https://www.youtube.com/watch?v=...` URL into the Devpost **Video demo link** field.

Do not set the video to Public unless you want it public. Unlisted is enough for judges who have the link.

## Check before you paste the link

- The banner saying synthetic data is readable.
- You showed NW-1001, a cited policy rule, a case, and a follow-up.
- You said merchant submission and Alexa+ are not done.
- The URL opens in a private window while signed out.
