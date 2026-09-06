---
source: quizzer-codebase
status: verified
last_verified: 2026-09-06
confidence: high
---

# Arena — Live Quiz Battles

## Overview

Arena is Quizzer's live, real-time quiz battle mode. A teacher (host)
creates a room from an approved quiz pack, shares a six-character room
code, and runs the game live while players answer questions for
speed-based points. Arena is completely separate from the graded exam
flow — it has its own scoring, its own history, and its own section
in Analytics.

Think of it as a Kahoot-style live quiz competition built into Quizzer.

Users may call this: live quiz, battle, game, competition, quiz game,
Kahoot-style, live quiz battle.

## Step-by-Step UI Guide: Hosting an Arena Live Quiz Battle

Step 1 — Open Arena:
In the left sidebar, click Arena (it has a game/battle icon). The
Arena workspace loads showing your quiz packs and game history.

Step 2 — Create or select a quiz pack:
Option A — Quick-create: click the Create Quiz Pack button (emerald-
green). Add questions using the editor — choose types (MCQ, True/False,
Multi-Select, One Word Answer, Guess It), type the question, add
options, mark the correct answer. For Guess It questions, upload an
image (click the image upload area). Review and approve all questions.

Option B — Use existing: if you already have a quiz with Approved
questions, select it from the pack library.

Step 3 — Configure battle settings:
Before creating the room, a settings panel appears. Set:

Timer per question — click the dropdown to choose: 10, 15, 20, 30,
45, 60, 90, or 120 seconds (default 20).
Show leaderboard — choose "After each question" or "End only."
Negative marking — toggle switch (off by default). When on, wrong
answers lose 250 points.
Randomize questions — toggle (on by default).
Randomize options — toggle (on by default).
Team mode — toggle (off by default). When on, players are auto-assigned
to teams: Red, Blue, Green, Gold.

Step 4 — Create the room:
Click the Create Room button (emerald-green). Quizzer generates a
six-character room code and a join URL.

Step 5 — Share the code:
The room screen shows the code prominently. You have options:
Copy Code — click to copy the six-character code.
Copy Link — click to copy the join URL.
QR Code — a scannable QR code is displayed.
Project this screen on a classroom display so students can see the code.

Step 6 — Wait for players:
Players appear in the lobby as they join. Their nicknames show up in
the player list. You can kick a player by clicking the X next to their
name.

Step 7 — Start the game:
When enough players have joined (at least one), click the Start button
(emerald-green). A countdown appears (default 5 seconds), then the
first question displays.

Step 8 — Control the game:
During each question, you see the question and a timer counting down.
After the timer expires or you click Reveal, the correct answer is
shown. Use the control buttons:

Reveal — end the current question early and show the answer.
Next — advance to the next question (available after revealing).
Skip — skip this question entirely.
Pause/Resume — freeze or unfreeze the timer.
End — finish the game immediately.

Step 9 — View results:
After the last question, the final leaderboard appears with rankings.
Click Export to save game history as CSV, JSON, or Google Sheets.

## How Arena Differs from Graded Exams

Graded exams: asynchronous. Publish a link, students take it on their
own time, individually timed, detailed proctoring, graded results in
the Results tab.

Arena: synchronous. Everyone plays at the same time. Host controls the
pace. Speed-based scoring with streaks. No detailed proctoring.
Results go to game history, not the exam Results tab.

Arena packs do not appear in the regular exam Results or Monitoring
tabs. Arena analytics appear in a separate section of the Analytics
workspace.

## Roles in Arena

Host: the teacher who creates and runs the room. Controls game flow
(start, reveal answers, next question, pause, skip, end). Needs a
teacher-role Quizzer account.

Player: anyone who joins with the room code and a nickname. No account
required. Answers questions in real time for points.

Spectator: read-only viewer with a spectator ticket. Can see the live
question, timer, and leaderboard but cannot answer or control the game.
Useful for projecting the game on a screen.

## Creating an Arena Quiz Pack

