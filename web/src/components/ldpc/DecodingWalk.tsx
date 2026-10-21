"use client";

import { useState } from "react";

// A single-check teaching fixture, not a learner run or a full NR decoder.
const channel = [4, -0.2, 3];
const ruleMessages = channel.map((_, destination) => {
  const others = channel.filter((_, i) => i !== destination);
  return others.reduce((sign, value) => sign * (value < 0 ? -1 : 1), 1) * Math.min(...others.map(Math.abs));
});
const combined = channel.map((value, i) => value + ruleMessages[i]);
const labels = ["1 · Radio clues", "2 · Test the rule", "3 · Other bits advise", "4 · Revise the guess", "5 · Test again"];
const explanations = [
  {title: "The middle bit is only a weak guess", text: "The receiver has three noisy observations. The first and last strongly suggest 0. The middle only slightly suggests 1. If we keep just the guesses, we get [0, 1, 0]. We have not checked the coding rule yet."},
  {title: "The guesses disagree with a known rule", text: "Both transmitter and receiver know this rule: these three bits must contain an even number of ones. Our guesses [0, 1, 0] contain one 1, so the rule fails. This tells us something is inconsistent—not which bit is wrong."},
  {title: "Ask what the OTHER two bits suggest", text: "To advise the middle bit, this rule looks only at the first and last bits. Both strongly suggest 0. If those two are 0, the middle must also be 0 to make the rule pass. So the rule sends evidence favoring 0 to the middle bit. It does not use the middle bit's own guess as fresh evidence."},
  {title: "The new evidence outweighs the weak guess", text: "The middle bit's radio clue weakly favors 1. The rule's evidence more strongly favors 0. The decoder combines them, and the middle bit's guess changes to 0. This is an evidence-based update, not a command to flip any bit in a failing rule."},
  {title: "The revised guesses now satisfy the rule", text: "After each bit combines its radio clue with its rule message, the guesses are [0, 0, 0]. There are zero ones—an even number—so the rule passes. We found a valid candidate. We still do not know for certain that it is what was sent."}
];

export function DecodingWalk() {
  const [step, setStep] = useState(0);
  const revised = step >= 3;
  const values = revised ? combined : channel;
  return <div className="decoding-walk">
    <h2>How can a rule help a weak guess?</h2>
    <p>Follow one small example. Three received bits share one even-parity rule. The receiver does not know the original bits.</p>
    <p className="decode-legend">A <strong>guess</strong> says 0 or 1. <strong>Confidence</strong> says how strongly the observation supports that guess. The numbers are explained below; you do not need their formula yet.</p>
    <div className="ldpc-stepper" aria-label="Decoding walkthrough steps">{labels.map((label,i) => <button key={label} aria-pressed={step === i} className={step === i ? "selected" : ""} onClick={() => setStep(i)}>{label}</button>)}</div>
    <div className="decode-scene" aria-live="polite">
      {revised && <p className="decode-legend">Now put numbers to the evidence: <strong>positive favors 0; negative favors 1.</strong> A larger distance from zero means stronger support. Read the labels if you prefer; the calculation method is optional below.</p>}
      <div className="decode-bits">{values.map((score,i) => <div className={`decode-bit ${i === 1 ? "decode-target" : ""}`} key={i}><small>{["First bit · b0", "Middle bit · b1", "Last bit · b2"][i]}</small><strong>Guess: {score < 0 ? 1 : 0}</strong><span>{Math.abs(score) < 1 ? "Weak" : "Strong"} support for {score < 0 ? 1 : 0}</span>{revised && <><small>Radio clue: {channel[i] > 0 ? "+" : ""}{channel[i]}</small><small>Combined: {score > 0 ? "+" : ""}{score.toFixed(1)}</small></>}</div>)}</div>
      <div className="decode-rule"><strong>Known rule: an even number of ones</strong><span>b0 XOR b1 XOR b2 must equal 0</span>{step === 0 ? <p>Not checked yet.</p> : <p>{step === 4 ? "0 XOR 0 XOR 0 = 0 → rule passes" : step === 3 ? "New candidate ready; next, test it again." : "0 XOR 1 XOR 0 = 1 → rule fails"}</p>}</div>
      {step === 2 && <div className="decode-message"><div className="decode-arrows" aria-label="First and last bits provide evidence to the rule, which sends advice to the middle bit"><span>b0: likely 0</span><span>b2: likely 0</span><strong>↓ other bits’ evidence ↓</strong><span className="decode-check">EVEN-PARITY RULE</span><strong>↓ advice for b1 ↓</strong><span>“These clues favor you being 0.”</span></div><p>The rule’s message is advice computed by the decoder. It is not a new bit arriving over the radio.</p></div>}
      {step === 3 && <div className="decode-combine"><div><small>Original radio clue</small><strong>−0.2</strong><span>weakly favors 1</span></div><b aria-hidden="true">+</b><div><small>Rule’s new evidence</small><strong>+3</strong><span>favors 0</span></div><b aria-hidden="true">=</b><div><small>Combined confidence</small><strong>+2.8</strong><span>now favors 0</span></div></div>}
      <div className="primer-worked"><h3>{explanations[step].title}</h3><p>{explanations[step].text}</p></div>
    </div>
    <details className="decode-maths"><summary>What do +4, −0.2 and +3 mean? Show the optional maths</summary>
      <p>These signed confidence scores are called LLRs. In this course, positive favors bit 0, negative favors bit 1, and a larger distance from zero means stronger support. Zero is undecided; our code chooses 0 for that tie. These are not probabilities or raw radio amplitudes.</p>
      <p>The radio scores stay fixed: [+4, −0.2, +3]. A separate combined score is updated. For the middle bit, a Min-Sum check uses ONLY the other scores, +4 and +3. Both favor 0, and the weaker magnitude is 3, so its advice is +3. This approximation limits the message by its weakest input.</p>
      <pre>{"b1 radio clue        = -0.2\nrule → b1 message    = +3.0\nb1 combined score    = +2.8\npositive score       → guess 0"}</pre>
      <p>The rule also advises the other bits. Their combined scores are +3.8 and +2.8, so their guesses remain 0. This is why the final candidate is [0, 0, 0], not just a guessed change to the middle bit. The later assignments derive the signs, minima, and exclusion of each destination.</p>
    </details>
    <p className="ldpc-caption">Big picture: radio clues → test the known rule → exchange evidence → revise guesses → test again. A real LDPC graph has many overlapping rules and repeats this process up to a stopping condition or limit. This single-rule example illustrates one update, not guaranteed error correction.</p>
    <nav className="primer-toolbar" aria-label="Worked example navigation"><button disabled={step === 0} onClick={() => setStep(s => s-1)}>← Back one step</button><span>Step {step+1} of {labels.length}</span><button disabled={step === labels.length-1} onClick={() => setStep(s => s+1)}>Next step →</button></nav>
  </div>;
}
