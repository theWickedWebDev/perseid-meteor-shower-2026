---
description: Independently verify a project's claims by recomputing them from source, not by reading the code and reasoning about it
argument-hint: "[path, subsystem, or 'everything'] (optional)"
---

# /audit

Audit $ARGUMENTS. If nothing was named, audit whatever changed most recently — check
`git log` and `git status` first.

## The stance

**A review reads the code and reasons about it. An audit recomputes the claim from an
independent source and compares.** Only the second kind finds anything. Every real finding
worth having comes from building your own answer and discovering it disagrees.

You are auditing *without* the builder's context, and that is the point. Do not ask what
was intended. Read what is there, work out what it claims, and check whether the claim is
true.

Assume the code runs. Assume the author was competent. The errors that survive to this
stage are not syntax — they are **numbers that are wrong, methods that measure something
other than what they name, and confidence that exceeds the evidence.**

## Method

### 1. Read cold, all of it

Read the whole subsystem before forming a view — code, docstrings, generated output, and
any prose the project publishes about itself. Note every number that a person would act on.
Those are your targets.

### 2. Recompute the load-bearing numbers yourself

This is the whole job. For each headline figure, build an independent path to it:

- Physical/astronomical claims → implement the standard algorithm yourself and compare
- Statistical claims → pull the raw data and redo the statistic
- Geometric claims → project the coordinates yourself
- Detection claims → cross-match the detections against ground truth

Write the check into your scratchpad directory and run it. **Do not accept a number because
the code that produced it looks correct.** Two independent implementations agreeing is
evidence; one implementation reading plausibly is not.

Budget most of your effort here. Reading is cheap and finds little.

### 3. Audit the assertions, not just the logic

Docstrings and documentation that claim validation are where errors hide, because nobody
re-checks them:

> "Validated against the almanac: computes sunset 20:03…"

Check it. In this project that claim was false — the function returned 20:07, and the
docstring was comparing a geometric zero-crossing against an upper-limb almanac value. The
function was fine; the stated validation was coincidence.

Same for any sentence of the form *"this was checked and it agrees."*

### 4. Separate three different kinds of wrong

Findings are much more useful when you say which one this is:

| Kind | Example |
|---|---|
| **The number is wrong** | A moon fiducial off by 2.7°, propagating into a derived measurement |
| **The method measures the wrong thing** | A "long-range skill" column averaging only the leads each model happens to reach, so short-range models win by being absent |
| **The confidence exceeds the evidence** | A 1-point effect reported as a finding when the series' own internal inconsistency sets the noise floor at ±6 |

The third is the most common and the least often caught.

### 5. Interrogate the sample

For any statistic, ask and answer explicitly:

- What is *n*, really? Seven models scoring the same 51 hours is not 357 observations.
- Are the samples independent? Consecutive hours of one night are one draw.
- What is the noise floor, and is the claimed effect bigger than it?
- Is there a **no-skill baseline**? A model beating "always say overcast" by three points on
  an overcast week has done almost nothing. Compute persistence and climatology baselines
  and put the result next to the headline.
- Is there a confound? Check whether the ranking is measuring the thing it names or
  something correlated with it.

### 6. Run the degraded paths

The happy path is tested by existing. The others are not:

- Kill each external dependency and rebuild. What silently disappears?
- Feed empty inputs to any fallback. Empty list into `x[-1]` is a real bug that only fires
  on the day everything else is already broken.
- Find code that **has never executed** — a compaction step gated on a threshold the data
  has not yet crossed, a branch that fires on the 13th entry. Force it in a copy and check
  it does what the docstring promises. Say so if it has never run.

### 7. Absence is not a clean bill of health

Look for indicators that render only when data exists. A missing badge beside a present one
reads as *"checked, nothing to report"* when it means *"not checked."* This is a whole class
of finding and it is nearly invisible from inside.

### 8. Security and privacy pass

- Are secrets gitignored **and absent from every commit reachable from any ref**? Check the
  history, not just the working tree.
- Do committed images carry EXIF GPS?
- Are there third-party assets, and are they attributed?
- Do tracked artifacts include generated logs, derived binaries, or caches?

### 9. Be willing to overturn yourself

If you make a strong claim, try hardest to break your own. In this project the biggest
finding — that an ensemble's joint probability was inflated by decorrelation — was wrong,
and pulling 30 years of reanalysis proved it wrong. **Say so plainly and lead with it.**
An audit that never retracts is not being run honestly.

## Report format

Lead with whichever is true:

- the finding that would change what someone does, or
- the correction to your own earlier finding

Then:

**What holds up.** Specific, with the numbers you reproduced. This is not padding — it tells
the reader which parts they no longer need to worry about, and it proves you actually
checked rather than skimmed.

**Findings, ranked by whether anyone would act differently.** For each:
- what is wrong, in one sentence
- the evidence, as the two numbers side by side
- the concrete consequence
- the fix, if it is short

**What is still weak.** Things that are not errors but limit what the work can support.

Rules:
- Show both numbers. "Doc says 209.1°, computed 203.7°" beats "the moon position is wrong."
- Cite `file:line`.
- Say when a finding changes nothing today but would on a marginal day.
- Do not pad the list. Six real findings beat twenty with fourteen nits.
- No moralising, no praise sandwich. State it and move on.

## Do not

- Fix anything unless asked. Audit, report, then offer.
- Accept "it looks right" as verification.
- Report a finding you have not reproduced. If you suspect but could not check, say that.
- Soften a finding because the surrounding work is good. Say the work is good *and* state
  the finding at full strength.
- Rewrite the author's conclusions. Show where the evidence stops supporting them.
