/* Dr. Mia dental demo — scripted patient-conversation simulation. Synthetic data only. */
(function () {
  "use strict";

  var log = document.getElementById("chat-log");
  var form = document.getElementById("chat-form");
  var input = document.getElementById("chat-text");
  var chips = document.getElementById("chip-row");

  var state = "idle";       // idle | book_day | book_time | book_name
  var booking = {};

  function scrollDown() { log.scrollTop = log.scrollHeight; }

  function addMsg(text, who) {
    var d = document.createElement("div");
    d.className = "msg " + (who || "bot");
    d.textContent = text;
    log.appendChild(d);
    scrollDown();
    return d;
  }

  function botSay(text, delay) {
    var t = document.createElement("div");
    t.className = "msg bot typing";
    t.innerHTML = "<span></span><span></span><span></span>";
    log.appendChild(t);
    scrollDown();
    setTimeout(function () {
      t.remove();
      addMsg(text, "bot");
    }, delay || 700);
  }

  function setChips(list) {
    chips.innerHTML = "";
    list.forEach(function (c) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.textContent = c;
      b.onclick = function () { sendUser(c); };
      chips.appendChild(b);
    });
  }

  var DEFAULT_CHIPS = ["Book a cleaning", "What are your hours?", "Do you take my insurance?", "I have a toothache"];

  /* ---------- intent matching ---------- */
  function matchIntent(text) {
    var t = text.toLowerCase();
    if (/\b(hour|open|close|when|time)\b/.test(t) && !/book/.test(t)) return "hours";
    if (/(insurance|delta|aetna|cigna|metlife|ppos?|coverage|cover)/.test(t)) return "insurance";
    if (/(book|appointment|cleaning|schedule|visit|checkup|check-up)/.test(t)) return "booking";
    if (/(price|cost|much|whitening|implant|crown|filling)/.test(t)) return "pricing";
    if (/(hurt|pain|ache|emergency|broken|chipped|swollen|bleed)/.test(t)) return "emergency";
    if (/(where|location|address|park|direction)/.test(t)) return "location";
    if (/(human|person|real|staff|receptionist|call me|manager|dentist)/.test(t)) return "human";
    if (/(hi|hello|hey|good morning|good afternoon|salam)/.test(t)) return "greeting";
    if (/(thank|thanks|great|awesome|perfect)/.test(t)) return "thanks";
    return "fallback";
  }

  var REPLIES = {
    greeting: "Hi there! I'm Mia, the front desk assistant at Lakeside Family Dental. I can help with hours, booking, insurance, or prices — what's on your mind?",
    hours: "We're open Mon–Fri 8am–6pm and Sat 9am–2pm. Evenings fill up fast — want me to check a slot for you?",
    insurance: "We take most PPO plans — Delta, Aetna, Cigna, MetLife and more. If you tell me your plan name, I'll have the front desk verify your exact coverage before your visit. Which plan do you have?",
    pricing: "A few common ones: cleaning & exam from $129, whitening from $299, and most fillings $150–$350 before insurance. For anything exact, the front desk gives a written estimate — want me to ask them to call you?",
    location: "You'll find us at 4210 Lakeside Drive — free parking right out front, and we're on the 12 bus line. Anything else I can help with?",
    thanks: "Anytime! That's what I'm here for. Anything else — booking, hours, insurance?"
  };

  function handleIntent(intent, raw) {
    switch (intent) {
      case "booking":
        state = "book_day";
        botSay("Happy to help you book! Which day works best — a weekday or Saturday?");
        setChips(["Weekday", "Saturday"]);
        break;
      case "emergency":
        botSay("I'm sorry you're dealing with that — let's get you seen fast. We hold same-day emergency slots every morning. Is the pain severe right now, or can it wait until morning?");
        setChips(["It's severe", "It can wait until morning"]);
        addSysNote("Mia flags this as urgent and notifies the front desk immediately.");
        break;
      case "human":
        escalate("You asked for a human — of course.");
        break;
      case "fallback":
        botSay("I want to make sure you get the right answer, so I'm passing this to our front desk team — they'll reply here within minutes during office hours. Meanwhile I can help with hours, booking, insurance, or prices. What do you need?");
        addSysNote("Mia escalates to the front desk with the full conversation attached.");
        setChips(DEFAULT_CHIPS);
        break;
      default:
        botSay(REPLIES[intent] || REPLIES.fallback);
        setChips(DEFAULT_CHIPS);
    }
  }

  function addSysNote(text) {
    setTimeout(function () { addMsg(text, "sys"); }, 900);
  }

  function escalate(prefix) {
    botSay((prefix ? prefix + " " : "") + "Looping in our front desk team now — they'll pick this up within minutes during office hours. Is there anything you'd like me to pass along to them?");
    addSysNote("Escalation sent to front desk · full transcript attached.");
    setChips(DEFAULT_CHIPS);
  }

  /* ---------- booking flow ---------- */
  function handleBooking(raw) {
    var t = raw.toLowerCase();
    if (state === "book_day") {
      booking.day = /saturday/.test(t) ? "Saturday" : "a weekday";
      state = "book_time";
      botSay("Got it — " + booking.day + ". Morning or afternoon?");
      setChips(["Morning", "Afternoon"]);
    } else if (state === "book_time") {
      booking.time = /afternoon/.test(t) ? "afternoon" : "morning";
      state = "book_name";
      botSay("Perfect. And what's the name for the booking?");
      setChips([]);
    } else if (state === "book_name") {
      booking.name = raw.trim() || "Guest";
      state = "idle";
      botSay("Thanks " + booking.name.split(" ")[0] + "! I've sent your request — " + booking.day + " " + booking.time + ", cleaning & exam — to our front desk. They'll confirm your exact time here within the hour. Anything else?");
      addSysNote("Booking request routed to front desk for confirmation.");
      setChips(DEFAULT_CHIPS);
      booking = {};
    }
  }

  /* ---------- input ---------- */
  function sendUser(text) {
    text = (text || "").trim();
    if (!text) return;
    addMsg(text, "user");
    input.value = "";
    if (state !== "idle") { handleBooking(text); return; }
    if (/^(it's severe|severe)$/i.test(text)) {
      botSay("Understood — I'm marking this urgent and the front desk will call you right now. If there's swelling, trouble swallowing, or trauma, please head to urgent care. Stay on the line — they're being notified.");
      addSysNote("URGENT flag raised · front desk paged.");
      setChips(DEFAULT_CHIPS);
      return;
    }
    if (/wait until morning/i.test(text)) {
      state = "book_day";
      botSay("Okay — I'll get you the first morning slot. Weekday or Saturday?");
      setChips(["Weekday", "Saturday"]);
      return;
    }
    handleIntent(matchIntent(text), text);
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    sendUser(input.value);
  });

  /* ---------- demo buttons ---------- */
  document.getElementById("missed-call-btn").addEventListener("click", function () {
    addMsg("Missed call · 7:42pm (after hours)", "sys");
    setTimeout(function () {
      addMsg("Hi, this is Mia from Lakeside Family Dental — sorry we missed your call! Were you trying to book a visit, or is something urgent? Reply here and I'll take care of it.", "bot");
    }, 800);
    setTimeout(function () {
      addMsg("Auto follow-up sent 2 minutes after the missed call — before the caller dials the next clinic.", "sys");
    }, 1600);
  });

  document.getElementById("escalate-btn").addEventListener("click", function () {
    addMsg("Can I talk to someone about my bill?", "user");
    setTimeout(function () { escalate("Of course."); }, 600);
  });

  /* ---------- greeting ---------- */
  setTimeout(function () {
    addMsg("Hi! I'm Mia — I answer questions and take booking requests for Lakeside Family Dental, right here on WhatsApp. Try me: ask about hours, insurance, or tap “Book a cleaning”.", "bot");
    setChips(DEFAULT_CHIPS);
  }, 500);
})();