Arena uses quiz packs, not regular published exams. Two ways to get one:

Quick-create: go to Arena in the sidebar, use the quick-create flow.
Add questions (Multiple Choice, True/False, Multi-Select, One Word
Answer, or Guess It), review and approve them. Guess It questions can
include an image.

Use an existing quiz: if you have a quiz with approved questions,
you can use it as an Arena pack. All questions must be Approved before
hosting.

Question types supported in Arena:
- Multiple Choice (MCQ) — pick one correct answer
- True/False — binary choice
- Multi-Select — pick all correct answers
- One Word Answer (Short Answer) — type a short answer, fuzzy-matched
- Guess It (Short Answer with image) — see an image, type the answer

Long Answer questions are not supported in Arena and are skipped.

## Hosting a Game

Step 1: select or create a quiz pack in the Arena workspace.
Step 2: configure battle settings (timer, scoring, team mode, etc.).
Step 3: create the room. You get a room code and join URL.
Step 4: share the code with players (copy, QR code, or link).
Step 5: wait in the lobby for players to join.
Step 6: start the game when ready (at least one player must have joined).

During the game, the host controls the flow:
- Reveal: end the current question early and show the correct answer.
- Next: advance to the next question (after revealing).
- Skip: skip a question entirely.
- Pause/Resume: freeze or unfreeze the timer.
- Restart question: reset the current question and let players answer
  again.
- End: finish the game immediately.

