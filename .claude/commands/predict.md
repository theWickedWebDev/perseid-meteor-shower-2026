---
description: Make an independent, falsifiable forecast of what a project's own data will say on a future date, without seeing anyone else's prediction
argument-hint: "[target date, e.g. 2026-08-09] (optional)"
---

# /predict

## Before anything else: are you in a fresh session?

This command only works from a cold start. **Stop and check what is already in your
context.** If any of the following is true, you are contaminated:

- you have discussed this project's forecast, numbers, or predictions in this session
- you have read files from `predictions/`
- someone has pasted a prediction, an audit, or a summary of either
- you built any part of this project

A prediction made with another model's reasoning already in mind is not independent, and
independence is the entire point — it is what makes scoring several of them mean anything.

**If you are contaminated, say so and ask the user whether to continue anyway** before
writing anything. They may want it regardless, for a reason you do not have; that is their
call to make knowingly, not yours to make silently. Name specifically what you already know,
so they can judge how much it matters.

If your context is clean, carry on and do not mention this section again.

---

Forecast what this project's data will say on $ARGUMENTS. If no date was given, read
`predictions/README.md`'s target if one exists — **without reading any prediction file** —
or pick the date where the project's own skill curve flattens and say why you chose it.

## Do not read

```
predictions/          the whole directory, including its README
```

Other models have written predictions there. Reading any of it destroys the point, which is
independent forecasts scored against each other. Do not open them, grep them, or let them
reach your context sideways — `git log -p`, `git show`, `git diff`, and anything that dumps
a tree will all leak them. **Do not list the directory**: filenames alone reveal when the
others were written, and a README beside them may summarise what they said.

If their contents reach you by accident, say so plainly at the top of your output. A
contaminated forecast that admits it is still useful. One that hides it is worthless.

## The stance

**You are forecasting the numbers, not the world.** The question is what this project's own
figures will read on the target date — not what the weather, the market, or the system under
observation will actually do. Those are different questions and conflating them produces a
prediction that cannot be scored.

Commit to numbers. An interval wide enough to be unfalsifiable is not a forecast, it is a
hedge wearing a forecast's clothes. Prefer being visibly wrong to being uselessly safe.

## Method

### 1. Establish where you are

Run `date`. Read the newest timestamp in the project's own history file. **Do not assume the
current date** — this command is run repeatedly and the answer changes every time.

State explicitly: today's date and time, how many observations exist, and the lead time from
now to the target. A prediction is only interpretable alongside how much data it had.

### 2. Find what the project already knows about its own reliability

Most projects that log data also measure their own error somewhere. Look for it before
predicting. If the project knows its error at a given lead, that number bounds how confident
you may reasonably be, and predicting more precisely than the measured error is a claim you
cannot support.

If no such measurement exists, say so — and derive one if the data allows.

### 3. Distinguish the machinery from the phenomenon

Two kinds of prediction, and the first is nearly free:

| Kind | Example | Scores |
|---|---|---|
| **Machinery** | which data sources come into range, how sample sizes grow, what stays byte-identical | cleanly, regardless of what the world does |
| **Phenomenon** | the actual measured values | only against reality |

Make both. Machinery predictions are where you can be precise, and a surprise there is a
**bug, not a forecast miss** — which is worth more than being right about the weather.

If a 30-year statistic changes between now and the target, something is broken.

### 4. Check the rules that derive one number from another

Where the project renders a verdict, a label, or a category from a number, **read the code
and find the threshold.** Do not infer it from what is currently displayed.

Predicting a value and an incompatible label is an internal contradiction, and it is an easy
mistake: a model once predicted a probability and, two rows later, a verdict wording that its
own shipped thresholds could not produce from that probability. Both rows cannot be right.
The number is the prediction; the label follows from it by a rule you can read.

### 5. Anchor on the base rate, not on today

Today's figure is one draw from a noisy process. If the project has a climatology, a
long-run average, or a historical base rate, that is the anchor. Then ask how far the current
value sits from it, and compare that distance to the measured error at this lead.

**When a forecast claims an anomaly the size of its own error bar, expect the anomaly to
shrink.** That is not pessimism, it is regression — and it is the single most useful prior
available at long lead.

### 6. Name the one thing that would most change your forecast, and does not exist

Before writing, ask: **what would I want to know that this project does not measure?**

You have just spent real effort inside this data. That makes you briefly well placed to see
what is missing — better placed than the people who built it, who have stopped noticing the
shape of their own instrument.

Name **one** thing. Not a list; a list is a way of avoiding a judgement. The single
measurement, framing, or comparison whose absence most limits what can be concluded, and say
concretely what it would change.

Good answers are specific and buildable:

- a quantity that exists in an API already being called, but is not pulled
- a comparison between two things already logged separately
- a control or baseline that would show whether an effect is real
- a way of slicing existing data that would separate two explanations currently confounded
- a question the project's own documentation raises and then does not answer

Weak answers, which you should discard: "more data", "more models", "better validation",
anything requiring hardware, anything that is really a restatement of a known limitation.

This is run repeatedly by different models. If several independently name the same gap, that
is a strong signal. If you name something nobody else does, that is worth more than agreeing
about a number.

### 7. State what would show you wrong

Concretely, in advance, so it cannot be argued away afterwards. Name the observation that
would falsify each significant claim. If you cannot name one, the claim is not a prediction.

## Output

Write `predictions/<timestamp>.md`, where `<timestamp>` is when you write it in
`YYYY-MM-DDTHHMM` form, taken from `date`. Write it directly — do not list the directory
first.

Include:

1. **When you wrote it**, how many observations existed, lead time to each target.
2. **Numbers with ranges.** Every figure a person would act on.
3. **Reasoning, briefly.** What you weighted. Mark guesses as guesses.
4. **Machinery predictions**, separated from the phenomenon ones.
5. **The one missing measurement**, under a heading of its own — what it is, why it matters,
   and roughly how to get it. Keep it to a paragraph.
6. **What would show you wrong.**
7. **A scoring table** with a blank "actual" column.
8. **A machine-readable block at the very end**, so a scorer can grade it without parsing
   prose. Match whatever schema previous runs used if the project has a scorer; otherwise:

````
```yaml
written: 2026-08-06T09:15
snapshots: 41
lead_days: [5, 6, 7]
missing: one short phrase naming the gap you identified
<one line per predicted quantity>
```
````

## Rules

- Distinguish what you measured from what you assumed. Say which is which.
- Do not hedge in prose what you already stated as a number.
- If the data contradicts the project's own documentation, say so — that is a finding, and
  it is worth more than the forecast.
- Do not read the other predictions to "check you are reasonable." Being an outlier is
  informative; converging on someone else's answer is not.
- Run this from a fresh session every time. Two predictions from one session are one
  prediction with extra steps.
- If you revise between writing and the target, record the correction and its reason inside
  the file. Never silently edit a prediction after the fact.

## Do not

- Predict the phenomenon when you were asked to predict the numbers.
- Give an interval so wide it cannot be wrong.
- Assume today's date, the current values, or a threshold — check all three.
- Pad with predictions nobody would act on.
