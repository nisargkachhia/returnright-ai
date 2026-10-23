# Devpost submission checklist

Fill these fields only with links you have actually created. This file does not invent a GitHub, YouTube, or live-app URL.

## Try it out link

**Current value:** blank.

No live application URL was verified, and this folder is not yet a GitHub repository. After you create and push the repository, paste that repository URL here. A GitHub link is the honest “built with” destination until the app is deployed.

Git is initialized on `main`, and no remote exists. There is no commit yet because this machine has no `user.name` or `user.email`. Set those yourself, then commit. Do not skip this step.

```bash
cd "/Users/nisarg/Documents/ReturnRight AL"
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git add -A
git status
git commit -m "$(cat <<'EOF'
feat: add ReturnRight AI demo and submission assets

Ship the synthetic return-resolution demo, MCP server, and Devpost materials needed for the hackathon submission.
EOF
)"
```

Create the public repository only when you want it published:

```bash
cd "/Users/nisarg/Documents/ReturnRight AL"
gh repo create returnright-ai --public --source=. --remote=origin --description "ReturnRight AI — synthetic return and warranty resolution demo" --push
git remote -v
```

If `gh` is not logged in, run `gh auth login` first. If you prefer the website, create an empty public repo named `returnright-ai` with no README, then:

```bash
git remote add origin git@github.com:YOUR_USER/returnright-ai.git
git push -u origin main
```

Replace `YOUR_USER` with your GitHub username. Copy the URL GitHub shows. Do not guess it.

## Video demo link

**Current value:** PENDING.

Record with [video-recording-guide.md](video-recording-guide.md), upload to YouTube as **Unlisted**, and paste the real watch URL. If Devpost requires the field before you upload, finish the upload first. An empty or placeholder URL is worse than waiting a few minutes.

## Project media

Upload this file in the Devpost gallery:

- Path: `docs/media/returnright-ai-concept.png`
- Recommended filename: `returnright-ai-concept.png`
- Caption: `Concept artwork for ReturnRight AI. The running demo uses synthetic orders and sample policies. It does not contact merchants or issue refunds.`

Optional extra images: take your own screenshots of the DEMO MODE banner, the policy result, and the case follow-up while the app is running. Do not upload the unused Vite graphic at `frontend/src/assets/hero.png`.

## Paste-ready text

**Name:** ReturnRight AI

**Elevator pitch:** An AI-powered consumer resolution agent that helps people navigate returns, warranties, and purchase issues by checking policies, preparing claims, and tracking follow-ups through conversational AI.

**Built with:** React, TypeScript, Vite, Python, FastAPI, SQLite, Model Context Protocol (official Python SDK, Streamable HTTP)

**About, short:** ReturnRight AI helps a shopper find a purchase, check a documented policy, prepare a claim, and track the follow-up. The hackathon demo implements that workflow on synthetic orders through a real MCP server. Confirmed actions are labeled demo only. Free-form conversation, live merchant submission, and an Alexa+ integration are planned and not claimed as working.