The host can also kick players from the lobby (banned for the rest of
that room's lifetime).

Only one active room per host is allowed at a time.

## Joining a Game (Players)

Players open the join link or go to the Arena join page and enter the
room code manually.

They choose a nickname (2 to 20 characters, alphanumeric plus spaces,
underscores, and hyphens). Nicknames must be unique in the room.
Profanity and reserved names are filtered.

If the host linked a Google Classroom course, players can pick from the
class roster instead of typing a nickname.

Players can join during the lobby phase. If the game has already started,
they can join mid-game only if the allow_late_join setting is on (it is
on by default, though the host cannot toggle it from the UI currently).

Maximum players per room: 100 (configurable by the server).

## Spectating

The host can generate a spectator ticket (valid for 4 hours). Spectators
see the live question, timer, and leaderboard but cannot submit answers
or send host commands.

Spectator mode is useful for projecting the game on a classroom screen.

## Game Settings

Timer per question: how many seconds players have to answer each
question. Default: 20 seconds. Options: 10, 15, 20, 30, 45, 60, 90,
or 120 seconds.

Auto-start countdown: seconds of countdown before the first question
after the host clicks Start. Default: 5 seconds. Options: 3, 5, or 10.

Show leaderboard: when to show the leaderboard to players.
- After each question (default): everyone sees standings after every
  question is revealed.
- End only: players see standings only at the end. The host always
  sees interim standings on their dashboard.

Negative marking: deduct 250 points for wrong answers. Default: off.

Randomize questions: shuffle the question order. Default: on.

Randomize options: shuffle answer option order. Default: on.

Team mode: automatically assign players to teams (Red, Blue, Green,
Gold) in round-robin order. Team score is the sum of member scores.
Default: off.

Settings can only be changed in the lobby before the game starts.
Once the game begins, settings are locked.

## Scoring

Arena scoring is entirely server-side. Players cannot manipulate scores.

Correct answer:
Base score: 1000 points.
Speed bonus: up to 1000 additional points based on how quickly the
player answered. Faster answers get more bonus points.
Streak multiplier: answering consecutive questions correctly builds a
streak. Each streak question adds 0.1x to the multiplier, capping at
1.5x (streak of 5).

Wrong answer:
0 points by default.
Minus 250 points if negative marking is enabled.

Timeout (no answer before timer expires):
0 points. Streak resets.

Formula: score = (1000 + speed_bonus) multiplied by streak_multiplier.

Players can change their answer while the timer is running. The server
reverses the previous score before applying the new one.

A small grace period (0.5 seconds) after the timer expires still
accepts answers.

## Leaderboard

Rankings are determined by:
1. Highest total score
2. Tiebreaker: lowest total response time (faster overall wins ties)
3. Tiebreaker: alphabetical nickname

When team mode is on, team standings are also shown alongside individual
rankings.

## Game Lifecycle

Waiting (lobby): host and players are in the room. Host can edit
settings, kick players, share the code. Game has not started.

Countdown: host clicked Start. A countdown runs before the first
question.

Playing: questions are shown one at a time. Timer runs per question.
Host controls flow (reveal, next, skip, pause).

Finished: game is over. Final leaderboard shown. Winner screen
displayed. Host can export results.

## Lobby Idle Timeouts

If the lobby has zero players for 5 minutes, the host gets a warning.
If still empty after 2 more minutes, the room closes automatically.

Hard timeout: any room older than 15 minutes total closes regardless
of activity.

If the host disconnects mid-game: players see a warning. After 60
seconds of warning, then 5 minutes of total absence, the game
auto-ends.

## Scheduled Battles

Teachers can schedule Arena battles in advance. A scheduled battle
saves the quiz pack and settings for a future time.

Start modes:
- Timed: set a specific date and time.
- Anytime: start whenever before the expiry.

Expiry: 1, 2, 7, or 30 days.

When the time comes, the host clicks Start to create the live room
from the saved settings. Expired schedules auto-archive.

## Game History

After a game ends, a summary is saved to permanent storage:

Winner and top rankings (top 20).
Per-question stats: accuracy (what percentage got it right), option
distribution, average response time.
Overall stats: average score, hardest question, fastest player, team
standings.

Game history is accessible from the Arena workspace and can be exported
to CSV, JSON, or Google Sheets.

Arena game history also appears in the Analytics workspace under the
Arena section.

## Google Classroom Integration

If a Classroom course is linked during room creation:
- Players can pick their name from the class roster when joining.
- After the game ends, a Classroom announcement with top 3 results can
  be posted automatically.

## Arena Quiz Limits (Beta)

During the public beta, every user gets Elite-level Arena caps. Post-
beta, these limits will vary by subscription tier:

Explorer: 1 quiz pack, 10 questions per pack, 2 images per pack.
Professional: unlimited packs, 25 questions, 10 images.
Elite: unlimited packs, 50 questions, 20 images.

Image size limit: 2 MB per image. Images are converted to WebP.

These numbers may change when beta ends.

## Common Questions

What is Arena?
A live quiz battle mode where a teacher hosts a room, shares a code,
and players answer questions in real time for points. Like Kahoot but
built into Quizzer.

How is Arena different from a regular exam?
Arena is live and synchronous (everyone plays at the same time with
speed-based scoring). Regular exams are asynchronous (students take
them on their own time with individual timers and proctoring).

How do I host an Arena game?
Go to Arena in the sidebar, select or create a quiz pack, configure
settings, create the room, share the code, and start when players
have joined.

Do players need a Quizzer account?
No. Players just need the room code and a nickname.

Can students retake an Arena game?
Arena games are live events, not stored exams. Each game is a one-time
session. You can host a new game with the same pack.

Where do Arena scores show up?
In Arena game history and the Arena section of Analytics. NOT in the
regular exam Results tab.

How does scoring work?
1000 base points for a correct answer, plus up to 1000 speed bonus
for faster answers, multiplied by a streak bonus (up to 1.5x for 5
in a row). Wrong answers score 0 (or -250 with negative marking).

Can I have teams?
Yes. Enable team mode in the battle settings. Players are automatically
assigned to teams (Red, Blue, Green, Gold). Team score is the sum of
member scores.

What happens if I lose connection as the host?
Players see a warning. You have about 5 minutes to reconnect before
the game auto-ends.

Can spectators answer questions?
No. Spectators are read-only. They see the game but cannot submit
answers or control it.

## Related Features

See also: Analytics (Arena section), Google Classroom Integration,
Terminology (Arena), Creating Exams (question types)
